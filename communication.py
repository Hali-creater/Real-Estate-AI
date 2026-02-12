import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    Attempts real SMTP if configured, else stubs.
    """
    footer = (
        "\n\n---\n"
        "You are receiving this because you inquired about our AI Sales Infrastructure. "
        "To unsubscribe, please reply STOP. [Enterprise Compliance]"
    )
    full_body = f"{body}{footer}"

    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if smtp_server and smtp_user and smtp_password:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(full_body, 'plain'))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            print(f"Successfully sent email to {email} via SMTP.")
            return True
        except Exception as e:
            print(f"Failed to send email via SMTP: {e}")
            return False
    else:
        print(f"--- [EMAIL STUB] to {email} ---")
        print(f"Subject: {subject}")
        print(full_body)
        print("--- [SMTP NOT CONFIGURED] ---")
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
