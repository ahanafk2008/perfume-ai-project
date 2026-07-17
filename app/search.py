"""Product search pipeline.

Handles:
- query normalization
- intent detection
- database retrieval
- duplicate removal
- product ranking
"""

import logging
from collections.abc import Mapping
from typing import Any

try:
    from .database import fetch_product_candidates
    from .filters import (
        extract_budget,
        tokenize_query,
        detect_gender,
        detect_brand,
        detect_category,
        detect_combo,
    )
    from .ranking import rank_products

except ImportError:  # pragma: no cover
    from database import fetch_product_candidates
    from filters import (
        extract_budget,
        tokenize_query,
        detect_gender,
        detect_brand,
        detect_category,
        detect_combo,
    )
    from ranking import rank_products


logger = logging.getLogger(__name__)


MAX_SEARCH_TOKENS = 15


def _deduplicate_products(
    products: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """
    Remove duplicate products while preserving order.
    """

    unique: list[dict[str, Any]] = []

    seen_ids: set[Any] = set()

    for product in products:

        product_id = product.get("id")

        identifier = (
            product_id
            if product_id is not None
            else id(product)
        )

        if identifier in seen_ids:
            continue

        unique.append(dict(product))
        seen_ids.add(identifier)

    return unique



def search_products(
    query: str = "",
) -> list[dict]:
    """
    Complete product search pipeline.

    Flow:

    User Query
        ↓
    Normalize
        ↓
    Detect Intent
        ↓
    Database Search
        ↓
    Ranking
        ↓
    Final Products
    """

    if not query.strip():
        return []


    # Normalize query
    query = query.lower().strip()
    
    tokens = tokenize_query(query)

    tokens = tokens[:MAX_SEARCH_TOKENS]


    # Extract user intent
    budget = extract_budget(query)

    gender = detect_gender(query)

    brand = detect_brand(query)

    category = detect_category(query)

    combo_requested = detect_combo(query)


    logger.debug(
        """
        Search Intent:
        tokens=%s
        budget=%s
        gender=%s
        brand=%s
        category=%s
        combo=%s
        """,
        tokens,
        budget,
        gender,
        brand,
        category,
        combo_requested,
    )


    # Database search
    candidates = fetch_product_candidates(
        query=query,
        tokens=tokens,
        budget=budget,
        gender=gender,
        brand=brand,
        category=category,
        combo_requested=combo_requested,
    )


    # No matching products found
    if not candidates:
        logger.debug(
            "No matching products found"
        )
        return []


    unique_candidates = _deduplicate_products(
        candidates
    )

    logger.debug(
        "Candidates after cleanup: %d",
        len(unique_candidates),
    )


    # Ranking with intent information
    return rank_products(
        unique_candidates,
        query,
        tokens=tokens,
        budget=budget,
        gender=gender,
        brand=brand,
        category=category,
        combo_requested=combo_requested,
    )