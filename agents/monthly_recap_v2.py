"""
Fortnightly Audio Recap — v2
=============================
Uses Sarvam AI Bulbul v3 with Shubh voice.
Actual API limit is 500 chars/request. A ~3000 char script
needs ~7 chunks. Stitched into one WAV output.

Free credits: Rs.1000 (never expire) ~140 recaps at Rs.14 each (v3 rate).
Voice: Shubh — male, conversational, Indian English
"""
import os, json, datetime, requests, re, base64
from dotenv import load_dotenv
load_dotenv()

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
CHUNK_SIZE     = 450    # actual API limit is 500 — stay under with buffer


# ── PROMPT ────────────────────────────────────────────────────

STANDUP_PROMPT = """You are writing a spoken comedy script covering the biggest AI news from the last 15 days.

YOUR STYLE:
- Opening story: Anubhav Singh Bassi — slow build, full context, Indian everyday angle
- Remaining 4 stories: Samay Raina podcast energy — fast, sharp, conversational

NOT western standup. Indian storytelling comedy.

IMPORTANT — PLAIN TEXT ONLY. NO XML, NO TAGS, NO ANGLE BRACKETS.
Create rhythm through sentence structure:
- Short sentences. Full stops. Natural gaps.
- Use "..." max 3 times for dramatic effect only
- Punctuation creates the rhythm

SECTION 1 — OPENING STORY (Bassi style, ~2 minutes):
1. Set the scene. Who these people are. What they do. Why anyone cares.
   Like telling a friend over chai. Short sentences.
2. What everyone expected. What was promised. The hype.
3. What actually happened. The gap between promise and reality.
4. One observation. One sentence. Then one that twists it.
5. Relate to something every Indian understands — job pressure,
   relatives asking about future, board exams, jugaad.

SECTION 2 — FOUR QUICK HITS (Samay style):
Each story: "Okay so [company] did [thing]. [What it means plainly]. [The funny observation]."
Three sentences. Done. Move on.

HARD RULES:
- NO XML or angle bracket tags whatsoever
- NO opening greeting — start mid-thought
- Plain text only
- 600-700 words MAX
- Roast companies. Never the listener.
- Hindi words fine: yaar, matlab, bhai, waise
- End with one useful thing to try + warm sign-off

Period: {period}
Stories:
---
{stories_text}
---

Write the full script now. Plain text only.
"""


# ── SCRIPT WRITER ─────────────────────────────────────────────

def write_standup_script(stories: list, period: str) -> str:
    from utils.llm import call_llm

    stories_text = ""
    for i, s in enumerate(stories, 1):
        stories_text += f"{i}. {s.get('headline', '')}\n"
        stories_text += f"   Source: {s.get('source', '')}\n"
        stories_text += f"   What: {s.get('what', '')}\n"
        stories_text += f"   Roast: {s.get('roast', '')}\n\n"

    print(f"[Recap] Writing script for {period}...")
    script = call_llm(
        STANDUP_PROMPT.format(period=period, stories_text=stories_text),
        expect_json=False,
        temperature=0.95,
    )
    # Strip any XML tags the LLM snuck in anyway
    script = re.sub(r"<[^>]+>", "", script).strip()
    print(f"[Recap] Script: {len(script)} chars")
    return script


# ── SARVAM TTS ────────────────────────────────────────────────

def _chunk_text(text: str, size: int = CHUNK_SIZE) -> list:
    """
    Split at sentence boundaries, max `size` chars per chunk.
    With bulbul:v3's 2500 char limit and size=2000,
    a 4700 char script becomes just 2-3 clean chunks.
    """
    parts   = re.split(r"(?<=[.!?])\s+", text)
    chunks  = []
    current = ""

    for part in parts:
        if len(current) + len(part) + 1 <= size:
            current = (current + " " + part).strip()
        else:
            if current:
                chunks.append(current)
            # Single sentence longer than chunk — hard split
            if len(part) > size:
                for i in range(0, len(part), size):
                    chunks.append(part[i:i+size])
                current = ""
            else:
                current = part

    if current:
        chunks.append(current)

    return chunks


def _sarvam_chunk(api_key: str, text: str) -> bytes | None:
    """Call Sarvam bulbul:v3 for one chunk. Returns WAV bytes or None."""
    try:
        resp = requests.post(
            SARVAM_TTS_URL,
            headers={
                "api-subscription-key": api_key,
                "Content-Type":         "application/json",
            },
            json={
                "inputs":               [text],
                "target_language_code": "en-IN",
                "speaker":              "shubh",      # v3 default, Indian English male
                "model":                "bulbul:v3",  # Shubh is v3 voice
                "speech_sample_rate":   24000,         # v3 default
                "pace":                 0.9,           # slightly slower for storytelling
                "temperature":          0.7,           # expressive but stable
            },
            timeout=60,
        )

        if resp.status_code == 200:
            audio_b64 = resp.json().get("audios", [None])[0]
            if audio_b64:
                return base64.b64decode(audio_b64)
            print(f"[Sarvam] No audio in response: {resp.json()}")
            return None

        print(f"[Sarvam] {resp.status_code}: {resp.text[:300]}")
        return None

    except Exception as e:
        print(f"[Sarvam] Request error: {e}")
        return None


