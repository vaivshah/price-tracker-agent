"""
Application factory — creates and configures the FastAPI app.

Single Responsibility: only wires middleware, telemetry, routers, and startup hooks.
Zero business logic lives here.
"""
import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.logger import setup_logging
from src.database.session import engine, Base
from src.scheduler import start_scheduler

# --- Bootstrap logging before anything else ---
setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Build and return the fully configured FastAPI application."""

    # Create tables (fast iteration — replace with Alembic for production)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="Price Tracker Agent")

    # --- Telemetry ---
    Instrumentator().instrument(app).expose(app)

    # --- Register channel routers (Open/Closed: add new channels here) ---
    from src.channels.whatsapp import router as whatsapp_router
    from src.channels.telegram import router as telegram_router
    app.include_router(whatsapp_router, prefix="/webhook")
    app.include_router(telegram_router, prefix="/webhook")

    # --- Register report serving ---
    from src.reports.server import router as reports_router
    app.include_router(reports_router)

    # --- Register services with the orchestrator ---
    _register_services()

    # --- Startup hooks ---
    @app.on_event("startup")
    def on_startup():
        start_scheduler()
        logger.info("Application started")

    # --- Health check ---
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}

    return app


def _register_services() -> None:
    """Wire service implementations to the orchestrator (Dependency Inversion)."""
    from src.services.orchestrator import orchestrator
    from src.services.price_check import PriceCheckService
    from src.services.tracking import TrackingService
    from src.services.research import ResearchService
    from src.services.alternatives import AlternativesService
    from src.services.review import ReviewService

    orchestrator.register("price_check", PriceCheckService())
    orchestrator.register("track", TrackingService())
    orchestrator.register("research", ResearchService())
    orchestrator.register("alternatives", AlternativesService())
    orchestrator.register("review", ReviewService())

    logger.info("All services registered with orchestrator")


app = create_app()
