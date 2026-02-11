# SpeedToLead AI: US Realtor Appointment Engine

A high-performance lead intelligence and automated follow-up system designed for US Real Estate professionals. Convert Zillow, Realtor.com, and Facebook leads into booked appointments with extreme care and precision.

## 🚀 Key Features

*   **US Market Optimized**: Tailored for Zillow/Realtor.com lead sources and ZIP-code based neighborhood targeting.
*   **AI Lead Scoring & ROI**: Rule-based engine that classifies leads (**HOT**, **WARM**, **COLD**) and calculates **Estimated Commission ROI** (2.5% standard).
*   **Automated US Drip Campaigns**: Professional SMS and Email drips (1, 3, and 7 days) with **TCPA/CAN-SPAM Compliance** ("Reply STOP to opt-out").
*   **Quiet Hours Logic**: Intelligent scheduling that prevents automated SMS during nighttime hours (8 PM - 8 AM).
*   **Appointment Tracking**: Dedicated dashboard to track booked appointments and sync status.
*   **Agent Dashboard**: Real-time metrics including "Speed to Lead", "Total ROI", and "Appointment Conversion".
*   **Flexible UI**: Choice between a powerful **Streamlit** dashboard and a lightweight **FastAPI** web intake form.

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI
*   **Frontend**: Streamlit / Jinja2 + Bootstrap
*   **Database**: SQLite (SQLAlchemy ORM)
*   **Automation**: APScheduler
*   **Alerts**: python-telegram-bot

## 📂 Project Structure

```text
.
├── app.py              # Streamlit Application (Main UI)
├── main.py             # FastAPI Backend & API
├── models.py           # Database Models
├── database.py         # Database Configuration
├── lead_scoring.py     # AI Scoring & ROI Logic
├── communication.py    # US SMS/Email Scripts & Stubs
├── telegram_bot.py     # Internal Agent Alerts
├── scheduler.py        # Follow-up Automation
├── templates/          # HTML Templates for FastAPI
└── requirements.txt    # Project Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Telegram (Optional)
Set your environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 3. Run the Application

#### Streamlit (Recommended for Dashboards)
```bash
streamlit run app.py
```

#### FastAPI (Recommended for Web Form Integration)
```bash
uvicorn main:app --reload
```

## 🌐 Deployment Options

### 1. Streamlit Cloud (Free & Easiest)
*   Push this code to a GitHub repository.
*   Connect to [Streamlit Cloud](https://share.streamlit.io/).
*   **IMPORTANT**: In the deployment settings, ensure the **Main file path** is set to `app.py`. (Previously it might have been `real_estate_ai/app.py`).
*   Add your Telegram secrets in the "Settings > Secrets" section.

### 2. Render / Heroku / DigitalOcean
*   You can deploy the FastAPI version as a standard web service.
*   Use a persistent disk for the `real_estate.db` file if not using an external Postgres database.

### ⚠️ Note on GitHub Pages
This project **cannot** be deployed on GitHub Pages because it requires a Python backend to handle lead scoring, database storage, and background scheduling. GitHub Pages only supports static files.
