"""One-time price lookup service."""
import logging
from sqlalchemy.orm import Session
from src.channels.base import IncomingMessage
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class PriceCheckService(BaseService):

    @property
    def name(self) -> str:
        return "price_check"

    async def execute(self, message: IncomingMessage, user_id: int, db: Session) -> str:
        logger.info("Executing price check for user %s: %s", user_id, message.text)
        # TODO: invoke NemoClaw agent to scrape price from the URL in the message
        return "I'm looking up the price for you. I'll reply shortly with the result."
