import random
import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.firestore_client import get_firestore
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter()


def _random_code(n=6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


class CreateGameRequest(BaseModel):
    rounds: int = 3


class JoinGameRequest(BaseModel):
    code: str


@router.post("/create")
async def create_game(body: CreateGameRequest, user: User = Depends(get_current_user)):
    db = get_firestore()
    code = _random_code()
    game_ref = db.collection("games").document()
    await game_ref.set({
        "code": code,
        "rounds": body.rounds,
        "current_round": 0,
        "status": "waiting",  # waiting | hiding | hunting | finished
        "created_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "players": {
            str(user.id): {"username": user.username, "role": None, "ready": False}
        },
        "round_order": [],
        "errors": 0,
        "used_questions": [],
        "discarded_stations": [],
        "fugitive_station": None,
        "fugitive_station_confirmed": False,
        "hide_radius_m": 150,
    })
    return {"game_id": game_ref.id, "code": code}


@router.post("/join")
async def join_game(body: JoinGameRequest, user: User = Depends(get_current_user)):
    db = get_firestore()
    query = db.collection("games").where("code", "==", body.code.upper()).where("status", "==", "waiting")
    docs = await query.get()
    if not docs:
        raise HTTPException(status_code=404, detail="Game not found or already started")
    doc = docs[0]
    game = doc.to_dict()
    if str(user.id) in game["players"]:
        return {"game_id": doc.id, "code": body.code.upper()}
    if len(game["players"]) >= 2:
        raise HTTPException(status_code=400, detail="Game is full")
    await doc.reference.update({
        f"players.{user.id}": {"username": user.username, "role": None, "ready": False}
    })
    return {"game_id": doc.id, "code": body.code.upper()}


@router.post("/{game_id}/start")
async def start_game(game_id: str, user: User = Depends(get_current_user)):
    db = get_firestore()
    ref = db.collection("games").document(game_id)
    doc = await ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = doc.to_dict()
    if game["created_by"] != user.id:
        raise HTTPException(status_code=403, detail="Only the creator can start")
    if len(game["players"]) < 2:
        raise HTTPException(status_code=400, detail="Need 2 players")

    player_ids = list(game["players"].keys())
    random.shuffle(player_ids)
    # Build round order: alternating roles for N rounds
    rounds = game["rounds"]
    round_order = []
    for i in range(rounds):
        fugitive = player_ids[i % 2]
        hunter = player_ids[(i + 1) % 2]
        round_order.append({"fugitive": fugitive, "hunter": hunter})

    await ref.update({
        "status": "hiding",
        "round_order": round_order,
        "current_round": 0,
        "hide_start": datetime.now(timezone.utc).isoformat(),
        f"players.{round_order[0]['fugitive']}.role": "fugitive",
        f"players.{round_order[0]['hunter']}.role": "hunter",
    })
    return {"round_order": round_order}


@router.post("/{game_id}/end")
async def end_game(game_id: str, user: User = Depends(get_current_user)):
    db = get_firestore()
    ref = db.collection("games").document(game_id)
    doc = await ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = doc.to_dict()
    if str(user.id) not in game.get("players", {}):
        raise HTTPException(status_code=403, detail="Not a player in this game")
    await ref.update({"status": "finished", "finished_at": datetime.now(timezone.utc).isoformat()})
    return {"ok": True}


@router.post("/{game_id}/caught")
async def caught(game_id: str, user: User = Depends(get_current_user)):
    """Hunter marks fugitive as caught. Advances to next round or ends game."""
    db = get_firestore()
    ref = db.collection("games").document(game_id)
    doc = await ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = doc.to_dict()

    current_round = game.get("current_round", 0)
    round_order = game.get("round_order", [])
    total_rounds = game.get("rounds", 1)

    # Calculate time hidden this round
    from datetime import datetime, timezone
    hunt_start = game.get("hunt_start")
    time_hidden = 0
    if hunt_start:
        time_hidden = int((datetime.now(timezone.utc) - datetime.fromisoformat(hunt_start)).total_seconds())

    # Record time for fugitive
    fugitive_id = round_order[current_round]["fugitive"]
    scores = game.get("scores", {})
    scores[fugitive_id] = scores.get(fugitive_id, 0) + time_hidden

    next_round = current_round + 1
    if next_round >= total_rounds:
        await ref.update({"status": "finished", "scores": scores})
        return {"status": "finished", "scores": scores}

    # Advance to next round — swap roles
    new_fugitive = str(round_order[next_round]["fugitive"])
    new_hunter = str(round_order[next_round]["hunter"])
    player_updates = {}
    for pid in game.get("players", {}):
        player_updates[f"players.{pid}.role"] = "fugitive" if str(pid) == new_fugitive else "hunter"
    await ref.update({
        "status": "hiding",
        "current_round": next_round,
        "scores": scores,
        "errors": 0,
        "used_questions": [],
        "discarded_stations": [],
        "fugitive_station": None,
        "fugitive_station_confirmed": False,
        "hide_radius_m": 150,
        "hide_start": datetime.now(timezone.utc).isoformat(),
        "hunt_start": None,
        "radar_overlays": [],
        "radar_pending_result": None,
        "pending_question": None,
        **player_updates,
    })
    return {"status": "next_round", "round": next_round}


@router.get("/active/mine")
async def get_active_games(user: User = Depends(get_current_user)):
    """Return games where this user is a player and status is not finished."""
    db = get_firestore()
    docs = await db.collection("games").where("status", "in", ["waiting", "hiding", "hunting", "changing_hideout"]).get()
    result = []
    for doc in docs:
        game = doc.to_dict()
        if str(user.id) in game.get("players", {}):
            result.append({"game_id": doc.id, "code": game.get("code"), "status": game.get("status"), "rounds": game.get("rounds")})
    return result


@router.get("/{game_id}")
async def get_game(game_id: str, user: User = Depends(get_current_user)):
    db = get_firestore()
    doc = await db.collection("games").document(game_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = doc.to_dict()
    # Never expose fugitive_station to hunters
    my_id = str(user.id)
    current_round = game.get("current_round", 0)
    round_order = game.get("round_order", [])
    if round_order and str(round_order[current_round]["hunter"]) == my_id:
        game["fugitive_station"] = None
    return {"game_id": game_id, **game}
