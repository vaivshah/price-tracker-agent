"""
Services package initialization.

Imports all services and registers them with the orchestrator singleton.
"""
from src.services.orchestrator import orchestrator
from src.services.price_check import PriceCheckService
from src.services.tracking import TrackingService
from src.services.research import ResearchService
from src.services.alternatives import AlternativesService
from src.services.review import ReviewService

# Register services
orchestrator.register("price_check", PriceCheckService())
orchestrator.register("tracking", TrackingService())
orchestrator.register("research", ResearchService())
orchestrator.register("alternatives", AlternativesService())
orchestrator.register("review", ReviewService())
