import asyncio
import os
from telegram import Bot
from telegram.constants import ParseMode

# These should be set in environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_alert(lead_details: dict):
    """
    Sends a formatted alert to the agent group on Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram Bot Token or Chat ID not configured. Skipping alert.")
        print(f"Alert Content: {lead_details}")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    status_emoji = "🔥" if lead_details['status'] == "HOT" else "⚠️" if lead_details['status'] == "WARM" else "❄️"

    message = (
        f"{status_emoji} *{lead_details['status']} LEAD ALERT*\n\n"
        f"*Name:* {lead_details['name']}\n"
        f"*Budget:* ${lead_details['budget']:,}\n"
        f"*Area:* {lead_details['area']}\n"
        f"*Timeframe:* {lead_details['timeframe']}\n"
        f"*Close Probability:* {lead_details['probability']}%\n\n"
        f"*Recommended Action:*\n"
        f"{lead_details['action']}"
    )

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        print("Telegram alert sent successfully.")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

async def send_follow_up_reminder(lead_name: str, status: str, last_contact: str):
    """
    Sends a follow-up reminder to Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"Telegram Reminder (Not Sent): Follow up with {lead_name}")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    message = (
        f"⏰ *Follow-Up Reminder*\n\n"
        f"*Lead:* {lead_name}\n"
        f"*Status:* {status}\n"
        f"*Last Contact:* {last_contact}\n\n"
        f"*Suggested Message:*\n"
        f"\"Hi {lead_name}, just checking if you'd like to schedule a viewing this week.\""
    )

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"Failed to send Telegram reminder: {e}")
