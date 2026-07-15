"""Lightweight customer language detection."""

import logging
import re
from typing import Literal


logger = logging.getLogger(__name__)

LanguageCode = Literal["en", "bn", "bn-en"]

BANGLA_UNICODE_START = "\u0980"
BANGLA_UNICODE_END = "\u09ff"

BANGLISH_WORDS: set[str] = {
    "ache",
    "ase",
    "bhalo",
    "chai",
    "chele",
    "cheleder",
    "dam",
    "er",
    "jonno",
    "koto",
    "lagbe",
    "moddhe",
    "meye",
    "meyeder",
    "nai",
    "taka",
    "takar",
}

ENGLISH_WORDS: set[str] = {
    "below",
    "budget",
    "for",
    "fragrance",
    "men",
    "mens",
    "perfume",
    "please",
    "recommend",
    "show",
    "under",
    "women",
    "womens",
}


def is_bangla(text: str) -> bool:
    """Return True when text contains Bangla script characters."""

    return any(BANGLA_UNICODE_START <= char <= BANGLA_UNICODE_END for char in text)


def _latin_tokens(text: str) -> list[str]:
    """Return lowercase Latin word tokens from text."""

    return re.findall(r"[a-z]+", text.lower())


def is_banglish(text: str) -> bool:
    """Return True when text looks like Romanized Bangla."""

    if is_bangla(text):
        return False

    tokens = set(_latin_tokens(text))
    return bool(tokens & BANGLISH_WORDS)


def is_english(text: str) -> bool:
    """Return True when text looks like English rather than Bangla/Banglish."""

    if is_bangla(text) or is_banglish(text):
        return False

    tokens = set(_latin_tokens(text))
    if not tokens:
        return True

    return bool(tokens & ENGLISH_WORDS) or all(token.isascii() for token in tokens)


def detect_language(text: str) -> LanguageCode:
    """Detect customer language and return en, bn, or bn-en."""

    if is_bangla(text):
        language: LanguageCode = "bn"
    elif is_banglish(text):
        language = "bn-en"
    else:
        language = "en"

    logger.debug("Detected language=%s for text=%r", language, text)
    return language
