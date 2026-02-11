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
except ImportError:
    from telegram_bot import send_follow_up_reminder

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

async def schedule_lead_follow_ups(lead_id: int, lead_name: str, lead_status: str):
    """
    Schedules 1, 3, and 7-day follow-up reminders for a new lead.
    """
    now = datetime.now(timezone.utc)

    def run_reminder(name, status, timeframe):
        try:
            asyncio.run(send_follow_up_reminder(name, status, timeframe))
        except RuntimeError:
            # Already in an event loop?
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(send_follow_up_reminder(name, status, timeframe))
            else:
                loop.run_until_complete(send_follow_up_reminder(name, status, timeframe))

    # Determine the job function based on scheduler type
    is_async = isinstance(scheduler, AsyncIOScheduler)
    job_func = send_follow_up_reminder if is_async else run_reminder

    # 1 Day Reminder
    scheduler.add_job(
        job_func,
        'date',
        run_date=now + timedelta(days=1),
        args=[lead_name, lead_status, "1 day ago"],
        id=f"followup_1d_{lead_id}",
        replace_existing=True
    )

    # 3 Day Follow-up
    scheduler.add_job(
        job_func,
        'date',
        run_date=now + timedelta(days=3),
        args=[lead_name, lead_status, "3 days ago"],
        id=f"followup_3d_{lead_id}",
        replace_existing=True
    )

    # 7 Day Reminder
    scheduler.add_job(
        job_func,
        'date',
        run_date=now + timedelta(days=7),
        args=[lead_name, lead_status, "7 days ago"],
        id=f"followup_7d_{lead_id}",
        replace_existing=True
    )

    print(f"Follow-ups scheduled for lead {lead_id}: {lead_name}")
