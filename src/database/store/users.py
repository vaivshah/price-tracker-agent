"""User store operations."""
from typing import Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.models import User

logger = logging.getLogger(__name__)


def get_or_create_user(db: Session, identifier: str, channel: str = "whatsapp") -> User:
    """
    Safely retrieve or create a user (ACID + race-condition safe).

    Currently maps identifier → phone_number. Generalise when adding
    channels that use non-phone identifiers.
    """
    user = db.query(User).filter(User.phone_number == identifier).first()
    if user:
        return user

    try:
        user = User(phone_number=identifier)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user id=%s for %s via %s", user.id, identifier, channel)
        return user
    except IntegrityError:
        db.rollback()
        user = db.query(User).filter(User.phone_number == identifier).first()
        if not user:
            raise Exception("Failed to create or retrieve user due to database error.")
        return user


def get_user_by_identifier(db: Session, identifier: str) -> Optional[User]:
    """Look up a user by their channel identifier (phone number)."""
    return db.query(User).filter(User.phone_number == identifier).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Look up a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()
