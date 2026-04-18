from math import radians, cos, sin, asin, sqrt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.firestore_client import get_firestore
from app.routers.auth import get_current_user
from app.models import User
import random as _random

STADIUM_GROUPS = {
    "Nou Mestalla": ["aeroport","av_cid","benaguasil","benicalap","beniferri","benimamet","burjassot","burjassot_godella","betera","campament","campanar","campus","cantereria","carolines_fira","el_clot","empalme","entrepins","faitanar","fuente_jarro","torre_virrey","garbi","godella","horta_vella","eliana","la_canyada","la_coma","la_vallesa","pobla_vallbona","lliria","manises","mas_rosari","masies","massarrojos","mislata","mislata_almassil","montesol","nou_octubre","palau_congressos","paterna","quart_poblet","riba_roja","masia_traver","valencia_la_vella","la_presa","la_cova","fondo_benaguasil","gallipont_torre_virrey","font_barranc","ll_llarga","tomas_valiente","santa_gemma","a_punt","sant_joan","la_granja","rocafort","rosas","salt_aigua","santa_rita","torrent","torrent_avinguda","turia","v_andres_estelles","vicent_andres","angel_guimera","tvv","reus","marxalenes","transits","florista","fira_valencia"],
    "Roig Arena": ["alacant","alberic","alginet","amado_granell","ausias_march_carlet","benimodo","carlet","castello","ciudad_arts","ciutat_arts","collegi_vedat","font_almaguer","jesus","masalaves","montortal","moreres","natzaret","oceanografic","omet","paiporta","patraix","picanya","picassent","quatre_carreres","realon","espioca","l_alcudia","bailen","safranar","sant_isidre","sant_ramon","valencia_sud","joaquin_sorolla"],
    "Mestalla": ["alameda","amistat","aragon","ayora","colon","dr_lluch","facultats","grau_marina","grau_canyamelar","la_cadena","la_carrasca","maritim","neptu","placa_espanya","pont_fusta","russafa","tarongers","univ_politecnica","vicent_zaragoza","xativa","serradora","eugenia_vines","les_arenes","mediterrani","cabanyal","betero","platja_malva_rosa","platja_les_arenes","canyamelar","francesc_cubells"],
    "Estadi Ciutat de Valencia": ["albalat_sorells","alboraya_palmaret","alboraya_peris","alfauir","almassera","benimaclet","estadi_ciutat","foios","pobla_farnals","machado","massamagrell","meliana","moncada_alfara","museros","orriols","primat_reig","rafelbunyol","sant_miquel_reis","seminari_ceu","tossal_rei","trinitat","sagunt"],
}

TURIA_POINTS = [(39.473901844336275,-0.40580977380914257),(39.475875111148056,-0.39650531107182324),(39.47798076891964,-0.39103464995848797),(39.48107653918475,-0.3834406055526129),(39.48220327431968,-0.38028502205102055),(39.48125863905595,-0.3770557099638838),(39.478629526317334,-0.37210114895394597),(39.47609137083586,-0.3683704824788944),(39.47323441236276,-0.365952184842581),(39.47037733658648,-0.36356337864147575),(39.46605165997359,-0.3612188095918059),(39.463023526335526,-0.35946406923399743),(39.4608149547715,-0.35776831174492707),(39.45916417258277,-0.3543473053361762),(39.45755889162093,-0.35157511048480977),(39.455008581954985,-0.34775596970500783),(39.45412050577638,-0.34495428342197915),(39.45425713361816,-0.3421378514216714)]

def dist_to_segment(p, a, b):
    from math import cos, radians, sqrt
    cosLat = cos(radians(a[0]))
    ax, ay = (a[1]-p[1])*111000*cosLat, (a[0]-p[0])*111000
    bx, by = (b[1]-p[1])*111000*cosLat, (b[0]-p[0])*111000
    dx, dy = bx-ax, by-ay
    t = max(0, min(1, -(ax*dx+ay*dy)/(dx*dx+dy*dy+1e-10)))
    return sqrt((ax+t*dx)**2+(ay+t*dy)**2)

def dist_to_turia(lat, lon):
    return min(dist_to_segment((lat,lon), TURIA_POINTS[i], TURIA_POINTS[i+1]) for i in range(len(TURIA_POINTS)-1))