def text_to_speech(script: str) -> bytes | None:
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY missing from .env")

    chunks = _chunk_text(script)
    print(f"[Sarvam] {len(script)} chars split into {len(chunks)} chunks")

    parts = []
    for i, chunk in enumerate(chunks):
        print(f"[Sarvam] Chunk {i+1}/{len(chunks)} — {len(chunk)} chars")
        audio = _sarvam_chunk(api_key, chunk)
        if audio:
            parts.append(audio)
        else:
            print(f"[Sarvam] Chunk {i+1} failed — skipping")

    if not parts:
        print("[Sarvam] All chunks failed")
        return None

    combined = b"".join(parts)
    print(f"[Sarvam] Done — {len(combined)//1024} KB ({len(parts)}/{len(chunks)} chunks ok)")
    return combined


# ── EMAIL ─────────────────────────────────────────────────────

def send_recap_email(audio_bytes: bytes, script: str, period: str) -> bool:
    import resend
    resend.api_key = os.environ["RESEND_API_KEY"]

    recipients = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
    if not recipients:
        raise ValueError("EMAIL_TO missing from .env")

    safe_period = period.replace(" ", "-").replace("–", "to")
    filename    = f"AI-Roast-{safe_period}.wav"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="background:#0e0e10;color:#f0f0f4;
             font-family:'Helvetica Neue',Arial,sans-serif;
             max-width:600px;margin:0 auto;padding:32px 24px;">
  <div style="border-bottom:3px solid #00ff88;padding-bottom:20px;margin-bottom:28px;">
    <div style="font-size:12px;color:#808090;font-family:monospace;
                text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
      Fortnightly Audio Recap
    </div>
    <h1 style="font-size:26px;font-weight:800;color:#ffe566;margin:0 0 6px 0;">
      AI Roast Brief
    </h1>
    <p style="font-size:15px;color:#b0b0c0;margin:0;">{period}</p>
  </div>
  <div style="background:#001a0d;border:1px solid #003322;border-left:4px solid #00ff88;
              border-radius:8px;padding:18px 20px;margin-bottom:24px;">
    <p style="font-family:monospace;font-size:12px;color:#00ff88;
              text-transform:uppercase;letter-spacing:.5px;margin:0 0 8px 0;">
      AUDIO ATTACHED
    </p>
    <p style="font-size:14px;color:#b0b0c0;margin:0;line-height:1.6;">
      Download <strong style="color:#fff">{filename}</strong> and listen on your commute. ~5 min.
    </p>
  </div>
  <div style="background:#17171a;border:1px solid #2c2c32;border-radius:8px;
              padding:20px;margin-bottom:24px;">
    <p style="font-family:monospace;font-size:11px;color:#808090;
              text-transform:uppercase;letter-spacing:.5px;margin:0 0 14px 0;">
      Full Script
    </p>
    <p style="font-size:14px;color:#b0b0c0;line-height:1.9;margin:0;
              white-space:pre-wrap;">{script}</p>
  </div>
  <p style="font-family:monospace;font-size:11px;color:#3a3a42;text-align:center;margin:0;">
    AI Roast Brief · Fortnightly Recap
  </p>
</body></html>"""

    try:
        resp = resend.Emails.send({
            "from":    os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
            "to":      recipients,
            "subject": f"AI Roast Recap — {period}",
            "html":    html,
            "attachments": [{
                "filename":     filename,
                "content":      __import__("base64").b64encode(audio_bytes).decode("utf-8"),
                "content_type": "audio/wav",
            }],
        })
        rid = resp.id if hasattr(resp, "id") else resp.get("id", "unknown")
        print(f"[Sender] Sent — {rid}")
        return True
    except Exception as e:
        print(f"[Sender] {e}")
        return False


def _send_script_only(script: str, period: str):
    import resend
    resend.api_key = os.environ["RESEND_API_KEY"]
    recipients = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
    try:
        resend.Emails.send({
            "from":    os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
            "to":      recipients,
            "subject": f"AI Roast Recap — {period} (script only, audio failed)",
            "html":    f"<pre style='font-family:sans-serif;line-height:1.9'>{script}</pre>",
        })
        print("[Fallback] Script-only email sent")
    except Exception as e:
        print(f"[Fallback] {e}")


# ── STORY COLLECTOR ───────────────────────────────────────────

def collect_stories() -> list:
    brief_path = os.path.join(os.path.dirname(__file__), "..", "last_brief.json")
    try:
        with open(brief_path, encoding="utf-8") as f:
            stories = json.load(f).get("stories", [])
        print(f"[Recap] {len(stories)} stories loaded")
        return stories
    except FileNotFoundError:
        print("[Recap] No last_brief.json — using placeholder")
        return [{"headline": "AI had a wild fortnight", "source": "Various",
                 "what": "Many things happened.", "roast": "AGI still 6 months away."}]


# ── ENTRY POINT ───────────────────────────────────────────────

def run_fortnightly_recap():
    today = datetime.date.today()
    if today.day == 1:
        end   = today - datetime.timedelta(days=1)
        start = end.replace(day=16)
    else:
        start = today.replace(day=1)
        end   = today.replace(day=15)

    period = f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"

    print("\n" + "=" * 60)
    print(f"  FORTNIGHTLY RECAP v2 — Sarvam bulbul:v3 / Shubh")
    print(f"  Period: {period}")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    stories = collect_stories()
    script  = write_standup_script(stories, period)
    audio   = text_to_speech(script)

    if not audio:
        _send_script_only(script, period)
        return

    send_recap_email(audio, script, period)
    print(f"\n  DONE — {period}\n")


if __name__ == "__main__":
    run_fortnightly_recap()