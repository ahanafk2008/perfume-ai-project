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
    "good morning",
    "good afternoon",
    "good evening",
    "good night",
    "yo",
    "sup",
    "what's up",

    # Bangla
    "হাই",
    "হ্যালো",
    "সালাম",
    "আসসালামু আলাইকুম",

    # Banglish
    "salam",
    "assalamu alaikum",
    "assalamualaikum",
    "assalamu alikum",
    "assalam",
    "vai",
    "bhai",
    "apu",
    "bro",
}


THANKS = {
    "thanks",
    "thank you",
    "thankyou",
    "thank u",
    "thx",
    "ty",
    "ধন্যবাদ",
    "অনেক ধন্যবাদ",
}


GOODBYES = {
    "bye",
    "goodbye",
    "see you",
    "see ya",
    "take care",
    "allah hafez",
    "khoda hafez",
    "বিদায়",
    "আল্লাহ হাফেজ",
}


PRODUCT_KEYWORDS = {
    "perfume",
    "fragrance",
    "attar",
    "oud",
    "vanilla",
    "rose",
    "fresh",
    "sweet",
    "men",
    "man",
    "male",
    "women",
    "woman",
    "female",
    "girl",
    "boy",
    "gift",
    "wife",
    "husband",
    "budget",
    "price",
    "under",
    "ml",
    "combo",
    "lattafa",
    "armaf",
    "rasasi",
    "dior",
    "tom ford",
    "tomford",
    "khamrah",
    "hawas",
    "yara",
    "asad",
    "fakhar",

    # Bangla
    "পারফিউম",
    "সুগন্ধি",
    "দাম",
    "গিফট",

    # Banglish
    "perfume lagbe",
    "price",
    "taka",
}


def normalize(text: str) -> str:
    """
    Normalize user input.
    """
    text = text.lower().strip()

    # Remove punctuation but keep Bengali characters
    text = re.sub(r"[^\w\s\u0980-\u09FF]", "", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text


def detect_intent(message: str) -> Intent:
    """
    Detect the user's intent.
    """

    message = normalize(message)

    # Greeting
    if any(message.startswith(greeting) for greeting in GREETINGS):
        return Intent.GREETING

    # Thanks
    if any(word in message for word in THANKS):
        return Intent.THANKS

    # Goodbye
    if any(message.startswith(word) for word in GOODBYES):
        return Intent.GOODBYE

    # Product search
    if any(keyword in message for keyword in PRODUCT_KEYWORDS):
        return Intent.PRODUCT_SEARCH

    return Intent.UNKNOWN