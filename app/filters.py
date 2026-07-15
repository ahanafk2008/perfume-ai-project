"""Query normalization and intent detection helpers."""

import re
from collections.abc import Iterable


# Bangla, Banglish, and English normalization.
NORMALIZATION: dict[str, str] = {

    # Female relationships / gift intent
    "wife": "female",
    "wives": "female",
    "girlfriend": "female",
    "gf": "female",
    "mother": "female",
    "mom": "female",

    # Male relationships / gift intent
    "husband": "male",
    "boyfriend": "male",
    "bf": "male",
    "father": "male",
    "dad": "male",
    "brother": "male",
    # Female
    "fiancee": "female",
    "fiancée": "female",
    "mum": "female",
    "sister": "female",
    "daughter": "female",
    "female": "female",
    "women": "female",
    "woman": "female",
    "lady": "female",
    "ladies": "female",
    "girl": "female",
    "girls": "female",
    "meye": "female",
    "meyeder": "female",
    "মেয়ে": "female",
    "মেয়েদের": "female",
    "মহিলা": "female",
    "নারী": "female",

    # Male
    "fiance": "male",
    "fiancé": "male",
    "son": "male",
    "male": "male",
    "men": "male",
    "man": "male",
    "gents": "male",
    "gent": "male",
    "boy": "male",
    "boys": "male",
    "chele": "male",
    "ছেলে": "male",
    "পুরুষ": "male",

    # Unisex
    "unisex": "unisex",

    # Perfume
    "perfume": "",
    "parfum": "",
    "fragrance": "",
    "পারফিউম": "",
}


STOP_WORDS: set[str] = {
    "under",
    "below",
    "within",
    "budget",
    "taka",
    "tk",
    "price",
    "show",
    "need",
    "want",
    "please",
    "er",
    "moddhe",
    "jonno",
    "ase",
    "lagbe",
    "chai",
    "টাকার",
    "টাকা",
    "মধ্যে",
    "জন্য",
    "দেখান",
    "চাই",
    "আছে",
}


BUDGET_KEYWORDS: set[str] = {
    "under",
    "below",
    "within",
    "budget",
    "taka",
    "tk",
    "টাকার",
    "টাকা",
    "মধ্যে",
}


TYPO_CORRECTIONS: dict[str, str] = {
    "savaj": "sauvage",
    "savage": "sauvage",
    "latafa": "lattafa",
    "devidoff": "davidoff",
}


KNOWN_BRANDS: set[str] = {
    "ajmal",
    "armaf",
    "davidoff",
    "dior",
    "lattafa",
    "rasasi",
}


KNOWN_CATEGORIES: set[str] = {
    "body",
    "combo",
    "deodorant",
    "edp",
    "edt",
    "mist",
    "perfume",
    "spray",
}


COMBO_WORDS: set[str] = {
    "combo",
    "combos",
    "set",
    "pack",
    "bundle",
    "কম্বো",
    "সেট",
}


def correct_common_typos(word: str) -> str:
    """Correct a single common perfume-related typo."""

    cleaned = word.lower().strip()
    return TYPO_CORRECTIONS.get(cleaned, cleaned)


def normalize_words(words: list[str]) -> list[str]:
    """Normalize words by removing stop words and mapping known synonyms."""

    normalized: list[str] = []

    for word in words:
        word = correct_common_typos(word)

        if word in STOP_WORDS:
            continue

        if word in NORMALIZATION:
            mapped = NORMALIZATION[word]
            if mapped:
                normalized.append(mapped)
        else:
            normalized.append(word)

    return normalized


def tokenize_query(query: str) -> list[str]:
    """Return normalized search tokens from a raw user query."""

    clean_query = re.sub(r"\d+", "", query.lower())
    clean_query = (
        clean_query
        .replace("৳", "")
        .replace("tk", "")
        .replace("taka", "")
    )

    return normalize_words(clean_query.split())


def extract_budget(query: str) -> int | None:
    """Extract a budget from English, Bangla, or Banglish query text."""

    lower = query.lower()

    match = re.search(r"৳\s*(\d+)", query)
    if match:
        return int(match.group(1))

    for keyword in BUDGET_KEYWORDS:
        pattern = rf"\b{re.escape(keyword)}\s+(\d+)"
        match = re.search(pattern, lower)
        if match:
            return int(match.group(1))

    match = re.search(r"(\d+)\s*(?:taka|tk|টাকা|টাকার)\b", lower)
    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s+টাকার\s+মধ্যে", lower)
    if match:
        return int(match.group(1))

    return None


def detect_gender(query: str) -> str | None:
    """Detect requested gender from normalized query."""

    tokens = tokenize_query(query)

    for token in tokens:
        if token in {
            "male",
            "female",
            "unisex",
        }:
            return token

    return None


def detect_brand(
    query: str,
    known_brands: Iterable[str] | None = None,
) -> str | None:
    """Detect a brand name from the query using known brand tokens."""

    brands = {brand.lower() for brand in (known_brands or KNOWN_BRANDS)}
    tokens = tokenize_query(query)

    for token in tokens:
        if token in brands:
            return token

    return None


def detect_category(query: str) -> str | None:
    """Detect a product category-like token from the query, if present."""

    tokens = tokenize_query(query)

    for token in tokens:
        if token in KNOWN_CATEGORIES:
            return token

    return None


def detect_combo(query: str) -> bool:
    """Return True when the query explicitly asks for a combo or set."""

    raw_tokens = {correct_common_typos(word) for word in query.lower().split()}
    normalized_tokens = set(tokenize_query(query))
    return bool((raw_tokens | normalized_tokens) & COMBO_WORDS)
