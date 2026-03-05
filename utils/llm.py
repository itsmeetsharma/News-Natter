"""
LLM client — Groq primary, Gemini fallback.
Single call_llm() function used everywhere.
"""
import os, json, re
from dotenv import load_dotenv
load_dotenv()


def call_llm(prompt: str, expect_json: bool = False, temperature: float = 0.8) -> str:
    """
    Call Groq. If it fails for any reason, transparently fall back to Gemini.
    Returns the raw string response (or parsed dict if expect_json=True and valid).
    """
    result = _try_groq(prompt, temperature)
    if result is None:
        print("[LLM] Groq failed — trying Gemini fallback")
        result = _try_gemini(prompt, temperature)
    if result is None:
        raise RuntimeError("Both Groq and Gemini failed. Check your API keys.")

    if expect_json:
        return _extract_json(result)
    return result


def _try_groq(prompt: str, temperature: float) -> str | None:
    try:
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4096,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[Groq] Error: {e}")
        return None


def _try_gemini(prompt: str, temperature: float) -> str | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=4096,
            )
        )
        return resp.text
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return None


def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse JSON. Raises ValueError if unparseable."""
    # Remove ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    # Find the first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\n\nRaw:\n{text[:500]}")
