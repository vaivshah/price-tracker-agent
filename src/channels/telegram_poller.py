"""
Telegram polling mode — pulls messages from the Bot API and forwards
them to the local webhook. No ngrok or public URL required.

Usage:
    python -m src.channels.telegram_poller

This runs alongside the Docker stack and bridges Telegram → localhost.
"""
import time
import logging
import sys
import os

import httpx

# Allow running as a standalone script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("telegram_poller")

TELEGRAM_API = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
LOCAL_WEBHOOK = "http://localhost:8000/webhook/telegram"
POLL_INTERVAL = 1  # seconds


def poll() -> None:
    """Long-poll Telegram for updates and forward them to the local webhook."""
    offset = 0
    logger.info("Starting Telegram poller (Ctrl+C to stop)...")
    logger.info("Send a message to your bot on Telegram — you'll see it here!")

    with httpx.Client(timeout=30.0) as client:
        while True:
            try:
                # Long polling — Telegram holds the connection for up to 25s
                resp = client.get(
                    f"{TELEGRAM_API}/getUpdates",
                    params={"offset": offset, "timeout": 25},
                )
                data = resp.json()

                if not data.get("ok"):
                    logger.error("Telegram API error: %s", data)
                    time.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    logger.info(
                        "Received update %s: %s",
                        update["update_id"],
                        update.get("message", {}).get("text", "<non-text>"),
                    )

                    # Forward the raw Telegram update to our local webhook
                    try:
                        webhook_resp = client.post(LOCAL_WEBHOOK, json=update)
                        logger.info(
                            "Forwarded to webhook → %s %s",
                            webhook_resp.status_code,
                            webhook_resp.json(),
                        )
                    except Exception:
                        logger.exception("Failed to forward update to webhook")

            except KeyboardInterrupt:
                logger.info("Poller stopped.")
                break
            except Exception:
                logger.exception("Polling error — retrying in %ss", POLL_INTERVAL)
                time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        sys.exit(1)
    poll()
