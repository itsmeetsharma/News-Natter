"""
Content Writer Agent — turns raw news summaries into structured brief JSON.
Medium roast tone. Roasts companies/trends, never the reader.
"""
import datetime
from utils.llm import call_llm

# Day-of-week → default style (Gemini can override based on news vibe)
DAY_STYLES = {
    0: "NEWSPAPER",   # Mon
    1: "MEME",        # Tue
    2: "COMIC",       # Wed
    3: "STARTUP",     # Thu
    4: "TERMINAL",    # Fri
    5: "MAGAZINE",    # Sat
    6: "NEWSPAPER",   # Sun
}

VIBE_OPTIONS   = ["hype", "interesting", "bullish", "thoughtful", "useful"]
MEME_OPTIONS   = ["galaxy_brain", "npc", "okay"]
STYLE_OPTIONS  = ["NEWSPAPER", "MEME", "COMIC", "STARTUP", "TERMINAL", "MAGAZINE"]


WRITER_PROMPT = """You are the editor of "AI Roast Brief" — a daily AI news digest for developers, students, and tech enthusiasts.

Today: {date} ({day_name})
Default style for today: {default_style}
Available styles: NEWSPAPER, MEME, COMIC, STARTUP, TERMINAL, MAGAZINE

Here are today's raw news stories from research:
---
{raw_news}
---

Your job:
1. Pick the 5 best stories from the research above.
2. Choose the best STYLE for today's vibe:
   - Major product launch → STARTUP
   - Chaotic/funny/absurd story → MEME
   - Fun product moment → COMIC
   - Dev tool / late-night coding energy → TERMINAL
   - Thoughtful policy or research → MAGAZINE
   - Serious market/geopolitics → NEWSPAPER
   - Otherwise → use the default style for today
3. Write in MEDIUM ROAST tone: roast the company or trend, NEVER the reader.
   If a story is genuinely positive (free useful tool, open source release), write a meme observation instead of forcing a roast.
4. "use_today" must be ONE specific actionable thing — a real URL, a command, a concrete step.

Respond with ONLY a valid JSON object. No markdown. No backticks. No explanation. Start with {{ end with }}.

{{
  "date": "{date}",
  "style": "COMIC",
  "episode": {episode},
  "tagline": "one punchy tagline for today (max 80 chars)",
  "stories": [
    {{
      "id": 1,
      "headline": "Clean headline, max 90 chars",
      "source": "TechCrunch",
      "what": "2-3 sentences: what actually happened in plain English",
      "why": "1-2 sentences: why a developer or student should care",
      "use_today": "One specific action with a real URL or command",
      "roast": "One witty observation about the company/trend. Max 120 chars. NOT about the reader.",
      "meme_ref": "galaxy_brain",
      "vibe": "hype"
    }}
  ],
  "power_move": "One thing to do before noon. Starts with action verb. Max 2 sentences.",
  "power_move_time": "15 min",
  "stat_stories": "5",
  "stat_cost": "₹0"
}}

Rules:
- meme_ref must be one of: galaxy_brain, npc, okay
- vibe must be one of: hype, interesting, bullish, thoughtful, useful
- style must be one of: NEWSPAPER, MEME, COMIC, STARTUP, TERMINAL, MAGAZINE
- roast is about the company/industry, NEVER the reader
- All 5 stories must be real stories from the research — do not invent stories
"""


def write_brief(raw_news: str, episode: int = 1) -> dict:
    """
    Takes raw news research string.
    Returns structured brief as a Python dict.
    """
    today = datetime.date.today()
    date_str = today.strftime("%Y-%m-%d")
    day_name = today.strftime("%A")
    default_style = DAY_STYLES[today.weekday()]

    prompt = WRITER_PROMPT.format(
        date=date_str,
        day_name=day_name,
        default_style=default_style,
        raw_news=raw_news,
        episode=episode,
    )

    print(f"[Writer] Generating brief for {date_str} ({day_name}) — default style: {default_style}")
    brief = call_llm(prompt, expect_json=True, temperature=0.85)

    # Validate and patch required fields
    brief.setdefault("date", date_str)
    brief.setdefault("style", default_style)
    brief.setdefault("episode", episode)
    brief.setdefault("tagline", "Your daily AI news, now with more roast")
    brief.setdefault("power_move", "Try one new AI tool today.")
    brief.setdefault("power_move_time", "15 min")
    brief.setdefault("stat_stories", str(len(brief.get("stories", []))))
    brief.setdefault("stat_cost", "₹0")

    # Validate style
    if brief["style"] not in STYLE_OPTIONS:
        brief["style"] = default_style

    print(f"[Writer] Brief ready — style: {brief['style']}, stories: {len(brief.get('stories', []))}")
    return brief
