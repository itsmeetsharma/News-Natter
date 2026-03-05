"""
Meme Generator
==============
Asks the LLM to pick the best Imgflip template for each story,
then captions it via the Imgflip API.
Falls back gracefully to no meme if anything fails.
"""
import os, requests
from dotenv import load_dotenv
load_dotenv()

TEMPLATES = [
    ("181913649", "Drake Pointing",           "Drake approving X but rejecting Y — comparing two things"),
    ("87743020",  "Two Buttons",              "Sweating over an impossible choice between two options"),
    ("112126428", "Distracted Boyfriend",     "Distracted by shiny new thing, ignoring the existing thing"),
    ("131087935", "Running Away Balloon",     "Person running from their own labeled problem"),
    ("101470",    "Ancient Aliens Guy",       "Obvious conspiracy / unexplained phenomenon"),
    ("61579",     "One Does Not Simply",      "One does not simply do X"),
    ("93895088",  "Expanding Brain",          "Escalating galaxy-brain ideas — each more unhinged than last"),
    ("102156234", "Mocking Spongebob",        "Sarcastic repetition of something clueless"),
    ("217743513", "UNO Draw 25",              "Refusing the obvious solution, choosing maximum chaos"),
    ("124822590", "Left Exit 12",             "Taking the unexpected exit — sudden pivot or U-turn"),
    ("148909805", "Disaster Girl",            "Smiling in front of complete disaster"),
    ("55311130",  "This Is Fine",             "Dog calmly sitting in a burning room"),
    ("14371066",  "Most Interesting Man",     "I don't always X but when I do, Y"),
    ("4087833",   "Waiting Skeleton",         "Still waiting for something that never arrives"),
    ("80707627",  "Condescending Wonka",      "Condescending 'oh really?' to an obvious statement"),
]

_TEMPLATE_LIST = "\n".join(
    f"  {i+1}. id={t[0]}  name={t[1]}  — {t[2]}"
    for i, t in enumerate(TEMPLATES)
)
_VALID_IDS = {t[0] for t in TEMPLATES}


def get_meme(headline: str, roast: str) -> dict:
    """
    Returns: {"url": str | None, "type": "imgflip" | "none", "template": str}
    """
    from utils.llm import call_llm

    prompt = f"""Pick the best meme template for this AI news story.

Story: {headline}
Roast: {roast}

Templates:
{_TEMPLATE_LIST}

Choose ONE template. Write punchy top and bottom text (max 8 words each).
Respond ONLY with JSON, no markdown:
{{"template_id": "181913649", "template_name": "Drake Pointing", "top_text": "...", "bottom_text": "..."}}"""

    try:
        data = call_llm(prompt, expect_json=True, temperature=0.9)
        tid  = str(data.get("template_id", ""))

        # Reject hallucinated template IDs
        if tid not in _VALID_IDS:
            print(f"[Meme] LLM picked unknown template id={tid}, skipping")
            return {"url": None, "type": "none", "template": ""}

        url = _imgflip(tid, data.get("top_text", ""), data.get("bottom_text", ""))
        if url:
            return {"url": url, "type": "imgflip", "template": data.get("template_name", "")}
    except Exception as e:
        print(f"[Meme] {e}")

    return {"url": None, "type": "none", "template": ""}


def _imgflip(template_id: str, top: str, bottom: str) -> str | None:
    username = os.getenv("IMGFLIP_USERNAME")
    password = os.getenv("IMGFLIP_PASSWORD")
    if not username or not password:
        return None
    try:
        resp = requests.post(
            "https://api.imgflip.com/caption_image",
            data={
                "template_id": template_id,
                "username":    username,
                "password":    password,
                "text0":       top,
                "text1":       bottom,
                "font":        "impact",
                "max_font_size": "50",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("success"):
            return data["data"]["url"]
        print(f"[Imgflip] {data.get('error_message', 'unknown error')}")
        return None
    except Exception as e:
        print(f"[Imgflip] {e}")
        return None
