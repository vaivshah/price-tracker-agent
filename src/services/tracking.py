"""Periodic price tracking service (6h min interval, 14d max duration)."""
import logging
from sqlalchemy.orm import Session
from src.channels.base import IncomingMessage
from src.services.base import BaseService

logger = logging.getLogger(__name__)

# Business constraints
MIN_INTERVAL_HOURS = 6
MAX_DURATION_DAYS = 14
DEFAULT_INTERVAL_HOURS = 6
DEFAULT_DURATION_DAYS = 7


class TrackingService(BaseService):

    @property
    def name(self) -> str:
        return "tracking"

    async def execute(self, message: IncomingMessage, user_id: int, db: Session) -> str:
        logger.info("Executing tracking setup for user %s: %s", user_id, message.text)
        # TODO: parse URL, interval, duration from message
        # TODO: create TrackingJob via store, enforce MIN/MAX constraints
        return (
            f"I can track prices for you every {DEFAULT_INTERVAL_HOURS} hours "
            f"for up to {MAX_DURATION_DAYS} days. Send me the product URL to get started."
        )
