from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
import os

try:
    from database import get_db
    from models import Lead
except ImportError:
    from .database import get_db
    from .models import Lead

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()

    # Stats calculation
    total = db.query(func.count(Lead.id)).scalar()
    hot = db.query(func.count(Lead.id)).filter(Lead.lead_status == "HOT").scalar()
    warm = db.query(func.count(Lead.id)).filter(Lead.lead_status == "WARM").scalar()

    avg_response = db.query(func.avg(Lead.response_time_minutes)).filter(Lead.response_time_minutes != None).scalar() or 0

    stats = {
        "total": total,
        "hot": hot,
        "warm": warm,
        "avg_response": avg_response
    }

    return templates.TemplateResponse("dashboard.html", {"request": request, "leads": leads, "stats": stats})

@router.post("/mark-contacted/{lead_id}")
async def mark_contacted(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead and not lead.last_contacted:
        lead.last_contacted = datetime.now(timezone.utc)
        # Calculate response time
        diff = lead.last_contacted - lead.created_at.replace(tzinfo=timezone.utc) if lead.created_at.tzinfo is None else lead.last_contacted - lead.created_at
        lead.response_time_minutes = diff.total_seconds() / 60
        db.commit()

    return RedirectResponse(url="/dashboard", status_code=303)
