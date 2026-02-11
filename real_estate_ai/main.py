import uvicorn
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
from contextlib import asynccontextmanager

try:
    from database import init_db, get_db
    from models import Lead
    from lead_scoring import calculate_lead_score
    from telegram_bot import send_telegram_alert
    from scheduler import start_scheduler, schedule_lead_follow_ups
except ImportError:
    from .database import init_db, get_db
    from .models import Lead
    from .lead_scoring import calculate_lead_score
    from .telegram_bot import send_telegram_alert
    from .scheduler import start_scheduler, schedule_lead_follow_ups

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    start_scheduler()
    yield
    # Shutdown (if needed)

app = FastAPI(title="UAE Real Estate AI Lead System", lifespan=lifespan)

# Ensure templates directory is found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/submit-lead")
async def submit_lead(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    budget: float = Form(...),
    area: str = Form(...),
    property_type: str = Form(...),
    timeframe: str = Form(...),
    source: str = Form("Website"),
    mortgage_status: str = Form(...),
    cash_buyer: bool = Form(False),
    message: str = Form(""),
    db: Session = Depends(get_db)
):
    # 1. Lead Scoring
    lead_data = {
        "budget": budget,
        "timeframe": timeframe,
        "mortgage_status": mortgage_status,
        "cash_buyer": cash_buyer,
        "message": message
    }
    scoring_result = calculate_lead_score(lead_data)

    # 2. Save to Database
    new_lead = Lead(
        name=name,
        email=email,
        phone=phone,
        budget=budget,
        area=area,
        property_type=property_type,
        timeframe=timeframe,
        source=source,
        mortgage_status=mortgage_status,
        cash_buyer=cash_buyer,
        message=message,
        score=scoring_result['score'],
        lead_status=scoring_result['status'],
        close_probability=scoring_result['probability'],
        recommended_action=scoring_result['action']
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    # 3. Send Telegram Alert
    lead_details_for_alert = {
        "name": name,
        "budget": budget,
        "area": area,
        "timeframe": timeframe,
        "status": scoring_result['status'],
        "probability": scoring_result['probability'],
        "action": scoring_result['action']
    }

    import asyncio
    asyncio.create_task(send_telegram_alert(lead_details_for_alert))

    # 4. Schedule Follow-ups
    asyncio.create_task(schedule_lead_follow_ups(new_lead.id, name, scoring_result['status']))

    return HTMLResponse(content="<h2>Thank you for your inquiry! An agent will contact you shortly.</h2><a href='/'>Go Back</a>")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
