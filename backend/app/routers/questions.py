from math import radians, cos, sin, asin, sqrt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.firestore_client import get_firestore
from app.routers.auth import get_current_user
from app.models import User
import random as _random

router = APIRouter()

QUESTION_REWARDS = {
    "radar": {"draw": 3, "keep": 2},
    "match": {"draw": 3, "keep": 1},
    "photo": {"draw": 2, "keep": 1},
}


def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000
    φ1, φ2 = radians(lat1), radians(lat2)
    dφ = radians(lat2 - lat1)
    dλ = radians(lon2 - lon1)
    a = sin(dφ / 2) ** 2 + cos(φ1) * cos(φ2) * sin(dλ / 2) ** 2
    return 2 * R * asin(sqrt(a))


@router.get("/list")
async def list_questions():
    db = get_firestore()
    docs = await db.collection("questions").get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


class AskQuestion(BaseModel):
    game_id: str
    question_id: str
    radar_radius_m: float | None = None


@router.post("/ask")
async def ask_question(body: AskQuestion, user: User = Depends(get_current_user)):
    db = get_firestore()
    game_doc = await db.collection("games").document(body.game_id).get()
    if not game_doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = game_doc.to_dict()

    if body.question_id in game.get("used_questions", []):
        raise HTTPException(status_code=400, detail="Question already used")

    q_doc = await db.collection("questions").document(body.question_id).get()
    if not q_doc.exists:
        raise HTTPException(status_code=404, detail="Question not found")
    q = q_doc.to_dict()
    category = q["category"]
    reward = QUESTION_REWARDS.get(category, {"draw": 2, "keep": 1})

    # For radar: store as pending too — fugitive sees effect before accepting
    if category == "radar":
        hunter_data = game["players"].get(str(user.id), {})
        hunter_lat = hunter_data.get("lat")
        hunter_lon = hunter_data.get("lon")
        if not hunter_lat:
            raise HTTPException(status_code=400, detail="Ubicación del cazador no disponible")
        radius = body.radar_radius_m or 1000
        await game_doc.reference.update({
            "pending_question": {
                "question_id": body.question_id,
                "category": "radar",
                "title": q.get("title", ""),
                "description": q.get("description", ""),
                "reward": reward,
                "status": "pending",
                "answer": None,
                "asked_by": str(user.id),
                "radar_radius_m": radius,
                "hunter_lat": hunter_lat,
                "hunter_lon": hunter_lon,
            }
        })
        return {"question_id": body.question_id, "category": "radar", "answer": None, "reward": reward, "pending": True}

    # For match/photo: store as pending, fugitive must respond
    await game_doc.reference.update({
        "pending_question": {
            "question_id": body.question_id,
            "category": category,
            "title": q.get("title", ""),
            "description": q.get("description", ""),
            "reward": reward,
            "status": "pending",  # pending | answered | vetoed | randomized
            "answer": None,
            "asked_by": str(user.id),
        }
    })
    return {"question_id": body.question_id, "category": category, "answer": None, "reward": reward, "pending": True}


class RespondQuestion(BaseModel):
    game_id: str
    action: str  # "answer" | "veto" | "randomize"
    answer: bool | None = None  # for match


