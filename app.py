import streamlit as st
import pandas as pd
import json
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio
import os
import sys

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import init_db, SessionLocal
    from models import Lead, AgencyLead
    from lead_scoring import calculate_lead_score
    from telegram_bot import send_telegram_alert
    from scheduler import start_scheduler, schedule_lead_follow_ups
    from agency_intelligence import (
        clean_and_score_agency, scrape_homepage, analyze_website_with_gpt,
        qualify_agency, generate_outreach_email
    )
except ImportError:
    # Handle cases where it's run from the root or inside real_estate_ai
    from .database import init_db, SessionLocal
    from .models import Lead, AgencyLead
    from .lead_scoring import calculate_lead_score
    from .telegram_bot import send_telegram_alert
    from .scheduler import start_scheduler, schedule_lead_follow_ups
    from .agency_intelligence import (
        clean_and_score_agency, scrape_homepage, analyze_website_with_gpt,
        qualify_agency, generate_outreach_email
    )

# Page Config
st.set_page_config(page_title="SpeedToLead AI: Appointment Engine", layout="wide")

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
tabs = st.tabs(["📊 Agent Dashboard", "📝 Lead Capture Form", "🏢 Enterprise Lead Engine"])

# --- DASHBOARD TAB ---
with tabs[0]:
    st.title("🚀 SpeedToLead AI: US Realtor Dashboard")

    db = SessionLocal()
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()

        # Stats
        total_leads = len(leads)
        hot_leads = sum(1 for l in leads if l.lead_status == "HOT")
        appointments = sum(1 for l in leads if l.appointment_booked)
        total_roi = sum(l.estimated_commission for l in leads if l.lead_status == "HOT")

        responses = [l.response_time_minutes for l in leads if l.response_time_minutes is not None]
        avg_response = sum(responses) / len(responses) if responses else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Leads", total_leads)
        col2.metric("🔥 HOT Leads", hot_leads)
        col3.metric("📅 Appointments", appointments)
        col4.metric("Avg Response", f"{avg_response:.1f} min")
        col5.metric("Est. HOT ROI ($)", f"${total_roi:,.0f}")

        st.divider()

        # Lead Table
        if leads:
            data = []
            for l in leads:
                data.append({
                    "ID": l.id,
                    "Name": l.name,
                    "Budget ($)": f"${l.budget:,.0f}",
                    "Est. Commission": f"${l.estimated_commission:,.0f}",
                    "Source": l.source,
                    "Status": l.lead_status,
                    "Prob.": f"{l.close_probability}%",
                    "Recommended Action": l.recommended_action,
                    "Appt": "📅" if l.appointment_booked else "No",
                    "SMS Opt-in": "✅" if l.sms_opt_in else "❌",
                    "Created": l.created_at.strftime('%Y-%m-%d %H:%M'),
                    "Contacted": "✓" if l.last_contacted else "No"
                })

            df = pd.DataFrame(data)
            # use width="stretch" to avoid deprecation warning in newer Streamlit versions
            st.dataframe(df, width="stretch", hide_index=True)

            # Action Area
            st.subheader("Lead Management")
            col_act1, col_act2 = st.columns(2)

            with col_act1:
                uncontacted_leads = [l for l in leads if not l.last_contacted]
                if uncontacted_leads:
                    lead_to_mark = st.selectbox("Mark as Contacted",
                                                options=uncontacted_leads,
                                                format_func=lambda x: f"{x.name} ({x.source})")
                    if st.button("Confirm Contact"):
                        lead_to_mark.last_contacted = datetime.now(timezone.utc)
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

            with col_act2:
                unbooked_leads = [l for l in leads if not l.appointment_booked]
                if unbooked_leads:
                    lead_to_book = st.selectbox("Book Appointment",
                                                options=unbooked_leads,
                                                format_func=lambda x: f"{x.name} ({x.lead_status})")
                    if st.button("Schedule Appointment"):
                        lead_to_book.appointment_booked = True
                        db.commit()
                        st.success(f"Appointment booked for {lead_to_book.name}!")
                        st.rerun()
                else:
                    st.info("All appointments booked.")
        else:
            st.write("No leads found yet.")

    finally:
        db.close()

