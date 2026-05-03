"""
WhatsApp channel adapter.

Handles inbound webhooks from Twilio / Meta Cloud API and sends
responses back via the same provider.
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from src.channels.base import Channel, IncomingMessage
from src.core.telemetry import messages_received_total, messages_sent_total
from src.database.session import get_db, SessionLocal
from src.database import store
from src.services.orchestrator import orchestrator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Channel implementation
# ---------------------------------------------------------------------------

class WhatsAppChannel(Channel):
    """Concrete channel adapter for WhatsApp (Liskov-substitutable)."""

    @property
    def name(self) -> str:
        return "whatsapp"

    async def parse_request(self, request: Request) -> IncomingMessage:
        """Parse Twilio form-data or a JSON fallback into an IncomingMessage."""
        try:
            form_data = await request.form()
            return IncomingMessage(
                user_identifier=form_data.get("From", ""),
                channel=self.name,
                text=form_data.get("Body", "").strip(),
                raw_payload=dict(form_data),
                message_id=form_data.get("MessageSid"),
            )
        except Exception:
            json_data = await request.json()
            return IncomingMessage(
                user_identifier=json_data.get("phone_number", ""),
                channel=self.name,
                text=json_data.get("message", ""),
                raw_payload=json_data,
                message_id=json_data.get("message_id"),
            )

    async def send_response(self, user_identifier: str, message: str) -> None:
        """Send a WhatsApp message via Twilio/Meta API."""
        # TODO: integrate with Twilio/Meta Cloud API
        logger.info("[WhatsApp] Would send to %s: %s", user_identifier, message)
        messages_sent_total.labels(channel=self.name).inc()


whatsapp_channel = WhatsAppChannel()


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

async def _background_handle(user_id: int, message: IncomingMessage) -> None:
    """Run the orchestrator in the background to avoid webhook timeout."""
    db = SessionLocal()
    try:
        response = await orchestrator.handle(message, db)
        await whatsapp_channel.send_response(message.user_identifier, response)
    except Exception:
        logger.exception("Background task failed for user %s", user_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(tags=["WhatsApp"])


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Receive incoming WhatsApp messages."""
    message = await whatsapp_channel.parse_request(request)
    messages_received_total.labels(channel=whatsapp_channel.name).inc()

    if not message.user_identifier:
        logger.warning("Received message with no sender identifier")
        return {"status": "error", "message": "No sender identifier provided"}

    try:
        user = store.get_or_create_user(db, message.user_identifier, channel="whatsapp")
    except Exception:
        logger.exception("Failed to resolve user for identifier %s", message.user_identifier)
        return {"status": "error", "message": "Database error"}

    background_tasks.add_task(_background_handle, user.id, message)
    return {"status": "ok", "message": "Task queued"}
