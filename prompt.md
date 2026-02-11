UAE Real Estate AI Lead Intelligence System

With Telegram Deal Alerts

 SYSTEM OVERVIEW

Flow:

Buyer → Web Form → Backend → Lead Scoring → Database →
Telegram Alert → Agent Dashboard → Follow-Up Engine

 TECH STACK (Python Only)
Backend

FastAPI → API + form handling

Uvicorn → ASGI server

Database

SQLite (V1)

Later upgrade to PostgreSQL

Use:

SQLAlchemy (ORM)

Lead Scoring / Intelligence

Pure rule engine (Python)

Optional: scikit-learn (logistic regression for close probability)

Telegram

python-telegram-bot

Scheduling / Follow-ups

APScheduler

Dashboard

Option A: Streamlit
Option B: Simple Jinja2 templates inside FastAPI

For speed → Use Jinja2 with FastAPI.

Data Handling

pandas (optional for analytics)

 PROJECT STRUCTURE
real_estate_ai/
│
├── main.py
├── database.py
├── models.py
├── lead_scoring.py
├── telegram_bot.py
├── scheduler.py
├── dashboard.py
├── templates/
│   ├── form.html
│   ├── dashboard.html
│
└── requirements.txt

 MODULE BREAKDOWN
1️ LEAD CAPTURE MODULE
Purpose:

Capture buyer inquiries from website.

Form Fields:

Full Name

Phone

Email

Budget (AED)

Preferred Area

Property Type

Buying Timeframe

Mortgage Approved? (Yes/No)

Cash Buyer? (Yes/No)

Message

FastAPI Endpoint

POST /submit-lead

Stores data into database.

2️ DATABASE MODELS

Using SQLAlchemy:

Lead Table:

id

name

phone

email

budget

area

property_type

timeframe

mortgage_status

cash_buyer

message

score

close_probability

lead_status (HOT/WARM/COLD)

created_at

last_contacted

response_time_minutes

3️ LEAD SCORING ENGINE

File: lead_scoring.py

Rule-based logic example:

score = 0

if cash_buyer:
    score += 25

if mortgage_status == "approved":
    score += 20

if timeframe == "1 month":
    score += 30
elif timeframe == "3 months":
    score += 15

if budget > 1_500_000:
    score += 15

if "urgent" in message.lower():
    score += 10


Classification:

if score >= 70:
    status = "HOT"
elif score >= 40:
    status = "WARM"
else:
    status = "COLD"


Close probability:

probability = min(score * 1.2, 95)


Return:

score

probability

status

4️⃣ TELEGRAM ALERT ENGINE

Using python-telegram-bot

When new lead is stored:

Send message to agent group:

Example alert:

 HOT LEAD ALERT

Name: Ahmed
Budget: 2.3M AED
Area: Dubai Marina
Timeframe: 1 Month
Close Probability: 78%

Recommended Action:
Call within 10 minutes.

5️ FOLLOW-UP AUTOMATION ENGINE

Using APScheduler

When lead is created:

Schedule:

1 day reminder

3 day follow-up

7 day reminder

Telegram reminder example:

 Follow-Up Reminder

Lead: Ahmed
Status: HOT
Last Contact: 2 days ago

Suggested Message:
"Hi Ahmed, just checking if you'd like to schedule a viewing this week."

6️⃣ DASHBOARD MODULE

Basic features:

Total leads

HOT leads count

WARM leads count

Average response time

Close probability leaderboard

Filter by date

Metrics that impress agency:

Speed to Lead

% Hot Leads

Agent Response Ranking

7️ SPEED-TO-LEAD TRACKER (Important Feature)

When lead is created:
Store timestamp.

When agent clicks “Mark Contacted”:
Calculate:

response_time = contacted_time - created_time

Store minutes.

Display:

“Average Response Time: 18 minutes”

This is powerful.

 requirements.txt
fastapi
uvicorn
sqlalchemy
jinja2
python-telegram-bot
apscheduler
pydantic
pandas
scikit-learn
