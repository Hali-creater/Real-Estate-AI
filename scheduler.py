try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
    # Fallback if not installed (though it should be)
    AsyncIOScheduler = None
    BackgroundScheduler = None

from datetime import datetime, timedelta, timezone
import asyncio

try:
    from .telegram_bot import send_follow_up_reminder
    from .communication import send_sms_lead, send_email_lead, get_us_realtor_script
except ImportError:
    from telegram_bot import send_follow_up_reminder
    from communication import send_sms_lead, send_email_lead, get_us_realtor_script

# Detect if we are in an environment that prefers BackgroundScheduler (like Streamlit)
# or AsyncIOScheduler (like FastAPI)
# For simplicity, we'll try to use AsyncIOScheduler first if a loop is running.

scheduler = AsyncIOScheduler()

def start_scheduler():
    global scheduler
    if not scheduler.running:
        try:
            # Check if there is a running event loop
            asyncio.get_running_loop()
            scheduler.start()
        except RuntimeError:
            # No running event loop, we might need to handle this for Streamlit
            # Actually AsyncIOScheduler.start() might fail if no loop.
            # Let's use BackgroundScheduler if no loop is found.
            if not isinstance(scheduler, BackgroundScheduler):
                scheduler = BackgroundScheduler()
            scheduler.start()
        print(f"Scheduler started using {type(scheduler).__name__}.")

def is_quiet_hours():
    """
    Check if current time is outside 8 AM - 8 PM.
    In production, this should be adjusted for the lead's local timezone.
    """
    # Using UTC for simplicity in this demo, but real-world would use lead's local time
    now_hour = datetime.now().hour
    return now_hour < 8 or now_hour > 20

async def run_us_drip(lead_id: int, name: str, email: str, phone: str, status: str, opt_in: bool, timeframe: str):
    """
    Executes a US-style SMS/Email drip step.
    """
    script = get_us_realtor_script(name, status)

    # Send Internal Telegram Alert to Agent (Always send to agent)
    await send_follow_up_reminder(name, status, timeframe)

    # Send Customer SMS (Compliance check + Quiet Hours check)
    if not is_quiet_hours():
        await send_sms_lead(phone, script, opt_in)
    else:
        print(f"Quiet hours active. Skipping SMS for {name} at this time.")

    # Send Customer Email (Usually okay 24/7, but we could restrict it too)
    await send_email_lead(email, f"Quick question regarding your home search", script)

async def schedule_lead_follow_ups(lead_id: int, lead_name: str, lead_email: str, lead_phone: str, lead_status: str, sms_opt_in: bool):
    """
    Schedules US-style 1, 3, and 7-day drip campaigns for a new lead.
    """
    now = datetime.now(timezone.utc)

    def run_drip_wrapper(id, n, e, p, s, opt, t):
        try:
            asyncio.run(run_us_drip(id, n, e, p, s, opt, t))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(run_us_drip(id, n, e, p, s, opt, t))
            else:
                loop.run_until_complete(run_us_drip(id, n, e, p, s, opt, t))

    is_async = isinstance(scheduler, AsyncIOScheduler)
    job_func = run_us_drip if is_async else run_drip_wrapper

    # 1 Day Drip
    scheduler.add_job(
        job_func,
        'date',
        run_date=now + timedelta(days=1),
        args=[lead_id, lead_name, lead_email, lead_phone, lead_status, sms_opt_in, "1 day follow-up"],
        id=f"followup_1d_{lead_id}",
        replace_existing=True
    )

    # 3 Day Drip
    scheduler.add_job(
        job_func,
        'date',
        run_date=now + timedelta(days=3),
        args=[lead_id, lead_name, lead_email, lead_phone, lead_status, sms_opt_in, "3 day follow-up"],
        id=f"followup_3d_{lead_id}",
        replace_existing=True
    )

    # 7 Day Drip
    scheduler.add_job(
        job_func,
        'date',
        run_date=now + timedelta(days=7),
        args=[lead_id, lead_name, lead_email, lead_phone, lead_status, sms_opt_in, "7 day follow-up"],
        id=f"followup_7d_{lead_id}",
        replace_existing=True
    )

    print(f"Follow-ups scheduled for lead {lead_id}: {lead_name}")
