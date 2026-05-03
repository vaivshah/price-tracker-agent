from fastapi import FastAPI, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import logging
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.logger import setup_logging
from src.database.session import engine, Base, get_db
from src.database import repository
from src.agent import agent
from src.reporting import router as reporting_router
from src.scheduler import start_scheduler

# Setup central logging configuration
setup_logging()
logger = logging.getLogger(__name__)

# Create all tables (for fast iteration, no alembic yet)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Price Tracker WhatsApp Agent")

# Setup telemetry
Instrumentator().instrument(app).expose(app)

app.include_router(reporting_router)

@app.on_event("startup")
def on_startup():
    start_scheduler()

async def background_agent_task(user_id: int, message: str, phone_number: str):
    """
    Runs the agent in the background to prevent webhook timeout.
    """
    response = await agent.process_message(user_id, message, phone_number)
    logger.info(f"Agent finished. Would send WhatsApp message to {phone_number}: {response}")
    # Here you would call Twilio/Meta API to send the final response back to WhatsApp.

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receives incoming WhatsApp messages.
    """
    # Parse the incoming form data or JSON (depends on provider, e.g., Twilio sends Form data)
    try:
        form_data = await request.form()
        incoming_msg = form_data.get('Body', '').strip()
        sender_number = form_data.get('From', '')
    except Exception:
        # Fallback for JSON if not using form data
        json_data = await request.json()
        incoming_msg = json_data.get('message', '')
        sender_number = json_data.get('phone_number', '')

    if not sender_number:
        return {"status": "error", "message": "No sender number provided"}

    try:
        user = repository.get_or_create_user(db, sender_number)
    except Exception as e:
        logger.exception("Database error while fetching user")
        return {"status": "error", "message": "Database error"}

    # Offload to background task
    background_tasks.add_task(background_agent_task, user.id, incoming_msg, sender_number)

    # Return immediately to prevent timeout
    return {"status": "ok", "message": "Task queued"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
