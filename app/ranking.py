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


def _text(value: Any) -> str:
    """Normalize text."""

    return str(value or "").lower()



def _product_text(
    product: Mapping[str, Any],
) -> str:
    """Return searchable product text."""

    fields = (
        product.get("name"),
        product.get("brand"),
        product.get("category"),
        product.get("description"),
    )

    return " ".join(
        _text(field)
        for field in fields
    )



def _is_combo_product(
    product: Mapping[str, Any],
) -> bool:
    """Detect combo products."""

    text = _product_text(product)

    return any(
        word in text
        for word in COMBO_WORDS
    )



def _matches_budget(
    product: Mapping[str, Any],
    budget: int | None,
) -> bool:
    """Check budget."""

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
    """Calculate field-aware keyword score with strict word boundaries."""

    name = f" {_text(product.get('name'))} "
    brand = f" {_text(product.get('brand'))} "
    category = f" {_text(product.get('category'))} "
    description = f" {_text(product.get('description'))} "

    score = 0
    for token in set(tokens):
        if not token:
            continue
            
        padded_token = f" {token} "
        
        # Take the highest value field where the token appears
        if padded_token in name:
            score += 5
        elif padded_token in brand:
            score += 4
        elif padded_token in category:
            score += 3
        elif padded_token in description:
            score += 1

    return score



def _gender_penalty(
    product_text: str,
    gender: str | None,
) -> int:
    """
    Penalize wrong gender products.
    """

    if not gender:
        return 0


    if gender == "male":

        if any(
            word in product_text
            for word in [
                "female",
                "women",
                "woman",
                "girl",
                "lady",
            ]
        ):
            return WRONG_GENDER_PENALTY


    if gender == "female":

        if any(
            word in product_text
            for word in [
                "male",
                "men",
                "man",
                "boy",
            ]
        ):
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

    tokens = (
        tokens
        if tokens is not None
        else tokenize_query(query)
    )

    gender = (
        gender
        if gender is not None
        else detect_gender(query)
    )

    brand = (
        brand
        if brand is not None
        else detect_brand(query)
    )

    category = (
        category
        if category is not None
        else detect_category(query)
    )

    combo_requested = (
        combo_requested
        if combo_requested is not None
        else detect_combo(query)
    )


    score = 0

    query_text = _text(query)

    product_name = _text(
        product.get("name")
    )

    product_brand = _text(
        product.get("brand")
    )

    product_category = _text(
        product.get("category")
    )

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
    if brand and brand in product_brand:
        score += BRAND_WEIGHT



    # Category match
    if category and category in product_category:
        score += CATEGORY_WEIGHT



    # Gender match
    if gender:

        if gender == "male":
            if any(word in product_text for word in [
                "male",
                "men",
                "man",
                "boy"
            ]):
                score += GENDER_WEIGHT


        elif gender == "female":
            if any(word in product_text for word in [
                "female",
                "women",
                "woman",
                "girl",
                "lady"
            ]):
                score += GENDER_WEIGHT



    # Wrong gender penalty
    score += _gender_penalty(
        product_text,
        gender,
    )




    # Budget
    if _matches_budget(
        product,
        budget,
    ):
        score += BUDGET_WEIGHT



    # Combo handling
    is_combo = _is_combo_product(product)

    if combo_requested and is_combo:
        score += COMBO_MATCH_WEIGHT

    elif not combo_requested and is_combo:
        score += UNREQUESTED_COMBO_PENALTY



    # Field-aware keyword relevance
    score += _keyword_score(
        product,
        tokens,
    )

    return score



def _deduplicate_products(
    products: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Remove duplicates."""

    unique = []
    seen = set()


    for product in products:

        product_id = product.get("id")

        identifier = (
            product_id
            if product_id is not None
            else id(product)
        )


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
    gender: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    combo_requested: bool | None = None,
    max_results: int = MAX_SEARCH_RESULTS,
) -> list[dict[str, Any]]:

    """Rank and return best products."""

    unique_products = _deduplicate_products(products)


    tokens = (
        tokens
        if tokens is not None
        else tokenize_query(query)
    )

    gender = (
        gender
        if gender is not None
        else detect_gender(query)
    )

    brand = (
        brand
        if brand is not None
        else detect_brand(query)
    )

    category = (
        category
        if category is not None
        else detect_category(query)
    )

    combo_requested = (
        combo_requested
        if combo_requested is not None
        else detect_combo(query)
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

        scored.append(
            (
                score,
                index,
                product,
            )
        )


    scored.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )


    logger.debug(
        "Ranked %d products for query=%s",
        len(scored),
        query,
    )


    return [
        dict(product)
        for _, _, product in scored[:max_results]
    ]