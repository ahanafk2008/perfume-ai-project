"""Product relevance ranking."""

from collections.abc import Mapping, Sequence
import logging
from typing import Any

try:
    from .config import MAX_SEARCH_RESULTS
    from .filters import (
        COMBO_WORDS,
        detect_brand,
        detect_category,
        detect_combo,
        detect_gender,
        tokenize_query,
    )
except ImportError:  # pragma: no cover - supports running main.py directly
    from config import MAX_SEARCH_RESULTS
    from filters import (
        COMBO_WORDS,
        detect_brand,
        detect_category,
        detect_combo,
        detect_gender,
        tokenize_query,
    )


logger = logging.getLogger(__name__)

EXACT_NAME_WEIGHT = 10
BRAND_WEIGHT = 8
CATEGORY_WEIGHT = 6
GENDER_WEIGHT = 5
BUDGET_WEIGHT = 3
COMBO_MATCH_WEIGHT = 3
UNREQUESTED_COMBO_PENALTY = -5
MAX_KEYWORD_BONUS = 3


def _text(value: Any) -> str:
    """Return a normalized lowercase string for product fields."""

    return str(value or "").lower()


def _product_text(product: Mapping[str, Any]) -> str:
    """Return searchable text from the main product fields."""

    fields = (
        product.get("name"),
        product.get("brand"),
        product.get("category"),
        product.get("description"),
    )
    return " ".join(_text(field) for field in fields)


def _is_combo_product(product: Mapping[str, Any]) -> bool:
    """Return True when a product looks like a combo, set, or bundle."""

    product_text = _product_text(product)
    return any(word in product_text for word in COMBO_WORDS)


def _matches_budget(product: Mapping[str, Any], budget: int | None) -> bool:
    """Return True when the product price is within the requested budget."""

    if budget is None:
        return False

    try:
        return float(product.get("price", 0)) <= budget
    except (TypeError, ValueError):
        return False


def _keyword_match_count(
    product: Mapping[str, Any],
    tokens: Sequence[str],
) -> int:
    """Count how many query tokens appear in the product text."""

    product_text = _product_text(product)
    unique_tokens = {token for token in tokens if token}
    return sum(1 for token in unique_tokens if token in product_text)


def calculate_score(
    product: Mapping[str, Any],
    query: str,
    *,
    tokens: Sequence[str] | None = None,
    budget: int | None = None,
    gender: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    combo_requested: bool | None = None,
) -> int:
    """Calculate a relevance score for one product."""

    tokens = tokens if tokens is not None else tokenize_query(query)
    gender = gender if gender is not None else detect_gender(query)
    brand = brand if brand is not None else detect_brand(query)
    category = category if category is not None else detect_category(query)
    combo_requested = (
        combo_requested if combo_requested is not None else detect_combo(query)
    )

    score = 0
    query_text = _text(query)
    product_name = _text(product.get("name"))
    product_brand = _text(product.get("brand"))
    product_category = _text(product.get("category"))
    product_text = _product_text(product)

    if product_name and product_name in query_text:
        score += EXACT_NAME_WEIGHT

    if brand and brand in product_brand:
        score += BRAND_WEIGHT

    if category and category in product_category:
        score += CATEGORY_WEIGHT

    if gender and gender in product_text:
        score += GENDER_WEIGHT

    if _matches_budget(product, budget):
        score += BUDGET_WEIGHT

    is_combo = _is_combo_product(product)
    if combo_requested and is_combo:
        score += COMBO_MATCH_WEIGHT
    elif not combo_requested and is_combo:
        score += UNREQUESTED_COMBO_PENALTY

    keyword_matches = _keyword_match_count(product, tokens)
    if keyword_matches > 1:
        score += min(keyword_matches - 1, MAX_KEYWORD_BONUS)

    return score


def _deduplicate_products(
    products: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Remove duplicate products while preserving first-seen order."""

    unique: list[Mapping[str, Any]] = []
    seen: set[Any] = set()

    for product in products:
        product_id = product.get("id")
        identifier = product_id if product_id is not None else id(product)
        if identifier in seen:
            continue

        unique.append(product)
        seen.add(identifier)

    return unique


def rank_products(
    products: Sequence[Mapping[str, Any]],
    query: str,
    *,
    tokens: Sequence[str] | None = None,
    budget: int | None = None,
    max_results: int = MAX_SEARCH_RESULTS,
) -> list[dict[str, Any]]:
    """Return products sorted by relevance and limited to max_results."""

    unique_products = _deduplicate_products(products)
    tokens = tokens if tokens is not None else tokenize_query(query)
    gender = detect_gender(query)
    brand = detect_brand(query)
    category = detect_category(query)
    combo_requested = detect_combo(query)

    scored_products: list[tuple[int, int, Mapping[str, Any]]] = []

    for index, product in enumerate(unique_products):
        score = calculate_score(
            product,
            query,
            tokens=tokens,
            budget=budget,
            gender=gender,
            brand=brand,
            category=category,
            combo_requested=combo_requested,
        )
        scored_products.append((score, index, product))

    scored_products.sort(key=lambda item: (-item[0], item[1]))

    logger.debug("Ranked %d products for query: %s", len(scored_products), query)
    for score, _, product in scored_products[:max_results]:
        logger.debug(
            "Score %d: %s",
            score,
            product.get("name", "unknown"),
        )

    return [dict(product) for score, _, product in scored_products[:max_results]]
