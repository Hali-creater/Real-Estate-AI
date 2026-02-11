import os
from datetime import datetime
import pytz

# Constants for US Compliance
QUIET_HOURS_START = 20 # 8 PM
QUIET_HOURS_END = 8    # 8 AM

async def send_sms_lead(phone: str, message: str, opt_in: bool):
    """
    Sends a professional US-style SMS.
    Includes TCPA compliance check.
    """
    if not opt_in:
        print(f"TCPA Block: SMS not sent to {phone} (No Opt-in).")
        return False

    # Check Quiet Hours (Simplified, assumes US Eastern Time or server time)
    now_hour = datetime.now().hour
    if now_hour >= QUIET_HOURS_START or now_hour < QUIET_HOURS_END:
        print(f"Compliance Block: SMS to {phone} delayed due to quiet hours.")
        return False

    # US Style Message addition
    compliance_suffix = "\n\nReply STOP to unsubscribe."
    full_message = f"{message}{compliance_suffix}"

    print(f"--- [SMS SENT via Twilio Stub] to {phone} ---")
    print(full_message)
    print("---------------------------------------------")
    return True

async def send_email_lead(email: str, subject: str, body: str):
    """
    Sends a professional US-style Email drip.
    Includes CAN-SPAM compliance footer.
    """
    footer = (
        "\n\n---\n"
        "You are receiving this because you inquired about a property listing. "
        "To unsubscribe, please click here: [Unsubscribe Link]"
    )
    full_body = f"{body}{footer}"

    print(f"--- [EMAIL SENT via SendGrid Stub] to {email} ---")
    print(f"Subject: {subject}")
    print(full_body)
    print("-----------------------------------------------")
    return True

def get_us_realtor_script(lead_name: str, lead_status: str):
    """
    Returns friendly, helpful US-style professional scripts.
    """
    if lead_status == "HOT":
        return (
            f"Hi {lead_name}! I saw your interest in the property. I'd love to help you "
            f"schedule a showing. What day works best for you this week?"
        )
    elif lead_status == "WARM":
        return (
            f"Hi {lead_name}, thanks for reaching out! I've put together a list of similar "
            f"homes you might like. Would you like me to send them over?"
        )
    else:
        return (
            f"Hi {lead_name}, thanks for your inquiry! I'm here to help whenever you're "
            f"ready to start your home search. Feel free to reach out with any questions."
        )
