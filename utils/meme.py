"""
Meme generator — Imgflip API primary, HTML fallback.
Returns a meme URL (Imgflip) or an inline base64 SVG (fallback).
"""
import os, requests, base64
from dotenv import load_dotenv
load_dotenv()

# Top meme templates that work well for AI/tech news roasts
# Format: (template_id, name, description_for_llm)
TEMPLATES = [
    ("181913649", "Drake Pointing",        "Drake approving X but not Y — comparing two things"),
    ("87743020",  "Two Buttons",            "Character sweating over two choices — impossible decision"),
    ("112126428", "Distracted Boyfriend",   "Distracted by new thing, ignoring existing thing"),
    ("131087935", "Running Away Balloon",   "Person running from their own labeled problem"),
    ("101470",    "Ancient Aliens Guy",     "Conspiracy / obvious explanation"),
    ("61579",     "One Does Not Simply",    "One does not simply do X"),
    ("93895088",  "Expanding Brain",        "Escalating increasingly galaxy-brain ideas"),
    ("102156234", "Mocking Spongebob",      "Mocking/repeating something sarcastically"),
    ("217743513", "UNO Draw 25 Cards",      "Refusing simple solution, choosing chaos"),
    ("124822590", "Left Exit 12",           "Taking unexpected exit — sudden pivot"),
    ("148909805", "Disaster Girl",          "Smiling in front of disaster"),
    ("55311130",  "This Is Fine",           "Dog sitting calmly in burning room"),
    ("14371066",  "Most Interesting Man",   "I don't always X but when I do Y"),
    ("4087833",   "Waiting Skeleton",       "Still waiting for something that never comes"),
    ("80707627",  "Creepy Condescending Wonka", "Condescending 'Oh really?' reaction"),
]

TEMPLATE_LIST_FOR_PROMPT = "\n".join(
    f"  {i+1}. id={t[0]} name={t[1]} — {t[2]}"
    for i, t in enumerate(TEMPLATES)
)


def get_meme(story_headline: str, story_roast: str) -> dict:
    """
    Given a headline and roast line, return a meme.
    Returns: { "url": str, "type": "imgflip"|"fallback", "template": str }
    """
    # Ask LLM to pick a template and write the caption
    from utils.llm import call_llm
    prompt = f"""You are picking the perfect meme for this AI news story.

Story: {story_headline}
Roast: {story_roast}

Available meme templates:
{TEMPLATE_LIST_FOR_PROMPT}

Pick the single best template. Write punchy top text and bottom text (max 8 words each).
Respond ONLY with JSON, no markdown:
{{"template_id": "181913649", "template_name": "Drake Pointing", "top_text": "text here", "bottom_text": "text here"}}"""

    try:
        data = call_llm(prompt, expect_json=True, temperature=0.9)
        meme_url = _generate_imgflip(
            data["template_id"],
            data.get("top_text", ""),
            data.get("bottom_text", ""),
        )
        if meme_url:
            return {"url": meme_url, "type": "imgflip", "template": data.get("template_name", "")}
    except Exception as e:
        print(f"[Meme] LLM/Imgflip failed: {e}")

    # Fallback: return None — caller will skip meme
    print("[Meme] Using no meme for this story")
    return {"url": None, "type": "none", "template": ""}


def _generate_imgflip(template_id: str, top_text: str, bottom_text: str) -> str | None:
    """Call Imgflip API, return image URL or None."""
    username = os.getenv("IMGFLIP_USERNAME")
    password = os.getenv("IMGFLIP_PASSWORD")
    if not username or not password:
        print("[Imgflip] No credentials — skipping")
        return None
    try:
        resp = requests.post(
            "https://api.imgflip.com/caption_image",
            data={
                "template_id": template_id,
                "username": username,
                "password": password,
                "text0": top_text,
                "text1": bottom_text,
                "font": "impact",
                "max_font_size": "50",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("success"):
            return data["data"]["url"]
        else:
            print(f"[Imgflip] API error: {data.get('error_message')}")
            return None
    except Exception as e:
        print(f"[Imgflip] Request failed: {e}")
        return None
