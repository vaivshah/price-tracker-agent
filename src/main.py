"""
Application factory — creates and configures the FastAPI app.

Single Responsibility: only wires middleware, telemetry, routers, and startup hooks.
Zero business logic lives here.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.logger import setup_logging
from src.database.session import engine, Base
from src.scheduler import start_scheduler

# --- Bootstrap logging before anything else ---
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    
    # 1. Start Background Scheduler
    # We delay starting the scheduler until the DB is ready
    start_scheduler()
    logger.info("Application started")

    yield

    # Shutdown
    from src.scheduler import scheduler

    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")


def create_app() -> FastAPI:
    """Build and return the fully configured FastAPI application."""

    # Create tables (fast iteration — replace with Alembic for production)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="Price Tracker Agent", lifespan=lifespan)

    # --- Initialize & Register Services ---
    import src.services

    # --- Register channel routers (Open/Closed: add new channels here) ---
    from src.channels.whatsapp import router as whatsapp_router
    from src.channels.telegram import router as telegram_router
    app.include_router(whatsapp_router, prefix="/webhook")
    app.include_router(telegram_router, prefix="/webhook")

    # --- Register report serving ---
    from src.reports.server import router as reports_router
    app.include_router(reports_router)

    # --- Health check ---
    @app.get("/health")
    async def health_check():
        from src.services.agent import agent_client
        openclaw_ok = await agent_client.health_check()
        return {
            "status": "healthy" if openclaw_ok else "degraded",
            "openclaw_connected": openclaw_ok
        }

    # --- Telemetry ---
    # We instrument at the end so all routes (including routers) are registered
    Instrumentator().instrument(app).expose(app)

    return app


app = create_app()
