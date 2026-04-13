import json
import re

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bonus_ai import ask_bonus_assistant


QUESTIONS = {
    "football": {
        "question": "Does the college have a football team?",
        "answer": (
            "Yes — the college has an intercollegiate football program. Students "
            "can attend games, support campus athletics, and take part in the "
            "school spirit and traditions that come with the season."
        ),
    },
    "computer_science": {
        "question": "Does it offer a Computer Science major?",
        "answer": (
            "Yes — the college offers a Computer Science major. Students typically "
            "study programming, data structures, software development, and related "
            "technical subjects that prepare them for internships and careers in "
            "technology."
        ),
    },
    "tuition": {
        "question": "What is the in-state tuition?",
        "answer": (
            "In-state tuition is approximately $11,500 per academic year. It is "
            "also helpful to budget for additional costs such as fees, books, "
            "housing, and meal plans when estimating the full cost of attendance."
        ),
    },
    "housing": {
        "question": "Does it provide on-campus housing?",
        "answer": (
            "Yes — the college provides on-campus housing options for students, "
            "including residence halls that support convenience, community life, "
            "and easy access to campus resources."
        ),
    },
}

CREATOR = {
    "first_name": "Mansurbek",
    "last_name": "Satarov",
    "school_email": "sataromk@mail.uc.edu",
}

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = FastAPI(title="College Inquiry Chatbot")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def force_https_scheme_on_cloud_run(request: Request, call_next):
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto.split(",")[0].strip()
    response = await call_next(request)
    return response


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


def intro_message(first_name: str) -> str:
    return (
        f"Welcome, {first_name}. I can help answer common questions about "
        "academics, tuition, athletics, and campus housing. Choose a question "
        "below to continue."
    )


def build_initial_messages(first_name: str) -> list[dict[str, str]]:
    return [{"role": "bot", "content": intro_message(first_name)}]


def parse_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def serialize_messages(messages: list[dict[str, str]]) -> str:
    return json.dumps(messages, separators=(",", ":"))


def deserialize_messages(history_json: str | None, first_name: str) -> list[dict[str, str]]:
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

    messages[0] = {"role": "bot", "content": intro_message(first_name)}
    return messages


def render_index(
    request: Request,
    user_info: dict[str, str] | None = None,
    errors: dict[str, str] | None = None,
    form_error: str | None = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user_info": user_info or {"first_name": "", "last_name": "", "email": ""},
            "errors": errors or {},
            "form_error": form_error,
        },
        status_code=status_code,
    )


def render_chat(
    request: Request,
    user_info: dict[str, str],
    messages: list[dict[str, str]] | None = None,
    bonus_mode_enabled: bool = False,
    chat_error: str | None = None,
    bonus_error: str | None = None,
    selected_question_id: str | None = None,
    custom_question: str = "",
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    current_messages = messages or build_initial_messages(user_info["first_name"])
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "user_info": user_info,
            "questions": QUESTIONS,
            "messages": current_messages,
            "history_json": serialize_messages(current_messages),
            "bonus_mode_enabled": bonus_mode_enabled,
            "chat_error": chat_error,
            "bonus_error": bonus_error,
            "selected_question_id": selected_question_id,
            "custom_question": custom_question,
        },
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return render_index(request)


