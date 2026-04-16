from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.firestore_client import get_firestore
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter()


@router.get("/list")
async def list_cards():
    db = get_firestore()
    docs = await db.collection("cards").get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


class PlayCard(BaseModel):
    game_id: str
    card_id: str
    target_question_id: str | None = None  # for veto/randomize


@router.post("/play")
async def play_card(body: PlayCard, user: User = Depends(get_current_user)):
    db = get_firestore()
    game_doc = await db.collection("games").document(body.game_id).get()
    if not game_doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = game_doc.to_dict()

    card_doc = await db.collection("cards").document(body.card_id).get()
    if not card_doc.exists:
        raise HTTPException(status_code=404, detail="Card not found")
    card = card_doc.to_dict()

    player_key = f"players.{user.id}"
    player_hand = game["players"][str(user.id)].get("hand", [])
    if body.card_id not in player_hand:
        raise HTTPException(status_code=400, detail="Card not in hand")

    updates = {f"{player_key}.hand": [c for c in player_hand if c != body.card_id]}

    card_type = card["type"]

    if card_type == "time":
        updates["bonus_minutes"] = game.get("bonus_minutes", 0) + card["minutes"]

    elif card_type == "expand_hideout":
        current = game.get("hide_radius_m", 150)
        updates["hide_radius_m"] = 500 if current == 150 else 1000

    elif card_type == "change_hideout":
        updates["status"] = "changing_hideout"
        updates["change_hideout_start"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        updates["fugitive_station"] = None
        updates["fugitive_station_confirmed"] = False
        updates["used_questions"] = []

    elif card_type == "freeze_hunters":
        updates["hunters_frozen_until"] = (
            __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            + __import__("datetime").timedelta(minutes=15)
        ).isoformat()

    elif card_type == "veto":
        if not body.target_question_id:
            raise HTTPException(status_code=400, detail="target_question_id required for veto")
        used = game.get("used_questions", [])
        if body.target_question_id not in used:
            used.append(body.target_question_id)
        updates["used_questions"] = used
        updates["vetoed_questions"] = game.get("vetoed_questions", []) + [body.target_question_id]

    elif card_type == "randomize":
        if not body.target_question_id:
            raise HTTPException(status_code=400, detail="target_question_id required for randomize")
        # Remove from used so it can be asked again
        used = [q for q in game.get("used_questions", []) if q != body.target_question_id]
        updates["used_questions"] = used

    elif card_type == "duplicate":
        if not body.target_question_id:
            raise HTTPException(status_code=400, detail="Provide card_id to duplicate as target_question_id")
        if len(player_hand) < 5:
            updates[f"{player_key}.hand"] = updates[f"{player_key}.hand"] + [body.target_question_id]

    await game_doc.reference.update(updates)
    return {"ok": True, "card_type": card_type}