# --- FORM TAB ---
with tabs[1]:
    st.title("🏡 SpeedToLead AI: US Realtor Intake Form")
    st.write("Convert Zillow and Facebook leads into appointments instantly.")
    with st.form("lead_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone (for SMS alerts)")

        col_a, col_b = st.columns(2)
        budget = col_a.number_input("Budget ($)", min_value=0, step=50000)
        area = col_b.text_input("Target ZIP Code / Neighborhood")

        prop_type = st.selectbox("Property Type", ["Single Family Home", "Condo", "Townhouse", "Multi-Family"])
        timeframe = st.selectbox("Buying Timeframe", ["Immediate", "3 months", "6 months+", "Just Browsing"])
        source = st.selectbox("Lead Source", ["Zillow", "Realtor.com", "Facebook Ads", "Google Ads", "Website", "Open House"])

        col_c, col_d = st.columns(2)
        mortgage = col_c.selectbox("Pre-Approved?", ["approved", "not_approved", "checking"])
        cash_buyer = col_d.checkbox("Cash Buyer?")

        st.write("---")
        st.subheader("US Compliance")
        sms_opt_in = st.checkbox("I agree to receive SMS alerts. Reply STOP to opt-out. (TCPA Compliant)")

        message = st.text_area("Client Message / Notes")

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
                        recommended_action=scoring_result['action'],
                        sms_opt_in=sms_opt_in,
                        estimated_commission=scoring_result['commission']
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
                        await schedule_lead_follow_ups(
                            new_lead.id,
                            name,
                            email,
                            phone,
                            scoring_result['status'],
                            sms_opt_in
                        )

                    asyncio.run(run_tasks())

                    st.success("Thank you for your inquiry! An agent will contact you shortly.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                finally:
                    db.close()

# --- ENTERPRISE LEAD ENGINE TAB ---
with tabs[2]:
    st.title("🏢 Enterprise Real Estate Lead Intelligence")
    st.write("Upload scraped agency data to qualify leads and generate premium outreach.")

    uploaded_file = st.file_uploader("Upload Scraped Leads (CSV)", type="csv")

    if uploaded_file is not None:
        df_uploaded = pd.read_csv(uploaded_file)
        st.write("### Preview Uploaded Data")
        st.dataframe(df_uploaded.head(), width="stretch")

        if st.button("🚀 Process & Analyze Leads"):
            db = SessionLocal()
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                for index, row in df_uploaded.iterrows():
                    # Update progress
                    progress = (index + 1) / len(df_uploaded)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {row.get('agency_name', 'Unknown')}...")

                    # Module 1: Clean and Score
                    agency_data = {
                        "agency_name": row.get("agency_name"),
                        "num_listings": row.get("num_listings", 0),
                        "google_rating": row.get("google_rating", 0),
                        "city": row.get("city"),
                        "owner_name": row.get("owner_name")
                    }
                    initial_analysis = clean_and_score_agency(agency_data)

                    # Module 2: Website Analysis
                    website = row.get("website")
                    homepage_text = ""
                    analysis_result = {}
                    if website:
                        homepage_text = scrape_homepage(website)
                        analysis_result = analyze_website_with_gpt(homepage_text, agency_data["agency_name"])

                    # Module 3: Qualification
                    qualification = qualify_agency(agency_data, analysis_result)

                    # Module 4: Outreach
                    outreach = generate_outreach_email(agency_data, analysis_result, qualification)

                    # Save to DB
                    agency_lead = AgencyLead(
                        agency_name=agency_data["agency_name"],
                        owner_name=row.get("owner_name"),
                        website=website,
                        phone=row.get("phone"),
                        email=row.get("email"),
                        city=row.get("city"),
                        state=row.get("state"),
                        google_rating=row.get("google_rating"),
                        num_listings=row.get("num_listings"),
                        classification=initial_analysis["classification"],
                        score=initial_analysis["score"],
                        strength_summary=initial_analysis["strength_summary"],
                        growth_opportunity_summary=initial_analysis["growth_opportunity_summary"],
                        tier=qualification["tier"],
                        market_analysis=json.dumps(analysis_result),
                        weaknesses=", ".join(analysis_result.get("weaknesses", [])),
                        outreach_email=f"Subject: {outreach['subject']}\n\n{outreach['body']}",
                        outreach_status="GENERATED"
                    )
                    db.add(agency_lead)

                db.commit()
                st.success(f"Successfully processed {len(df_uploaded)} leads!")
            except Exception as e:
                st.error(f"Error processing leads: {e}")
                db.rollback()
            finally:
                db.close()

    st.divider()
    st.subheader("📋 Analyzed Agency Leads")

    db = SessionLocal()
    try:
        agency_leads = db.query(AgencyLead).order_by(AgencyLead.created_at.desc()).all()
        if agency_leads:
            display_data = []
            for al in agency_leads:
                display_data.append({
                    "Agency": al.agency_name,
                    "Tier": al.tier,
                    "Score": al.score,
                    "Classification": al.classification,
                    "City": al.city,
                    "Listings": al.num_listings,
                    "Status": al.outreach_status
                })

            df_display = pd.DataFrame(display_data)
            st.dataframe(df_display, width="stretch", hide_index=True)

            # Action: View Details & Export
            selected_agency = st.selectbox("Select Agency to view Outreach", options=agency_leads, format_func=lambda x: x.agency_name)

            if selected_agency:
                col_view1, col_view2 = st.columns(2)
                with col_view1:
                    st.info(f"**Strength:** {selected_agency.strength_summary}")
                    st.warning(f"**Weaknesses:** {selected_agency.weaknesses}")
                with col_view2:
                    st.success(f"**Opportunity:** {selected_agency.growth_opportunity_summary}")
                    st.write(f"**Tier Explanation:** {selected_agency.tier}")

                st.text_area("Generated Outreach Email", selected_agency.outreach_email, height=300)

            # Export
            csv_export = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Analyzed Leads to CSV",
                data=csv_export,
                file_name="analyzed_agency_leads.csv",
                mime="text/csv",
            )
        else:
            st.write("No analyzed agency leads found. Upload a CSV to get started.")
    finally:
        db.close()
