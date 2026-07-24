"""Objection handling for sales-related user concerns.

Each function returns a natural, concise response from the perspective
of a Bangladesh perfume seller. Functions do NOT invent discounts,
promise fake offers, or claim authenticity unless verified.
"""

import logging
import re

from app.intent import Intent

logger = logging.getLogger(__name__)

# Known Bangla/Banglish filler words to ignore when extracting product names
_FILLER_WORDS = {
    "eta", "eita", "oi", "oita", "shei", "seta", "ei", "ai",
    "ki", "keno", "kno", "koto", "ar", "er", "tar", "der",
    "this", "that", "the", "a", "an", "is", "are", "was",
    "why", "how", "what", "which", "your", "you", "it", "its",
    "price", "dam", "dham", "perfume", "fragrance", "attar",
    "give", "last", "convince", "sell", "tell", "show", "want",
    "need", "can", "will", "would", "could", "should", "does",
    "have", "has", "had", "not", "but", "for", "with", "from",
    "free", "more", "less", "much", "many", "very", "too",
    "get", "buy", "bought", "been", "being",
    "daraz", "another", "other", "cheap", "cheaper",
    "discount", "offer", "final", "reduce", "reduced",
}


def _extract_product_name(message: str) -> str | None:
    """Try to extract a product/perfume name from an objection message.

    Matches capitalized words (brand/product names) and quoted strings.
    """
    for quoted in re.findall(r'"([^"]+)"', message):
        return quoted.strip()

    cap_matches = re.findall(r"\b([A-Z][A-Z0-9]{2,}(?:\s+[A-Z][a-z0-9]+)*)\b", message)
    if cap_matches:
        return cap_matches[0]

    cap_matches = re.findall(r"\b([A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)*)\b", message)
    seen: set[str] = set()
    for name in cap_matches:
        lower = name.lower()
        if lower not in _FILLER_WORDS and lower not in seen:
            seen.add(lower)
            if len(name) > 2:
                return name

    return None


def handle_price_objection(perfume_name: str | None = None) -> str:
    """Respond to a price-related objection, optionally with a known perfume name."""
    if perfume_name:
        return (
            f"I understand your concern about the price of {perfume_name}. "
            f"Our pricing reflects the authenticity, quality sourcing, and service we provide. "
            f"If you share your budget, I can suggest alternatives or explain what makes it worth the price."
        )
    return (
        "Our prices depend on authenticity, quality sourcing, and current offers. "
        "If you tell me which perfume you are comparing, I can explain the value."
    )


def handle_competitor_objection(competitor_name: str | None = None) -> str:
    """Respond when a user mentions a competitor's lower price."""
    if competitor_name and competitor_name.lower() in {"daraz", "daraz এ", "daraz a", "দারাজ"}:
        return (
            "I understand you found a lower price on Daraz. "
            "We focus on 100% authentic products with proper customer support and reliable delivery. "
            "If you share the specific perfume name, I can explain the quality and service differences."
        )
    return (
        "I understand you found a better price elsewhere. "
        "We ensure product authenticity, quality assurance, and reliable customer support. "
        "If you tell me which perfume you're comparing, I can explain the value we offer."
    )


def handle_discount_request(perfume_name: str | None = None) -> str:
    """Respond when a user asks for a discount."""
    if perfume_name:
        return (
            f"I understand you're looking for a discount on {perfume_name}. "
            f"Let me check if there are any current offers available. "
            f"Could you let me know your budget? I can also suggest similar options."
        )
    return (
        "Let me check our current offers for you. "
        "Which perfume are you interested in? I can help find the best available deal."
    )


def handle_negotiation(perfume_name: str | None = None) -> str:
    """Respond to price negotiation attempts."""
    if perfume_name:
        return (
            f"I understand you're interested in {perfume_name}. "
            f"Let me check if there are any current offers or deals available. "
            f"Our prices are already competitive for authentic products."
        )
    return (
        "Which perfume are you interested in? "
        "I can check the price and any available offers for you."
    )


def handle_delivery_objection() -> str:
    """Respond when a user asks about free delivery."""
    return (
        "Delivery charges depend on your location and order value. "
        "For specific information about free delivery eligibility, "
        "please contact Scent Of Time directly."
    )


def handle_sales_persuasion(perfume_name: str | None = None) -> str:
    """Respond when a user asks to be convinced or sold."""
    if perfume_name:
        return (
            f"{perfume_name} is a quality product that offers great value. "
            f"We ensure authenticity, competitive pricing, and reliable delivery across Bangladesh. "
            f"Would you like to know more about its performance and notes?"
        )
    return (
        "We offer 100% authentic perfumes sourced directly from authorized distributors. "
        "Our prices are competitive for genuine products, and we ensure fast delivery across Bangladesh. "
        "Tell me what you're looking for and I'll help find the perfect match!"
    )


def handle_trust_concern() -> str:
    """Respond to trust or authenticity concerns."""
    return (
        "I understand your concern. We take authenticity seriously and source our products "
        "from authorized distributors. Scent Of Time provides customer support and reliable delivery. "
        "If you have a specific perfume in mind, I can check details for you. "
        "You can also contact Scent Of Time directly for more information about our return policy."
    )


def handle_intent(
    intent: Intent,
    message: str,
    product_context: dict | None = None,
) -> str | None:
    """Route an objection intent to the appropriate handler.

    Args:
        intent: The detected objection intent.
        message: The user's raw message.
        product_context: Optional previously-discussed product (from conversation history).

    Returns:
        A response string, or None if this handler does not apply.
    """
    perfume_name = _extract_product_name(message) or (
        product_context.get("name") if product_context else None
    )

    logger.info("Detected objection intent: %s (perfume: %s)", intent, perfume_name)

    if intent == Intent.OBJECTION_PRICE:
        return handle_price_objection(perfume_name)
    if intent == Intent.OBJECTION_COMPETITOR:
        competitor = None
        msg_lower = message.lower()
        for site in ["daraz", "priyoshop", "daraz এ", "daraz a"]:
            if site in msg_lower:
                competitor = "Daraz"
                break
        return handle_competitor_objection(competitor)
    if intent == Intent.REQUEST_DISCOUNT:
        return handle_discount_request(perfume_name)
    if intent == Intent.REQUEST_NEGOTIATION:
        return handle_negotiation(perfume_name)
    if intent == Intent.REQUEST_DELIVERY:
        return handle_delivery_objection()
    if intent == Intent.SALES_PERSUASION:
        return handle_sales_persuasion(perfume_name)
    if intent == Intent.TRUST_CONCERN:
        return handle_trust_concern()

    return None
