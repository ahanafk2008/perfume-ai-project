import logging
import time

import ollama

try:
    from . import conversation
    from .config import OLLAMA_MODEL, TEMPERATURE
    from .language import detect_language
    from .prompt_builder import build_prompt
except ImportError:  # pragma: no cover - supports running main.py directly
    import conversation
    from config import OLLAMA_MODEL, TEMPERATURE
    from language import detect_language
    from prompt_builder import build_prompt

logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "cli"


def ask_ai(
    question: str,
    products: list[dict],
    history: list[dict] | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> tuple[str, list[dict]]:
    """
    Ask the local Ollama model a perfume-related question.

    The history argument is kept for backward-compatible callers. Conversation
    state is managed by app.conversation and stores only raw user/assistant
    messages, never product context.

    Returns:
        (assistant_reply, updated_history)
    """

    logger.debug("Building prompt...")

    prompt = build_prompt(
        user_message=question,
        products=products,
        history=conversation.get_history(user_id),
        language=detect_language(question),
    )

    logger.info("Sending request to Ollama...")

    start = time.time()

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

    elapsed = time.time() - start

    logger.info("Finished in %.2f seconds", elapsed)

    assistant_reply = response["message"]["content"]

    conversation.add_user_message(user_id, question)
    conversation.add_assistant_message(user_id, assistant_reply)

    return assistant_reply, conversation.get_history(user_id)
