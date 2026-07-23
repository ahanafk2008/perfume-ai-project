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
    from .product_attrs import get_product_attributes
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
    from product_attrs import get_product_attributes


logger = logging.getLogger(__name__)


# Scoring weights
EXACT_NAME_WEIGHT = 100
BRAND_WEIGHT = 50
CATEGORY_WEIGHT = 10
GENDER_WEIGHT = 30
BUDGET_WEIGHT = 20

COMBO_MATCH_WEIGHT = 10
UNREQUESTED_COMBO_PENALTY = -999

# Strong penalty for wrong gender
WRONG_GENDER_PENALTY = -100

# Additional scoring for new filters
OCCASION_WEIGHT = 20
SCENT_WEIGHT = 20
PERFORMANCE_WEIGHT = 20
SIMILARITY_WEIGHT = 40
SEASON_WEIGHT = 20

MAX_KEYWORD_BONUS = 5

# Recommendation/premium brand boost
RECOMMENDATION_WEIGHT = 30

# Luxury query premium brand boost (stronger)
LUXURY_WEIGHT = 60

# Performance boost from description keywords
PERFORMANCE_DESC_WEIGHT = 20

# Category diversity bonus for gender-agnostic queries
CATEGORY_DIVERSITY_BONUS = 15

# Price tier thresholds for luxury boost scaling
PRICE_TIER_LUXURY_HIGH = 2000
PRICE_TIER_LUXURY_MID = 1200

# Cheap sort boost
CHEAP_SORT_WEIGHT = 30

# Gift intent boost
GIFT_WEIGHT = 25

# Designer, niche, and premium brands (subset of KNOWN_BRANDS with higher reputation).
# These get a scoring boost when the user asks for "best", "top", "premium", etc.
PREMIUM_BRANDS: set[str] = {
    "dior",
    "tom ford",
    "tomford",
    "gucci",
    "prada",
    "versace",
    "armani",
    "giorgio armani",
    "burberry",
    "carolina herrera",
    "chanel",
    "ysl",
    "yves saint laurent",
    "louis vuitton",
    "luis vuitton",
    "dolce & gabbana",
    "dolce and gabbana",
    "bvlgari",
    "bulgari",
    "paco rabanne",
    "rabanne",
    "hugo boss",
    "boss",
    "calvin klein",
    "ck",
    "givenchy",
    "valentino",
    "lacoste",
    "montblanc",
    "issey miyake",
    "hermes",
    "jo malone",
    "mugler",
    "narciso rodriguez",
    "moschino",
    "mancera",
    "montale",
    "xerjoff",
    "parfums de marly",
    "creed",
    "initio",
    "amouage",
    "roja",
    "byredo",
    "le labo",
    "diptyque",
    "kilian",
}


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


def _matches_occasion(
    product: Mapping[str, Any],
    occasion: str | None,
) -> bool:
    """Check whether product data matches requested occasion (via bestTime field)."""
    if not occasion:
        return False
    attrs = get_product_attributes(product)
    best_time = _text(attrs.get("best_time") or "")
    if not best_time:
        return False
    return occasion.lower() in best_time


def _matches_scent(
    product: Mapping[str, Any],
    scent: str | None,
) -> bool:
    """Check whether product fragrance notes match requested scent profile.

    Matches against known scent-category keywords (e.g. 'floral' matches
    'rose', 'jasmine') so users can ask for 'floral perfume' and get
    products with floral notes.
    """
    if not scent:
        return False
    attrs = get_product_attributes(product)
    all_notes = []
    for key in ("notes_top", "notes_middle", "notes_base"):
        notes = attrs.get(key)
        if notes:
            all_notes.extend(notes)
    if not all_notes:
        return False
    scent_lower = scent.lower()
    match_keywords = _SCENT_NOTE_MATCH.get(scent_lower, {scent_lower})
    notes_text = " ".join(n.lower() for n in all_notes)
    return any(kw in notes_text for kw in match_keywords)


_STRONG_KW = {"strong", "powerful", "intense", "beast"}

# Scent category → matching note keywords
_SCENT_NOTE_MATCH: dict[str, set[str]] = {
    "floral": {"rose", "jasmine", "lavender", "peony", "tuberose", "floral", "flower", "blossom", "violet", "iris", "lily", "gardenia", "orchid", "narcissus"},
    "sweet": {"sweet", "vanilla", "sugar", "candy", "caramel", "honey", "gourmand", "chocolate", "toffee"},
    "fresh": {"fresh", "citrus", "bergamot", "lemon", "orange", "grapefruit", "lime", "aquatic", "marine", "ocean", "clean", "aldehydes", "neroli"},
    "woody": {"woody", "wood", "cedar", "sandalwood", "sandal", "vetiver", "oakmoss", "patchouli", "pine"},
    "oud": {"oud", "oudh", "agar", "agarwood"},
    "spicy": {"spicy", "pepper", "ginger", "cinnamon", "clove", "nutmeg", "cardamom", "saffron"},
    "vanilla": {"vanilla"},
}

