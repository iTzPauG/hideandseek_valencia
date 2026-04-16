from google.cloud import firestore

_db = None


def get_firestore() -> firestore.AsyncClient:
    global _db
    if _db is None:
        _db = firestore.AsyncClient()
    return _db
