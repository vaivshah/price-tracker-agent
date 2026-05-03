"""Manage active tracking jobs — list, cancel, extend."""
import logging
from sqlalchemy.orm import Session
from src.channels.base import IncomingMessage
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class ReviewService(BaseService):

    @property
    def name(self) -> str:
        return "review"

    async def execute(self, message: IncomingMessage, user_id: int, db: Session) -> str:
        logger.info("Executing job review for user %s: %s", user_id, message.text)
        # TODO: list active jobs for user via store
        # TODO: handle cancel / extend commands
        return "Here are your active tracking jobs. Reply with a job number to cancel or extend it."
