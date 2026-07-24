import logging
import time

import ollama

try:
    from . import conversation
    from .config import OLLAMA_MODEL, TEMPERATURE
    from .language import detect_language
    from .prompt_builder import build_prompt
except ImportError:  # pragma: no cover
    import conversation
    from config import OLLAMA_MODEL, TEMPERATURE
    from language import detect_language
    from prompt_builder import build_prompt


logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "cli"

# Track detected language per user to maintain consistency across turns
_user_language: dict[str, str] = {}

FALLBACK_MESSAGE = (
    "Sorry, I am having trouble processing your request right now. "
    "Please try again in a moment."
)


def ask_ai(
    question: str,
    products: list[dict],
    searched: bool,
    user_id: str = DEFAULT_USER_ID,
) -> tuple[str, list[dict]]:
    """
    Send a perfume-related question to Ollama.

    Handles:
    - prompt creation
    - language detection
    - Ollama failures
    - invalid responses
    - conversation storage

    Returns:
        (assistant_reply, updated_history)
    """

    if not question.strip():
        return (
            "Please tell me what perfume you are looking for.",
            conversation.get_history(user_id),
        )

    try:
        language = detect_language(question)

        # Preserve detected language across turns for consistency.
        # Only update when the new message has enough content to detect.
        prev_lang = _user_language.get(user_id)
        if language == "en" and prev_lang and prev_lang != "en":
            # If user was speaking Bangla/Banglish and sends a short English
            # query like "price?" or "notes?" (follow-up), keep the previous
            # language so the assistant responds in the same language.
            word_count = len(question.strip().split())
            if word_count <= 4:
                language = prev_lang
        if prev_lang != language and (language != prev_lang and len(question.strip().split()) > 3 or not prev_lang):
                _user_language[user_id] = language

        logger.debug(
            "Building prompt | user=%s | language=%s",
            user_id,
            language,
        )

        prompt = build_prompt(
            user_message=question,
            products=products,
            searched=searched,
            history=conversation.get_history(user_id),
            language=language,
            user_id=user_id,
        )

    except Exception:
        logger.exception("Prompt building failed")

        return (
            FALLBACK_MESSAGE,
            conversation.get_history(user_id),
        )


    logger.info(
        "Sending request to Ollama | model=%s",
        OLLAMA_MODEL,
    )

    start_time = time.time()

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            options={
                "temperature": TEMPERATURE,
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

    except Exception:
        logger.exception("Ollama request failed")

        return (
            FALLBACK_MESSAGE,
            conversation.get_history(user_id),
        )


    elapsed = time.time() - start_time

    logger.info(
        "Ollama completed | %.2fs",
        elapsed,
    )


    assistant_reply = (
        response
        .get("message", {})
        .get("content", "")
        .strip()
    )


    if not assistant_reply:
        logger.warning(
            "Ollama returned empty response"
        )

        assistant_reply = FALLBACK_MESSAGE


    try:
        conversation.add_user_message(
            user_id,
            question,
        )

        conversation.add_assistant_message(
            user_id,
            assistant_reply,
        )

        history = conversation.get_history(user_id)

    except Exception:
        logger.exception(
            "Conversation storage failed"
        )

        history = []


    return assistant_reply, history