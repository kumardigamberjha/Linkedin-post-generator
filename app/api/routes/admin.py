import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.db.database import (
    count_history,
    count_trending_topics,
    get_admin_stats,
    get_history,
    get_trending_topics,
)
from app.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def fetch_stats(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    stats = get_admin_stats(current_user["id"])
    return stats


@router.get("/posts")
async def fetch_posts(
    limit: int = 50, offset: int = 0, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    role = current_user.get("role", "user")
    user_id = None if role == "admin" else current_user["id"]

    items = get_history(limit=limit, offset=offset, user_id=user_id)
    total = count_history(user_id=user_id)
    return {"items": items, "total": total}


@router.get("/trends")
async def fetch_trends(
    limit: int = 50, offset: int = 0, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    # Trending topics are shared, but we could restrict if needed.
    # Leaving it globally accessible since trends are just external news articles.
    items = get_trending_topics(limit=limit, offset=offset)
    total = count_trending_topics()
    return {"items": items, "total": total}
