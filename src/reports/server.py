"""
Report serving routes and link generation.

Single Responsibility: only handles HTTP serving of reports. Rendering
lives in renderer.py, DB access in database/store.py.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime

from src.database.session import get_db
from src.database import store
from src.reports import renderer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reports"])


@router.get("/report/{access_token}", response_class=HTMLResponse)
async def view_report(request: Request, access_token: str, db: Session = Depends(get_db)):
    """Serve a report if the access token is valid and not expired."""
    report = store.get_report_by_token(db, access_token)

    if not report:
        logger.warning("Report not found for token %s", access_token)
        raise HTTPException(status_code=404, detail="Report not found")

    if report.expires_at and datetime.utcnow() > report.expires_at:
        logger.info("Report %s has expired", report.id)
        raise HTTPException(status_code=410, detail="This report has expired")

    context = {
        "request": request,
        "report_type": report.report_type,
        "content": "Dynamically generated report content.",  # TODO: load from content_path
    }

    html = renderer.render("report_template.html", context)
    return HTMLResponse(content=html)


def generate_report_link(
    db: Session,
    user_id: int,
    report_type: str,
    content_path: str,
    expiry_hours: int = 24,
) -> str:
    """Create a report record and return its shareable link."""
    access_token = store.create_report(db, user_id, report_type, content_path, expiry_hours)
    logger.info("Generated report link for user %s, type=%s", user_id, report_type)
    return f"/report/{access_token}"
