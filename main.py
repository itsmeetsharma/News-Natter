"""
AI Roast Brief — Daily Pipeline
================================
Orchestrates the full pipeline:
  1. Research  — Serper searches today's AI news
  2. Write     — Groq/Gemini structures a roast-style brief
  3. Memes     — Imgflip captions one meme per story
  4. Send      — Resend delivers the HTML email

Usage:
  python main.py                    Full run
  python main.py --test             Fake news, skips Serper
  python main.py --dry-run          Saves to output.html, no email sent
  python main.py --style TERMINAL   Force a specific visual style
  python main.py --test --dry-run   Zero API calls, fastest local test
"""
import argparse, datetime, json, os, sys
from dotenv import load_dotenv
load_dotenv()


def get_episode_number() -> int:
    ep_file = os.path.join(os.path.dirname(__file__), "episode.txt")
    try:
        with open(ep_file) as f:
            n = int(f.read().strip()) + 1
    except Exception:
        n = datetime.date.today().timetuple().tm_yday
    with open(ep_file, "w") as f:
        f.write(str(n))
    return n


def run(test_mode: bool = False, force_style: str = None, dry_run: bool = False):
    print("\n" + "=" * 60)
    print("  🤖 AI ROAST BRIEF — DAILY PIPELINE")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    episode = get_episode_number()

    # ── 1. RESEARCH ───────────────────────────────────────────
    print("[1/4] Researching today's AI news...")
    if test_mode:
        raw_news = _fake_news()
        print("      (test mode — using fake news)")
    else:
        from agents.researcher import research_news
        raw_news = research_news()
    print(f"      Got {len(raw_news)} chars of raw news\n")

    # ── 2. WRITE BRIEF ────────────────────────────────────────
    print("[2/4] Writing brief with roast tone...")
    from agents.writer import write_brief
    brief = write_brief(raw_news, episode=episode)
    if force_style:
        brief["style"] = force_style.upper()
        print(f"      Style overridden to: {force_style.upper()}")
    print(f"      Style: {brief['style']} | Stories: {len(brief.get('stories', []))}\n")

    # ── 3. MEMES ──────────────────────────────────────────────
    print("[3/4] Generating memes...")
    from utils.meme import get_meme
    for story in brief.get("stories", []):
        meme = get_meme(story["headline"], story["roast"])
        story["meme_url"] = meme.get("url")
        status = f"✓ {meme.get('template', 'meme')}" if story["meme_url"] else "- no meme"
        print(f"      Story {story['id']}: {status}")
    print()

    # ── 4. BUILD + SEND ───────────────────────────────────────
    print("[4/4] Building email...")
    from agents.email_builder import build_email
    html = build_email(brief)

    if dry_run:
        out_path = os.path.join(os.path.dirname(__file__), "output.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"      [DRY RUN] Saved to {out_path} — open in browser to preview")
    else:
        print("      Sending via Resend...")
        from agents.sender import send_brief
        if not send_brief(html, brief):
            print("\n✗ Pipeline failed at send step")
            sys.exit(1)

    # Save brief for debugging / monthly recap
    debug_path = os.path.join(os.path.dirname(__file__), "last_brief.json")
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"  ✓ DONE — Episode #{episode} | {brief['style']} | {datetime.date.today()}")
    print("=" * 60 + "\n")


def _fake_news() -> str:
    return """
1. OpenAI releases GPT-5 with real-time voice and vision
   Source: TechCrunch
   Summary: OpenAI announced GPT-5, which includes real-time voice and live camera vision. Scores 95% on reasoning benchmarks.
   Why it matters: Developers can now build products that see and hear in real time.

2. Google DeepMind trains AI on 10 million YouTube hours
   Source: The Verge
   Summary: DeepMind's new video model can answer questions about any video clip after training on an unprecedented dataset.
   Why it matters: Every tutorial and lecture becomes queryable.

3. Mistral launches Le Chat Enterprise for EU compliance
   Source: VentureBeat
   Summary: Mistral's privacy-first assistant is GDPR-native with zero data retention by default.
   Why it matters: Finally a compliant AI tool for European businesses.

4. Anthropic publishes Claude's full model spec publicly
   Source: Ars Technica
   Summary: Anthropic open-sourced the full 10,000-word document governing Claude's behavior and alignment approach.
   Why it matters: First major AI lab to fully disclose their alignment methodology.

5. Microsoft Copilot now embedded in every Office app
   Source: The Verge
   Summary: Copilot is now default in Word, Excel, PowerPoint, and Teams for all Microsoft 365 subscribers.
   Why it matters: 1.1 billion Office users just got AI tools whether they wanted them or not.
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Roast Brief — Daily Pipeline")
    parser.add_argument("--test",     action="store_true", help="Use fake news, skip Serper")
    parser.add_argument("--dry-run",  action="store_true", help="Save to output.html, don't send")
    parser.add_argument("--style",    type=str,            help="Force style: NEWSPAPER / MEME / COMIC / STARTUP / TERMINAL / MAGAZINE")
    args = parser.parse_args()
    run(test_mode=args.test, force_style=args.style, dry_run=args.dry_run)
