from fastapi import APIRouter, HTTPException
from app.db.database import count_history, get_history, get_post

router = APIRouter()


@router.get("/api/history")
def list_history(limit: int = 20, offset: int = 0):
    return {"items": get_history(limit, offset), "total": count_history()}


@router.get("/api/history/{item_id}")
def get_history_item(item_id: int):
    item = get_post(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item
