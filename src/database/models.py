"""
SQLAlchemy ORM models.

Each model maps 1:1 to a Postgres table. Relationships are defined
here; all query logic lives in database/store.py.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
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

    tracking_jobs = relationship("TrackingJob", back_populates="user")
    reports = relationship("Report", back_populates="user")
    conversations = relationship("ConversationLog", back_populates="user")


class TrackingJob(Base):
    __tablename__ = "tracking_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_url = Column(String, nullable=False)
    interval_hours = Column(Integer, default=6)
    duration_days = Column(Integer, default=7)
    target_price = Column(Float, nullable=True)  # Optional price alert threshold
    notify_on = Column(
        String, default="every_check"
    )  # every_check, price_drop, target_reached
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String, default="active")  # active, completed, cancelled

    user = relationship("User", back_populates="tracking_jobs")
    snapshots = relationship("PriceSnapshot", back_populates="tracking_job")


class PriceSnapshot(Base):
    """Individual price data point captured during tracking."""

    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    tracking_job_id = Column(Integer, ForeignKey("tracking_jobs.id"))
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    source_url = Column(String)
    captured_at = Column(DateTime, default=datetime.utcnow)

    tracking_job = relationship("TrackingJob", back_populates="snapshots")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String)  # research, alternatives, price_history
    content_path = Column(String)
    access_token = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="reports")


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
