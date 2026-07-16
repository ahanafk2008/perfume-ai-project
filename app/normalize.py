from __future__ import annotations

import re

WORD_MAP = {
    # =====================================================
    # Female
    # =====================================================
    "girl": "female",
    "girls": "female",
    "lady": "female",
    "ladies": "female",
    "girly": "female",
    "girlfriend": "female",
    "wife": "female",
    "woman": "female",
    "women": "female",
    "womens": "female",
    "womens": "female",
    "lady's": "female",
    "ladys": "female",

    # =====================================================
    # Male
    # =====================================================
    "boy": "male",
    "boys": "male",
    "gentleman": "male",
    "gentlemen": "male",
    "gent": "male",
    "gents": "male",
    "boyfriend": "male",
    "husband": "male",
    "man": "male",
    "men": "male",
    "mens": "male",
    "menswear": "male",

    # =====================================================
    # Product terms
    # =====================================================
    "perfumes": "perfume",
    "fragrance": "perfume",
    "fragrances": "perfume",
    "scents": "scent",
    "products": "product",
    "items": "product",
    "collections": "collection",

    # =====================================================
    # Search intent
    # =====================================================
    "recommended": "recommend",
    "recommendation": "recommend",
    "recommendations": "recommend",
    "suggestions": "suggest",
    "showing": "show",
    "available": "stock",

    # =====================================================
    # Common abbreviations
    # =====================================================
    "mls": "ml",
    "tks": "tk",

    # =====================================================
    # Banglish
    # =====================================================
    "cheleder": "male",
    "meyeder": "female",
    "chele": "male",
    "meye": "female",
    "bhai": "bro",
}

def normalize(text: str) -> str:
    if not text:
        return ""

    # Lowercase
    text = text.lower().strip()

    # Convert possessives before removing punctuation
    # women's -> womens
    # men's -> mens
    # lady's -> ladys
    text = text.replace("'s", "s")

    # Keep Bangla characters while removing other punctuation
    text = re.sub(
        r"[^\w\s\u0980-\u09FF]",
        "",
        text,
    )

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Replace words with their canonical forms
    words = [
        WORD_MAP.get(word, word)
        for word in text.split()
    ]

    return " ".join(words)


def tokenize(text: str) -> list[str]:
    """Return normalized tokens."""
    return normalize(text).split()