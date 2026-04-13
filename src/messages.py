from src.config import QUESTIONS

def intro_message(first_name: str) -> str:
    return (
        f"Welcome, {first_name}. I can help answer common questions about "
        "academics, tuition, athletics, and campus housing. Choose a question "
        "below to continue."
    )

def build_initial_messages(first_name: str) -> list[dict[str, str]]:
    return [{"role": "bot", "content": intro_message(first_name)}]
