"""
Email Sender — Resend API.
Compatible with resend >= 2.0.0
"""
import os, datetime
from dotenv import load_dotenv
load_dotenv()


def send_brief(html: str, brief: dict) -> bool:
    import resend
    resend.api_key = os.environ["RESEND_API_KEY"]

    to_raw = os.getenv("EMAIL_TO", "")
    recipients = [e.strip() for e in to_raw.split(",") if e.strip()]
    if not recipients:
        raise ValueError("EMAIL_TO is empty in .env — add your email address")

    from_addr = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    style    = brief.get("style", "DAILY")
    episode  = brief.get("episode", 1)
    date_str = brief.get("date", datetime.date.today().strftime("%Y-%m-%d"))
    try:
        display_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d")
    except Exception:
        display_date = date_str

    subject = f"🤖 AI Roast Brief — {display_date} | {style} Edition (#{episode})"

    print(f"[Sender] Sending to: {recipients}")
    print(f"[Sender] Subject: {subject}")

    try:
        # resend >= 2.0 uses resend.Emails.send()
        response = resend.Emails.send({
            "from": from_addr,
            "to": recipients,
            "subject": subject,
            "html": html,
        })
        # Response is an object in newer versions, dict in older
        rid = response.id if hasattr(response, "id") else response.get("id", "unknown")
        print(f"[Sender] ✓ Sent! Resend ID: {rid}")
        return True
    except Exception as e:
        print(f"[Sender] ✗ Failed: {e}")
        return False