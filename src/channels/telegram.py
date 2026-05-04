"""
Telegram channel adapter.

Handles inbound webhooks from the Telegram Bot API and sends
responses back via the sendMessage endpoint.

Setup:
    1. Message @BotFather on Telegram → /newbot → get your token.
    2. Set TELEGRAM_BOT_TOKEN in .env.
    3. Register your webhook URL:
       curl https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<ngrok>/webhook/telegram
"""
import logging

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from src.channels.base import Channel, IncomingMessage
from src.core.config import config
from src.core.telemetry import messages_received_total, messages_sent_total
from src.database.session import get_db, SessionLocal
from src.database import store
from src.services.orchestrator import orchestrator

logger = logging.getLogger(__name__)

_TELEGRAM_API_BASE = "https://api.telegram.org/bot"


# ---------------------------------------------------------------------------
# Channel implementation
# ---------------------------------------------------------------------------

class TelegramChannel(Channel):
    """Concrete channel adapter for Telegram (Liskov-substitutable)."""

    @property
    def name(self) -> str:
        return "telegram"

    async def parse_request(self, request) -> IncomingMessage:
        """Parse a Telegram Bot API webhook update into an IncomingMessage.

        Accepts either a FastAPI Request or a pre-parsed dict (to avoid
        double-reading the request body).
        """
        if isinstance(request, dict):
            data = request
        else:
            data = await request.json()

        message_data = data.get("message", {})
        chat = message_data.get("chat", {})

        return IncomingMessage(
            user_identifier=str(chat.get("id", "")),
            channel=self.name,
            text=message_data.get("text", "").strip(),
            raw_payload=data,
            message_id=str(message_data.get("message_id", "")),
        )

    async def send_response(self, user_identifier: str, message: str) -> None:
        """Send a message back via the Telegram Bot API."""
        token = config.TELEGRAM_BOT_TOKEN
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN is not configured — cannot send message")
            return

        url = f"{_TELEGRAM_API_BASE}{token}/sendMessage"
        payload = {
            "chat_id": user_identifier,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                if resp.status_code != 200:
                    logger.error(
                        "Telegram API error %s: %s", resp.status_code, resp.text
                    )
                else:
                    logger.info("[Telegram] Sent message to chat_id=%s", user_identifier)
        except httpx.HTTPError:
            logger.exception("Failed to send Telegram message to %s", user_identifier)

        messages_sent_total.labels(channel=self.name).inc()


telegram_channel = TelegramChannel()


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

async def _background_handle(user_id: int, message: IncomingMessage) -> None:
    """Run the orchestrator in the background to avoid webhook timeout."""
    db = SessionLocal()
    try:
        response = await orchestrator.handle(message, db)
        await telegram_channel.send_response(message.user_identifier, response)
    except Exception:
        logger.exception("Background task failed for user %s", user_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(tags=["Telegram"])


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Receive incoming Telegram messages via Bot API webhook."""
    data = await request.json()

    # Telegram sends various update types — we only handle text messages
    if "message" not in data or "text" not in data.get("message", {}):
        return {"status": "ok", "message": "Non-text update ignored"}

    message = await telegram_channel.parse_request(data)
    messages_received_total.labels(channel=telegram_channel.name).inc()

    if not message.user_identifier:
        logger.warning("Received Telegram update with no chat ID")
        return {"status": "error", "message": "No chat identifier"}

    try:
        user = store.get_or_create_user(db, message.user_identifier, channel="telegram")
    except Exception:
        logger.exception(
            "Failed to resolve user for Telegram chat_id %s", message.user_identifier
        )
        return {"status": "error", "message": "Database error"}

    background_tasks.add_task(_background_handle, user.id, message)
    return {"status": "ok", "message": "Task queued"}