def _matches_performance(
    product: Mapping[str, Any],
    performance: str | None,
) -> bool:
    """Check whether product longevity/sillage data matches requested performance."""
    if not performance:
        return False
    attrs = get_product_attributes(product)
    longevity = _text(attrs.get("longevity") or "")
    sillage = _text(attrs.get("sillage") or "")

    if performance == "longlasting":
        return bool(longevity)
    if performance == "strong":
        return any(kw in longevity or kw in sillage for kw in _STRONG_KW)
    if performance == "projection":
        return bool(sillage)
    if performance == "compliment":
        return False
    perf_text = " ".join([longevity, sillage])
    return performance.lower() in perf_text


def _matches_season(
    product: Mapping[str, Any],
    season: str | None,
) -> bool:
    """Check whether product bestTime data matches requested season."""
    if not season:
        return False
    attrs = get_product_attributes(product)
    best_time = _text(attrs.get("best_time") or "")
    if not best_time:
        return False
    return season.lower() in best_time


def _matches_similarity(
    product: Mapping[str, Any],
    similar_to: str | None,
) -> bool:
    """Check whether product metadata lists similar_to reference."""
    if not similar_to:
        return False
    meta = product.get("metadata") or {}
    similar_products = [
        s.lower()
        for s in (meta.get("similar_to") or [])
    ]
    return similar_to.lower() in " ".join(similar_products)


def _premium_brand_boost(
    product: Mapping[str, Any],
    recommendation: bool = False,
) -> int:
    """Return RECOMMENDATION_WEIGHT when recommendation intent and premium brand match."""
    if not recommendation:
        return 0
    product_brand = _text(product.get("brand"))
    for brand in PREMIUM_BRANDS:
        if brand in product_brand:
            return RECOMMENDATION_WEIGHT
    return 0


def _luxury_brand_boost(
    product: Mapping[str, Any],
    luxury: bool = False,
) -> int:
    """Return LUXURY_WEIGHT when luxury intent and premium brand match."""
    if not luxury:
        return 0
    product_brand = _text(product.get("brand"))
    is_premium = any(brand in product_brand for brand in PREMIUM_BRANDS)
    if not is_premium:
        return 0
    return LUXURY_WEIGHT


def _luxury_price_tier_boost(
    product: Mapping[str, Any],
    luxury: bool = False,
) -> int:
    """Scale luxury brand boost by price tier so full bottles
    outrank cheap decants/samples for luxury queries."""
    if not luxury:
        return 0
    product_brand = _text(product.get("brand"))
    is_premium = any(brand in product_brand for brand in PREMIUM_BRANDS)
    if not is_premium:
        return 0
    try:
        price = float(product.get("price", 0))
    except (TypeError, ValueError):
        return 0
    if price >= PRICE_TIER_LUXURY_HIGH:
        return LUXURY_WEIGHT
    if price >= PRICE_TIER_LUXURY_MID:
        return int(LUXURY_WEIGHT * 0.6)
    return int(LUXURY_WEIGHT * 0.2)


def _cheap_sort_boost(
    product: Mapping[str, Any],
    cheap_intent: bool = False,
    max_price_in_results: float = 1.0,
) -> int:
    """Reward lower-priced products when the user asks for cheap/affordable."""
    if not cheap_intent:
        return 0
    try:
        price = float(product.get("price", 0))
    except (TypeError, ValueError):
        return 0
    if max_price_in_results <= 0:
        return 0
    ratio = 1.0 - (price / max_price_in_results)
    return int(CHEAP_SORT_WEIGHT * ratio)


def _gift_boost(
    product: Mapping[str, Any],
    gift: bool = False,
) -> int:
    """Boost premium brands for gift queries."""
    if not gift:
        return 0
    product_brand = _text(product.get("brand"))
    for brand in PREMIUM_BRANDS:
        if brand in product_brand:
            return GIFT_WEIGHT
    return 0


_PERFORMANCE_DESC_KEYWORDS: set[str] = {
    "long lasting",
    "long-lasting",
    "lasting",
    "strong",
    "powerful",
    "intense",
    "beast",
    "longwear",
    "all day",
}


def _description_performance_boost(product: Mapping[str, Any]) -> int:
    """Boost products whose descriptions contain performance keywords."""
    desc = _text(product.get("description"))
    if not desc:
        return 0
    for kw in _PERFORMANCE_DESC_KEYWORDS:
        if kw in desc:
            return PERFORMANCE_DESC_WEIGHT
    return 0


