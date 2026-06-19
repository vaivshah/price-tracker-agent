"""Report store operations."""
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import logging

from sqlalchemy.orm import Session

from src.database.models import Report
from src.core.telemetry import reports_generated_total

logger = logging.getLogger(__name__)


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
