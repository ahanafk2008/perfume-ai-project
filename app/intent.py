"""
Intent detection for Perfume AI Assistant.
"""

from __future__ import annotations

from .normalize import normalize
from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    THANKS = "thanks"
    GOODBYE = "goodbye"
    CASUAL = "casual"
    PRODUCT_SEARCH = "product_search"
    UNKNOWN = "unknown"

CASUAL = {
    "nice",
    "perfect",
    "great",
    "awesome",
    "cool",
    "ok",
    "okay",
    "good",
    "excellent",
}

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
    # English
    "thanks",
    "thank you",
    "thankyou",
    "thank u",
    "thanks a lot",
    "thank you so much",
    "many thanks",
    "great thanks",
    "thanks so much",
    "thanks buddy",
    "thanks bro",
    "thanks brother",
    "thanks man",
    "thanks sir",
    "thanks dear",
    "thanks again",
    "appreciate it",
    "much appreciated",
    "thx",
    "ty",
    "tysm",

    # Islamic
    "jazakallah",
    "jazak allah",
    "jazakallah khair",
    "jazakallahu khair",
    "jazakallah khairan",

    # Bangla
    "ধন্যবাদ",
    "অনেক ধন্যবাদ",
    "অনেক অনেক ধন্যবাদ",
    "আপনাকে ধন্যবাদ",
    "ধন্যবাদ ভাই",
    "ধন্যবাদ আপনাকে",
    "অসংখ্য ধন্যবাদ",
    "অনেক অনেক ধন্যবাদ ভাই",

    # Banglish
    "dhonnobad",
    "onek dhonnobad",
    "apnake dhonnobad",
    "dhonnobad bhai",
    "onek onek dhonnobad",
    "osonkho dhonnobad",
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
    "talk later",
    "i will come later",
    "that's all",
    "thats all",
    "no more",
    "done",

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
    "male",
    "women",
    "female",
    "unisex",

    # Buying
    "buy",
    "buying",
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
    "attar lagbe",
    "sugondhi chai",
    "nibo ekta",
    "perfume nibo",
}



def matches_phrase(message: str, phrases: set[str]) -> bool:
    """
    Match exact phrases only.
    Prevent false positives.
    """
    return message in phrases

def starts_with_phrase(message: str, phrases: set[str]) -> bool:
    """
    Allow a phrase to match exactly or at the beginning of a message.
    Example:
        hi
        hi brother
        thanks
        thanks a lot
    """
    return any(
        message == phrase or message.startswith(phrase + " ")
        for phrase in phrases
    )



def contains_keyword(message: str, keywords: set[str]) -> bool:
    words = set(message.split())

    for keyword in keywords:
        # Handle multi-word keywords
        if " " in keyword:
            if keyword in message:
                return True

        # Handle single words
        elif keyword in words:
            return True

    return False


def detect_intent(message: str, debug: bool = False) -> Intent:
    message = normalize(message)

    result = Intent.UNKNOWN

    # Exact goodbye/thanks/greeting first
    if (
    matches_phrase(message, THANKS)
    or starts_with_phrase(message, THANKS)
):
        result = Intent.THANKS

    elif matches_phrase(message, GOODBYES):
        result = Intent.GOODBYE

    elif matches_phrase(message, GREETINGS) or starts_with_phrase(message, GREETINGS):
        result = Intent.GREETING

    elif matches_phrase(message, CASUAL):
        result = Intent.CASUAL

    elif contains_keyword(message, PRODUCT_KEYWORDS):
        result = Intent.PRODUCT_SEARCH
    
    if debug:
        print(f"Input: {message}")
        print(f"Detected: {result}")

    return result