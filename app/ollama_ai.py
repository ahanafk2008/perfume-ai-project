import json
import logging
import time

import ollama

try:
    from . import conversation
    from .config import OLLAMA_MODEL, TEMPERATURE
    from .prompts import SYSTEM_PROMPT
except ImportError:  # pragma: no cover - supports running main.py directly
    import conversation
    from config import OLLAMA_MODEL, TEMPERATURE
    from prompts import SYSTEM_PROMPT

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

    product_text = ""

    for p in products:
        product_text += (
            f"Name: {p['name']}\n"
            f"Brand: {p['brand']}\n"
            f"Category: {p['category']}\n"
            f"Price: ৳{p['price']}\n"
        )

        if p.get("data"):
            try:
                data = json.loads(p["data"])

                if "variants" in data and data["variants"]:
                    product_text += "Available sizes:\n"

                    for v in data["variants"]:
                        size = v.get("size", "Unknown")
                        price = v.get("price", "Unknown")
                        product_text += f"- {size}: ৳{price}\n"

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(
                    "Failed to parse variant data for product %s: %s",
                    p.get("name", "unknown"),
                    e,
                )

        product_text += "\n"

    user_prompt = f"""Customer question:
{question}

Available products:

{product_text}"""

    logger.info(
        "Prompt length: %d characters",
        len(SYSTEM_PROMPT) + len(user_prompt),
    )

    logger.info("Sending request to Ollama...")

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    messages.extend(conversation.get_history(user_id))

    messages.append(
        {
            "role": "user",
            "content": user_prompt,
        }
    )

    start = time.time()

    response = ollama.chat(
        model=OLLAMA_MODEL,
        options={
            "temperature": TEMPERATURE,
        },
        messages=messages,
    )

    elapsed = time.time() - start

    logger.info("Finished in %.2f seconds", elapsed)

    assistant_reply = response["message"]["content"]

    conversation.add_user_message(user_id, question)
    conversation.add_assistant_message(user_id, assistant_reply)

    return assistant_reply, conversation.get_history(user_id)
