"""
News Researcher
===============
Runs 4 Serper searches, deduplicates results, then asks the LLM
to pick and summarize the 8 best stories.
Returns a clean numbered list string passed to the Writer agent.
"""
import os, datetime, requests
from utils.llm import call_llm
from dotenv import load_dotenv
load_dotenv()

SEARCH_QUERIES = [
    "AI news today {date}",
    "artificial intelligence product launch {date}",
    "AI research breakthrough this week",
    "AI startup funding news today",
]


def research_news() -> str:
    date_str = datetime.date.today().strftime("%B %d %Y")
    raw_results = []

    for template in SEARCH_QUERIES:
        query   = template.format(date=date_str)
        results = _serper_search(query, n=5)
        raw_results.extend(results)
        print(f"[Researcher] '{query}' → {len(results)} results")

    if not raw_results:
        raise RuntimeError("Serper returned zero results. Check your SERPER_API_KEY in .env")

    # Deduplicate by title
    seen, unique = set(), []
    for r in raw_results:
        t = r.get("title", "").lower()
        if t not in seen:
            seen.add(t)
            unique.append(r)

    print(f"[Researcher] {len(unique)} unique stories — asking LLM to pick best 8")
    return _summarize_with_llm(unique)


def _serper_search(query: str, n: int = 5) -> list:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY missing from .env")
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": n, "gl": "us", "hl": "en"},
            timeout=15,
        )
        resp.raise_for_status()
        return [
            {
                "title":   item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link":    item.get("link", ""),
                "source":  item.get("source", _readable_domain(item.get("link", ""))),
            }
            for item in resp.json().get("organic", [])[:n]
        ]
    except requests.RequestException as e:
        print(f"[Serper] {e}")
        return []


def _summarize_with_llm(results: list) -> str:
    numbered = "\n\n".join(
        f"{i+1}. [{r['source']}] {r['title']}\n   {r['snippet']}\n   URL: {r['link']}"
        for i, r in enumerate(results)
    )
    prompt = f"""You are a sharp tech journalist screening AI news stories.

Here are {len(results)} raw search results from today:
---
{numbered}
---

Pick the 8 most significant, interesting, or surprising AI stories.
Skip pure PR fluff, opinion pieces, and anything older than 3 days.

Format EXACTLY like this — no extra text, no headers:

1. [Source] Headline here
   Summary: 2-3 sentences explaining what happened in plain English.
   Why it matters: 1 sentence on why a developer or student should care.

2. [Source] ...
"""
    return call_llm(prompt, expect_json=False, temperature=0.3)


def _readable_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        names  = {
            "techcrunch.com": "TechCrunch", "theverge.com": "The Verge",
            "venturebeat.com": "VentureBeat", "arstechnica.com": "Ars Technica",
            "wired.com": "Wired", "bloomberg.com": "Bloomberg",
            "reuters.com": "Reuters", "openai.com": "OpenAI Blog",
            "anthropic.com": "Anthropic", "google.com": "Google",
        }
        return names.get(domain, domain)
    except Exception:
        return "Web"
