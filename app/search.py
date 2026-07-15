import logging
from collections.abc import Mapping
from typing import Any

try:
    from .database import fetch_product_candidates
    from .filters import (
        BUDGET_KEYWORDS,
        NORMALIZATION,
        STOP_WORDS,
        detect_brand,
        detect_category,
        detect_combo,
        detect_gender,
        extract_budget,
        normalize_words,
        tokenize_query,
    )
    from .ranking import rank_products
except ImportError:  # pragma: no cover - supports running main.py directly
    from database import fetch_product_candidates
    from filters import (
        BUDGET_KEYWORDS,
        NORMALIZATION,
        STOP_WORDS,
        detect_brand,
        detect_category,
        detect_combo,
        detect_gender,
        extract_budget,
        normalize_words,
        tokenize_query,
    )
    from ranking import rank_products

logger = logging.getLogger(__name__)


def _deduplicate_products(
    products: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Remove duplicate products while preserving database result order."""

    unique: list[dict[str, Any]] = []
    seen: set[Any] = set()

    for product in products:
        product_id = product.get("id")
        identifier = product_id if product_id is not None else id(product)

        if identifier in seen:
            continue

        unique.append(dict(product))
        seen.add(identifier)

    return unique


def search_products(query: str = "") -> list[dict]:
    """Retrieve, rank, and return products matching the user query."""

    tokens = tokenize_query(query)
    budget = extract_budget(query)
    gender = detect_gender(query)
    brand = detect_brand(query)
    category = detect_category(query)
    combo_requested = detect_combo(query)

    logger.debug(
        "Search filters: tokens=%s budget=%s gender=%s brand=%s "
        "category=%s combo=%s",
        tokens,
        budget,
        gender,
        brand,
        category,
        combo_requested,
    )

    candidates = fetch_product_candidates(tokens=tokens, budget=budget)
    unique_candidates = _deduplicate_products(candidates)

    logger.debug("Product candidates found: %d", len(unique_candidates))

    return rank_products(
        unique_candidates,
        query,
        tokens=tokens,
        budget=budget,
    )
