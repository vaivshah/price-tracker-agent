"""Conversation log model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database.session import Base


class ConversationLog(Base):
    """Multi-turn conversation context per user per channel."""

    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    identifier = Column(String, index=True)  # phone_number, email, chat_id
    channel = Column(String)  # whatsapp, telegram, email, web
    role = Column(String)  # user, assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
