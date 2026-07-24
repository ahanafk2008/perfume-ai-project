"""Query normalization and intent detection helpers."""

import re
from collections.abc import Iterable
from typing import Any

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
    "cheleder": "male",
    "ছেলে": "male",
    "ছেলেদের": "male",
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

    # Non-search conversational words
    "best",
    "good",
    "great",
    "nice",
    "recommend",
    "suggest",
    "find",
    "looking",
    "get",
    "buy",
    "gift",
    "for",
    "me",
    "my",
    "some",
    "any",
    "the",
    "a",
    "an",
    "is",
    "are",
    "can",
    "you",
    "i",
    "do",
    "what",

    # Budget-related (extracted separately)
    "less",
    "than",
    "max",
    "maximum",
    "upto",
    "up",

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

    # Connectors / fillers
    "but",
    "very",
    "just",
    "also",
    "too",

    # Price intent words (detected separately from raw query)
    "cheap",
    "cheapest",
    "affordable",
    "value",
    "economy",
    "sasto",
    "sasta",
    "komdami",

    # Bangla stop words
    "করে",
    "করা",
    "হবে",
    "কোন",
    "কোনো",
    "একটি",
    "একটা",
    "এই",
    "ওই",
    "সেই",
    "সেটা",
    "এটা",
    "ওটা",
    "কে",
    "কিভাবে",
    "কেন",
    "বলে",
    "দিয়ে",
    "থেকে",
    "কাছে",
    "বিষয়ে",
    "আমি",
    "আপনি",
    "তুমি",
    "সে",
    "আমার",
    "আপনার",
    "তার",
    "তোমার",
}