STADIUMS = [
    {"name": "Mestalla", "lat": 39.4747, "lon": -0.3583},
    {"name": "Nou Mestalla", "lat": 39.4894, "lon": -0.3964},
    {"name": "Estadi Ciutat de Valencia", "lat": 39.4947, "lon": -0.3642},
    {"name": "Roig Arena", "lat": 39.4492, "lon": -0.3642},
]

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

    # For match_turia: store hunter's distance to river
    if body.question_id == "match_turia":
        hunter_data = game["players"].get(str(user.id), {})
        hunter_lat = hunter_data.get("lat")
        hunter_lon = hunter_data.get("lon")
        if not hunter_lat:
            raise HTTPException(status_code=400, detail="Ubicación del cazador no disponible")
        hunter_dist = dist_to_turia(hunter_lat, hunter_lon)
        await game_doc.reference.update({
            "pending_question": {
                "question_id": body.question_id,
                "category": "match",
                "title": q.get("title", ""),
                "description": q.get("description", ""),
                "reward": reward,
                "status": "pending",
                "answer": None,
                "asked_by": str(user.id),
                "hunter_turia_dist": hunter_dist,
                "hunter_lat": hunter_lat,
                "hunter_lon": hunter_lon,
            }
        })
        return {"question_id": body.question_id, "category": "match", "answer": None, "reward": reward, "pending": True}

    # For match_stadium: store hunter's nearest stadium
    if body.question_id == "match_stadium":
        hunter_data = game["players"].get(str(user.id), {})
        hunter_lat = hunter_data.get("lat")
        hunter_lon = hunter_data.get("lon")
        if not hunter_lat:
            raise HTTPException(status_code=400, detail="Ubicación del cazador no disponible")
        nearest = min(STADIUMS, key=lambda s: haversine(hunter_lat, hunter_lon, s["lat"], s["lon"]))
        await game_doc.reference.update({
            "pending_question": {
                "question_id": body.question_id,
                "category": "match",
                "title": q.get("title", ""),
                "description": q.get("description", ""),
                "reward": reward,
                "status": "pending",
                "answer": None,
                "asked_by": str(user.id),
                "hunter_stadium": nearest["name"],
            }
        })
        return {"question_id": body.question_id, "category": "match", "answer": None, "reward": reward, "pending": True}

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
            "radar_pending_result": {"answer": answer, "radius_m": pending["radar_radius_m"]},
        })
        return {"action": "answered", "answer": answer, "reward": pending.get("reward")}

    # match_turia: compare fugitive station distance to river vs hunter distance
    if pending.get("question_id") == "match_turia":
        fugitive_station_id = game.get("fugitive_station")
        if not fugitive_station_id:
            raise HTTPException(status_code=400, detail="Fugitivo no tiene estación seleccionada")
        st = await db.collection("metro_stations").document(fugitive_station_id).get()
        st_data = st.to_dict()
        fugitive_dist = dist_to_turia(st_data["lat"], st_data["lon"])
        hunter_dist = pending["hunter_turia_dist"]
        answer = fugitive_dist <= hunter_dist  # fugitive closer to river
        overlay = {"type": "turia", "hunter_dist": hunter_dist, "inside": answer}
        overlays = game.get("radar_overlays", []) + [overlay]
        await game_doc.reference.update({
            "pending_question": {**pending, "status": "answered", "answer": answer},
            "used_questions": game.get("used_questions", []) + [pending["question_id"]],
            "radar_overlays": overlays,
            "radar_pending_result": {"answer": answer, "turia_dist": round(hunter_dist)},
        })
        return {"action": "answered", "answer": answer, "reward": pending.get("reward")}

    # match_stadium: compute fugitive's nearest stadium using station
    if pending.get("question_id") == "match_stadium":
        fugitive_station_id = game.get("fugitive_station")
        if not fugitive_station_id:
            raise HTTPException(status_code=400, detail="Fugitivo no tiene estación seleccionada")
        hunter_stadium = pending["hunter_stadium"]
        # Find fugitive's stadium group
        fugitive_stadium = next((name for name, stations in STADIUM_GROUPS.items() if fugitive_station_id in stations), None)
        answer = fugitive_stadium == hunter_stadium
        # Overlay: stations to discard (all stations NOT in hunter's group if miss, none if hit)
        if answer:
            # Hit: fugitive is in same zone — discard all other zones
            discarded = [s for name, stations in STADIUM_GROUPS.items() if name != hunter_stadium for s in stations]
        else:
            # Miss: fugitive is NOT in hunter's zone — discard hunter's zone
            discarded = STADIUM_GROUPS.get(hunter_stadium, [])
        overlay = {"type": "stadium", "stadium": hunter_stadium, "inside": answer, "discarded_stations": discarded}
        overlays = game.get("radar_overlays", []) + [overlay]
        await game_doc.reference.update({
            "pending_question": {**pending, "status": "answered", "answer": answer},
            "used_questions": game.get("used_questions", []) + [pending["question_id"]],
            "radar_overlays": overlays,
            "radar_pending_result": {"answer": answer, "stadium": hunter_stadium},
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
    pending = game.get("pending_question") or {}
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


class DismissRadar(BaseModel):
    game_id: str

@router.post("/dismiss-radar-result")
async def dismiss_radar_result(body: DismissRadar, user: User = Depends(get_current_user)):
    db = get_firestore()
    await db.collection("games").document(body.game_id).update({"radar_pending_result": None})
    return {"ok": True}


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
