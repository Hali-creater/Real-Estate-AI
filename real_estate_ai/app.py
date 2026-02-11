import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio
import os
import sys

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import init_db, SessionLocal
    from models import Lead
    from lead_scoring import calculate_lead_score
    from telegram_bot import send_telegram_alert
    from scheduler import start_scheduler, schedule_lead_follow_ups
except ImportError:
    # Handle cases where it's run from the root or inside real_estate_ai
    from .database import init_db, SessionLocal
    from .models import Lead
    from .lead_scoring import calculate_lead_score
    from .telegram_bot import send_telegram_alert
    from .scheduler import start_scheduler, schedule_lead_follow_ups

# Page Config
st.set_page_config(page_title="UAE Real Estate AI Lead System", layout="wide")

# Initialize DB and Scheduler once
@st.cache_resource
def startup():
    init_db()
    try:
        start_scheduler()
    except Exception as e:
        print(f"Scheduler already running or error: {e}")
    return True

startup()

# Navigation
tabs = st.tabs(["📊 Agent Dashboard", "📝 Lead Capture Form"])

# --- DASHBOARD TAB ---
with tabs[0]:
    st.title("Real Estate Lead Dashboard")

    db = SessionLocal()
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()

        # Stats
        total_leads = len(leads)
        hot_leads = sum(1 for l in leads if l.lead_status == "HOT")
        warm_leads = sum(1 for l in leads if l.lead_status == "WARM")

        responses = [l.response_time_minutes for l in leads if l.response_time_minutes is not None]
        avg_response = sum(responses) / len(responses) if responses else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Leads", total_leads)
        col2.metric("🔥 HOT Leads", hot_leads)
        col3.metric("⚠️ WARM Leads", warm_leads)
        col4.metric("Avg Response", f"{avg_response:.1f} min")

        st.divider()

        # Lead Table
        if leads:
            data = []
            for l in leads:
                data.append({
                    "ID": l.id,
                    "Name": l.name,
                    "Phone": l.phone,
                    "Budget (AED)": f"{l.budget:,.0f}",
                    "Area": l.area,
                    "Timeframe": l.timeframe,
                    "Source": l.source,
                    "Status": l.lead_status,
                    "Prob.": f"{l.close_probability}%",
                    "Recommended Action": l.recommended_action,
                    "Created": l.created_at.strftime('%Y-%m-%d %H:%M'),
                    "Contacted": "✓" if l.last_contacted else "No"
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Action Area
            st.subheader("Actions")
            uncontacted_leads = [l for l in leads if not l.last_contacted]
            if uncontacted_leads:
                lead_to_mark = st.selectbox("Select Lead to Mark as Contacted",
                                            options=uncontacted_leads,
                                            format_func=lambda x: f"{x.name} ({x.area})")
                if st.button("Mark Contacted"):
                    lead_to_mark.last_contacted = datetime.now(timezone.utc)
                    # Handle possible tz-naive created_at
                    created_at = lead_to_mark.created_at
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)

                    diff = lead_to_mark.last_contacted - created_at
                    lead_to_mark.response_time_minutes = diff.total_seconds() / 60
                    db.commit()
                    st.success(f"Marked {lead_to_mark.name} as contacted!")
                    st.rerun()
            else:
                st.info("All leads have been contacted.")
        else:
            st.write("No leads found yet.")

    finally:
        db.close()

# --- FORM TAB ---
with tabs[1]:
    st.title("UAE Real Estate Inquiry Form")
    with st.form("lead_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")

        col_a, col_b = st.columns(2)
        budget = col_a.number_input("Budget (AED)", min_value=0, step=100000)
        area = col_b.text_input("Preferred Area")

        prop_type = st.selectbox("Property Type", ["Apartment", "Villa", "Townhouse", "Penthouse"])
        timeframe = st.selectbox("Buying Timeframe", ["1 month", "3 months", "6 months+", "Just Browsing"])
        source = st.selectbox("Lead Source", ["Website", "PropertyFinder", "Bayut", "Dubizzle", "Referral"])

        col_c, col_d = st.columns(2)
        mortgage = col_c.selectbox("Mortgage Approved?", ["approved", "not_approved", "checking"])
        cash_buyer = col_d.checkbox("Cash Buyer?")

        message = st.text_area("Message")

        submitted = st.form_submit_button("Submit Inquiry")

        if submitted:
            if not name or not email or not phone:
                st.error("Please fill in name, email, and phone.")
            else:
                db = SessionLocal()
                try:
                    # Scoring
                    lead_data = {
                        "budget": budget,
                        "timeframe": timeframe,
                        "mortgage_status": mortgage,
                        "cash_buyer": cash_buyer,
                        "message": message
                    }
                    scoring_result = calculate_lead_score(lead_data)

                    # Save
                    new_lead = Lead(
                        name=name, email=email, phone=phone, budget=budget,
                        area=area, property_type=prop_type, timeframe=timeframe,
                        source=source, mortgage_status=mortgage, cash_buyer=cash_buyer,
                        message=message, score=scoring_result['score'],
                        lead_status=scoring_result['status'],
                        close_probability=scoring_result['probability'],
                        recommended_action=scoring_result['action']
                    )
                    db.add(new_lead)
                    db.commit()
                    db.refresh(new_lead)

                    # Telegram and Follow-ups
                    lead_details = {
                        "name": name, "budget": budget, "area": area,
                        "timeframe": timeframe, "status": scoring_result['status'],
                        "probability": scoring_result['probability'],
                        "action": scoring_result['action']
                    }

                    # Running async in Streamlit form submission
                    async def run_tasks():
                        await send_telegram_alert(lead_details)
                        await schedule_lead_follow_ups(new_lead.id, name, scoring_result['status'])

                    asyncio.run(run_tasks())

                    st.success("Thank you for your inquiry! An agent will contact you shortly.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                finally:
                    db.close()
