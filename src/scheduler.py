"""
Background scheduler for periodic tasks.

Runs independently of the web process to check tracking jobs
and clean up expired reports.
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from src.database.session import SessionLocal
from src.database import store
from src.core.telemetry import active_tracking_jobs_gauge

logger = logging.getLogger(__name__)


def check_prices() -> None:
    """Periodic task to process active tracking jobs."""
    logger.info("Running scheduled price check...")
    db: Session = SessionLocal()
    try:
        active_jobs = store.get_active_tracking_jobs(db)
        active_tracking_jobs_gauge.set(len(active_jobs))

        for job in active_jobs:
            if job.end_time and datetime.utcnow() > job.end_time:
                store.mark_job_completed(db, job)
                logger.info("Job %s marked as completed (expired)", job.id)
                continue

            # TODO: dispatch NemoClaw agent to scrape current price
            logger.info("Would check price for job %s: %s", job.id, job.product_url)

    except Exception:
        db.rollback()
        logger.exception("Error in scheduled price check")
    finally:
        db.close()


def cleanup_expired_reports() -> None:
    """Periodic task to clean up expired report records."""
    logger.info("Running expired report cleanup...")
    db: Session = SessionLocal()
    try:
        expired = store.get_expired_reports(db)
        for report in expired:
            logger.info("Cleaning up expired report id=%s", report.id)
            # TODO: delete associated content_path file from disk
        logger.info("Cleaned up %s expired reports", len(expired))
    except Exception:
        db.rollback()
        logger.exception("Error in report cleanup")
    finally:
        db.close()


def start_scheduler() -> None:
    """Initialise and start the background scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_prices, "interval", hours=1)
    scheduler.add_job(cleanup_expired_reports, "interval", hours=6)
    scheduler.start()
    logger.info("Background scheduler started (price check: 1h, report cleanup: 6h)")
