import json
import logging
import time

import ollama

from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

DEFAULT_MODEL: str = "qwen3-coder:30b"


def ask_ai(question: str, products: list[dict]) -> str:
    """Ask the local Ollama model a perfume-related question with product context."""

    logger.debug("Building prompt...")

    product_text = ""

    for p in products:
        product_text += (
            f"Name: {p['name']}\n"
            f"Brand: {p['brand']}\n"
            f"Category: {p['category']}\n"
            f"Price: ৳{p['price']}\n"
        )

        # Add available variants/sizes
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

    user_prompt = f"""\
Customer question:
{question}

Available products:

{product_text}"""

    logger.info(
        "Prompt length: %d characters",
        len(SYSTEM_PROMPT) + len(user_prompt),
    )
    logger.info("Sending request to Ollama...")

    start = time.time()

    response = ollama.chat(
        model=DEFAULT_MODEL,
        options={
            "temperature": 0.2
        },
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    elapsed = time.time() - start

    logger.info("Finished in %.2f seconds", elapsed)

    return response["message"]["content"]