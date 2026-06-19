"""Conversation log store operations."""
from typing import List
import logging

from sqlalchemy.orm import Session

from src.database.models import User, ConversationLog

logger = logging.getLogger(__name__)


def log_conversation(
    db: Session,
    identifier: str,
    channel: str,
    role: str,
    content: str,
) -> None:
    """Persist a conversation turn (ACID)."""
    user = db.query(User).filter(User.phone_number == identifier).first()
    entry = ConversationLog(
        user_id=user.id if user else None,
        identifier=identifier,
        channel=channel,
        role=role,
        content=content,
    )
    try:
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to log conversation for %s", identifier)
        # Non-critical — don't re-raise, just log


def get_recent_conversation(
    db: Session,
    identifier: str,
    channel: str,
    limit: int = 10,
) -> List[ConversationLog]:
    """Retrieve the most recent conversation turns for context."""
    return (
        db.query(ConversationLog)
        .filter(
            ConversationLog.identifier == identifier,
            ConversationLog.channel == channel,
        )
        .order_by(ConversationLog.created_at.desc())
        .limit(limit)
        .all()
    )[::-1]  # Reverse to chronological order
