"""Query normalization and intent detection helpers."""

import re
from collections.abc import Iterable

from .normalize import normalize

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

    # Search intent normalization
    "cheapest": "cheap",
    "lowest": "cheap",
    "low": "cheap",

    "highest": "expensive",
    "luxury": "premium",

    "longlasting": "long lasting",
    "long-lasting": "long lasting",
}

STOP_WORDS: set[str] = {
    # English
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
    "list",
    "all",
    "give",
    "available",
    "have",

    # Banglish
    "ki",
    "ase",
    "ache",
    "apnader",
    "tomader",
    "amader",
    "amar",
    "amake",
    "lagbe",
    "chai",
    "jonno",
    "moddhe",
    "dekhan",
    "ekta",
    "ekti",

    # Bangla
    "কি",
    "আছে",
    "আসে",
    "আমাদের",
    "আপনাদের",
    "চাই",
    "জন্য",
    "মধ্যে",
    "দেখান",

    # Generic perfume words
    "perfume",
    "perfumes",
    "fragrance",
    "parfum",
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
    # Lattafa
    "latafa": "lattafa",
    "lattaf": "lattafa",
    "lattafah": "lattafa",
    "lataf": "lattafa", 

    # Khamrah
    "khamra": "khamrah",
    "khamrahh": "khamrah",
    "khamrahhh": "khamrah",

    # Sauvage
    "savage": "sauvage",
    "savaj": "sauvage",
    "savagee": "sauvage",
    "savaz": "sauvage",
    "sovage": "sauvage",
    "suavage": "sauvage",

    # Davidoff
    "devidoff": "davidoff",
    "davidof": "davidoff",
    "davidofff": "davidoff",

    # Tom Ford
    "tomford": "tom ford",
    "tom-ford": "tom ford",
    "tomfordd": "tom ford",

    # Armani
    "armanii": "armani",
    "arman": "armani",

    # Dior
    "diorr": "dior",
    "dioro": "dior",

    # Rasasi
    "rasaasi": "rasasi",
    "rasassi": "rasasi",

    # Hawas
    "hawaz": "hawas",
    "hawass": "hawas",

    # Yara
    "yarra": "yara",
    "yaara": "yara",

    # Asad
    "asaad": "asad",

    # Fakhar
    "fakar": "fakhar",
    "fakkhar": "fakhar",

    # Good Girl
    "goodgirl": "good girl",

    # Carolina Herrera
    "carolina": "carolina herrera",
    "herreraa": "herrera",

    # Burberry
    "burbery": "burberry",
    "burbary": "burberry",

    # Gucci
    "guci": "gucci",

    # Prada
    "pradda": "prada",

    # Versace
    "versachi": "versace",
    "versacce": "versace",

    # Chanel
    "channel": "chanel",

    # Paco Rabanne
    "rabane": "rabanne",

    # Mancera
    "mansera": "mancera",

    # Armaf
    "armaaf": "armaf",
    "armf": "armaf",

    # Afnan
    "affnan": "afnan",

    # General Terms
    "parfume": "perfume",
    "fragnance": "fragrance",
}


KNOWN_BRANDS: set[str] = {
    # Middle Eastern
    "lattafa",
    "rasasi",
    "armaf",
    "afnan",
    "ajmal",
    "al haramain",
    "maison alhambra",
    "fragrance world",
    "pendora scents",
    "ard al zaafaran",

    # Designer
    "dior",
    "tom ford",
    "gucci",
    "prada",
    "versace",
    "armani",
    "giorgio armani",
    "burberry",
    "carolina herrera",
    "chanel",
    "ysl",
    "yves saint laurent",
    "dolce & gabbana",
    "dolce and gabbana",
    "bvlgari",
    "bulgari",
    "paco rabanne",
    "rabanne",
    "hugo boss",
    "boss",
    "calvin klein",
    "ck",
    "givenchy",
    "valentino",
    "lacoste",
    "montblanc",
    "issey miyake",
    "hermes",
    "jo malone",
    "mugler",
    "narciso rodriguez",
    "moschino",

    # Niche
    "mancera",
    "montale",
    "xerjoff",
    "parfums de marly",
    "creed",
    "initio",
    "amouage",
    "roja",
    "byredo",
    "le labo",
    "diptyque",
    "kilian",
}


