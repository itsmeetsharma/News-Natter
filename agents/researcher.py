"""
News Researcher — direct Serper API + LLM summarization.
No CrewAI dependency. Works on Python 3.9+.
"""
import os, requests, datetime
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
    """
    Search Serper for today's AI news across 4 queries.
    Feed all results to LLM to extract the 8 best stories.
    Returns a clean numbered list string.
    """
    date_str = datetime.date.today().strftime("%B %d %Y")
    raw_results = []

    for query_template in SEARCH_QUERIES:
        query = query_template.format(date=date_str)
        results = _serper_search(query, n=5)
        if results:
            raw_results.extend(results)
            print(f"[Researcher] '{query}' → {len(results)} results")
        else:
            print(f"[Researcher] '{query}' → no results")

    if not raw_results:
        raise RuntimeError("Serper returned zero results. Check your SERPER_API_KEY.")

    # Deduplicate by title
    seen = set()
    unique = []
    for r in raw_results:
        title = r.get("title", "").lower()
        if title not in seen:
            seen.add(title)
            unique.append(r)

    print(f"[Researcher] {len(unique)} unique stories found, asking LLM to pick best 8")
    return _summarize_with_llm(unique)


def _serper_search(query: str, n: int = 5) -> list[dict]:
    """Call Serper API, return list of {title, snippet, link, source} dicts."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY missing from .env")

    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": n, "gl": "us", "hl": "en"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic", [])[:n]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link":    item.get("link", ""),
                "source":  item.get("source", _domain_from_url(item.get("link", ""))),
            })
        return results

    except requests.RequestException as e:
        print(f"[Serper] Request error: {e}")
        return []


def _summarize_with_llm(results: list[dict]) -> str:
    """Ask LLM to pick the 8 best stories and summarize them cleanly."""

    # Format results for the prompt
    numbered = "\n\n".join(
        f"{i+1}. [{r['source']}] {r['title']}\n   {r['snippet']}\n   URL: {r['link']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a sharp tech journalist screening AI news stories.

Here are {len(results)} raw search results from today:
---
{numbered}
---

Your task:
1. Pick the 8 most significant, interesting, or surprising AI stories.
2. Skip pure PR fluff, opinion pieces, and anything older than 3 days.
3. For each story write a clean summary.

Format your output EXACTLY like this (numbered list, no extra text):

1. [Source Name] Headline here
   Summary: 2-3 sentences explaining what happened in plain English.
   Why it matters: 1 sentence on why a developer or student should care.

2. [Source Name] ...
(continue for all 8)
"""
    return call_llm(prompt, expect_json=False, temperature=0.3)


def _domain_from_url(url: str) -> str:
    """Extract readable domain from URL."""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        # Map common domains to readable names
        names = {
            "techcrunch.com": "TechCrunch",
            "theverge.com": "The Verge",
            "venturebeat.com": "VentureBeat",
            "arstechnica.com": "Ars Technica",
            "wired.com": "Wired",
            "bloomberg.com": "Bloomberg",
            "reuters.com": "Reuters",
            "openai.com": "OpenAI",
            "anthropic.com": "Anthropic",
            "google.com": "Google",
            "microsoft.com": "Microsoft",
        }
        return names.get(domain, domain)
    except Exception:
        return "Web"