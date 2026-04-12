COLLEGE_FACTS = [
    "The college has an intercollegiate football team.",
    "The college offers a Computer Science major.",
    "In-state tuition is approximately $11,500 per academic year.",
    "The college provides on-campus housing options for students.",
]

SUPPORTED_TOPIC_KEYWORDS = {
    "academic",
    "academics",
    "athletic",
    "athletics",
    "campus",
    "college",
    "computer",
    "cs",
    "football",
    "housing",
    "major",
    "on-campus",
    "program",
    "programs",
    "residence",
    "student",
    "students",
    "tuition",
}


def facts_as_bullets() -> str:
    return "\n".join(f"- {fact}" for fact in COLLEGE_FACTS)