KNOWN_CATEGORIES: set[str] = {
    # Fragrance types
    "perfume",
    "fragrance",
    "attar",
    "oud",
    "edp",
    "edt",
    "edc",
    "parfum",
    "extrait",

    # Product types
    "spray",
    "mist",
    "body mist",
    "body spray",
    "deodorant",
    "roll on",
    "roll-on",

    # Store categories
    "combo",
    "discovery",
    "gift",
    "gift set",

    # Audience
    "men",
    "women",
    "unisex",
    "male",
    "female",
}

COMBO_WORDS: set[str] = {
    # English
    "combo",
    "combos",
    "set",
    "gift set",
    "giftset",
    "pack",
    "bundle",
    "kit",
    "collection",
    "duo",
    "pair",

    # Banglish
    "combo lagbe",
    "set lagbe",
    "gift set",
    "giftset",

    # Bangla
    "কম্বো",
    "সেট",
    "গিফট সেট",
    "প্যাক",
    "বান্ডেল",
}

def correct_common_typos(word: str) -> str:
    """Correct a single common perfume-related typo."""

    cleaned = word.lower().strip()
    return TYPO_CORRECTIONS.get(cleaned, cleaned)


def normalize_words(words: list[str]) -> list[str]:
    """Normalize words, remove stop words, fix typos, and remove duplicates."""

    normalized: list[str] = []
    seen: set[str] = set()

    for word in words:
        word = correct_common_typos(word).strip().lower()

        if not word:
            continue

        # Remove conversational words
        if word in STOP_WORDS:
            continue

        # Normalize synonyms
        word = NORMALIZATION.get(word, word)

        if not word:
            continue

        # Remove duplicates while preserving order
        if word in seen:
            continue

        seen.add(word)
        normalized.append(word)

    return normalized


def tokenize_query(query: str) -> list[str]:
    """Return normalized search tokens from a raw user query."""

    clean_query = normalize(query)

    clean_query = re.sub(r"\d+", "", clean_query)

    clean_query = (
        clean_query
        .replace("৳", "")
        .replace("tk", "")
        .replace("taka", "")
    )

    tokens = normalize_words(clean_query.split())

    return tokens


def extract_budget(query: str) -> int | None:
    """Extract a budget from English, Bangla, or Banglish query text."""

    lower = normalize(query)

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
    clean_query_str = " ".join(tokens)

    # 1. Sort brands by length descending to match longest phrases first
    sorted_brands = sorted(brands, key=len, reverse=True)

    # 2. Search the normalized full query string for phrases
    padded_query = f" {clean_query_str} "
    for brand in sorted_brands:
        if f" {brand} " in padded_query:
            return brand

    # 3. Fallback to token-based matching
    for token in tokens:
        if token in brands:
            return token

    return None


def detect_category(query: str) -> str | None:
    """Detect a product category-like token from the query, if present."""

    tokens = tokenize_query(query)
    clean_query_str = " ".join(tokens)

    # 1. Sort categories by length descending to match longest phrases first
    sorted_categories = sorted(KNOWN_CATEGORIES, key=len, reverse=True)

    # 2. Search the normalized full query string for phrases
    padded_query = f" {clean_query_str} "
    for category in sorted_categories:
        if f" {category} " in padded_query:
            return category

    # 3. Fallback to token-based matching
    for token in tokens:
        if token in KNOWN_CATEGORIES:
            return token

    return None


def detect_combo(query: str) -> bool:
    """Return True when the query explicitly asks for a combo or set."""

    raw_tokens = {
        correct_common_typos(word)
        for word in normalize(query).split()
    }

    normalized_tokens = set(tokenize_query(query))
    return bool((raw_tokens | normalized_tokens) & COMBO_WORDS)

def detect_sort(query: str) -> str | None:
    q = normalize(query)

    if any(word in q for word in (
        "cheap",
        "cheapest",
        "lowest",
        "low price",
    )):
        return "cheap"

    if any(word in q for word in (
        "expensive",
        "highest",
        "premium",
        "luxury",
    )):
        return "expensive"

    return None
