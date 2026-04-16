from datetime import datetime, timezone
from math import radians, cos, sin, asin, sqrt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.firestore_client import get_firestore
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter()

HIDE_RADIUS_DEFAULT = 150  # metres


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in metres between two GPS points."""
    R = 6_371_000
    φ1, φ2 = radians(lat1), radians(lat2)
    dφ = radians(lat2 - lat1)
    dλ = radians(lon2 - lon1)
    a = sin(dφ / 2) ** 2 + cos(φ1) * cos(φ2) * sin(dλ / 2) ** 2
    return 2 * R * asin(sqrt(a))


class LocationUpdate(BaseModel):
    game_id: str
    lat: float
    lon: float


class SelectStation(BaseModel):
    game_id: str
    station_id: str


@router.post("/location")
async def update_location(body: LocationUpdate, user: User = Depends(get_current_user)):
    db = get_firestore()
    await db.collection("games").document(body.game_id).update({
        f"players.{user.id}.lat": body.lat,
        f"players.{user.id}.lon": body.lon,
        f"players.{user.id}.location_updated_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True}


@router.post("/select-station")
async def select_station(body: SelectStation, user: User = Depends(get_current_user)):
    """Fugitive selects their hiding station. Validates they are within radius."""
    db = get_firestore()
    game_doc = await db.collection("games").document(body.game_id).get()
    if not game_doc.exists:
        raise HTTPException(status_code=404, detail="Game not found")
    game = game_doc.to_dict()

    if game.get("fugitive_station_confirmed"):
        raise HTTPException(status_code=400, detail="Station already confirmed")

    # Get station coords
    station_doc = await db.collection("metro_stations").document(body.station_id).get()
    if not station_doc.exists:
        raise HTTPException(status_code=404, detail="Station not found")
    station = station_doc.to_dict()

    player = game["players"].get(str(user.id), {})
    player_lat = player.get("lat")
    player_lon = player.get("lon")
    if player_lat is None or player_lon is None:
        raise HTTPException(status_code=400, detail="Player location unknown")

    dist = haversine(player_lat, player_lon, station["lat"], station["lon"])
    radius = game.get("hide_radius_m", HIDE_RADIUS_DEFAULT)
    if dist > radius:
        raise HTTPException(status_code=400, detail=f"Too far from station ({dist:.0f}m > {radius}m)")

    await game_doc.reference.update({
        "fugitive_station": body.station_id,
        "fugitive_station_confirmed": True,
        "status": "hunting",
        "hunt_start": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "station_id": body.station_id}


@router.get("/ranking")
async def get_ranking():
    """Top players by total time hidden."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, func
    from app.database import AsyncSessionLocal
    from app.models import GameHistory, User as UserModel

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserModel.username, func.sum(GameHistory.time_hidden_seconds).label("total"))
            .join(GameHistory, GameHistory.user_id == UserModel.id)
            .group_by(UserModel.username)
            .order_by(func.sum(GameHistory.time_hidden_seconds).desc())
            .limit(20)
        )
        rows = result.all()
    return [{"username": r.username, "total_seconds": r.total} for r in rows]
