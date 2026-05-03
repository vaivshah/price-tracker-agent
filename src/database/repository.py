from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import uuid
import logging

from src.database.models import User, TrackingJob, Report

logger = logging.getLogger(__name__)

def get_or_create_user(db: Session, phone_number: str) -> User:
    """Safely retrieves a user or creates one if they do not exist."""
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        try:
            user = User(phone_number=phone_number)
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            user = db.query(User).filter(User.phone_number == phone_number).first()
            if not user:
                raise Exception("Failed to create or retrieve user due to database error.")
    return user

def get_active_tracking_jobs(db: Session):
    """Retrieves all tracking jobs that are currently active."""
    return db.query(TrackingJob).filter(TrackingJob.status == "active").all()

def mark_job_completed(db: Session, job: TrackingJob):
    """Marks a tracking job as completed safely."""
    try:
        job.status = "completed"
        db.commit()
    except Exception:
        db.rollback()
        raise

def get_report_by_token(db: Session, access_token: str) -> Report:
    """Fetches a report using its unique access token."""
    return db.query(Report).filter(Report.access_token == access_token).first()

def create_report(db: Session, user_id: int, report_type: str, content_path: str, expiry_hours: int = 24) -> str:
    """Creates a new report record and returns its unique access token."""
    access_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    
    new_report = Report(
        user_id=user_id,
        report_type=report_type,
        content_path=content_path,
        access_token=access_token,
        expires_at=expires_at
    )
    
    try:
        db.add(new_report)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
        
    return access_token
