import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.database import save_post, get_subscription, increment_post_count
from app.api.routes.auth import verify_token
from app.pipeline.orchestrator import LinkedInPipelineOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    niche: str = "ai"
    provider: str | None = None  # defaults to settings.default_provider


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/generate")
async def generate(req: GenerateRequest):
    settings = get_settings()
    provider = req.provider or settings.default_provider
    run_id = str(uuid.uuid4())[:8]

    orchestrator = LinkedInPipelineOrchestrator(llm_provider=provider, run_id=run_id)
    result = await orchestrator.run(topic=req.topic, niche=req.niche)
    try:
        save_post(topic=req.topic, niche=req.niche, provider=provider, result=result)
    except Exception:
        pass
    return result


@router.websocket("/ws/generate")
async def ws_generate(websocket: WebSocket):
    await websocket.accept()
    try:
        raw = await websocket.receive_text()
        payload = json.loads(raw)

        # 1. Authenticate user
        token = payload.get("token")
        if not token:
            await websocket.send_json(
                {"type": "error", "message": "Authentication required. Please log in."}
            )
            return

        try:
            user = verify_token(token)
        except ValueError as e:
            await websocket.send_json(
                {"type": "error", "message": f"Auth failed: {str(e)}"}
            )
            return

        # 2. Check Subscription & Quota
        sub = get_subscription(user["id"])
        if not sub or sub["status"] != "active":
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "You need an active subscription to generate posts.",
                }
            )
            return

        tier = sub["plan_tier"]
        posts_used = sub["posts_generated_this_month"]

        limits = {"free": 5, "basic": 28, "pro": 50, "max": 100}

        max_posts = limits.get(tier, 0)
        if posts_used >= max_posts:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"You have reached your monthly limit of {max_posts} posts on the {tier.title()} plan.",
                }
            )
            return

        # 3. Validate Provider Selection
        provider = payload.get("provider") or get_settings().default_provider

        if tier in ["free", "basic"]:
            p_lower = provider.lower()
            if not (
                "google" in p_lower or "gemini" in p_lower or "nvidia" in p_lower or "ollama" in p_lower or "gemma" in p_lower
            ):
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"The {tier.title()} plan only supports standard Cloud and Local models. Upgrade to use premium models.",
                    }
                )
                return

        topic = payload.get("topic", "")
        niche = payload.get("niche", "ai")
        run_id = str(uuid.uuid4())[:8]

        loop = asyncio.get_event_loop()

        def step_callback(agent_name: str, task_name: str, output: str) -> None:
            asyncio.run_coroutine_threadsafe(
                websocket.send_json(
                    {
                        "type": "step",
                        "agent": agent_name,
                        "task": task_name,
                        "output": output,
                    }
                ),
                loop,
            )

        orchestrator = LinkedInPipelineOrchestrator(
            llm_provider=provider, run_id=run_id, step_callback=step_callback
        )
        result = await orchestrator.run(topic=topic, niche=niche)

        # 4. Save and increment quota
        try:
            save_post(
                topic=topic,
                niche=niche,
                provider=provider,
                result=result,
                user_id=user["id"],
            )
            increment_post_count(user["id"])
        except Exception as e:
            logger.error(f"Failed to save post history or increment quota: {e}")

        await websocket.send_json({"type": "done", "result": result})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
