"""
Content Writer
==============
Takes raw news research and structures it into a brief JSON object.
Uses a medium roast tone — roasts companies and trends, never the reader.
Groq/Gemini picks the best visual style based on the news vibe.
"""
import datetime
from utils.llm import call_llm

DAY_STYLES = {0: "NEWSPAPER", 1: "MEME", 2: "COMIC", 3: "STARTUP", 4: "TERMINAL", 5: "MAGAZINE", 6: "NEWSPAPER"}
VALID_STYLES = {"NEWSPAPER", "MEME", "COMIC", "STARTUP", "TERMINAL", "MAGAZINE"}

PROMPT = """You are the editor of "AI Roast Brief" — a daily AI news digest for developers and students.

Today: {date} ({day_name}) | Default style: {default_style}
Available styles: NEWSPAPER, MEME, COMIC, STARTUP, TERMINAL, MAGAZINE

Style selection guide:
  STARTUP   → major product launch or funding round
  MEME      → chaotic, funny, or absurd story dominates
  COMIC     → fun product moment, playful energy
  TERMINAL  → dev tool, open source, or late-night drop
  MAGAZINE  → thoughtful policy, research, or safety story
  NEWSPAPER → serious market or geopolitical AI news
  (default) → use today's default style if nothing fits

Raw research:
---
{raw_news}
---

Rules:
- Pick the 5 best stories from the research above. Do NOT invent stories.
- Roast the company or trend. NEVER roast the reader.
- If a story is genuinely good news (free tool, open source), use a meme observation instead of forcing a roast.
- "use_today" must be ONE specific action with a real URL or terminal command.
- meme_ref must be one of: galaxy_brain, npc, okay
- vibe must be one of: hype, interesting, bullish, thoughtful, useful

Respond ONLY with valid JSON. No markdown. No backticks. Start with {{ end with }}.

{{
  "date": "{date}",
  "style": "COMIC",
  "episode": {episode},
  "tagline": "one punchy tagline, max 80 chars",
  "stories": [
    {{
      "id": 1,
      "headline": "Clean headline, max 90 chars",
      "source": "TechCrunch",
      "what": "2-3 sentences: what actually happened",
      "why": "1-2 sentences: why a developer or student should care",
      "use_today": "One specific action with a real URL or command",
      "roast": "One witty observation about the company/trend. Max 120 chars.",
      "meme_ref": "galaxy_brain",
      "vibe": "hype"
    }}
  ],
  "power_move": "One thing to do before noon. Starts with a verb. Max 2 sentences.",
  "power_move_time": "15 min",
  "stat_stories": "5",
  "stat_cost": "₹0"
}}"""


def write_brief(raw_news: str, episode: int = 1) -> dict:
    today        = datetime.date.today()
    date_str     = today.strftime("%Y-%m-%d")
    day_name     = today.strftime("%A")
    default_style = DAY_STYLES[today.weekday()]

    print(f"[Writer] {date_str} ({day_name}) — default style: {default_style}")

    brief = call_llm(
        PROMPT.format(
            date=date_str, day_name=day_name,
            default_style=default_style,
            raw_news=raw_news, episode=episode,
        ),
        expect_json=True,
        temperature=0.85,
    )

    # Patch any missing fields
    brief.setdefault("date",             date_str)
    brief.setdefault("style",            default_style)
    brief.setdefault("episode",          episode)
    brief.setdefault("tagline",          "Your daily AI news, now with more roast")
    brief.setdefault("power_move",       "Try one new AI tool today.")
    brief.setdefault("power_move_time",  "15 min")
    brief.setdefault("stat_stories",     str(len(brief.get("stories", []))))
    brief.setdefault("stat_cost",        "₹0")

    if brief["style"] not in VALID_STYLES:
        brief["style"] = default_style

    print(f"[Writer] Done — style: {brief['style']}, stories: {len(brief.get('stories', []))}")
    return brief
