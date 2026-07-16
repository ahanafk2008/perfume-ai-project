"""
Intent detection for Perfume AI Assistant.
"""

from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    THANKS = "thanks"
    GOODBYE = "goodbye"
    PRODUCT_SEARCH = "product_search"
    UNKNOWN = "unknown"


GREETINGS = {
    # English
    "hi",
    "hello",
    "hey",
    "hey there",
    "hiya",
    "howdy",
    "good morning",
    "good afternoon",
    "good evening",
    "good night",
    "morning",
    "evening",
    "yo",
    "sup",
    "whats up",
    "what's up",
    "how are you",
    "how r u",
    "how are u",
    "are you there",

    # Bangla
    "হাই",
    "হ্যালো",
    "হেই",
    "সালাম",
    "আসসালামু আলাইকুম",
    "কেমন আছেন",
    "কেমন আছো",
    "কি খবর",

    # Banglish
    "salam",
    "salaam",
    "assalamu alaikum",
    "assalamualaikum",
    "assalamu alikum",
    "assalamu walikum",
    "kemon achen",
    "kemon acho",
    "ki khobor",

    # Chat
    "hi there",
    "hello there",
}


THANKS = {
    "thanks",
    "thank you",
    "thankyou",
    "thank u",
    "thanks a lot",
    "thank you so much",
    "many thanks",
    "appreciate it",
    "thx",
    "ty",
    "tysm",

    # Bangla
    "ধন্যবাদ",
    "অনেক ধন্যবাদ",
    "অনেক অনেক ধন্যবাদ",
    "আপনাকে ধন্যবাদ",

    # Banglish
    "dhonnobad",
    "onek dhonnobad",
    "apnake dhonnobad",
}


GOODBYES = {
    "bye",
    "goodbye",
    "good bye",
    "see you",
    "see ya",
    "see u",
    "take care",
    "have a good day",
    "have a nice day",

    # Bangla
    "বিদায়",
    "বিদায়",
    "আল্লাহ হাফেজ",
    "খোদা হাফেজ",
    "ভালো থাকবেন",
    "ভালো থেকো",

    # Banglish
    "allah hafez",
    "allah hafiz",
    "khoda hafez",
    "khuda hafez",
    "valo thakben",
    "bhalo thakben",

    # Casual
    "ok bye",
    "okay bye",
    "bye bye",
}


PRODUCT_KEYWORDS = {
    # Product
    "perfume",
    "fragrance",
    "attar",
    "ittr",
    "body spray",
    "mist",
    "deodorant",
    "scent",
    "oud",
    "musk",

    # Notes
    "vanilla",
    "rose",
    "floral",
    "woody",
    "fresh",
    "sweet",
    "citrus",
    "fruity",
    "spicy",
    "leather",
    "amber",
    "aquatic",
    "long lasting",

    # Gender
    "men",
    "man",
    "male",
    "women",
    "woman",
    "female",
    "unisex",

    # Buying
    "buy",
    "want",
    "need",
    "looking for",
    "suggest",
    "recommend",
    "show me",
    "available",
    "stock",
    "best",

    # Occasion
    "gift",
    "birthday",
    "wedding",
    "wife",
    "husband",

    # Price
    "budget",
    "price",
    "cost",
    "cheap",
    "under",
    "below",
    "taka",
    "tk",
    "৳",
    "ml",

    # Brands
    "lattafa",
    "armaf",
    "rasasi",
    "dior",
    "chanel",
    "versace",
    "gucci",
    "tom ford",
    "tomford",
    "khamrah",
    "hawas",
    "yara",
    "asad",
    "fakhar",
    "afnan",
    "al haramain",

    # Combo
    "combo",
    "set",
    "pack",
    "gift set",

    # Bangla
    "পারফিউম",
    "সুগন্ধি",
    "আতর",
    "দাম",
    "কত",
    "কিনবো",
    "লাগবে",
    "চাই",

    # Banglish
    "perfume lagbe",
    "perfume chai",
    "sugondhi",
    "attar lagbe",
    "dam",
    "koto",
    "chele",
    "meye",
}


def normalize(text: str) -> str:
    text = text.lower().strip()

    text = re.sub(
        r"[^\w\s\u0980-\u09FF]",
        "",
        text
    )

    text = re.sub(r"\s+", " ", text)

    return text


def matches_phrase(message: str, phrases: set[str]) -> bool:
    """
    Match complete phrases only.
    Prevents false positives.
    """
    return any(
        message == phrase or message.startswith(phrase + " ")
        for phrase in phrases
    )


def contains_keyword(message: str, keywords: set[str]) -> bool:
    """
    Check if any keyword exists.
    """
    return any(
        keyword in message
        for keyword in keywords
    )


def detect_intent(message: str, debug: bool = False) -> Intent:
    message = normalize(message)

    result = Intent.UNKNOWN

    # Product has highest priority
    if contains_keyword(message, PRODUCT_KEYWORDS):
        result = Intent.PRODUCT_SEARCH

    elif matches_phrase(message, THANKS):
        result = Intent.THANKS

    elif matches_phrase(message, GOODBYES):
        result = Intent.GOODBYE

    elif matches_phrase(message, GREETINGS):
        result = Intent.GREETING

    if debug:
        print(f"Input: {message}")
        print(f"Detected: {result}")

    return result