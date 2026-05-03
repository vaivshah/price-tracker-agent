from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    registration_status = Column(String, default="pending_name") # pending_name, pending_email, pending_address, complete

    tracking_jobs = relationship("TrackingJob", back_populates="user")
    reports = relationship("Report", back_populates="user")

class TrackingJob(Base):
    __tablename__ = "tracking_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_url = Column(String, nullable=False)
    interval_hours = Column(Integer, default=6)
    duration_days = Column(Integer, default=7)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String, default="active") # active, completed, cancelled

    user = relationship("User", back_populates="tracking_jobs")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String) # research, alternatives, price_history
    content_path = Column(String)
    access_token = Column(String, unique=True, index=True) # UUID
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="reports")
