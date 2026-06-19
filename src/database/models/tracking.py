"""Tracking job model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database.session import Base


class TrackingJob(Base):
    """User-initiated price monitoring job.

    Tracks a specific ProductVariant. Optionally locked to a single
    retailer via listing_id; if None, tracks the cheapest across all.
    """

    __tablename__ = "tracking_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    variant_id = Column(
        Integer, ForeignKey("product_variants.id"), nullable=True, index=True
    )
    listing_id = Column(
        Integer, ForeignKey("product_listings.id"), nullable=True, index=True
    )
    product_url = Column(String, nullable=True)  # Legacy / fallback
    interval_hours = Column(Integer, default=6)
    duration_days = Column(Integer, default=7)
    target_price = Column(Float, nullable=True)
    notify_on = Column(
        String, default="every_check"
    )  # every_check, price_drop, target_reached
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String, default="active")  # active, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tracking_jobs")
    variant = relationship("ProductVariant", back_populates="tracking_jobs")
