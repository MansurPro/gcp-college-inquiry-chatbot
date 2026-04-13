import re
import json

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def cleaned(value: str) -> str:
    return value.strip()

def build_user_info(first_name: str, last_name: str, email: str) -> dict[str, str]:
    return {
        "first_name": cleaned(first_name),
        "last_name": cleaned(last_name),
        "email": cleaned(email),
    }

def validate_user_info(user_info: dict[str, str]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not user_info["first_name"]:
        errors["first_name"] = "First name is required."
    if not user_info["last_name"]:
        errors["last_name"] = "Last name is required."
    if not user_info["email"]:
        errors["email"] = "Email address is required."
    elif not EMAIL_PATTERN.match(user_info["email"]):
        errors["email"] = "Enter a valid email address."
    return errors

def parse_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

def serialize_messages(messages: list[dict[str, str]]) -> str:
    return json.dumps(messages, separators=(",", ":"))

def deserialize_messages(history_json: str | None, first_name: str, build_initial_messages) -> list[dict[str, str]]:
    fallback = build_initial_messages(first_name)
    if not history_json:
        return fallback
    try:
        raw_messages = json.loads(history_json)
    except json.JSONDecodeError:
        return fallback
    if not isinstance(raw_messages, list):
        return fallback
    messages: list[dict[str, str]] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"bot", "user"} or not isinstance(content, str):
            continue
        normalized_content = cleaned(content)
        if normalized_content:
            messages.append({"role": role, "content": normalized_content})
    if not messages:
        return fallback
    messages[0] = {"role": "bot", "content": build_initial_messages(first_name)[0]["content"]}
    return messages
