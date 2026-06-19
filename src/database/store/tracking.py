"""Tracking job store operations."""
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from src.database.models import TrackingJob

logger = logging.getLogger(__name__)


def create_tracking_job(
    db: Session,
    user_id: int,
    variant_id: Optional[int] = None,
    listing_id: Optional[int] = None,
    product_url: Optional[str] = None,
    interval_hours: int = 6,
    duration_days: int = 7,
    target_price: Optional[float] = None,
    notify_on: str = "every_check",
) -> TrackingJob:
    """Create a new tracking job (ACID)."""
    end_time = datetime.utcnow() + timedelta(days=duration_days)
    job = TrackingJob(
        user_id=user_id,
        variant_id=variant_id,
        listing_id=listing_id,
        product_url=product_url,
        interval_hours=interval_hours,
        duration_days=duration_days,
        target_price=target_price,
        notify_on=notify_on,
        end_time=end_time,
    )
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info("Created tracking job id=%s for user %s", job.id, user_id)
        return job
    except Exception:
        db.rollback()
        logger.exception("Failed to create tracking job for user %s", user_id)
        raise


def get_active_tracking_jobs(db: Session) -> List[TrackingJob]:
    """Retrieve all currently active tracking jobs."""
    return db.query(TrackingJob).filter(TrackingJob.status == "active").all()


def get_user_tracking_jobs(db: Session, user_id: int) -> List[TrackingJob]:
    """Retrieve all tracking jobs for a specific user."""
    return db.query(TrackingJob).filter(TrackingJob.user_id == user_id).all()


def mark_job_completed(db: Session, job: TrackingJob) -> None:
    """Mark a tracking job as completed (ACID)."""
    try:
        job.status = "completed"
        db.commit()
        logger.info("Marked tracking job id=%s as completed", job.id)
    except Exception:
        db.rollback()
        logger.exception("Failed to mark job %s as completed", job.id)
        raise


def cancel_tracking_job(db: Session, job: TrackingJob) -> None:
    """Cancel a tracking job (ACID)."""
    try:
        job.status = "cancelled"
        db.commit()
        logger.info("Cancelled tracking job id=%s", job.id)
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel job %s", job.id)
        raise


def extend_tracking_job(db: Session, job: TrackingJob, extra_days: int) -> None:
    """Extend a tracking job's end time (ACID)."""
    try:
        job.end_time = job.end_time + timedelta(days=extra_days)
        job.duration_days = job.duration_days + extra_days
        db.commit()
        logger.info("Extended tracking job id=%s by %s days", job.id, extra_days)
    except Exception:
        db.rollback()
        logger.exception("Failed to extend job %s", job.id)
        raise
