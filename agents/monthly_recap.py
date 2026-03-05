"""
Fortnightly Audio Recap
=======================
Runs every 15 days (1st and 16th of each month).
Groq writes a standup script (Bassi opening + Samay quick hits)
→ ElevenLabs converts to MP3 → Resend emails it with audio attached.

Free tier math:
  ElevenLabs: 10,000 chars/month
  Each script: ~4,500 chars
  2 runs/month = ~9,000 chars ✓
"""
import os, json, datetime, requests
from dotenv import load_dotenv
load_dotenv()


# ── PROMPT ────────────────────────────────────────────────────

STANDUP_PROMPT = """You are writing a spoken comedy script covering the biggest AI news from the last 15 days.

YOUR STYLE:
- Opening story: Anubhav Singh Bassi — slow build, full context, Indian everyday angle, dramatic pause before punchline
- Remaining 4 stories: Samay Raina podcast energy — fast, sharp, conversational, still Indian

This is NOT western standup. No rapid-fire punchlines. Indian storytelling comedy.

═══════════════════════════
SECTION 1 — OPENING STORY (Bassi style, ~2 minutes)
═══════════════════════════
Pick the single BIGGEST or most absurd story from the list.

Structure:
1. Set the full scene — who these people are, what they do, why anyone cares.
   Explain like you're telling a friend who doesn't follow tech. No jargon without explanation.
   2-3 sentences. Conversational.

2. <break time="0.5s" /> What everyone expected. What the company promised. The hype. Slightly exaggerated.

3. <break time="0.8s" /> What actually happened. The gap between promise and reality.
   Or if it was genuinely good — what's suspicious about it.

4. <break time="1.2s" /> One sentence observation. Let it land.
   <break time="1.0s" /> One more sentence that twists it.
   <break time="1.5s" />

5. Relate to something every Indian understands — job pressure, relatives asking about future,
   board exams, startup culture, jugaad. This is the Bassi moment.
   <break time="1.0s" />

═══════════════════════════
SECTION 2 — FOUR QUICK HITS (Samay style, 30-40 sec each)
═══════════════════════════
Cover remaining 4 stories. Each one EXACTLY like this:

"Okay so [company] did [thing]. <break time="0.4s" />
[One sentence — what this actually means in plain words]. <break time="0.6s" />
[The observation — what's funny or ironic]. <break time="1.0s" />"

No over-explaining. No extra sentences. Move on immediately.
Think Samay reacting to chess drama — quick, sharp, done.

═══════════════════════════
PAUSE REFERENCE
═══════════════════════════
<break time="0.4s" /> = small breath between related sentences
<break time="0.6s" /> = before an observation
<break time="0.8s" /> = before a punchline
<break time="1.0s" /> = after any punchline — let it breathe
<break time="1.2s" /> = Bassi dramatic pause before main joke
<break time="1.5s" /> = after the biggest laugh of opening story

═══════════════════════════
HARD RULES
═══════════════════════════
- NO opening greeting. Start mid-thought about this fortnight's AI vibe.
- Write for the EAR. Zero markdown, zero bullets, zero headers.
- ONLY <break time="Xs" /> tags allowed — nothing else
- Total: 600-750 words MAX (keeps under 5000 chars for ElevenLabs free tier)
- Roast companies and hype. NEVER the listener.
- Hindi words fine if natural: yaar, matlab, bhai, waise, basically
- Do NOT explain the joke. Do NOT say "get it?" or "am I right?"
- End with: one useful thing to try + warm sign-off. Not a joke.

Period: {period}
Stories (pick best 1 for opening, remaining 4 for quick hits):
---
{stories_text}
---

Write the full script now.
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

    prompt = STANDUP_PROMPT.format(period=period, stories_text=stories_text)

    print(f"[Recap] Writing standup script for {period}...")
    script = call_llm(prompt, expect_json=False, temperature=0.95)
    char_count = len(script)
    print(f"[Recap] Script: {char_count} chars (~{char_count // 900} min spoken)")

    # Hard cap — ElevenLabs free tier safety
    if char_count > 4800:
        print("[Recap] ⚠ Too long — trimming to protect free tier quota")
        script = script[:4700] + " <break time='1.0s' /> That's the fortnight in AI. Stay curious, yaar."

    return script


# ── ELEVENLABS TTS ────────────────────────────────────────────

def text_to_speech(script: str) -> bytes | None:
    api_key  = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "nPczCjzI2devNBz1zQrb")  # Brian

    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY missing from .env")

    print(f"[ElevenLabs] {len(script)} chars → voice {voice_id}")

    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key":   api_key,
                "Content-Type": "application/json",
                "Accept":       "audio/mpeg",
            },
            json={
                "text":     script,
                "model_id": "eleven_turbo_v2",  # supports <break> SSML tags
                "voice_settings": {
                    "stability":         0.35,  # lower = more expressive range
                    "similarity_boost":  0.75,
                    "style":             0.45,  # storytelling rhythm
                    "use_speaker_boost": True,
                },
            },
            timeout=120,
        )
        if resp.status_code == 200:
            size_kb = len(resp.content) // 1024
            print(f"[ElevenLabs] ✓ {size_kb} KB audio ready")
            return resp.content
        err = resp.json()
        print(f"[ElevenLabs] ✗ {resp.status_code}: {err.get('detail', {}).get('message', resp.text)}")
        return None
    except requests.RequestException as e:
        print(f"[ElevenLabs] ✗ {e}")
        return None


# ── EMAIL ─────────────────────────────────────────────────────

def send_recap_email(audio_bytes: bytes, script: str, period: str) -> bool:
    import resend
    resend.api_key = os.environ["RESEND_API_KEY"]

    recipients = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
    if not recipients:
        raise ValueError("EMAIL_TO missing from .env")

    safe_period = period.replace(" ", "-").replace("–", "to")
    filename    = f"AI-Roast-{safe_period}.mp3"

    # Strip <break> tags from the readable script version in email body
    import re
    readable_script = re.sub(r"<break[^/]*/>\s*", " ", script).strip()

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
      🎙️ AI Roast Brief
    </h1>
    <p style="font-size:15px;color:#b0b0c0;margin:0;">{period}</p>
  </div>

  <div style="background:#001a0d;border:1px solid #003322;border-left:4px solid #00ff88;
              border-radius:8px;padding:18px 20px;margin-bottom:24px;">
    <p style="font-family:monospace;font-size:12px;color:#00ff88;
              text-transform:uppercase;letter-spacing:.5px;margin:0 0 8px 0;">
      ▶ AUDIO ATTACHED
    </p>
    <p style="font-size:14px;color:#b0b0c0;margin:0;line-height:1.6;">
      Download <strong style="color:#fff">{filename}</strong> — ~5 min.
      Bassi-style opening, Samay-style quick hits.
    </p>
  </div>

  <div style="background:#17171a;border:1px solid #2c2c32;border-radius:8px;
              padding:20px;margin-bottom:24px;">
    <p style="font-family:monospace;font-size:11px;color:#808090;
              text-transform:uppercase;letter-spacing:.5px;margin:0 0 14px 0;">
      Full Script
    </p>
    <p style="font-size:14px;color:#b0b0c0;line-height:1.9;margin:0;
              white-space:pre-wrap;">{readable_script}</p>
  </div>

  <p style="font-family:monospace;font-size:11px;color:#3a3a42;text-align:center;margin:0;">
    AI Roast Brief · Fortnightly Recap · Groq + ElevenLabs
  </p>

</body></html>"""

    try:
        resp = resend.Emails.send({
            "from":    os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
            "to":      recipients,
            "subject": f"🎙️ AI Roast Recap — {period}",
            "html":    html,
            "attachments": [{
                "filename":     filename,
                "content":      list(audio_bytes),
                "content_type": "audio/mpeg",
            }],
        })
        rid = resp.id if hasattr(resp, "id") else resp.get("id", "unknown")
        print(f"[Sender] ✓ Sent — {rid}")
        return True
    except Exception as e:
        print(f"[Sender] ✗ {e}")
        return False


