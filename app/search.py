import logging
import re
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB = BASE_DIR / "data" / "products.db"


# Bangla, Banglish and English normalization
NORMALIZATION: dict[str, str] = {
    # Female
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
    "মধ্যে",
    "জন্য",
    "দেখান",
    "চাই",
    "আছে",
}

# Budget-indicating words — if one appears before a number, that number is a budget
BUDGET_KEYWORDS: set[str] = {
    "under", "below", "within", "budget", "taka", "tk",
    "টাকার", "মধ্যে",
}


def normalize_words(words: list[str]) -> list[str]:
    """Normalize words using the mapping, removing stop words and perfume synonyms."""

    normalized: list[str] = []

    for word in words:

        word = word.lower().strip()

        if word in STOP_WORDS:
            continue

        if word in NORMALIZATION:
            mapped = NORMALIZATION[word]

            if mapped:
                normalized.append(mapped)

        else:
            normalized.append(word)

    return normalized


def extract_budget(query: str) -> int | None:
    """Extract a budget from the query using contextual patterns.

    Looks for patterns like 'under 500', 'below 1000', '৳500', 'budget 800',
    'taka 500', etc. Falls back to the last number only if a budget keyword
    is present somewhere in the query.
    """

    lower = query.lower()

    # Pattern 1: currency symbol directly before a number — ৳500, ৳ 500
    match = re.search(r"৳\s*(\d+)", query)
    if match:
        return int(match.group(1))

    # Pattern 2: budget keyword followed by a number — "under 500", "budget 1000"
    for keyword in BUDGET_KEYWORDS:
        pattern = rf"\b{re.escape(keyword)}\s+(\d+)"
        match = re.search(pattern, lower)
        if match:
            return int(match.group(1))

    # Pattern 3: number followed by budget keyword — "500 taka", "500 tk"
    match = re.search(r"(\d+)\s*(?:taka|tk|টাকা)\b", lower)
    if match:
        return int(match.group(1))

    return None


def search_products(query: str = "") -> list[dict]:
    """Search the product database with keyword matching and optional budget filtering."""

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    budget = extract_budget(query)

    # Remove numbers and currency markers for keyword extraction
    clean_query = re.sub(r"\d+", "", query.lower())

    clean_query = (
        clean_query
        .replace("৳", "")
        .replace("tk", "")
        .replace("taka", "")
    )

    words = clean_query.split()

    words = normalize_words(words)

    results: list[dict] = []

    # If no keywords, return products within budget
    if not words:

        cursor.execute("SELECT * FROM products")

        rows = cursor.fetchall()

        for row in rows:

            product = dict(row)

            if budget is None or product["price"] <= budget:
                results.append(product)

    else:

        for word in words:

            cursor.execute("""
                SELECT *
                FROM products
                WHERE LOWER(name) LIKE ?
                   OR LOWER(brand) LIKE ?
                   OR LOWER(category) LIKE ?
            """, (
                f"%{word}%",
                f"%{word}%",
                f"%{word}%",
            ))

            rows = cursor.fetchall()

            for row in rows:

                product = dict(row)

                if budget is None or product["price"] <= budget:
                    results.append(product)

    conn.close()

    # Remove duplicates
    unique: list[dict] = []
    seen: set[str] = set()

    for p in results:
        if p["id"] not in seen:
            unique.append(p)
            seen.add(p["id"])

    logger.debug("Products found: %d", len(unique))
    for p in unique:
        logger.debug("- %s (৳%s)", p["name"], p["price"])

    return unique