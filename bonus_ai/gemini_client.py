import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .prompts import OUT_OF_SCOPE_MESSAGE, UNAVAILABLE_MESSAGE, build_system_instruction, is_supported_question
from .schemas import GeminiResult, GeminiSettings


def _load_local_env() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def _get_settings() -> GeminiSettings:
    _load_local_env()
    return GeminiSettings(
        api_key=os.getenv("GEMINI_API_KEY"),
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )


def _parse_response_text(payload: dict) -> str | None:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return None

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        content = candidate.get("content")
        if not isinstance(content, dict):
            continue

        parts = content.get("parts")
        if not isinstance(parts, list):
            continue

        texts: list[str] = []
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text = part["text"].strip()
                if text:
                    texts.append(text)

        if texts:
            return "\n".join(texts)

    return None


def _call_gemini(question: str) -> GeminiResult:
    settings = _get_settings()
    if not settings.api_key:
        return GeminiResult(text=UNAVAILABLE_MESSAGE, ok=False)

    request_body = {
        "system_instruction": {
            "parts": [{"text": build_system_instruction()}],
        },
        "contents": [
            {
                "parts": [{"text": question}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 300,
        },
    }
    request_data = json.dumps(request_body).encode("utf-8")
    endpoint = settings.endpoint_template.format(model=settings.model)

    request = Request(
        endpoint,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return GeminiResult(text=UNAVAILABLE_MESSAGE, ok=False)

    response_text = _parse_response_text(payload)
    if not response_text:
        return GeminiResult(text=UNAVAILABLE_MESSAGE, ok=False)

    return GeminiResult(text=response_text, ok=True)


def ask_bonus_assistant(question: str) -> str:
    normalized_question = question.strip()
    if not normalized_question:
        return UNAVAILABLE_MESSAGE

    if not is_supported_question(normalized_question):
        return OUT_OF_SCOPE_MESSAGE

    result = _call_gemini(normalized_question)
    return result.text if result.text else UNAVAILABLE_MESSAGE