def _send_script_only(script: str, period: str):
    """Fallback: email just the script if TTS fails."""
    import resend, re
    resend.api_key = os.environ["RESEND_API_KEY"]
    readable = re.sub(r"<break[^/]*/>\s*", " ", script).strip()
    recipients = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
    try:
        resend.Emails.send({
            "from":    os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
            "to":      recipients,
            "subject": f"🎙️ AI Roast Recap — {period} (script only, audio failed)",
            "html":    f"<pre style='font-family:sans-serif;line-height:1.9;white-space:pre-wrap'>{readable}</pre>",
        })
        print("[Fallback] ✓ Script-only email sent")
    except Exception as e:
        print(f"[Fallback] ✗ {e}")


# ── STORY COLLECTOR ───────────────────────────────────────────

def collect_stories() -> list:
    brief_path = os.path.join(os.path.dirname(__file__), "..", "last_brief.json")
    try:
        with open(brief_path, encoding="utf-8") as f:
            brief = json.load(f)
        stories = brief.get("stories", [])
        print(f"[Recap] {len(stories)} stories from last_brief.json")
        return stories
    except FileNotFoundError:
        print("[Recap] No last_brief.json — using placeholder")
        return [{"headline": "AI had a wild fortnight", "source": "Various",
                 "what": "Many things happened.", "roast": "AGI is still 6 months away."}]


# ── ENTRY POINT ───────────────────────────────────────────────

def run_fortnightly_recap():
    today = datetime.date.today()

    # 1st of month  → recap of 16th–end of last month
    # 16th of month → recap of 1st–15th of this month
    if today.day == 1:
        end   = today - datetime.timedelta(days=1)
        start = end.replace(day=16)
    else:
        start = today.replace(day=1)
        end   = today.replace(day=15)

    period = f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"

    print("\n" + "=" * 60)
    print(f"  🎙️  AI ROAST FORTNIGHTLY RECAP")
    print(f"  Period: {period}")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    stories = collect_stories()
    script  = write_standup_script(stories, period)
    audio   = text_to_speech(script)

    if not audio:
        print("\n[!] TTS failed — sending script only")
        _send_script_only(script, period)
        return

    success = send_recap_email(audio, script, period)
    if not success:
        print("\n✗ Email failed")
        return

    print("\n" + "=" * 60)
    print(f"  ✓ DONE — {period}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_fortnightly_recap()