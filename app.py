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
        qualify_agency, generate_outreach_email, discover_agencies
    )
except ImportError:
    from .database import init_db, SessionLocal
    from .models import Lead, AgencyLead
    from .lead_scoring import calculate_lead_score
    from .telegram_bot import send_telegram_alert
    from .scheduler import start_scheduler, schedule_lead_follow_ups
    from .agency_intelligence import (
        clean_and_score_agency, scrape_homepage, analyze_website_with_gpt,
        qualify_agency, generate_outreach_email, discover_agencies
    )

# Page Config
st.set_page_config(page_title="SpeedToLead AI: Enterprise Engine", layout="wide", page_icon="🚀")

# Initialize DB
@st.cache_resource
def startup():
    init_db()
    try:
        start_scheduler()
    except Exception as e:
        print(f"Scheduler error: {e}")
    return True

startup()

# Navigation
tabs = st.tabs(["📊 Agent Dashboard", "📝 Lead Capture Form", "🏢 Enterprise Engine"])

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
            st.dataframe(df, use_container_width=True, hide_index=True)

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

# --- ENTERPRISE ENGINE TAB ---
with tabs[2]:
    st.title("🏢 Enterprise Business Intelligence Engine")
    st.markdown("### Identify. Qualify. Automate.")

    # Discovery Sub-section
    with st.expander("🔍 Lead Discovery (Google Search)", expanded=False):
        col_d1, col_d2 = st.columns([3, 1])
        search_query = col_d1.text_input("Search Query", placeholder="e.g. site:zillow.com real estate agents Miami", key="ent_search")
        if col_d2.button("Discover Agencies"):
            if search_query:
                with st.spinner("Scraping Intelligence..."):
                    discovered = discover_agencies(search_query)
                    if discovered:
                        st.session_state['discovered_leads'] = discovered
                        st.success(f"Found {len(discovered)} candidates.")
                    else:
                        st.warning("No candidates found.")

        if 'discovered_leads' in st.session_state:
            df_discovered = pd.DataFrame(st.session_state['discovered_leads'])
            st.dataframe(df_discovered, use_container_width=True)
            if st.button("Process Discovered Leads"):
                db = SessionLocal()
                try:
                    for d in st.session_state['discovered_leads']:
                        agency_lead = AgencyLead(agency_name=d['agency_name'], website=d['website'], city=d['city'], outreach_status="PENDING")
                        db.add(agency_lead)
                    db.commit()
                    st.success("Imported for analysis.")
                finally:
                    db.close()

    st.divider()

    # Processing Section
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("📤 Bulk Upload")
        uploaded_file = st.file_uploader("Upload CSV", type="csv", key="ent_upload")
        if uploaded_file:
            df_up = pd.read_csv(uploaded_file)
            if st.button("Process Upload"):
                db = SessionLocal()
                progress_bar = st.progress(0)
                try:
                    total = len(df_up)
                    for idx, row in df_up.iterrows():
                        progress_bar.progress((idx + 1) / total)
                        agency_data = {
                            "agency_name": row.get('agency_name'),
                            "num_listings": row.get('num_listings', 0),
                            "google_rating": row.get('google_rating', 0),
                            "city": row.get('city'),
                            "owner_name": row.get('owner_name')
                        }
                        init_analysis = clean_and_score_agency(agency_data)
                        text = scrape_homepage(row.get('website'))
                        gpt_analysis = analyze_website_with_gpt(text, agency_data['agency_name'])
                        qual = qualify_agency(agency_data, gpt_analysis)
                        outreach = generate_outreach_email(agency_data, gpt_analysis, qual)

                        al = AgencyLead(
                            agency_name=agency_data['agency_name'],
                            owner_name=agency_data['owner_name'],
                            website=row.get('website'),
                            phone=row.get('phone'),
                            email=row.get('email'),
                            city=agency_data['city'],
                            state=row.get('state'),
                            num_listings=agency_data['num_listings'],
                            google_rating=agency_data['google_rating'],
                            classification=init_analysis['classification'],
                            score=init_analysis['score'],
                            strength_summary=init_analysis['strength_summary'],
                            growth_opportunity_summary=init_analysis['growth_opportunity_summary'],
                            tier=qual['tier'],
                            market_analysis=json.dumps(gpt_analysis),
                            weaknesses=", ".join(gpt_analysis.get('weaknesses', [])),
                            outreach_email=f"Subject: {outreach['subject']}\n\n{outreach['body']}",
                            outreach_status="GENERATED"
                        )
                        db.add(al)
                    db.commit()
                    st.success("Processing complete.")
                except Exception as e:
                    st.error(f"Processing error: {e}")
                finally:
                    db.close()

    # Dashboard Section
    st.subheader("📊 Enterprise Lead Pipeline")
    db = SessionLocal()
    try:
        agencies = db.query(AgencyLead).order_by(AgencyLead.created_at.desc()).all()
        if agencies:
            # Stats
            t1 = sum(1 for a in agencies if "Tier 1" in (a.tier or ""))
            t2 = sum(1 for a in agencies if "Tier 2" in (a.tier or ""))

            s1, s2, s3 = st.columns(3)
            s1.metric("Tier 1 (Enterprise)", t1)
            s2.metric("Tier 2 (Growth)", t2)
            s3.metric("Avg Quality Score", f"{sum(a.score or 0 for a in agencies)/len(agencies):.1f}/10")

            # List
            for a in agencies:
                with st.expander(f"🏢 {a.agency_name} - {a.tier or 'Unranked'} (Score: {a.score}/10)"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Business Intelligence:**")
                        st.write(f"📍 Market: {a.city}")
                        st.write(f"🏠 Listings: {a.num_listings}")
                        st.write(f"🏷️ Class: {a.classification}")
                        st.info(f"Strength: {a.strength_summary}")
                    with c2:
                        st.markdown("**Gaps & Opportunities:**")
                        st.warning(f"Weaknesses: {a.weaknesses}")
                        st.success(f"Growth: {a.growth_opportunity_summary}")

                    st.divider()
                    st.markdown("**Enterprise Outreach Generator:**")
                    st.text_area("Personalized Email", a.outreach_email, height=200, key=f"email_{a.id}")
                    if st.button("Send Outreach", key=f"send_{a.id}"):
                        st.info("Outreach queued via Enterprise SMTP.")

            # Enhanced CSV Export including outreach emails
            export_data = []
            for a in agencies:
                export_data.append({
                    "Agency": a.agency_name,
                    "Tier": a.tier,
                    "Score": a.score,
                    "City": a.city,
                    "Listings": a.num_listings,
                    "Weaknesses": a.weaknesses,
                    "Outreach Email": a.outreach_email
                })

            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Intelligence Report & Emails", data=csv, file_name="enterprise_leads_full.csv", mime="text/csv")
        else:
            st.info("No agency leads found in the system.")
    finally:
        db.close()
