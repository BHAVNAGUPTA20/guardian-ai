import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.models import AuditResult, MainAnswer
from backend.prompts import (
    AUDIT_PROMPT,
    GENERATOR_PROMPT,
    GENERATOR_SYSTEM_PROMPT,
    GUARDIAN_SYSTEM_PROMPT,
)

load_dotenv()


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Add it to your .env file."
        )
    return genai.Client(api_key=api_key)


def _response_text(response) -> str:
    text = getattr(response, "text", None)
    if text:
        return text

    try:
        candidates = response.candidates or []
        if candidates:
            content = candidates[0].content
            parts = getattr(content, "parts", [])
            if parts:
                return parts[0].text
    except Exception:
        pass

    raise RuntimeError("Gemini returned an empty response.")


def _generate_json(model: str, system_prompt: str, user_prompt: str, schema):
    client = get_client()

    response = client.models.generate_content(
        model=model,
        contents=f"{system_prompt}\n\n{user_prompt}",
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    return _response_text(response)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def generate_main_answer(prompt: str, model: str = "gemini-2.5-flash") -> MainAnswer:
    raw = _generate_json(
        model=model,
        system_prompt=GENERATOR_SYSTEM_PROMPT,
        user_prompt=GENERATOR_PROMPT.format(text=prompt),
        schema=MainAnswer,
    )
    return MainAnswer.model_validate_json(raw)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def audit_answer(question: str, answer: str, model: str = "gemini-2.5-flash") -> AuditResult:
    raw = _generate_json(
        model=model,
        system_prompt=GUARDIAN_SYSTEM_PROMPT,
        user_prompt=AUDIT_PROMPT.format(question=question, answer=answer),
        schema=AuditResult,
    )
    return AuditResult.model_validate_json(raw)