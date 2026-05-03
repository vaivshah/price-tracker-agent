"""
Data store — all database read/write operations.

Single Responsibility: only this module touches SQLAlchemy queries.
ACID: every write is wrapped in try/except with explicit rollback.
"""
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.models import (
    User,
    TrackingJob,
    PriceSnapshot,
    Report,
    ConversationLog,
)
from src.core.telemetry import reports_generated_total

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tracking Jobs
# ---------------------------------------------------------------------------

def create_tracking_job(
    db: Session,
    user_id: int,
    product_url: str,
    interval_hours: int = 6,
    duration_days: int = 7,
    target_price: Optional[float] = None,
    notify_on: str = "every_check",
) -> TrackingJob:
    """Create a new tracking job (ACID)."""
    end_time = datetime.utcnow() + timedelta(days=duration_days)
    job = TrackingJob(
        user_id=user_id,
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


# ---------------------------------------------------------------------------
# Price Snapshots
# ---------------------------------------------------------------------------

def create_price_snapshot(
    db: Session,
    job_id: int,
    price: float,
    currency: str = "USD",
    source_url: str = "",
) -> PriceSnapshot:
    """Record a price data point (ACID)."""
    snapshot = PriceSnapshot(
        tracking_job_id=job_id,
        price=price,
        currency=currency,
        source_url=source_url,
    )
    try:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        logger.info("Recorded price snapshot id=%s for job %s: %s %s", snapshot.id, job_id, price, currency)
        return snapshot
    except Exception:
        db.rollback()
        logger.exception("Failed to record snapshot for job %s", job_id)
        raise


def get_snapshots_for_job(db: Session, job_id: int) -> List[PriceSnapshot]:
    """Retrieve all price snapshots for a tracking job, ordered chronologically."""
    return (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.tracking_job_id == job_id)
        .order_by(PriceSnapshot.captured_at.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def create_report(
    db: Session,
    user_id: int,
    report_type: str,
    content_path: str,
    expiry_hours: int = 24,
) -> str:
    """Create a report record and return its unique access token (ACID)."""
    access_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

    report = Report(
        user_id=user_id,
        report_type=report_type,
        content_path=content_path,
        access_token=access_token,
        expires_at=expires_at,
    )
    try:
        db.add(report)
        db.commit()
        reports_generated_total.labels(report_type=report_type).inc()
        logger.info("Created report id=%s type=%s for user %s", report.id, report_type, user_id)
        return access_token
    except Exception:
        db.rollback()
        logger.exception("Failed to create report for user %s", user_id)
        raise


def get_report_by_token(db: Session, access_token: str) -> Optional[Report]:
    """Fetch a report by its unique access token."""
    return db.query(Report).filter(Report.access_token == access_token).first()


def get_expired_reports(db: Session) -> List[Report]:
    """Fetch all reports that have passed their expiry time."""
    return (
        db.query(Report)
        .filter(Report.expires_at < datetime.utcnow())
        .all()
    )


# ---------------------------------------------------------------------------
# Conversation Logs
# ---------------------------------------------------------------------------

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
