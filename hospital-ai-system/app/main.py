"""
Hospital AI System — FastAPI Application Entrypoint.

Initializes DB, Telegram bot (polling mode), and mounts all API routes.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import engine, Base
from app.db import models  # noqa: F401 — ensure all models are registered
from app.core.logger import logger
from app.api.routes import router as api_router


async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # --- Startup ---
    logger.info("application_starting")
    await init_db()

    # Start Telegram bot in polling mode
    try:
        from app.telegram.bot import start_polling, telegram_app
        await start_polling()
    except Exception as exc:
        logger.warning("telegram_bot_init_failed", error=str(exc))

    logger.info("application_started")
    yield

    # --- Shutdown ---
    logger.info("application_shutting_down")
    try:
        from app.telegram.bot import stop_polling
        await stop_polling()
    except Exception:
        pass
    await engine.dispose()
    logger.info("application_stopped")


app = FastAPI(
    title="Hospital AI System",
    description="AI-powered hospital management with CrewAI agents, RAG, and Telegram bot",
    version="0.2.0",
    lifespan=lifespan,
)

# Mount API routes
app.include_router(api_router)


# ──────────────────────────  Health Endpoints  ──────────────────────────


@app.get("/")
async def root():
    return {"status": "Hospital AI Core Running", "version": "0.2.0"}


@app.get("/health")
async def health():
    """Aggregate health check for all infrastructure services."""
    results = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        results["postgres"] = "ok"
    except Exception as exc:
        results["postgres"] = f"error: {exc}"

    try:
        from app.core.redis_client import redis_client
        redis_client.ping()
        results["redis"] = "ok"
    except Exception as exc:
        results["redis"] = f"error: {exc}"

    try:
        from app.rag.qdrant_client import client as qdrant
        qdrant.get_collections()
        results["qdrant"] = "ok"
    except Exception as exc:
        results["qdrant"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in results.values())
    return {"status": "healthy" if all_ok else "degraded", "services": results}


@app.get("/health/db")
async def health_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"postgres": "ok"}
    except Exception as exc:
        return {"postgres": f"error: {exc}"}


@app.get("/health/redis")
async def health_redis():
    try:
        from app.core.redis_client import redis_client
        redis_client.ping()
        return {"redis": "ok"}
    except Exception as exc:
        return {"redis": f"error: {exc}"}


@app.get("/health/qdrant")
async def health_qdrant():
    try:
        from app.rag.qdrant_client import client as qdrant
        qdrant.get_collections()
        return {"qdrant": "ok"}
    except Exception as exc:
        return {"qdrant": f"error: {exc}"}
