from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
try:
    from .telegram_bot import send_follow_up_reminder
except ImportError:
    from telegram_bot import send_follow_up_reminder

scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started.")

async def schedule_lead_follow_ups(lead_id: int, lead_name: str, lead_status: str):
    """
    Schedules 1, 3, and 7-day follow-up reminders for a new lead.
    """
    now = datetime.now(timezone.utc)

    # 1 Day Reminder
    scheduler.add_job(
        send_follow_up_reminder,
        'date',
        run_date=now + timedelta(days=1),
        args=[lead_name, lead_status, "1 day ago"],
        id=f"followup_1d_{lead_id}",
        replace_existing=True
    )

    # 3 Day Follow-up
    scheduler.add_job(
        send_follow_up_reminder,
        'date',
        run_date=now + timedelta(days=3),
        args=[lead_name, lead_status, "3 days ago"],
        id=f"followup_3d_{lead_id}",
        replace_existing=True
    )

    # 7 Day Reminder
    scheduler.add_job(
        send_follow_up_reminder,
        'date',
        run_date=now + timedelta(days=7),
        args=[lead_name, lead_status, "7 days ago"],
        id=f"followup_7d_{lead_id}",
        replace_existing=True
    )

    print(f"Follow-ups scheduled for lead {lead_id}: {lead_name}")
