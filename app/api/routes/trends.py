import asyncio
import logging
from typing import List

import httpx
from fastapi import APIRouter, Depends
from app.api.routes.auth import get_current_user
from pydantic import BaseModel

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class TrendsResponse(BaseModel):
    serpapi: List[str]
    duckduckgo: List[str]
    hackernews: List[str]
    quora: List[str]


async def fetch_serpapi_trends(niche: str, api_key: str | None) -> List[str]:
    if not api_key:
        logger.warning("SERP_API_KEY is not set. Skipping SerpAPI.")
        return []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search.json",
                params={
                    "q": f"{niche} news OR trend",
                    "tbm": "nws",  # Google News
                    "tbs": "qdr:d",  # Past 24 hours
                    "api_key": api_key,
                    "num": 5,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            # When using tbm=nws, results are in 'news_results'
            for item in data.get("news_results", data.get("organic_results", [])):
                title = item.get("title", "")
                if title.endswith(" - Quora"):
                    title = title.replace(" - Quora", "")
                if title and len(results) < 3:
                    results.append(title)
            return results
    except Exception as e:
        logger.error(f"SerpAPI fetch error: {e}")
        return []


async def fetch_ddg_trends(niche: str) -> List[str]:
    if not DDGS:
        logger.warning("duckduckgo_search is not installed.")
        return []
    try:
        # Running synchronous DDGS in a thread pool to avoid blocking the event loop
        def _search():
            with DDGS() as ddgs:
                # Use DDG News for exact trending topics today
                results = list(ddgs.news(niche, timelimit="d", max_results=5))
                return [r.get("title", "") for r in results if r.get("title")][:3]

        return await asyncio.to_thread(_search)
    except Exception as e:
        logger.error(f"DDG fetch error: {e}")
        return []


async def fetch_hn_trends(niche: str) -> List[str]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://hn.algolia.com/api/v1/search_by_date",
                params={
                    "query": niche,
                    "tags": "story",
                    "numericFilters": "points>20",  # High quality recent stories
                    "hitsPerPage": 10,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for hit in data.get("hits", []):
                title = hit.get("title", "")
                if title and len(results) < 3:
                    results.append(title)
            return results
    except Exception as e:
        logger.error(f"Hacker News fetch error: {e}")
        return []


async def fetch_quora_trends(niche: str, api_key: str | None) -> List[str]:
    # We will use SerpAPI to search Quora
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search.json",
                params={
                    "q": f"site:quora.com {niche}",
                    "tbs": "qdr:w",  # Past week to get fresh discussions
                    "api_key": api_key,
                    "num": 5,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("organic_results", []):
                title = item.get("title", "")
                link = item.get("link", "")

                # Quora titles are often truncated by Google. The full question is in the URL slug.
                if "quora.com/" in link:
                    try:
                        import urllib.parse

                        # Example: https://www.quora.com/What-is-AI
                        path = link.split("quora.com/")[-1].split("?")[0].split("#")[0]
                        if path.startswith("unanswered/"):
                            path = path.replace("unanswered/", "")
                        # The slug is separated by hyphens
                        if path and "-" in path:
                            title = urllib.parse.unquote(path).replace("-", " ")
                            if not title.endswith("?"):
                                title += "?"
                    except Exception as e:
                        logger.error(f"Failed to parse Quora URL {link}: {e}")

                title = title.replace(" - Quora", "")
                if title and len(results) < 3:
                    results.append(title)
            return results
    except Exception as e:
        logger.error(f"Quora fetch error: {e}")
        return []


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(niche: str = "ai", current_user: dict = Depends(get_current_user)):
    settings = get_settings()

    serp_task = fetch_serpapi_trends(niche, settings.serp_api_key)
    ddg_task = fetch_ddg_trends(niche)
    hn_task = fetch_hn_trends(niche)
    quora_task = fetch_quora_trends(niche, settings.serp_api_key)

    serp, ddg, hn, quora = await asyncio.gather(
        serp_task, ddg_task, hn_task, quora_task
    )

    from app.db.database import save_trending_topics

    trends_dict = {"serpapi": serp, "duckduckgo": ddg, "hackernews": hn, "quora": quora}
    try:
        save_trending_topics(niche, trends_dict)
    except Exception as e:
        logger.error(f"Failed to save trending topics to DB: {e}")

    return TrendsResponse(**trends_dict)
