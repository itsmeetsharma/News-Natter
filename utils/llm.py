"""
LLM Client
==========
Single call_llm() function used by all agents.
Tries Groq (Llama 3.3 70B) first, transparently falls back to Gemini 2.0 Flash.
"""
import os, json, re
from dotenv import load_dotenv
load_dotenv()


def call_llm(prompt: str, expect_json: bool = False, temperature: float = 0.8) -> str | dict:
    result = _try_groq(prompt, temperature)
    if result is None:
        print("[LLM] Groq unavailable — switching to Gemini")
        result = _try_gemini(prompt, temperature)
    if result is None:
        raise RuntimeError("Both Groq and Gemini failed. Check your API keys in .env")
    if expect_json:
        return _extract_json(result)
    return result


def _try_groq(prompt: str, temperature: float) -> str | None:
    try:
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        model  = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        resp   = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4096,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[Groq] {e}")
        return None


def _try_gemini(prompt: str, temperature: float) -> str | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        resp  = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=4096,
            )
        )
        return resp.text
    except Exception as e:
        print(f"[Gemini] {e}")
        return None


def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse JSON. Raises ValueError if unparseable."""
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    match   = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\n\nRaw response:\n{text[:500]}")
