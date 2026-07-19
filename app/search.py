"""Product search pipeline.

Handles:
- query normalization
- intent detection
- database retrieval
- duplicate removal
- product ranking
"""

import logging
from typing import Any

try:
    from .repositories.product_repository import ProductRepository
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
    from repositories.product_repository import ProductRepository
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


def search_products(
    query: str = "",
) -> list[dict[str, Any]]:
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
        "Search intent | tokens=%s budget=%s gender=%s brand=%s category=%s combo=%s",
        tokens,
        budget,
        gender,
        brand,
        category,
        combo_requested,
    )


    # Database search
    candidates = ProductRepository.search_candidates(
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


    logger.debug(
        "Candidates: %d",
        len(candidates),
    )


    # Ranking with intent information
    return rank_products(
        candidates,
        query,
        tokens=tokens,
        budget=budget,
        gender=gender,
        brand=brand,
        category=category,
        combo_requested=combo_requested,
    )