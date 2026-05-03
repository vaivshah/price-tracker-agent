"""
Intent router — classifies user messages and dispatches to the correct service.

Single Responsibility: this module only routes; it does not execute business logic.
Open/Closed: new intents are added by registering new services, not modifying this file.
"""
import logging
import time

from sqlalchemy.orm import Session

from src.channels.base import IncomingMessage
from src.core.telemetry import (
    intents_classified_total,
    service_executions_total,
    service_duration_seconds,
)
from src.database import store
from src.services.base import BaseService

logger = logging.getLogger(__name__)

# Intent keywords — will be replaced by LLM classification in the future
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "track": ["track", "monitor", "watch", "alert me", "notify me"],
    "research": ["research", "review", "opinion", "what do you think", "is it good"],
    "alternatives": ["alternative", "suggest", "similar", "budget", "instead of"],
    "review": ["my jobs", "my tracking", "cancel", "extend", "status", "list"],
    "price_check": ["price", "how much", "cost", "check"],
}


class Orchestrator:
    """Routes incoming messages to the correct service."""

    def __init__(self) -> None:
        self._services: dict[str, BaseService] = {}

    def register(self, intent: str, service: BaseService) -> None:
        """Register a service for a given intent (Open/Closed Principle)."""
        self._services[intent] = service
        logger.info("Registered service '%s' for intent '%s'", service.name, intent)

    def classify_intent(self, text: str) -> str:
        """Classify user intent from message text (keyword-based stub)."""
        text_lower = text.lower()
        for intent, keywords in _INTENT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return intent
        return "price_check"  # default fallback

    async def handle(self, message: IncomingMessage, db: Session) -> str:
        """
        Main entry point called by every channel adapter.

        1. Logs conversation
        2. Classifies intent
        3. Dispatches to registered service
        4. Records telemetry
        """
        # Persist inbound conversation turn
        store.log_conversation(
            db, message.user_identifier, message.channel, "user", message.text
        )

        intent = self.classify_intent(message.text)
        intents_classified_total.labels(intent=intent).inc()
        logger.info(
            "Classified intent='%s' for message from %s",
            intent,
            message.user_identifier,
        )

        service = self._services.get(intent)
        if not service:
            logger.warning("No service registered for intent '%s'", intent)
            return (
                "I'm not sure how to help with that yet. "
                "Try asking about a product price, tracking, or research."
            )

        user = store.get_user_by_identifier(db, message.user_identifier)
        if not user:
            logger.error(
                "User not found for identifier %s — should have been created by channel",
                message.user_identifier,
            )
            return "Something went wrong. Please try again."

        start = time.monotonic()
        try:
            response = await service.execute(message, user.id, db)
            elapsed = time.monotonic() - start
            service_executions_total.labels(service=service.name, status="success").inc()
            service_duration_seconds.labels(service=service.name).observe(elapsed)
            logger.info(
                "Service '%s' completed in %.3fs for user %s",
                service.name,
                elapsed,
                user.id,
            )
        except Exception:
            elapsed = time.monotonic() - start
            service_executions_total.labels(service=service.name, status="error").inc()
            service_duration_seconds.labels(service=service.name).observe(elapsed)
            logger.exception("Service '%s' failed for user %s", service.name, user.id)
            return "Sorry, something went wrong while processing your request."

        # Persist outbound conversation turn
        store.log_conversation(
            db, message.user_identifier, message.channel, "assistant", response
        )

        return response


# Module-level singleton — services register themselves at import time
orchestrator = Orchestrator()
