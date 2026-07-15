import logging
import sqlite3
from pathlib import Path

try:
    from .filters import (
        BUDGET_KEYWORDS,
        NORMALIZATION,
        STOP_WORDS,
        extract_budget,
        normalize_words,
        tokenize_query,
    )
except ImportError:  # pragma: no cover - supports running main.py directly
    from filters import (
        BUDGET_KEYWORDS,
        NORMALIZATION,
        STOP_WORDS,
        extract_budget,
        normalize_words,
        tokenize_query,
    )

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB = BASE_DIR / "data" / "products.db"


def search_products(query: str = "") -> list[dict]:
    """Search the product database with keyword matching and optional budget filtering."""

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    budget = extract_budget(query)

    words = tokenize_query(query)

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
