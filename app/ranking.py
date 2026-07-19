"""Product relevance ranking."""

from collections.abc import Mapping, Sequence
import logging
import re
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
except ImportError:  # pragma: no cover
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


# Scoring weights
EXACT_NAME_WEIGHT = 20
BRAND_WEIGHT = 15
CATEGORY_WEIGHT = 10
GENDER_WEIGHT = 20
BUDGET_WEIGHT = 3

COMBO_MATCH_WEIGHT = 10
UNREQUESTED_COMBO_PENALTY = -30

# Strong penalty for wrong gender
WRONG_GENDER_PENALTY = -100

MAX_KEYWORD_BONUS = 5


MALE_WORDS = {
    "male",
    "men",
    "man",
    "boy",
}

FEMALE_WORDS = {
    "female",
    "women",
    "woman",
    "girl",
    "lady",
}


def _text(value: Any) -> str:
    """Normalize a value to lowercase, whitespace-trimmed text."""

    return str(value or "").lower().strip()


def _tokenize(text: str) -> set[str]:
    """Split normalized text into a set of lowercase word tokens."""

    return set(re.findall(r"\w+", text.lower()))


def _product_text(product: Mapping[str, Any]) -> str:
    """Return searchable, normalized product text."""

    fields = (
        product.get("name"),
        product.get("brand"),
        product.get("category"),
        product.get("description"),
    )

    return " ".join(_text(field) for field in fields)


def _is_combo_product(product: Mapping[str, Any]) -> bool:
    """Detect combo products using token intersection (no substring matching)."""

    tokens = _tokenize(_product_text(product))

    return bool(tokens & set(COMBO_WORDS))


def _matches_budget(
    product: Mapping[str, Any],
    budget: int | None,
) -> bool:
    """Check whether a product fits within the given budget."""

    if budget is None:
        return False

    try:
        return float(product.get("price", 0)) <= budget
    except (TypeError, ValueError):
        return False


def _keyword_score(
    product: Mapping[str, Any],
    tokens: Sequence[str],
) -> int:
    """
    Calculate keyword relevance using normalized, token-based word matching.
    """

    fields = {
        "name": (_tokenize(_text(product.get("name"))), 5),
        "brand": (_tokenize(_text(product.get("brand"))), 4),
        "category": (_tokenize(_text(product.get("category"))), 3),
        "description": (_tokenize(_text(product.get("description"))), 1),
    }

    score = 0

    for token in {t.lower() for t in tokens if t}:
        for words, weight in fields.values():
            if token in words:
                score += weight
                break

    return score


def _gender_penalty(
    product_text: str,
    gender: str | None,
) -> int:
    """
    Penalize products that target the opposite gender.

    Uses token-based matching to avoid false positives such as
    "womanizer" being treated as matching "man".
    """

    if gender is None:
        return 0

    product_words = _tokenize(product_text)

    if gender == "male" and product_words & FEMALE_WORDS:
        return WRONG_GENDER_PENALTY

    if gender == "female" and product_words & MALE_WORDS:
        return WRONG_GENDER_PENALTY

    return 0


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
    """Calculate product relevance score."""

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

    # Exact product name matching
    if product_name and query_text:
        padded_query = f" {query_text} "
        padded_product = f" {product_name} "
        query_words = query_text.split()

        if product_name == query_text:
            score += EXACT_NAME_WEIGHT
        elif len(query_words) > 1 and padded_query in padded_product:
            # Multi-word phrase exists inside product name
            score += int(EXACT_NAME_WEIGHT * 0.8)

    # Brand match
    if brand and brand.lower() in product_brand:
        score += BRAND_WEIGHT

    # Category match
    if category and category.lower() in product_category:
        score += CATEGORY_WEIGHT

    # Gender match (token-based, using shared gender word constants)
    if gender:
        product_words = _tokenize(product_text)

        if gender == "male" and product_words & MALE_WORDS:
            score += GENDER_WEIGHT
        elif gender == "female" and product_words & FEMALE_WORDS:
            score += GENDER_WEIGHT

    # Wrong gender penalty
    score += _gender_penalty(product_text, gender)

    # Budget
    if _matches_budget(product, budget):
        score += BUDGET_WEIGHT

    # Combo handling (token-based)
    is_combo = _is_combo_product(product)

    if combo_requested and is_combo:
        score += COMBO_MATCH_WEIGHT
    elif not combo_requested and is_combo:
        score += UNREQUESTED_COMBO_PENALTY

    # Field-aware keyword relevance
    score += _keyword_score(product, tokens)

    return score


def _deduplicate_products(
    products: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """
    Remove duplicate products using product id or a stable name+brand
    fingerprint. Never relies on Python's built-in object id().
    """

    unique = []
    seen = set()

    for product in products:
        product_id = product.get("id")

        if product_id is not None:
            identifier = f"id:{product_id}"
        else:
            name = _text(product.get("name"))
            brand = _text(product.get("brand"))
            identifier = f"name:{name}|brand:{brand}"

        if identifier in seen:
            continue

        seen.add(identifier)
        unique.append(product)

    return unique


def rank_products(
    products: Sequence[Mapping[str, Any]],
    query: str,
    *,
    tokens: Sequence[str] | None = None,
    budget: int | None = None,
    gender: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    combo_requested: bool | None = None,
    max_results: int = MAX_SEARCH_RESULTS,
) -> list[dict[str, Any]]:
    """
    Rank and return the best matching products.
    """

    # Normalize query
    query = query.lower().strip()

    # Remove duplicates
    unique_products = _deduplicate_products(products)

    # Detect query information if not provided
    tokens = tokens if tokens is not None else tokenize_query(query)
    gender = gender if gender is not None else detect_gender(query)
    brand = brand if brand is not None else detect_brand(query)
    category = category if category is not None else detect_category(query)
    combo_requested = (
        combo_requested if combo_requested is not None else detect_combo(query)
    )

    scored = []

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

        scored.append((score, index, product))

    # Highest score first; keep original order when scores are equal
    scored.sort(key=lambda item: (-item[0], item[1]))

    logger.debug(
        "Ranked %d unique products from %d input products for query='%s'",
        len(scored),
        len(products),
        query,
    )

    return [dict(product) for _, _, product in scored[:max_results]]