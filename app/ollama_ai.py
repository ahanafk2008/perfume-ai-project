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