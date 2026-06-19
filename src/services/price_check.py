import logging
from sqlalchemy.orm import Session
from src.channels.base import IncomingMessage
from src.services.base import BaseService
from src.services.agent import agent_client
from src.database import store

logger = logging.getLogger(__name__)


class PriceCheckService(BaseService):

    @property
    def name(self) -> str:
        return "price_check"

    async def execute(self, message: IncomingMessage, user_id: int, db: Session) -> str:
        logger.info("Executing price check for user %s: %s", user_id, message.text)
        
        # Use user_identifier as session_id to maintain session context in OpenClaw
        agent_response = await agent_client.send_message(
            session_id=message.user_identifier,
            text=message.text
        )

        if agent_response.error:
            logger.error("Price check agent returned error for user %s: %s", user_id, agent_response.error)
            return agent_response.summary

        # Persist structured product / variant / listings data in the DB
        if agent_response.product_data:
            try:
                store.persist_agent_response(
                    db=db,
                    product_data=agent_response.product_data,
                    variant_data=agent_response.variant_data,
                    listings_data=agent_response.listings_data,
                )
            except Exception:
                logger.exception("Failed to persist agent price lookup response in database")

        return agent_response.summary
