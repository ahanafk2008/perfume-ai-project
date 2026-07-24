# Gemini API integration

import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")

client = None
if api_key:
    client = genai.Client(api_key=api_key)

GEMINI_MODELS: list[str] = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def ask_gemini(question: str, products: list[dict]) -> str:
    """Ask Gemini a perfume-related question with product context."""

    if not question or not question.strip():
        return "Please enter a valid question."

    if not products:
        return "No products available right now."

    # Format products into a clean list
    product_text = ""

    for p in products:
        product_text += (
            f"Name: {p['name']}\n"
            f"Brand: {p['brand']}\n"
            f"Category: {p['category']}\n"
            f"Price: ৳{p['price']}\n\n"
        )

    user_prompt = f"""\
Customer question:
{question}

Available products:

{product_text}"""

    if client is None:
        return "[MOCK MODE] Gemini API key not configured."

    last_error: Exception | None = None

    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )
            return response.text.strip()
        except (ValueError, TypeError, RuntimeError) as e:
            logger.warning("Gemini model %s failed: %s", model_name, e)
            last_error = e

    logger.error("All Gemini models failed. Last error: %s", last_error)
    return "Sorry, I'm unable to process your request right now."