"""Prompt construction for AI providers."""

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any

try:
    from .config import MAX_HISTORY_MESSAGES, PROMPT_HARD_LIMIT
    from .language import detect_language
    from .prompts import SYSTEM_PROMPT
except ImportError:  # pragma: no cover - supports running modules directly
    from config import MAX_HISTORY_MESSAGES, PROMPT_HARD_LIMIT
    from language import detect_language
    from prompts import SYSTEM_PROMPT


logger = logging.getLogger(__name__)

MAX_PROMPT_PRODUCTS = 5

LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "en": "Respond only in English.",
    "bn": "Respond only in Bangla.",
    "bn-en": "Respond naturally in Banglish.",
}

FINAL_RESPONSE_RULES: tuple[str, ...] = (
    "Recommend no more than 3 products.",
    "Never invent products, prices, stock, sizes, or attributes.",
    "Recommend only from the supplied products.",
    "Prefer individual perfumes unless the customer asks for combos.",
    "If nothing matches, say so politely.",
    "Ask one follow-up question only if necessary.",
)


def build_prompt(
    user_message: str,
    products: list[dict],
    history: list[dict],
    language: str,
) -> str:
    """Build one complete prompt for any AI provider."""

    language = language or detect_language(user_message)
    safe_history = _sanitize_history(history)[-MAX_HISTORY_MESSAGES:]
    product_limit = min(len(products), MAX_PROMPT_PRODUCTS)

    prompt = _compose_prompt(user_message, products[:product_limit], safe_history, language)

    while len(prompt) > PROMPT_HARD_LIMIT and safe_history:
        safe_history = safe_history[2:] if len(safe_history) > 1 else []
        prompt = _compose_prompt(
            user_message,
            products[:product_limit],
            safe_history,
            language,
        )

    while len(prompt) > PROMPT_HARD_LIMIT and product_limit > 0:
        product_limit -= 1
        prompt = _compose_prompt(
            user_message,
            products[:product_limit],
            safe_history,
            language,
        )

    if len(prompt) > PROMPT_HARD_LIMIT:
        logger.warning(
            "Prompt exceeds hard limit after trimming: %d characters",
            len(prompt),
        )
    else:
        logger.info("Prompt length: %d characters", len(prompt))

    return prompt


def _compose_prompt(
    user_message: str,
    products: Sequence[Mapping[str, Any]],
    history: Sequence[Mapping[str, str]],
    language: str,
) -> str:
    """Compose prompt sections in the required order."""

    sections = [
        _section("System prompt", SYSTEM_PROMPT.strip()),
        _section("Conversation history", _format_history(history)),
        _section("Current customer message", user_message.strip()),
        _section("Current product list", _format_products(products)),
        _section("Final response instructions", _format_final_instructions(language)),
    ]
    return "\n\n".join(sections).strip()


def _section(title: str, content: str) -> str:
    """Format a named prompt section."""

    return f"{title.upper()}\n{content.strip() or 'None'}"


def _sanitize_history(history: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Keep only user and assistant messages with plain text content."""

    safe_history: list[dict[str, str]] = []

    for message in history:
        role = str(message.get("role", "")).lower()
        content = str(message.get("content", "")).strip()

        if role not in {"user", "assistant"} or not content:
            continue

        safe_history.append({"role": role, "content": content})

    return safe_history


def _format_history(history: Sequence[Mapping[str, str]]) -> str:
    """Format concise conversation history."""

    if not history:
        return "None"

    lines: list[str] = []
    for message in history:
        label = "Customer" if message["role"] == "user" else "Assistant"
        lines.append(f"{label}: {message['content']}")

    return "\n".join(lines)


def _format_products(products: Sequence[Mapping[str, Any]]) -> str:
    """Format current product context with only available fields."""

    if not products:
        return "No matching products were supplied."

    lines: list[str] = []

    for index, product in enumerate(products, start=1):
        fields = _product_fields(product)
        if fields:
            lines.append(f"{index}. " + " | ".join(fields))

        variants = _format_variants(product)
        if variants:
            lines.append(f"   Available variants/sizes: {variants}")

    return "\n".join(lines) if lines else "No matching products were supplied."


def _product_fields(product: Mapping[str, Any]) -> list[str]:
    """Return compact product fields that actually exist."""

    fields: list[str] = []

    if product.get("name"):
        fields.append(f"Name: {product['name']}")
    if product.get("brand"):
        fields.append(f"Brand: {product['brand']}")
    if product.get("category"):
        fields.append(f"Category: {product['category']}")
    if product.get("price") is not None:
        fields.append(f"Price: ৳{product['price']}")

    return fields


def _format_variants(product: Mapping[str, Any]) -> str:
    """Format available variants from stored product data."""

    raw_data = product.get("data")
    if not raw_data:
        return ""

    try:
        data = json.loads(raw_data)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning(
            "Failed to parse variant data for product %s: %s",
            product.get("name", "unknown"),
            exc,
        )
        return ""

    variants = data.get("variants")
    if not isinstance(variants, list):
        return ""

    formatted: list[str] = []
    for variant in variants:
        if not isinstance(variant, Mapping):
            continue

        size = variant.get("size")
        price = variant.get("price")

        if size and price is not None:
            formatted.append(f"{size}: ৳{price}")
        elif size:
            formatted.append(str(size))

    return "; ".join(formatted)


def _format_final_instructions(language: str) -> str:
    """Format final response instructions including language rule."""

    language_rule = LANGUAGE_INSTRUCTIONS.get(
        language,
        LANGUAGE_INSTRUCTIONS["en"],
    )
    rules = (language_rule, *FINAL_RESPONSE_RULES)
    return "\n".join(f"- {rule}" for rule in rules)
