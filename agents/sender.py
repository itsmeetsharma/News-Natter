"""
Email Sender
============
Delivers the final HTML email via Resend.
Supports comma-separated recipients in EMAIL_TO.
"""
import os, datetime
from dotenv import load_dotenv
load_dotenv()


def send_brief(html: str, brief: dict) -> bool:
    import resend
    resend.api_key = os.environ["RESEND_API_KEY"]

    recipients = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
    if not recipients:
        raise ValueError("EMAIL_TO is empty in .env")

    date_str = brief.get("date", datetime.date.today().strftime("%Y-%m-%d"))
    try:
        display_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d")
    except Exception:
        display_date = date_str

    subject = (
        f"🤖 AI Roast Brief — {display_date} | "
        f"{brief.get('style', 'DAILY')} Edition (#{brief.get('episode', 1)})"
    )

    print(f"[Sender] To: {recipients}")
    print(f"[Sender] Subject: {subject}")

    try:
        resp = resend.Emails.send({
            "from":    os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
            "to":      recipients,
            "subject": subject,
            "html":    html,
        })
        rid = resp.id if hasattr(resp, "id") else resp.get("id", "unknown")
        print(f"[Sender] ✓ Sent — Resend ID: {rid}")
        return True
    except Exception as e:
        print(f"[Sender] ✗ {e}")
        return False