BUDGET_KEYWORDS: set[str] = {
    "under",
    "below",
    "within",
    "budget",
    "max",
    "maximum",
    "upto",
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

    # Note: gender words (men, women, male, female, unisex) are
    # intentionally NOT here. Gender is handled by detect_gender().
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

    # "k" / "K" shorthand: 2k = 2000, 2.5k = 2500
    # Check the RAW query (before normalize()) because normalize() strips
    # the decimal point from "2.5k" turning it into "25k" -> 25000.
    # This must be the FIRST check so "up to 1.5k", "under 2.5k" don't
    # get captured by multi-word patterns as digits-only values.
    match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", query, re.IGNORECASE)
    if match:
        return int(float(match.group(1)) * 1000)

    # ৳ symbol before or after number (raw query, since normalize keeps ৳)
    match = re.search(r"[\u09f3]\s*(\d+)", query)
    if match:
        return int(match.group(1))

    # Multi-word budget phrases (check raw query for ৳ between keyword and number)
    multi_word_patterns = [
        r"less\s+than\s+[\u09f3]?\s*(\d+)",
        r"up\s+to\s+[\u09f3]?\s*(\d+)",
        r"cheaper\s+than\s+[\u09f3]?\s*(\d+)",
        r"cheap\s+than\s+[\u09f3]?\s*(\d+)",
        r"exactly\s+[\u09f3]?\s*(\d+)",
        r"around\s+[\u09f3]?\s*(\d+)",
        r"at\s+least\s+[\u09f3]?\s*(\d+)",
    ]
    for pattern in multi_word_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return int(match.group(1))
    for pattern in multi_word_patterns:
        match = re.search(pattern, lower)
        if match:
            return int(match.group(1))

    # Bangla "হাজার" (hazar = thousand): "২ হাজার" = 2000
    match = re.search(r"(\d+)\s*হাজার", lower)
    if match:
        return int(match.group(1)) * 1000

    for keyword in BUDGET_KEYWORDS:
        pattern = rf"\b{re.escape(keyword)}\s+[\u09f3]?\s*(\d+)"
        match = re.search(pattern, lower)
        if match:
            return int(match.group(1))

    match = re.search(r"(\d+)\s*(?:taka|tk|টাকা|টাকার)\b", lower)
    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s+টাকার\s+মধ্যে", lower)
    if match:
        return int(match.group(1))

    # "cheaper than X" / "cheap under X"
    match = re.search(r"(?:cheaper|cheap)\s+(?:than\s+)?(\d+)", lower)
    if match:
        return int(match.group(1))

    # "my budget is X" / "budget is X"
    match = re.search(r"(?:my\s+)?budget\s+is\s+(\d+)", lower)
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


def detect_occasion(query: str) -> str | None:
    """Detect occasion keywords from query.

    Maps abstract occasions like university, gym, interview, etc.
    to structured tags. Never returns None if close matches exist.
    """
    occasion_keywords = {
    "office": "office",
    "work": "office",
    "professional": "office",
    "formal": "office",
    "corporate": "office",
    "office wear": "office",
    "কাজ": "office",
    "অফিস": "office",
    "অফিসে": "office",
    "অফিসের জন্য": "office",
    "অফিসে ব্যবহার": "office",
    "অফিস যাওয়ার": "office",

        "date": "date",
        "dating": "date",
        "romantic": "date",
        "dinner": "date",
        "night out": "date",

        "party": "party",
        "club": "party",
        "nightclub": "party",
        "event": "party",

        "wedding": "wedding",
        "marriage": "wedding",
        "reception": "wedding",
        "function": "wedding",
        "biye": "wedding",
        "biyer": "wedding",
        "biya": "wedding",
        "বিয়ে": "wedding",
        "wedding guest": "wedding",
        "shaadi": "wedding",

        "casual": "casual",
        "everyday": "daily",
        "daily": "daily",
        "daily use": "daily",
        "everyday wear": "daily",
        "regular": "daily",
        "daily wear": "daily",
        "din din": "daily",

        "university": "daily",
        "college": "daily",
        "class": "daily",
        "student": "daily",
        "school": "daily",
        "বিশ্ববিদ্যালয়": "daily",
        "কলেজ": "daily",

        "gym": "sport",
        "workout": "sport",
        "fitness": "sport",
        "exercise": "sport",
        "sport": "sport",
        "sports": "sport",
        "জিম": "sport",
        "ব্যায়াম": "sport",

        "interview": "office",
        "job interview": "office",
        "চাকরির ইন্টারভিউ": "office",
        "ইন্টারভিউ": "office",

        "vacation": "casual",
        "holiday": "casual",
        "trip": "casual",
        "travel": "casual",
        "tour": "casual",
        "traveling": "casual",
        "ছুটি": "casual",
        "ভ্রমণ": "casual",
        "বেড়াতে": "casual",
        "tour e": "casual",

        "eid": "eid",
        "ঈদ": "eid",
    }

    q = normalize(query)
    for keyword, occasion in occasion_keywords.items():
        if keyword in q:
            return occasion
    return None


def detect_scent(query: str) -> str | None:
    """Detect scent preference keywords from query."""
    scent_keywords = {
    "sweet": "sweet",
    "sugary": "sweet",
    "candy": "sweet",
    "dessert": "sweet",
    "মিষ্টি": "sweet",

    "fresh": "fresh",
    "clean": "fresh",
    "aqua": "fresh",
    "aquatic": "fresh",
    "marine": "fresh",
    "ocean": "fresh",
    "ফ্রেশ": "fresh",
    "তাজা": "fresh",

    "woody": "woody",
    "wood": "woody",
    "forest": "woody",
    "earthy": "woody",

    "oud": "oud",
    "oudh": "oud",
    "agar": "oud",

    "spicy": "spicy",
    "pepper": "spicy",
    "ginger": "spicy",
    "hot": "spicy",

    "vanilla": "vanilla",
    "ভ্যানিলা": "vanilla",

    "floral": "floral",
    "flower": "floral",
    "flowers": "floral",
    "rose": "floral",
    "jasmine": "floral",
    "jasmin": "floral",
    "lavender": "floral",
    "peony": "floral",
    "tuberose": "floral",
}

    q = normalize(query)
    for keyword, scent in scent_keywords.items():
        if keyword in q:
            return scent
    return None


def detect_performance(query: str) -> str | None:
    """Detect performance/longevity keywords from query."""
    performance_keywords = {
        "long lasting": "longlasting",
        "long-lasting": "longlasting",
        "longlasting": "longlasting",
        "lasting": "longlasting",
        "stays long": "longlasting",
        "stay long": "longlasting",
        "lasts long": "longlasting",
        "long time": "longlasting",
        "hours": "longlasting",
        "বেশিক্ষণ": "longlasting",
        "বেশিক্ষণ থাকে": "longlasting",
        "সারাদিন": "longlasting",
        "সারাদিন থাকে": "longlasting",
        "ঘন্টার পর ঘন্টা": "longlasting",

        "strong": "strong",
        "powerful": "strong",
        "intense": "strong",
        "beast mode": "strong",
        "beast": "strong",

        "projection": "projection",
        "throw": "projection",
        "sillage": "projection",
        "spreads": "projection",
        "fill room": "projection",
        "প্রজেকশন": "projection",

        "compliment": "compliment",
        "compliments": "compliment",
        "gets compliments": "compliment",
        "attract": "compliment",
        "attention": "compliment",
    }

    q = normalize(query)
    for keyword, perf in performance_keywords.items():
        if keyword in q:
            return perf
    return None


def detect_similarity(query: str) -> str | None:
    """Detect similarity/reference product from query."""
    # Patterns like "similar to X", "like X", "alternative to X"
    patterns = [
        r"similar\s+to\s+([a-z0-9\s]+?)(?:\s+and|\s+perfume|\s+fragrance|$)",
        r"like\s+([a-z0-9\s]+?)(?:\s+and|\s+perfume|\s+fragrance|$)",
        r"alternative\s+to\s+([a-z0-9\s]+?)(?:\s+and|\s+perfume|\s+fragrance|$)",
        r"comparable\s+to\s+([a-z0-9\s]+?)(?:\s+and|\s+perfume|\s+fragrance|$)",
        r"inspired\s+by\s+([a-z0-9\s]+?)(?:\s+and|\s+perfume|\s+fragrance|$)",
    ]

    q = normalize(query)
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            reference = match.group(1).strip()
            if reference:
                return reference
    return None


RECOMMENDATION_WORDS: set[str] = {
    "best",
    "recommend",
    "recommended",
    "suggest",
    "suggestion",
    "top",
    "top rated",
    "popular",
    "favorite",
    "most popular",
    "highest",
}


def detect_recommendation(query: str) -> bool:
    """Detect whether the query is asking for a recommendation or top products."""
    q = normalize(query)
    for word in RECOMMENDATION_WORDS:
        if word in q:
            return True
    return False


LUXURY_WORDS: set[str] = {
    "luxury",
    "luxurious",
    "premium",
    "designer",
    "high end",
    "high-end",
    "expensive",
    "signature",
    "exclusive",
    "elite",
    "classy",
    "sophisticated",
    "high quality",
}


def detect_luxury(query: str) -> bool:
    """Detect whether the query asks for luxury, designer, or premium products."""
    q = normalize(query)
    for word in LUXURY_WORDS:
        if word in q:
            return True
    return False


GIFT_WORDS: set[str] = {
    "gift",
    "gifts",
    "present",
    "presents",
    "valentine",
    "anniversary",
    "birthday",
    "gift for",
    "for wife",
    "for husband",
    "for her",
    "for him",
    "for mom",
    "for dad",
    "for mother",
    "for father",
    "for sister",
    "for brother",
    "for girlfriend",
    "for boyfriend",
    "উপহার",
    "স surprise",
    "সারপ্রাইজ",
    "সরপ্রাইজ",
    "shurprise",
    "surprise",
    "eid",
    "eid gift",
    "ঈদ",
    "ঈদের উপহার",
    "বিয়ের উপহার",
    "biyer upohar",
}


def detect_gift(query: str) -> bool:
    """Detect whether the query is asking for a gift.

    Checks the raw query (for relational words like 'wife', 'husband' that
    trigger gift intent even without explicit 'gift' or 'present' words)
    and the normalized query (for standard gift words).
    """
    q_norm = normalize(query)
    q_raw = query.lower().strip()

    for word in GIFT_WORDS:
        if word in q_norm or word in q_raw:
            return True

    # "for X" or "to X" where X is a relational word → gift intent
    relational = {"wife", "husband", "her", "him", "girlfriend", "boyfriend", "mom", "dad",
                  "mother", "father", "sister", "brother", "fiance", "fiancee"}
    raw_tokens = q_raw.split()
    for t in raw_tokens:
        if t in relational:
            return True

    return False


VAGUE_BUDGET_PHRASES: set[str] = {
    "budget kom",
    "budget beshi na",
    "kom budget",
    "low budget",
    "sasto",
    "sasta",
    "kom dam",
    "komdami",
    "budget e",
    "bekar",
}


def detect_vague_budget(query: str) -> bool:
    """Detect vague budget intent like 'budget kom', 'sasto', etc."""
    q = query.lower().strip()
    for phrase in VAGUE_BUDGET_PHRASES:
        if phrase in q:
            return True
    return False


def detect_cheap_intent(query: str) -> bool:
    """Detect cheap/budget/affordable intent without a specific price."""
    q = normalize(query)
    cheap_words = {"cheap", "cheapest", "affordable", "budget", "value", "economy", "reasonable", "discount"}
    return any(w in q for w in cheap_words)


COMPLIMENT_WORDS: set[str] = {
    "compliment",
    "compliments",
    "gets compliments",
    "attract",
    "attention",
    "get compliments",
    "compliment getter",
    "people notice",
    "turn heads",
}


def detect_compliment(query: str) -> bool:
    """Detect whether the query asks for compliment-getting perfumes."""
    q = normalize(query)
    for word in COMPLIMENT_WORDS:
        if word in q:
            return True
    return False


SEASON_WORDS: dict[str, str] = {
    "summer": "summer",
    "hot": "summer",
    "heat": "summer",
    "sunny": "summer",
    "warm": "summer",
    "spring": "summer",
    "winter": "winter",
    "cold": "winter",
    "cool": "winter",
    "chilly": "winter",
    "fall": "winter",
    "autumn": "winter",
    "rainy": "summer",
    "monsoon": "summer",
    "গ্রীষ্ম": "summer",
    "গরম": "summer",
    "গরম কাল": "summer",
    "শীত": "winter",
    "ঠান্ডা": "winter",
    "শীত কাল": "winter",
    "বর্ষা": "winter",
    "গরমে": "summer",
    "শীতে": "winter",
}


def detect_season(query: str) -> str | None:
    """Detect season preference from query."""
    q = normalize(query)
    for keyword, season in SEASON_WORDS.items():
        if keyword in q:
            return season
    return None


# =============================================================================
# Nuanced Request Mapping
# Maps abstract/ nuanced requests to weighted attribute preferences.
# =============================================================================

class NuancedRequest:
    """Represents a parsed nuanced request with weighted preferences."""

    def __init__(
        self,
        *,
        sweetness: float = 0.0,
        freshness: float = 0.0,
        masculinity: float = 0.0,
        elegance: float = 0.0,
        luxury_level: float = 0.0,
        versatility: float = 0.0,
        compliment_factor: float = 0.0,
        mass_appeal: float = 0.0,
        citrus: float = 0.0,
        gourmand: float = 0.0,
        aquatic: float = 0.0,
        woody: float = 0.0,
        floral: float = 0.0,
        spicy: float = 0.0,
        price_perception: str | None = None,
    ):
        self.sweetness = sweetness
        self.freshness = freshness
        self.masculinity = masculinity
        self.elegance = elegance
        self.luxury_level = luxury_level
        self.versatility = versatility
        self.compliment_factor = compliment_factor
        self.mass_appeal = mass_appeal
        self.citrus = citrus
        self.gourmand = gourmand
        self.aquatic = aquatic
        self.woody = woody
        self.floral = floral
        self.spicy = spicy
        self.price_perception = price_perception

    def is_empty(self) -> bool:
        return all(
            getattr(self, attr) == 0.0 or getattr(self, attr) is None
            for attr in [
                "sweetness", "freshness", "masculinity", "elegance",
                "luxury_level", "versatility", "compliment_factor", "mass_appeal",
                "citrus", "gourmand", "aquatic", "woody", "floral", "spicy",
                "price_perception",
            ]
        )

    def to_prompt_hint(self) -> str:
        hints = []
        if self.sweetness > 0.5:
            hints.append("sweet")
        elif self.sweetness > 0 and self.sweetness <= 0.5:
            hints.append("lightly sweet (not cloying)")
        if self.freshness > 0.5:
            hints.append("fresh")
        elif self.freshness > 0 and self.freshness <= 0.5:
            hints.append("subtle freshness")
        if self.citrus > 0.5:
            hints.append("citrus")
        elif self.citrus > 0 and self.citrus <= 0.3:
            hints.append("low citrus")
        if self.masculinity > 0.5:
            hints.append("masculine leaning")
        elif self.masculinity > 0 and self.masculinity <= 0.5:
            hints.append("lightly masculine")
        if self.elegance > 0.5:
            hints.append("elegant")
        if self.luxury_level > 0.5:
            hints.append("luxury/expensive smelling")
        if self.versatility > 0.5:
            hints.append("versatile")
        if self.compliment_factor > 0.5:
            hints.append("compliment-getting")
        if self.mass_appeal > 0.5:
            hints.append("mass-appealing")
        if self.price_perception == "expensive":
            hints.append("smells expensive")
        if self.gourmand > 0.5:
            hints.append("gourmand")
        if self.aquatic > 0.5:
            hints.append("aquatic")
        if self.woody > 0.5:
            hints.append("woody")
        if self.floral > 0.5:
            hints.append("floral")
        if self.spicy > 0.5:
            hints.append("spicy")
        return ", ".join(hints) if hints else "standard"


def parse_nuanced_request(query: str) -> NuancedRequest:
    """Parse a nuanced request into weighted attribute preferences.

    Handles patterns like:
    - "sweet but not too sweet" -> sweetness=0.6
    - "fresh but not citrus" -> freshness=0.8, citrus=0.2
    - "masculine but not too masculine" -> masculinity=0.5
    - "expensive smelling" -> price_perception="expensive"
    - "compliment getter" -> compliment_factor=1.0
    - "elegant" -> elegance=1.0
    - "luxury" -> luxury_level=1.0
    - "versatile" -> versatility=1.0
    """
    q = query.lower().strip()
    nr = NuancedRequest()

    # Price perception
    if re.search(r"expensive.?smelling|looks? expensive|feels? expensive|premium quality", q):
        nr.price_perception = "expensive"
        nr.luxury_level = max(nr.luxury_level, 0.8)

    # Sweetness: "sweet but not too sweet"
    if "sweet" in q:
        if re.search(r"not too sweet|not very sweet|subtle sweet|lightly sweet|not sickly", q):
            nr.sweetness = 0.5
        elif re.search(r"very sweet|extremely sweet|super sweet|sugary|candy.?like", q):
            nr.sweetness = 1.0
        else:
            nr.sweetness = 0.8

    # Freshness (check negation BEFORE citrus check)
    has_citrus_negation = bool(re.search(r"not.*citrus|without citrus|no citrus|non.?citrus", q))
    if "fresh" in q or "refreshing" in q:
        if has_citrus_negation:
            nr.freshness = 0.8
            nr.citrus = 0.2
        else:
            nr.freshness = 0.8

    # Citrus (only if not negated)
    if not has_citrus_negation and re.search(r"citrus|lemony|orange|bergamot|grapefruit", q):
        nr.citrus = max(nr.citrus, 0.8)

    # Masculinity
    if re.search(r"masculine|manly|mardana|পুরুষোচিত", q):
        if re.search(r"not too masculine|not too manly|subtle|lightly|soft", q):
            nr.masculinity = 0.5
        else:
            nr.masculinity = 1.0

    # Compliment getter
    if re.search(r"compliment.?getter|compliment.?getting|get compliments|turn heads|people notice", q):
        nr.compliment_factor = 1.0

    # Elegance
    if re.search(r"elegant|classy|sophisticated|refined|graceful", q):
        nr.elegance = 1.0

    # Luxury
    if re.search(r"luxury|luxurious|premium|high.?end|designer", q):
        nr.luxury_level = max(nr.luxury_level, 1.0)

    # Versatility
    if re.search(r"versatile|all.?rounder|any occasion|day.?to.?night|multipurpose", q):
        nr.versatility = 1.0

    # Mass appeal
    if re.search(r"mass.?appeal|crowd.?pleaser|everyone.?like|universal|safe.?buy", q):
        nr.mass_appeal = 1.0

    # Gourmand
    if re.search(r"gourmand|edible|dessert|chocolate|caramel|vanilla|honey|coffee", q):
        nr.gourmand = max(nr.gourmand, 0.8)

    # Aquatic
    if re.search(r"aquatic|marine|ocean|sea|salt|water", q):
        nr.aquatic = max(nr.aquatic, 0.8)

    # Woody
    if re.search(r"woody|wood|cedar|sandalwood|vetiver|oakmoss", q):
        nr.woody = max(nr.woody, 0.8)

    # Floral
    if re.search(r"floral|flower|rose|jasmine|lavender|bloom", q):
        nr.floral = max(nr.floral, 0.8)

    # Spicy
    if re.search(r"spicy|pepper|cinnamon|clove|cardamom|warm", q):
        nr.spicy = max(nr.spicy, 0.8)

    return nr


def extract_structured_filters(query: str) -> dict[str, Any]:
    """Extract all structured filters from query."""
    return {
        "occasion": detect_occasion(query),
        "scent": detect_scent(query),
        "performance": detect_performance(query),
        "season": detect_season(query),
        "similar_to": detect_similarity(query),
        "recommendation": detect_recommendation(query),
        "luxury": detect_luxury(query),
        "gift": detect_gift(query),
        "cheap_intent": detect_cheap_intent(query),
        "vague_budget": detect_vague_budget(query),
        "compliment": detect_compliment(query),
        "sort": detect_sort(query),
        "nuanced": parse_nuanced_request(query),
    }
