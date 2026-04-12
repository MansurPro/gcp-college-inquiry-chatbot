from dataclasses import dataclass


@dataclass(slots=True)
class GeminiSettings:
    api_key: str | None
    model: str = "gemini-2.5-flash"
    endpoint_template: str = (
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    )


@dataclass(slots=True)
class GeminiResult:
    text: str
    ok: bool
