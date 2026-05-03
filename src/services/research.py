"""Product research and review aggregation service."""
import logging
from sqlalchemy.orm import Session
from src.channels.base import IncomingMessage
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class ResearchService(BaseService):

    @property
    def name(self) -> str:
        return "research"

    async def execute(self, message: IncomingMessage, user_id: int, db: Session) -> str:
        logger.info("Executing research for user %s: %s", user_id, message.text)
        # TODO: invoke NemoClaw to scrape reviews across multiple sites
        # TODO: generate report via reports.renderer and return link
        return "I'll research this product for you and send a report link shortly."
