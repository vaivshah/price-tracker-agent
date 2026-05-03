import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime

from .database import SessionLocal
from .models import TrackingJob
from .agent import agent

logger = logging.getLogger(__name__)

def check_prices():
    """
    Periodic task to check active tracking jobs.
    """
    logger.info("Running scheduled price check...")
    db: Session = SessionLocal()
    try:
        active_jobs = db.query(TrackingJob).filter(TrackingJob.status == "active").all()
        for job in active_jobs:
            if job.end_time and datetime.utcnow() > job.end_time:
                job.status = "completed"
                logger.info(f"Job {job.id} marked as completed.")
                continue
                
            # Here we would dispatch the NemoClaw agent to check the price
            logger.info(f"Would check price for job {job.id}: {job.product_url}")
            
        db.commit()
    except Exception as e:
        logger.exception("Error in scheduled task")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Check every hour for active jobs
    scheduler.add_job(check_prices, 'interval', hours=1)
    scheduler.start()
    logger.info("Background scheduler started.")
