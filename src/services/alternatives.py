"""Budget-based alternative product suggestions service."""
import logging
from sqlalchemy.orm import Session
from src.channels.base import IncomingMessage
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class AlternativesService(BaseService):

    @property
    def name(self) -> str:
        return "alternatives"

    async def execute(self, message: IncomingMessage, user_id: int, db: Session) -> str:
        logger.info("Executing alternatives search for user %s: %s", user_id, message.text)
        # TODO: parse budget from message
        # TODO: research product + find alternatives within budget
        # TODO: generate comparison report via reports.renderer and return link
        return "I'll find alternatives within your budget and send a comparison report."
