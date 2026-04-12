from .college_facts import SUPPORTED_TOPIC_KEYWORDS, facts_as_bullets


OUT_OF_SCOPE_MESSAGE = (
    "I can only answer based on the college information currently configured in this chatbot."
)

UNAVAILABLE_MESSAGE = "The AI assistant is currently unavailable. Please try again later."


def is_supported_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in SUPPORTED_TOPIC_KEYWORDS)


def build_system_instruction() -> str:
    return (
        "You are a bonus college inquiry assistant for a class project. "
        "Answer only from the configured college facts below. "
        "Keep responses helpful, concise, and professional. "
        f"If the question is not answerable from these facts, reply exactly with: {OUT_OF_SCOPE_MESSAGE}\n\n"
        "Configured college facts:\n"
        f"{facts_as_bullets()}"
    )