@app.post("/start", response_class=HTMLResponse)
async def start_chat(
    request: Request,
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    email: str = Form(default=""),
) -> HTMLResponse:
    user_info = build_user_info(first_name, last_name, email)
    errors = validate_user_info(user_info)

    if errors:
        return render_index(
            request,
            user_info=user_info,
            errors=errors,
            form_error="Please correct the highlighted fields before continuing.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return render_chat(request, user_info=user_info)


@app.post("/ask", response_class=HTMLResponse)
async def ask_question(
    request: Request,
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    email: str = Form(default=""),
    question_id: str = Form(default=""),
    history_json: str = Form(default=""),
    bonus_mode: str = Form(default=""),
) -> HTMLResponse:
    user_info = build_user_info(first_name, last_name, email)
    errors = validate_user_info(user_info)
    bonus_mode_enabled = parse_bool(bonus_mode)
    messages = deserialize_messages(history_json, user_info["first_name"])

    if errors:
        return render_index(
            request,
            user_info=user_info,
            errors=errors,
            form_error="Your session details are incomplete. Please re-enter your information.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    question = QUESTIONS.get(question_id)
    if question is None:
        return render_chat(
            request,
            user_info=user_info,
            messages=messages,
            bonus_mode_enabled=bonus_mode_enabled,
            chat_error="Please choose one of the four available college questions.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    updated_messages = [
        *messages,
        {"role": "user", "content": question["question"]},
        {"role": "bot", "content": question["answer"]},
    ]
    return render_chat(
        request,
        user_info=user_info,
        messages=updated_messages,
        bonus_mode_enabled=bonus_mode_enabled,
        selected_question_id=question_id,
    )


@app.post("/bonus-mode", response_class=HTMLResponse)
async def enable_bonus_mode(
    request: Request,
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    email: str = Form(default=""),
    history_json: str = Form(default=""),
) -> HTMLResponse:
    user_info = build_user_info(first_name, last_name, email)
    errors = validate_user_info(user_info)
    messages = deserialize_messages(history_json, user_info["first_name"])

    if errors:
        return render_index(
            request,
            user_info=user_info,
            errors=errors,
            form_error="Your session details are incomplete. Please re-enter your information.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    updated_messages = messages
    activation_notice = (
        "Gemini bonus mode is enabled. You can now ask a custom question, and I "
        "will answer using the college facts configured for this project."
    )
    if messages[-1]["content"] != activation_notice:
        updated_messages = [*messages, {"role": "bot", "content": activation_notice}]

    return render_chat(
        request,
        user_info=user_info,
        messages=updated_messages,
        bonus_mode_enabled=True,
    )


@app.post("/required-mode", response_class=HTMLResponse)
async def return_to_required_mode(
    request: Request,
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    email: str = Form(default=""),
    history_json: str = Form(default=""),
) -> HTMLResponse:
    user_info = build_user_info(first_name, last_name, email)
    errors = validate_user_info(user_info)
    messages = deserialize_messages(history_json, user_info["first_name"])

    if errors:
        return render_index(
            request,
            user_info=user_info,
            errors=errors,
            form_error="Your session details are incomplete. Please re-enter your information.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    updated_messages = [
        *messages,
        {
            "role": "bot",
            "content": (
                "You are back in the required guided mode. The original four "
                "college questions are still available below."
            ),
        },
    ]
    return render_chat(
        request,
        user_info=user_info,
        messages=updated_messages,
        bonus_mode_enabled=False,
    )


@app.post("/ask-ai", response_class=HTMLResponse)
async def ask_bonus_question(
    request: Request,
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    email: str = Form(default=""),
    custom_question: str = Form(default=""),
    history_json: str = Form(default=""),
    bonus_mode: str = Form(default=""),
) -> HTMLResponse:
    user_info = build_user_info(first_name, last_name, email)
    errors = validate_user_info(user_info)
    bonus_mode_enabled = parse_bool(bonus_mode)
    messages = deserialize_messages(history_json, user_info["first_name"])
    cleaned_question = cleaned(custom_question)

    if errors:
        return render_index(
            request,
            user_info=user_info,
            errors=errors,
            form_error="Your session details are incomplete. Please re-enter your information.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not bonus_mode_enabled:
        return render_chat(
            request,
            user_info=user_info,
            messages=messages,
            bonus_mode_enabled=False,
            bonus_error="Enable Gemini bonus mode before asking a custom question.",
            custom_question=cleaned_question,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not cleaned_question:
        return render_chat(
            request,
            user_info=user_info,
            messages=messages,
            bonus_mode_enabled=True,
            bonus_error="Enter a custom question before sending it to the AI assistant.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    ai_answer = ask_bonus_assistant(cleaned_question)
    updated_messages = [
        *messages,
        {"role": "user", "content": cleaned_question},
        {"role": "bot", "content": ai_answer},
    ]
    return render_chat(
        request,
        user_info=user_info,
        messages=updated_messages,
        bonus_mode_enabled=True,
    )


@app.post("/summary", response_class=HTMLResponse)
async def summary(
    request: Request,
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    email: str = Form(default=""),
) -> HTMLResponse:
    user_info = build_user_info(first_name, last_name, email)
    errors = validate_user_info(user_info)

    if errors:
        return render_index(
            request,
            user_info=user_info,
            errors=errors,
            form_error="Please provide your information again before viewing the summary.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request=request,
        name="summary.html",
        context={"user_info": user_info, "creator": CREATOR},
    )


@app.get("/summary")
async def summary_redirect() -> RedirectResponse:
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