def _category_diversity_boost(
    product: Mapping[str, Any],
    has_gender: bool,
) -> int:
    """Boost non-dominant categories when no gender is specified,
    so recommendation queries return diverse results (not just men products)."""
    if has_gender:
        return 0
    cat = _text(product.get("category"))
    # Boost women and unisex categories to balance men-heavy cheap products
    if cat in {"women", "female", "unisex"}:
        return CATEGORY_DIVERSITY_BONUS
    # Slight penalty for combo when not requested (already handled by UNREQUESTED_COMBO_PENALTY)
    return 0


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
    occasion: str | None = None,
    scent: str | None = None,
    performance: str | None = None,
    season: str | None = None,
    similar_to: str | None = None,
    recommendation: bool = False,
    luxury: bool = False,
    gift: bool = False,
    cheap_intent: bool = False,
    max_price_in_results: float = 1.0,
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
    has_gender = gender is not None

    query_text = _text(query)
    product_name = _text(product.get("name"))
    product_brand = _text(product.get("brand"))
    product_category = _text(product.get("category"))
    product_text = _product_text(product)

    # Exact product name matching
    if product_name and query_text:
        query_words = query_text.split()

        if product_name == query_text:
            score += EXACT_NAME_WEIGHT
        elif len(query_words) > 1 and f" {query_text} " in f" {product_name} ":
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

    # Metadata-based matching (boost if actual metadata exists)
    if _matches_occasion(product, occasion):
        score += OCCASION_WEIGHT
    if _matches_scent(product, scent):
        score += SCENT_WEIGHT
    if _matches_performance(product, performance):
        score += PERFORMANCE_WEIGHT
    if _matches_season(product, season):
        score += SEASON_WEIGHT
    if _matches_similarity(product, similar_to):
        score += SIMILARITY_WEIGHT

    # ---- Intent-based boosts ----

    # Luxury intent: strongest premium brand boost, scaled by price tier
    score += _luxury_price_tier_boost(product, luxury)

    # Recommendation intent: medium premium brand boost
    score += _premium_brand_boost(product, recommendation)

    # Performance/attribute query: boost products with performance keywords in description,
    # plus premium brand boost as a quality proxy
    if performance:
        score += _description_performance_boost(product)
        score += _premium_brand_boost(product, True)

    # Occasion query: also boost premium brands
    if occasion:
        score += _premium_brand_boost(product, True)

    # Category diversity for gender-agnostic queries (e.g. "best perfume" without gender)
    if recommendation or luxury:
        score += _category_diversity_boost(product, has_gender)

    # Gift intent: boost premium brand products
    score += _gift_boost(product, gift)

    # Budget query with numeric price: boost premium brands within budget
    if budget is not None:
        score += _premium_brand_boost(product, True)

    # Cheap intent (no specific budget): reward lower-priced products
    if cheap_intent:
        score += _cheap_sort_boost(product, cheap_intent, max_price_in_results)

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
    occasion: str | None = None,
    scent: str | None = None,
    performance: str | None = None,
    season: str | None = None,
    similar_to: str | None = None,
    recommendation: bool = False,
    luxury: bool = False,
    gift: bool = False,
    cheap_intent: bool = False,
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
    occasion = (
        occasion
        if occasion is not None
        else __import__("app.filters", fromlist=["detect_occasion"]).detect_occasion(query)
    )
    scent = (
        scent
        if scent is not None
        else __import__("app.filters", fromlist=["detect_scent"]).detect_scent(query)
    )
    season = (
        season
        if season is not None
        else __import__("app.filters", fromlist=["detect_season"]).detect_season(query)
    )
    performance = (
        performance
        if performance is not None
        else __import__("app.filters", fromlist=["detect_performance"]).detect_performance(query)
    )
    similar_to = (
        similar_to
        if similar_to is not None
        else __import__("app.filters", fromlist=["detect_similarity"]).detect_similarity(query)
    )
    recommendation = (
        recommendation
        if recommendation is not None
        else __import__("app.filters", fromlist=["detect_recommendation"]).detect_recommendation(query)
    )
    luxury = (
        luxury
        if luxury is not None
        else __import__("app.filters", fromlist=["detect_luxury"]).detect_luxury(query)
    )
    gift = (
        gift
        if gift is not None
        else __import__("app.filters", fromlist=["detect_gift"]).detect_gift(query)
    )
    cheap_intent = (
        cheap_intent
        if cheap_intent is not None
        else __import__("app.filters", fromlist=["detect_cheap_intent"]).detect_cheap_intent(query)
    )

    # Compute max price for cheap sort normalization
    prices = []
    for p in unique_products:
        try:
            prices.append(float(p.get("price", 0)))
        except (TypeError, ValueError):
            prices.append(0)
    max_price_in_results = max(prices) if prices else 1.0

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
            occasion=occasion,
            scent=scent,
            performance=performance,
            season=season,
            similar_to=similar_to,
            recommendation=recommendation,
            luxury=luxury,
            gift=gift,
            cheap_intent=cheap_intent,
            max_price_in_results=max_price_in_results,
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
