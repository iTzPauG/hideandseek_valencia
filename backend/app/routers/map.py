from fastapi import APIRouter, Response
from app.firestore_client import get_firestore

router = APIRouter()


@router.get("/stations")
async def get_stations(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    db = get_firestore()
    docs = await db.collection("metro_stations").get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


@router.get("/lines")
async def get_lines(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    db = get_firestore()
    docs = await db.collection("metro_lines").get()
    return [{**d.to_dict(), "id": d.id} for d in docs]
