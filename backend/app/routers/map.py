from fastapi import APIRouter
from app.firestore_client import get_firestore

router = APIRouter()


@router.get("/stations")
async def get_stations():
    db = get_firestore()
    docs = await db.collection("metro_stations").get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


@router.get("/lines")
async def get_lines():
    db = get_firestore()
    docs = await db.collection("metro_lines").get()
    return [{"id": d.id, **d.to_dict()} for d in docs]
