"""Product search pipeline.

Handles:
- query normalization
- intent detection
- database retrieval
- duplicate removal
- product ranking
"""

import logging
import re
from typing import Any

try:
    from .database import execute_query
    from .filters import (
        detect_brand,
        detect_category,
        detect_combo,
        detect_gender,
        extract_budget,
        extract_structured_filters,
        tokenize_query,
    )
    from .ranking import rank_products
    from .repositories.product_repository import ProductRepository

except ImportError:  # pragma: no cover
    from database import execute_query
    from filters import (
        detect_brand,
        detect_category,
        detect_combo,
        detect_gender,
        extract_budget,
        extract_structured_filters,
        tokenize_query,
    )
    from ranking import rank_products
    from repositories.product_repository import ProductRepository


logger = logging.getLogger(__name__)


MAX_SEARCH_TOKENS = 15


def _normalize_search_name(text: str) -> str:
    """Normalize text for exact name comparison."""
    text = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def exact_name_search(query: str) -> dict[str, Any] | None:
    """Public wrapper around _exact_name_search for use outside the search pipeline."""
    return _exact_name_search(query)


def _exact_name_search(query: str) -> dict[str, Any] | None:
    """Try to find a product by exact normalized name match.

    Strips common question words, searches name and name+brand columns.
    """
    q = _normalize_search_name(query)
    if not q:
        return None

    # Strip leading question/request words
    for prefix in ("do you have ", "tell me about ", "i want ", "show me ", "what about "):
        if q.startswith(prefix):
            q = q[len(prefix):]
            break

    # Search by exact normalized name match
    rows = execute_query(
        """
        SELECT * FROM products
        WHERE LOWER(REPLACE(REPLACE(REPLACE(name, '|', ''), '-', ' '), '.', '')) = ?
        OR LOWER(REPLACE(REPLACE(REPLACE(name || ' ' || brand, '|', ''), '-', ' '), '.', '')) = ?
        LIMIT 1
        """,
        (q, q),
    )
    if rows:
        return rows[0]

    # Fallback: search for the query as a substring of product name
    rows = execute_query(
        """
        SELECT * FROM products
        WHERE LOWER(name) LIKE ?
        LIMIT 1
        """,
        (f"%{q}%",),
    )
    if rows:
        # Verify the normalized forms match well
        pname = _normalize_search_name(rows[0]["name"])
        if q in pname or pname in q:
            return rows[0]

    return None


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


    # Extract structured filters
    structured_filters = extract_structured_filters(query)

    # Extract user intent
    budget = extract_budget(query)

    gender = detect_gender(query)

    brand = detect_brand(query) or structured_filters.get("similar_to")

    category = detect_category(query)

    combo_requested = detect_combo(query)

    # Price range extraction for strict filtering
    min_price = None
    max_price = None
    range_match = re.search(r"(?:between|from)\s+[\u09f3]?\s*(\d+)\s+(?:and|to)\s+[\u09f3]?\s*(\d+)", query)
    if range_match:
        min_price = int(range_match.group(1))
        max_price = int(range_match.group(2))
    else:
        # Single budget acts as max_price
        if budget is not None:
            max_price = budget

    # If brand is explicitly requested and no products found, do not
    # fall back to unrelated generic products.
    brand_requested = brand is not None


    logger.debug(
        "Search intent | tokens=%s budget=%s min_price=%s max_price=%s gender=%s brand=%s category=%s combo=%s",
        tokens,
        budget,
        min_price,
        max_price,
        gender,
        brand,
        category,
        combo_requested,
    )


    # Exact product name search (before fuzzy token search)
    exact_match = _exact_name_search(query)
    if exact_match and budget is not None and float(exact_match.get("price", 0)) > budget:
        exact_match = None
        logger.debug("Exact match eliminated by budget filter: price %s > budget %s", exact_match, budget)
    if exact_match:
        logger.debug("Exact product name match found: %s", exact_match.get("name"))
        candidates = [exact_match]
    else:
        candidates = ProductRepository.search_candidates(
        query=query,
        tokens=tokens,
        budget=budget,
        gender=gender,
        brand=brand,
        category=category,
        combo_requested=combo_requested,
        min_price=min_price,
        max_price=max_price,
    )

    # Brand search behavior: if a brand was requested and no candidates
    # matched, return empty list instead of falling back to unrelated products.
    if brand_requested and not candidates:
        logger.debug(
            "Brand '%s' not found; returning empty results instead of fallback.",
            brand,
        )
        return []


    # No matching products found via tokens — retry with only structural filters.
    if not candidates:
        has_structural_filters = any([
            structured_filters.get("occasion"),
            structured_filters.get("scent"),
            structured_filters.get("performance"),
            structured_filters.get("season"),
            gender,
            brand,
            budget is not None,
            structured_filters.get("recommendation"),
            structured_filters.get("luxury"),
            structured_filters.get("gift"),
            structured_filters.get("cheap_intent"),
            structured_filters.get("compliment"),
        ])
        if has_structural_filters:
            logger.debug("Token search returned 0; retrying with filters only (no token match)")
            candidates = ProductRepository.search_candidates(
                query=query,
                tokens=[],
                budget=budget,
                gender=gender,
                brand=brand,
                category=category,
                combo_requested=combo_requested,
                min_price=min_price,
                max_price=max_price,
            )

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
    recommendation = structured_filters.get("recommendation", False)
    luxury = structured_filters.get("luxury", False)
    gift = structured_filters.get("gift", False)
    cheap_intent = structured_filters.get("cheap_intent", False)
    compliment = structured_filters.get("compliment", False)
    occasion = structured_filters.get("occasion")
    scent = structured_filters.get("scent")
    performance = structured_filters.get("performance")
    season = structured_filters.get("season")
    ranked = rank_products(
        candidates,
        query,
        tokens=tokens,
        budget=budget,
        gender=gender,
        brand=brand,
        category=category,
        combo_requested=combo_requested,
        recommendation=recommendation,
        luxury=luxury,
        gift=gift,
        cheap_intent=cheap_intent,
        compliment=compliment,
        occasion=occasion,
        scent=scent,
        performance=performance,
        season=season,
    )

    # Post-ranking budget enforcement: budget extracted from query must be
    # strictly respected regardless of ranking scores.  The database layer
    # already filters candidates by budget, but ranking can receive unfiltered
    # data from other callers; this guard ensures no over-budget product
    # ever reaches the user.
    if budget is not None:
        ranked = [
            product
            for product in ranked
            if float(product.get("price", 0)) <= budget
        ]

    # Specific product query validation (only when exact name search failed):
    # if the query contains a known brand plus additional non-brand tokens,
    # and no product's name contains ALL tokens, the user likely searched for
    # a specific product that doesn't exist.  Return empty rather than showing
    # unrelated brand matches.
    if not exact_match and _is_specific_product_query(tokens, brand) and not _any_product_matches_all_tokens(ranked, tokens):
        logger.debug(
            "Specific product query with tokens %s found no product matching all tokens; returning empty.",
            tokens,
        )
        return []

    return ranked


def _is_specific_product_query(tokens: list[str], brand: str | None) -> bool:
    """Return True when the query looks like a specific product search
    (brand + additional descriptor words) rather than a category search."""
    if not tokens or len(tokens) < 2 or len(tokens) > 6:
        return False
    return brand is not None


def _any_product_matches_all_tokens(
    products: list[dict[str, Any]],
    tokens: list[str],
) -> bool:
    """Return True when at least one product's name contains every search token."""
    for p in products:
        pname = _normalize_search_name(p.get("name", ""))
        combined = _normalize_search_name(f"{p.get('name', '')} {p.get('brand', '')}")
        if all(token in pname for token in tokens):
            return True
        if all(token in combined for token in tokens):
            return True
    return False
