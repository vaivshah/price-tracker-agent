import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .database import get_db
from .models import Report

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/report/{access_token}", response_class=HTMLResponse)
async def view_report(request: Request, access_token: str, db: Session = Depends(get_db)):
    """
    Serves a static HTML report if the access_token is valid and not expired.
    """
    report = db.query(Report).filter(Report.access_token == access_token).first()
    
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
    access_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    
    new_report = Report(
        user_id=user_id,
        report_type=report_type,
        content_path=content_path,
        access_token=access_token,
        expires_at=expires_at
    )
    db.add(new_report)
    db.commit()
    
    return f"/report/{access_token}"
