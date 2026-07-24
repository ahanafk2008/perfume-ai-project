"""Prompt construction for AI providers."""

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any

try:
    from .config import MAX_HISTORY_MESSAGES, PROMPT_HARD_LIMIT
    from .language import detect_language
    from .preferences import get_preferences
    from .product_attrs import format_product_attributes
    from .prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_SHORT
except ImportError:  # pragma: no cover - supports running modules directly
    from config import MAX_HISTORY_MESSAGES, PROMPT_HARD_LIMIT
    from language import detect_language
    from preferences import get_preferences
    from product_attrs import format_product_attributes
    from prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_SHORT


logger = logging.getLogger(__name__)

MAX_PROMPT_PRODUCTS = 10

LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "en": "Respond only in English.",
    "bn": "Respond only in Bangla (Bengali). Use natural, conversational Bangla — prefer common words like পারফিউম, দাম, আছে, চান, ভালো over formal/sanskritized alternatives.",
    "bn-en": "Respond naturally in Banglish (mixed Bengali and English). Use common spoken forms like 'eta', 'ache', 'dam', 'valo'. Avoid formal Bangla.",
}

FINAL_RESPONSE_RULES: tuple[str, ...] = (
    "The product list below comes directly from the database.",
    "Recommend no more than 3 products.",
    "Never invent products, prices, stock, sizes, or attributes.",
    "Never recommend any perfume not in the product list, even from general knowledge.",
    "Prefer individual perfumes unless the customer asks for combos.",
)


def build_prompt(
    user_message: str,
    products: list[dict],
    searched: bool,
    history: list[dict],
    language: str,
    user_id: str = "cli",
) -> str:
    """Build one complete prompt for any AI provider.

    Priority order (highest to lowest):
    1. User message (never trimmed)
    2. Product data
    3. Preferences
    4. Instructions
    5. System prompt
    6. History
    """

    language = language or detect_language(user_message)
    safe_history = _sanitize_history(history)[-MAX_HISTORY_MESSAGES:]

    prompt = _compose_prompt(
        user_message,
        list(products),
        searched,
        safe_history,
        language,
        user_id=user_id,
    )

    # Step 1: Trim conversation history. Never remove user query or products.
    while len(prompt) > PROMPT_HARD_LIMIT and safe_history:
        safe_history = safe_history[2:] if len(safe_history) > 1 else []
        prompt = _compose_prompt(
            user_message,
            list(products),
            searched,
            safe_history,
            language,
            user_id=user_id,
        )

    # Step 2: Use shorter system prompt if still over limit.
    if len(prompt) > PROMPT_HARD_LIMIT:
        prompt = _compose_prompt(
            user_message,
            list(products),
            searched,
            safe_history,
            language,
            user_id=user_id,
            use_short_prompt=True,
        )

    # Step 3: Remove variant/attribute detail from all products if still over limit.
    if len(prompt) > PROMPT_HARD_LIMIT:
        trimmed = _without_variants(products)
        prompt = _compose_prompt(
            user_message,
            trimmed,
            searched,
            safe_history,
            language,
            user_id=user_id,
            use_short_prompt=True,
        )

    # Step 4: Keep only name + price (still preserving ALL products) if still over limit.
    if len(prompt) > PROMPT_HARD_LIMIT:
        trimmed = _minimal_products(products)
        prompt = _compose_prompt(
            user_message,
            trimmed,
            searched,
            safe_history,
            language,
            user_id=user_id,
            use_short_prompt=True,
        )

    # Log with section breakdown for debugging.
    if logger.isEnabledFor(logging.DEBUG):
        _log_section_sizes(user_message, products, searched, safe_history, language)

    if len(prompt) > PROMPT_HARD_LIMIT:
        logger.warning(
            "Prompt exceeds hard limit after all trimming: %d characters (budget: %d)",
            len(prompt),
            PROMPT_HARD_LIMIT,
        )
    else:
        logger.info("Prompt length: %d characters | products: %d", len(prompt), len(products))

    _log_prompt_debug(
        user_message,
        products,
        searched,
        prompt,
    )

    return prompt


def _log_prompt_debug(
    user_message: str,
    products: Sequence[Mapping[str, Any]],
    searched: bool,
    prompt: str,
) -> None:
    """Log prompt summary before sending to AI."""

    product_names = [
        product.get("name", "")
        for product in products
        if isinstance(product, Mapping) and product.get("name")
    ]

    logger.info(
        "PROMPT DEBUG:\n"
        "Length: %d\n"
        "Products included: %d\n"
        "Products:\n%s",
        len(prompt),
        len(products),
        "\n".join(f"- {name}" for name in product_names) if product_names else "- None",
    )


