import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.api.routes.generate import router
from app.api.routes.history import router as history_router
from app.api.routes.linkedin import router as linkedin_router
from app.api.routes.trends import router as trends_router
from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.payments import router as payments_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="LinkedIn Post Generator",
    description="4-agent pipeline: Hook Finder → Post Writer → Editor → Approver",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(history_router)
app.include_router(
    linkedin_router
)  # no prefix — /callback must match registered LinkedIn redirect URI
app.include_router(trends_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
