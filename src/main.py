from fastapi import FastAPI, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from .logger import setup_logging

# Setup central logging configuration
setup_logging()
logger = logging.getLogger(__name__)

from .database import engine, Base, get_db
from .models import User
from .agent import agent
from .reporting import router as reporting_router
from .scheduler import start_scheduler

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

    # Simple user lookup or creation
    user = db.query(User).filter(User.phone_number == sender_number).first()
    if not user:
        user = User(phone_number=sender_number)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Offload to background task
    background_tasks.add_task(background_agent_task, user.id, incoming_msg, sender_number)

    # Return immediately to prevent timeout
    return {"status": "ok", "message": "Task queued"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