@router.post("/respond")
async def respond_question(body: RespondQuestion, user: User = Depends(get_current_user)):
    db = get_firestore()
    game_doc = await db.collection("games").document(body.game_id).get()
    if not game_doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = game_doc.to_dict()
    pending = game.get("pending_question")
    if not pending or pending.get("status") != "pending":
        raise HTTPException(status_code=400, detail="No pending question")

    player = game["players"].get(str(user.id), {})
    hand = player.get("hand", [])

    if body.action == "veto":
        # Requires veto card
        veto_card = next((c for c in hand if c.startswith("veto_")), None)
        if not veto_card:
            raise HTTPException(status_code=400, detail="No tienes carta de veto")
        new_hand = [c for c in hand if c != veto_card]
        await game_doc.reference.update({
            "pending_question": {**pending, "status": "vetoed"},
            "used_questions": game.get("used_questions", []) + [pending["question_id"]],
            f"players.{user.id}.hand": new_hand,
        })
        return {"action": "vetoed"}

    if body.action == "randomize":
        rand_card = next((c for c in hand if c.startswith("randomize_")), None)
        if not rand_card:
            raise HTTPException(status_code=400, detail="No tienes carta de randomizar")
        # Get another question of same category
        all_q = await db.collection("questions").where("category", "==", pending["category"]).get()
        used = game.get("used_questions", [])
        available = [d for d in all_q if d.id != pending["question_id"] and d.id not in used]
        new_hand = [c for c in hand if c != rand_card]
        if available:
            new_q = _random.choice(available).to_dict()
            new_q_id = _random.choice(available).id
            await game_doc.reference.update({
                "pending_question": {
                    **pending,
                    "question_id": new_q_id,
                    "title": new_q.get("title", ""),
                    "description": new_q.get("description", ""),
                    "status": "pending",
                },
                f"players.{user.id}.hand": new_hand,
            })
            return {"action": "randomized", "new_question": new_q}
        await game_doc.reference.update({f"players.{user.id}.hand": new_hand})
        return {"action": "randomized", "new_question": None}

    # action == "answer" — for radar compute answer; for others store fugitive's answer
    if pending.get("category") == "radar":
        fugitive_station_id = game.get("fugitive_station")
        if not fugitive_station_id:
            raise HTTPException(status_code=400, detail="Fugitivo no tiene estación seleccionada")
        st = await db.collection("metro_stations").document(fugitive_station_id).get()
        st_data = st.to_dict()
        dist = haversine(pending["hunter_lat"], pending["hunter_lon"], st_data["lat"], st_data["lon"])
        answer = dist <= pending["radar_radius_m"]
        overlay = {
            "hunter_lat": pending["hunter_lat"],
            "hunter_lon": pending["hunter_lon"],
            "radius_m": pending["radar_radius_m"],
            "inside": answer,  # True = fugitive is inside circle
        }
        overlays = game.get("radar_overlays", []) + [overlay]
        await game_doc.reference.update({
            "pending_question": {**pending, "status": "answered", "answer": answer},
            "used_questions": game.get("used_questions", []) + [pending["question_id"]],
            "radar_overlays": overlays,
        })
        return {"action": "answered", "answer": answer, "reward": pending.get("reward")}

    # match/photo
    await game_doc.reference.update({
        "pending_question": {**pending, "status": "answered", "answer": body.answer},
        "used_questions": game.get("used_questions", []) + [pending["question_id"]],
    })
    return {"action": "answered", "reward": pending.get("reward")}


class ClaimReward(BaseModel):
    game_id: str
    chosen_card_ids: list[str]  # cards fugitive keeps (max = reward["keep"])


@router.post("/claim-reward")
async def claim_reward(body: ClaimReward, user: User = Depends(get_current_user)):
    """Fugitive draws cards and keeps chosen ones after answering a question."""
    db = get_firestore()
    game_doc = await db.collection("games").document(body.game_id).get()
    game = game_doc.to_dict()
    pending = game.get("pending_question", {})
    reward = pending.get("reward", {"draw": 2, "keep": 1})

    if len(body.chosen_card_ids) > reward["keep"]:
        raise HTTPException(status_code=400, detail=f"Puedes quedarte máximo {reward['keep']} cartas")

    player = game["players"].get(str(user.id), {})
    hand = player.get("hand", [])
    new_hand = (hand + body.chosen_card_ids)[:5]  # max 5 cards

    await game_doc.reference.update({
        f"players.{user.id}.hand": new_hand,
        "pending_question": None,
    })
    return {"hand": new_hand}


class GuessStation(BaseModel):
    game_id: str
    station_id: str


PENALTIES = [
    {"minutes": 5, "cards": 1}, {"minutes": 15, "cards": 1},
    {"minutes": 30, "cards": 2}, {"minutes": 60, "cards": 3},
    {"minutes": 120, "cards": 3},
]


@router.post("/guess-station")
async def guess_station(body: GuessStation, user: User = Depends(get_current_user)):
    db = get_firestore()
    game_doc = await db.collection("games").document(body.game_id).get()
    if not game_doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = game_doc.to_dict()
    correct = game.get("fugitive_station") == body.station_id
    errors = game.get("errors", 0)
    if correct:
        await game_doc.reference.update({"status": "round_end", "found_station": body.station_id})
        return {"correct": True}
    penalty = PENALTIES[min(errors, len(PENALTIES) - 1)]
    await game_doc.reference.update({
        "errors": errors + 1,
        "discarded_stations": game.get("discarded_stations", []) + [body.station_id],
        "penalty_minutes": game.get("penalty_minutes", 0) + penalty["minutes"],
    })
    return {"correct": False, "penalty": penalty}
