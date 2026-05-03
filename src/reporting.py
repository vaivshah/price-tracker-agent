import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.database.session import get_db
from src.database import repository

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/report/{access_token}", response_class=HTMLResponse)
async def view_report(request: Request, access_token: str, db: Session = Depends(get_db)):
    """
    Serves a static HTML report if the access_token is valid and not expired.
    """
    report = repository.get_report_by_token(db, access_token)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.expires_at and datetime.utcnow() > report.expires_at:
        raise HTTPException(status_code=410, detail="This report has expired")
        
    context = {
        "request": request,
        "report_type": report.report_type,
        "content": "This is the dynamically generated content of the report. It would contain the alternatives, research, or tracking graphs."
    }
    
    return templates.TemplateResponse("report_template.html", context)

def generate_report_link(db: Session, user_id: int, report_type: str, content_path: str, expiry_hours: int = 24):
    """
    Utility function to create a new report record and return the unguessable link.
    """
    access_token = repository.create_report(db, user_id, report_type, content_path, expiry_hours)
    return f"/report/{access_token}"