def _compose_prompt(
    user_message: str,
    products: Sequence[Mapping[str, Any]],
    searched: bool,
    history: Sequence[Mapping[str, str]],
    language: str,
    user_id: str = "cli",
    use_short_prompt: bool = False,
) -> str:
    """Compose prompt sections in the required order."""

    # Include user preferences if available
    prefs = get_preferences(user_id)
    prefs_text = prefs.format_for_prompt()

    system = SYSTEM_PROMPT_SHORT.strip() if use_short_prompt else SYSTEM_PROMPT.strip()

    sections = [
        _section("System prompt", system),
        _section("Conversation history", _format_history(history)),
        _section("Current customer message", user_message.strip()),
        _section("Customer preferences", prefs_text),
        _section(
            "Available products",
            _format_products(products, searched),
        ),
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


def _format_products(
    products: Sequence[Mapping[str, Any]],
    searched: bool,
) -> str:
    """Format current product context with only available fields."""

    if not searched:
        return (
            "No product search was performed. "
            "This does NOT mean the store has no products. "
            "If the customer asks generally about the store or its products, "
            "answer using the system instructions."
        )

    if not products:
        return (
            "A product search was performed, "
            "but no matching products were found."
        )

    lines: list[str] = []

    lines.append("PRODUCTS:")

    for index, product in enumerate(products, start=1):
        fields = _product_fields(product)
        if fields:
            lines.append(f"{index}. " + " | ".join(fields))

        variants = _format_variants(product)
        if variants:
            lines.append(f"   Available variants/sizes: {variants}")

    if not lines:
        return (
            "Product data was provided, but no displayable product information "
            "was available. Do not assume the store has no products."
        )

    return "\n".join(lines)


def _product_fields(product: Mapping[str, Any]) -> list[str]:
    """Return compact product fields that actually exist.

    Only includes structured database fields (name, brand, category, price)
    and structured fragrance attributes from fragrance_details.
    Never includes unstructured description or tagline — those cause AI hallucination.
    """

    fields: list[str] = []

    if product.get("name"):
        fields.append(product["name"])
    if product.get("brand"):
        fields.append(product["brand"])
    if product.get("category"):
        fields.append(product["category"])
    if product.get("price") is not None:
        fields.append(f"৳{product['price']}")

    attrs = format_product_attributes(product) if product.get("data") else None
    if attrs:
        fields.append(f"[{attrs}]")

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
            formatted.append(f"{size}(৳{price})")
        elif size:
            formatted.append(str(size))

    return ", ".join(formatted)


def _without_variants(products: Sequence[Mapping[str, Any]]) -> list[dict]:
    """Remove variant data (data field) from products to save space."""
    return [{k: v for k, v in p.items() if k != "data"} for p in products]


def _minimal_products(products: Sequence[Mapping[str, Any]]) -> list[dict]:
    """Keep only name and price for minimal product context."""
    minimal: list[dict] = []
    for p in products:
        entry: dict[str, Any] = {}
        if p.get("name"):
            entry["name"] = p["name"]
        if p.get("price") is not None:
            entry["price"] = p["price"]
        minimal.append(entry)
    return minimal


def _log_section_sizes(
    user_message: str,
    products: Sequence[Mapping[str, Any]],
    searched: bool,
    history: Sequence[Mapping[str, str]],
    language: str,
) -> None:
    """Log size of each prompt section (DEBUG level)."""

    system_len = len(SYSTEM_PROMPT.strip())
    history_len = len(_format_history(history))
    user_len = len(user_message.strip())
    prefs = get_preferences()
    prefs_len = len(prefs.format_for_prompt())
    products_len = len(_format_products(products, searched))
    instructions_len = len(_format_final_instructions(language))

    logger.debug(
        "Section sizes (chars) — system: %d, history: %d, user: %d, prefs: %d, products: %d, "
        "instructions: %d | total: %d",
        system_len,
        history_len,
        user_len,
        prefs_len,
        products_len,
        instructions_len,
        system_len + history_len + user_len + prefs_len + products_len + instructions_len,
    )


def _format_final_instructions(language: str) -> str:
    """Format final response instructions including language rule."""

    language_rule = LANGUAGE_INSTRUCTIONS.get(
        language,
        LANGUAGE_INSTRUCTIONS["en"],
    )
    rules = (language_rule, *FINAL_RESPONSE_RULES)
    return "\n".join(f"- {rule}" for rule in rules)