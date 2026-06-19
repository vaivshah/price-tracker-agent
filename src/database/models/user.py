"""User model."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    registration_status = Column(
        String, default="pending_name"
    )  # pending_name, pending_email, pending_address, complete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tracking_jobs = relationship("TrackingJob", back_populates="user")
    reports = relationship("Report", back_populates="user")
    conversations = relationship("ConversationLog", back_populates="user")
