# Gemini Bonus Assistant

This folder contains the optional Gemini-powered bonus assistant for the college inquiry chatbot project.

## Purpose

- Keep all Gemini-specific logic isolated from the required rubric implementation.
- Allow the main FastAPI app to enable AI mode explicitly without making Gemini the default path.
- Keep the required four-question chatbot fully functional even if Gemini is unavailable.

## Files

- `gemini_client.py`: Gemini REST client and error handling
- `prompts.py`: grounding instructions and fallback messages
- `college_facts.py`: configured college facts and supported topic keywords
- `schemas.py`: lightweight settings/result types
- `__init__.py`: small import surface for the main app

## Environment

Expected environment variable:

```env
GEMINI_API_KEY=your_api_key_here
```

Optional override:

```env
GEMINI_MODEL=gemini-2.5-flash
```

The client also reads `.env` directly for local development if the variable is not already exported in the shell.

## Behavior

- Gemini mode is bonus-only and must be explicitly enabled from the chat UI.
- The assistant is grounded to the configured college facts.
- Unsupported questions return a controlled fallback instead of a speculative answer.
- Gemini failures return a safe unavailable message and do not crash the main app.

## Local Use

1. Add `GEMINI_API_KEY` to `.env`.
2. Start the FastAPI app normally.
3. Open the required chatbot flow.
4. Click `Try Gemini Bonus Mode`.
5. Ask a custom question related to the configured college facts.

## Notes

- This module does not replace the graded rule-based chatbot.
- It is intended as an optional enhancement for demo purposes.
