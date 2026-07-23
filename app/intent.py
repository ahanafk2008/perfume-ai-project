"""
Intent detection for Perfume AI Assistant.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from .normalize import normalize


class Intent(str, Enum):
    GREETING = "greeting"
    THANKS = "thanks"
    GOODBYE = "goodbye"
    CASUAL = "casual"

    STORE_INFO = "store_info"

    PRODUCT_SEARCH = "product_search"
    PRODUCT_DETAIL = "product_detail"
    PRODUCT_INFO = "product_info"
    PRICE_QUERY = "price_query"
    ATTRIBUTE_QUERY = "attribute_query"
    COMPARISON_QUERY = "comparison_query"

    DELIVERY = "delivery"
    PAYMENT = "payment"
    LOCATION = "location"
    ORDER = "order"

    FOLLOW_UP = "follow_up"

    GIFT = "gift"
    LUXURY = "luxury"
    COMPLIMENT = "compliment"

    UNKNOWN = "unknown"


# -----------------------------
# Conversation
# -----------------------------

STORE_INFO_KEYWORDS = {
    "what do you sell",
    "what do you have",
    "what products",
    "what are you selling",
    "what do you guys sell",
    "what does your shop sell",

    "কি বিক্রি করেন",
    "কি কি বিক্রি করেন",
    "কি আছে",

    "ki bikri koren",
    "ki ki bikri koren",
    "ki ase",
    "apnara ki bikri koren",
    "apnara ki ki bikri koren",
}

GREETINGS = {
    "hi",
    "hello",
    "hey",
    "salam",
    "assalamu alaikum",
    "হাই",
    "হ্যালো",
    "সালাম",
    "কেমন আছেন",
    "kemon achen",
}


THANKS = {
    "thanks",
    "thank you",
    "thankyou",
    "thank u",
    "thx",
    "ধন্যবাদ",
    "dhonnobad",
}


GOODBYES = {
    "bye",
    "goodbye",
    "see you",
    "take care",
    "allah hafez",
    "আল্লাহ হাফেজ",
}


CASUAL = {
    "nice",
    "perfect",
    "great",
    "awesome",
    "cool",
    "ok",
    "okay",
}


# -----------------------------
# FAQ
# -----------------------------

DELIVERY_KEYWORDS = {
    "delivery",
    "deliver",
    "shipping",
    "courier",
    "delivery charge",
    "delivery time",
    "ডেলিভারি",
    "কত দিনে",
    "koto din",
}


PAYMENT_KEYWORDS = {
    "payment",
    "pay",
    "cod",
    "cash on delivery",
    "bkash",
    "nagad",
    "card",
    "পেমেন্ট",
    "বিকাশ",
    "নগদ",
}


LOCATION_KEYWORDS = {
    "location",
    "address",
    "shop",
    "store",
    "branch",
    "ঠিকানা",
    "কোথায়",
    "লোকেশন",
}


# -----------------------------
# Order
# ONLY strong, unambiguous buying-action phrases.
# Do NOT add bare words like "want" / "need" / "looking for" here —
# those are what caused order/product-search confusion before, since
# they show up constantly in ordinary product questions too.
# -----------------------------

ORDER_KEYWORDS = {
    # English - explicit checkout intent
    "place order",
    "confirm order",
    "order now",
    "checkout",
    "add to cart",
    "buy now",
    "purchase now",
    "i want to order",
    "i want this delivered",
    "send this to me",

    # Bangla
    "অর্ডার করবো",
    "অর্ডার দিবো",
    "অর্ডার করতে চাই",
    "এটা অর্ডার করবো",
    "এটা বুক করুন",

    # Banglish
    "order korbo",
    "order dibo",
    "order korte chai",
    "eta order korbo",
    "pathiye din",
    "send kore den",
}

# -----------------------------
# Gift
# -----------------------------

GIFT_KEYWORDS = {
    "gift",
    "gifts",
    "present",
    "presents",
    "birthday",
    "anniversary",
    "valentine",
    "for her",
    "for him",
    "for wife",
    "for husband",
    "for girlfriend",
    "for boyfriend",
    "for mom",
    "for dad",
    "for mother",
    "for father",
    "for sister",
    "for brother",
    "wife",
    "husband",
    "girlfriend",
    "boyfriend",
    "mom",
    "dad",
    "উপহার",
    "eid",
    "ঈদ",
    "সারপ্রাইজ",
    "surprise",
    "বিয়ে",
    "biye",
}

# -----------------------------
# Product Search
# -----------------------------

PRODUCT_KEYWORDS = {

    # Product types
    "perfume",
    "fragrance",
    "attar",
    "ittr",
    "scent",
    "body spray",
    "mist",
    "oud",
    "musk",

    # Brands
    "lattafa",
    "armaf",
    "rasasi",
    "dior",
    "chanel",
    "versace",
    "gucci",
    "tom ford",
    "hawas",
    "yara",
    "asad",

    # Price/budget
    "under",
    "below",
    "budget",
    "price",
    "cost",
    "cheap",
    "taka",
    "tk",
    "৳",

    # Notes
    "vanilla",
    "rose",
    "woody",
    "fresh",
    "sweet",
    "citrus",
    "amber",
    "aquatic",

    # Search patterns (multi-word, handled by substring check)
    "looking for",
    "looking",

    # Bangla
    "পারফিউম",
    "আতর",
    "সুগন্ধি",
    "দাম",
    "কত",
}


# -----------------------------
# Product detail keywords
# Only phrases that clearly reference a specific product context.
# -----------------------------

PRODUCT_INFO_KEYWORDS = {
    "how much is",
    "how much does it cost",
    "what is the price",
    "what's the price",
    "price of",
    "cost of",
    "কত টাকা",
    "দাম কত",
    "দাম",
    "কত দাম",
    "what are the notes",
    "what notes does it have",
    "notes of",
    "notes in",
    "how long does it last",
    "longevity",
    "long lasting",
    "lasts long",
    "how long",
    "is it original",
    "is this original",
    "is it authentic",
    "is this authentic",
    "authentic",
    "original",
    "description of",
    "about this",
    "about that",
    "tell me about",
    "information about",
    "details of",
    "size of",
    "weight of",
    "stock",
    "available",
    "original kina",
    "eta original",
    "kina",
    "আসল",
    "এটা আসল",
    "এটা অরিজিনাল",
}

PRICE_QUERY_KEYWORDS = {
    "how much",
    "what is the price",
    "price",
    "cost",
    "pricing",
}

ATTRIBUTE_QUERY_KEYWORDS = {
    "notes",
    "note",
    "ingredients",
    "composition",
    "top notes",
    "middle notes",
    "base notes",
    "longevity",
    "lasting",
    "sillage",
    "projection",
    "authentic",
    "original",
    "fake",
    "real",
    "replica",
    "copy",
    "dupe",
    "similar",
    "alternative",
    "size",
    "ml",
    "volume",
    "weight",
    "kina",
    "আসল",
    "অরিজিনাল",
    "eta",
}

COMPARISON_QUERY_KEYWORDS = {
    "vs",
    "versus",
    "compare",
    "comparison",
    "difference between",
    "which is better",
    "which one is better",
    "better than",
    "or",
    "or this one",
    "or that one",
    "should i buy",
    "which should i choose",
    "which one should i",
}

# -----------------------------
# Follow-up phrases
# Used only when the CALLER tells us the previous turn was a
# product search (see `previous_intent` param below). This is
# intentionally tiny — it just keeps a bare "which one is best?"
# from falling into UNKNOWN right after a product list was shown.
# Real multi-turn memory (storing the actual product list, filters,
# etc.) belongs in the calling app/session layer, not here.
# -----------------------------

FOLLOWUP_KEYWORDS = {
    "which one",
    "which is best",
    "best one",
    "recommend one",
    "kon ta",
    "kun ta bhalo",
    "eituku",
    "ei tao",
    "how about it",
    "should i buy",
    "this perfume",
    "this one",
    "that one",
}


# -----------------------------
# Helpers
# -----------------------------

def matches_phrase(message: str, phrases: set[str]) -> bool:
    return message in phrases


def starts_with_phrase(message: str, phrases: set[str]) -> bool:
    return any(
        message == p or message.startswith(p + " ")
        for p in phrases
    )


def _token_matches(word: str, keyword: str) -> bool:
    """Match a single-word keyword against a message token, tolerating
    simple English plurals (oud/ouds, attar/attars)."""
    if word == keyword:
        return True
    if word == keyword + "s":
        return True
    if word.endswith("s") and word[:-1] == keyword:
        return True
    return False


def contains_keyword(message: str, keywords: set[str]) -> bool:

    words = message.split()

    for keyword in keywords:

        if " " in keyword:
            if keyword in message:
                return True

        else:
            if any(_token_matches(w, keyword) for w in words):
                return True

    return False


# -----------------------------
# Main Detector
# -----------------------------

def detect_intent(
    message: str,
    previous_intent: Optional[Intent] = None,
    debug: bool = False,
) -> Intent:
    """Detect the user's intent."""

    raw_message = message.strip().lower()
    message = normalize(message)

    result = Intent.UNKNOWN

    # -----------------------------
    # Conversation
    # -----------------------------

    if starts_with_phrase(message, THANKS):
        result = Intent.THANKS

    elif starts_with_phrase(message, GOODBYES):
        result = Intent.GOODBYE

    elif starts_with_phrase(message, GREETINGS):
        result = Intent.GREETING

    # -----------------------------
    # FAQ
    # -----------------------------

    elif "cash on delivery" in message:
        result = Intent.PAYMENT

    elif contains_keyword(message, DELIVERY_KEYWORDS):
        result = Intent.DELIVERY

    elif contains_keyword(message, PAYMENT_KEYWORDS):
        result = Intent.PAYMENT

    elif contains_keyword(message, LOCATION_KEYWORDS):
        result = Intent.LOCATION

    # -----------------------------
    # Store information
    # -----------------------------

    elif contains_keyword(message, STORE_INFO_KEYWORDS):
        result = Intent.STORE_INFO

    # -----------------------------
    # Explicit product-info intents (must come before generic PRODUCT_SEARCH)
    # -----------------------------

    elif contains_keyword(message, PRODUCT_INFO_KEYWORDS):
        result = Intent.PRODUCT_INFO

    elif contains_keyword(message, PRICE_QUERY_KEYWORDS):
        result = Intent.PRICE_QUERY

    elif contains_keyword(message, ATTRIBUTE_QUERY_KEYWORDS):
        result = Intent.ATTRIBUTE_QUERY

    elif contains_keyword(message, COMPARISON_QUERY_KEYWORDS):
        result = Intent.COMPARISON_QUERY

    # -----------------------------
    # Gift intent (must be before generic PRODUCT_SEARCH and UNKNOWN)
    # -----------------------------

    elif contains_keyword(message, GIFT_KEYWORDS):
        result = Intent.GIFT

    elif contains_keyword(raw_message, GIFT_KEYWORDS):
        result = Intent.GIFT

    # -----------------------------
    # Product Search
    # -----------------------------

    elif contains_keyword(message, PRODUCT_KEYWORDS):
        result = Intent.PRODUCT_SEARCH

    # -----------------------------
    # Context order
    # -----------------------------

    elif (
        previous_intent == Intent.PRODUCT_SEARCH
        and message in {
            "i want this",
            "i need this",
            "want this one",
            "take this",
            "this one",
            "eta chai",
            "eta nibo",
            "এটা চাই",
            "এটা নিবো",
        }
    ):
        result = Intent.ORDER

    # -----------------------------
    # Strong order intent
    # -----------------------------

    elif contains_keyword(message, ORDER_KEYWORDS):
        result = Intent.ORDER

    # -----------------------------
    # Follow-up product question
    # -----------------------------

    elif (
        previous_intent in {
            Intent.PRODUCT_SEARCH,
            Intent.PRODUCT_DETAIL,
            Intent.PRODUCT_INFO,
            Intent.PRICE_QUERY,
            Intent.ATTRIBUTE_QUERY,
            Intent.COMPARISON_QUERY,
        }
        and contains_keyword(message, FOLLOWUP_KEYWORDS)
    ):
        result = Intent.FOLLOW_UP

    # -----------------------------
    # Casual
    # -----------------------------

    elif matches_phrase(message, CASUAL):
        result = Intent.CASUAL

    if debug:
        print(f"Input: {message}")
        print(f"Previous intent: {previous_intent}")
        print(f"Detected: {result}")

    return result
