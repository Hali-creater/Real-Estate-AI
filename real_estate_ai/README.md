# UAE Real Estate AI Lead Intelligence System

A sophisticated lead management system designed for UAE real estate agencies, featuring automated scoring, intelligence-driven actions, and real-time alerts.

## 🚀 Key Features

*   **Intelligent Lead Capture**: Multi-platform lead source tracking (PropertyFinder, Bayut, Website, etc.).
*   **AI Lead Scoring**: Rule-based engine that classifies leads as **HOT**, **WARM**, or **COLD** based on budget, timeframe, and financial status.
*   **Recommended Actions**: Instant instructions for agents (e.g., "Call within 10 minutes").
*   **Agent Dashboard**: Real-time metrics including "Speed to Lead" and "Close Probability".
*   **Telegram Integration**: Real-time alerts and automated follow-up reminders (1, 3, and 7 days).
*   **Flexible UI**: Choice between a modern **Streamlit** app and a lightweight **FastAPI** web form.

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI
*   **Frontend**: Streamlit / Jinja2 + Bootstrap
*   **Database**: SQLite (SQLAlchemy ORM)
*   **Automation**: APScheduler
*   **Alerts**: python-telegram-bot

## 📂 Project Structure

```text
real_estate_ai/
├── app.py              # Streamlit Application (Main UI)
├── main.py             # FastAPI Backend & API
├── models.py           # Database Models
├── database.py         # Database Configuration
├── lead_scoring.py     # AI Scoring Logic
├── telegram_bot.py     # Telegram Integration
├── scheduler.py        # Follow-up Automation
├── templates/          # HTML Templates for FastAPI
└── requirements.txt    # Project Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r real_estate_ai/requirements.txt
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
cd real_estate_ai
streamlit run app.py
```

#### FastAPI (Recommended for Web Form Integration)
```bash
cd real_estate_ai
uvicorn main:app --reload
```

## 🌐 Deployment Options

### 1. Streamlit Cloud (Free & Easiest)
*   Push this code to a GitHub repository.
*   Connect to [Streamlit Cloud](https://share.streamlit.io/).
*   Point to `real_estate_ai/app.py`.
*   Add your Telegram secrets in the "Settings > Secrets" section.

### 2. Render / Heroku / DigitalOcean
*   You can deploy the FastAPI version as a standard web service.
*   Use a persistent disk for the `real_estate.db` file if not using an external Postgres database.

### ⚠️ Note on GitHub Pages
This project **cannot** be deployed on GitHub Pages because it requires a Python backend to handle lead scoring, database storage, and background scheduling. GitHub Pages only supports static files.
