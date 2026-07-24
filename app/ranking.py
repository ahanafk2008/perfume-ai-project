"""Product relevance ranking."""

import logging
import re
from collections.abc import Mapping, Sequence
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
EXACT_NAME_WEIGHT = 40
BRAND_WEIGHT = 30
CATEGORY_WEIGHT = 10
GENDER_WEIGHT = 20
BUDGET_WEIGHT = 20

# Occasion-specific scoring weights
OCCASION_SCORE_BOOST = 25
OCCASION_SCORE_PENALTY = -30

COMBO_MATCH_WEIGHT = 10
UNREQUESTED_COMBO_PENALTY = -999
LUXURY_COMBO_PENALTY = -9999

# Strong penalty for wrong gender
WRONG_GENDER_PENALTY = -100

# Over-budget penalty
OVER_BUDGET_PENALTY = -100

# Additional scoring for new filters
OCCASION_WEIGHT = 20
SCENT_WEIGHT = 30
PERFORMANCE_WEIGHT = 15
SIMILARITY_WEIGHT = 30
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

# Compliment intent boost
COMPLIMENT_PREMIUM_BOOST = 30
COMPLIMENT_PERFORMANCE_BOOST = 20
COMPLIMENT_POPULAR_BOOST = 15

# Popularity weight
POPULARITY_WEIGHT = 10

# Diversity penalty for already-recommended products
ALREADY_RECOMMENDED_PENALTY = -999

# Blind-buy mode boost for versatile/mass-appealing products
BLIND_BUY_VERSATILITY_BOOST = 30
BLIND_BUY_MASS_APPEAL_BOOST = 25
BLIND_BUY_POPULARITY_BOOST = 20
BLIND_BUY_PREMIUM_BOOST = 15
BLIND_BUY_MULTI_OCCASION_BOOST = 20
BLIND_BUY_WINTER_PENALTY = -20

# Negative recommendation: penalty for owned/disliked products
OWNED_PRODUCT_PENALTY = -9999
DISLIKED_NOTE_PENALTY = -500

# Strength mismatch penalty (for "too strong" or "too weak" complaints)
WRONG_STRENGTH_PENALTY = -60

# Missing metadata penalty (discourage recommending products with no attribute data)
MISSING_METADATA_PENALTY = -30

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


def _normalize_for_exact_match(text: str) -> str:
    """Normalize text for exact comparison: lowercase, collapse spaces, remove punctuation."""
    text = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


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
    """Detect combo products using token intersection (no substring matching).

    Also checks the category field for 'combo' or 'gift' labels.
    """

    # Check category first (fast path)
    cat = _text(product.get("category"))
    if cat in ("combo", "gift", "gift set", "discovery"):
        return True

    tokens = _tokenize(_product_text(product))

    return bool(tokens & set(COMBO_WORDS))


def _matches_occasion(
    product: Mapping[str, Any],
    occasion: str | None,
) -> bool:
    """Check whether product data matches requested occasion."""
    if not occasion:
        return False
    attrs = get_product_attributes(product)
    best_time = _text(attrs.get("best_time") or "")
    occasion_list = attrs.get("occasion")
    if best_time and occasion.lower() in best_time:
        return True
    if occasion_list and isinstance(occasion_list, list):
        for o in occasion_list:
            if occasion.lower() == o.lower():
                return True
    return False


# Occasion-specific positive/negative keyword profiles
_OCCASION_PROFILES: dict[str, dict[str, set[str]]] = {
    "sport": {
        "boost": {"fresh", "clean", "aquatic", "marine", "citrus", "light", "aromatic", "green"},
        "penalize": {"sweet", "gourmand", "vanilla", "heavy", "strong", "oriental", "warm", "powdery"},
    },
    "gym": {
        "boost": {"fresh", "clean", "aquatic", "marine", "citrus", "light", "aromatic", "green"},
        "penalize": {"sweet", "gourmand", "vanilla", "heavy", "strong", "oriental", "warm", "powdery"},
    },
    "office": {
        "boost": {"fresh", "clean", "woody", "aromatic", "light", "citrus", "elegant", "soft", "professional", "subtle", "green", "aldehydic"},
        "penalize": {"heavy", "sweet", "gourmand", "strong", "beast", "loud", "club", "party", "oriental", "boozy", "animalic", "smoky", "incense"},
    },
    "daily": {
        "boost": {"fresh", "clean", "citrus", "light", "aromatic", "aquatic"},
        "penalize": {"heavy", "beast", "strong"},
    },
    "party": {
        "boost": {"sweet", "gourmand", "vanilla", "strong", "warm", "spicy", "oriental"},
        "penalize": {"light", "soft", "weak"},
    },
    "date": {
        "boost": {"sweet", "vanilla", "floral", "warm", "spicy", "attractive", "romantic", "compliment", "mass_appealing"},
        "penalize": {"heavy", "oud", "animalic", "leather"},
    },
    "wedding": {
        "boost": {"elegant", "floral", "sweet", "sophisticated", "luxury", "warm", "spicy"},
        "penalize": {"cheap", "weak", "light"},
    },
    "casual": {
        "boost": {"fresh", "clean", "light", "citrus", "aquatic", "aromatic"},
        "penalize": {"heavy", "strong", "beast"},
    },
}


def _occasion_specific_score(
    product: Mapping[str, Any],
    occasion: str | None,
) -> int:
    """Score product based on occasion-specific scent profiles.
    
    Rewards scents that are appropriate for the occasion.
    Penalizes scents that are inappropriate.
    """
    if not occasion:
        return 0
    profile = _OCCASION_PROFILES.get(occasion)
    if not profile:
        return 0
    attrs = get_product_attributes(product)
    scent_family = attrs.get("scent_family")
    if not scent_family or not isinstance(scent_family, list):
        return 0
    sf_text = " ".join(s.lower() for s in scent_family)
    score = 0
    for kw in profile["boost"]:
        if kw in sf_text:
            score += OCCASION_SCORE_BOOST
    for kw in profile["penalize"]:
        if kw in sf_text:
            score += OCCASION_SCORE_PENALTY
    return score


def _matches_scent(
    product: Mapping[str, Any],
    scent: str | None,
) -> bool:
    """Check whether product fragrance notes match requested scent profile.

    Matches against known scent-category keywords (e.g. 'floral' matches
    'rose', 'jasmine') so users can ask for 'floral perfume' and get
    products with floral notes. Also checks scent_family field.
    """
    if not scent:
        return False
    attrs = get_product_attributes(product)

    # Check scent_family field first
    scent_family = attrs.get("scent_family")
    if scent_family and isinstance(scent_family, list):
        for sf in scent_family:
            if scent.lower() == sf.lower():
                return True

    # Fallback to notes-based matching
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
    """Check whether product longevity/sillage data matches requested performance.
    
    Uses ONLY structured fragrance_details data. Never infers from description.
    """
    if not performance:
        return False
    attrs = get_product_attributes(product)

    # Check performance field first
    perf_list = attrs.get("performance")
    if perf_list and isinstance(perf_list, list):
        for p in perf_list:
            p_norm = p.lower().replace("-", "").replace("_", "").replace(" ", "")
            perf_norm = performance.lower().replace("-", "").replace("_", "").replace(" ", "")
            if perf_norm == p_norm or perf_norm in p_norm or p_norm in perf_norm:
                return True

    longevity = _text(attrs.get("longevity") or "")
    sillage = _text(attrs.get("sillage") or "")

    if performance == "longlasting":
        return bool(longevity)
    if performance == "strong":
        return any(kw in longevity or kw in sillage for kw in _STRONG_KW)
    if performance == "projection":
        return bool(sillage)
    if performance == "compliment":
        # Only match from structured data, never from description.
        return bool(perf_list)
    perf_text = f"{longevity} {sillage}"
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


def _description_performance_boost(product: Mapping[str, Any]) -> int:
    """Boost products whose structured data contains performance attributes."""
    attrs = get_product_attributes(product)
    if attrs.get("longevity") or attrs.get("sillage") or attrs.get("performance"):
        return PERFORMANCE_DESC_WEIGHT
    return 0


def _parse_hours(text: str) -> float:
    """Parse longevity/sillage text into numeric hours for sorting."""
    if not text:
        return 0.0
    text = text.lower().strip()
    # "6-8 hours" -> average of 6 and 8
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-to]+\s*(\d+(?:\.\d+)?)", text)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2.0
    # "8+ hours" or "8 hours"
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1))
    # Text-based ranking
    ranking = {
        "excellent": 10, "very good": 8, "good": 6,
        "moderate": 4, "weak": 2, "poor": 1,
    }
    for kw, val in ranking.items():
        if kw in text:
            return val
    return 5.0  # default middle value


def _sort_by_performance(
    products: list[dict[str, Any]],
    performance: str | None,
) -> list[dict[str, Any]]:
    """Reorder products by performance attribute (longevity, sillage, strength)."""
    if not performance:
        return products

    scored: list[tuple[float, int, dict[str, Any]]] = []
    for idx, p in enumerate(products):
        attrs = get_product_attributes(p)
        attr_text = ""
        score = 0.0
        if performance == "longlasting":
            attr_text = attrs.get("longevity") or ""
            score = _parse_hours(attr_text)
        elif performance == "projection":
            attr_text = attrs.get("sillage") or ""
            score = _parse_hours(attr_text)
        elif performance == "strong":
            lo = (attrs.get("longevity") or "").lower()
            si = (attrs.get("sillage") or "").lower()
            attr_text = f"{lo} {si}"
            strong_kws = {"strong", "powerful", "intense", "beast", "excellent"}
            score = sum(3.0 for kw in strong_kws if kw in attr_text)
            if not score:
                score = _parse_hours(attr_text) * 0.5
        scored.append((-score, idx, p))

    scored.sort(key=lambda x: (x[0], x[1]))
    return [p for _, _, p in scored]


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


def _matches_strength(
    product: Mapping[str, Any],
    strength: str | None,
) -> int:
    """Return penalty if product strength doesn't match user preference.

    Returns 0 if no preference or match, negative penalty for mismatch.
    """
    if not strength:
        return 0
    attrs = get_product_attributes(product)
    product_strength = attrs.get("strength") or None
    perf_list = attrs.get("performance")
    if perf_list and isinstance(perf_list, list):
        perf_text = " ".join(p.lower() for p in perf_list)
        if strength == "light":
            strong_kw = {"strong", "powerful", "intense", "beast"}
            if any(kw in perf_text for kw in strong_kw):
                return WRONG_STRENGTH_PENALTY
        elif strength == "strong":
            light_kw = {"light", "soft", "mild", "weak"}
            if any(kw in perf_text for kw in light_kw):
                return WRONG_STRENGTH_PENALTY
    if product_strength:
        ps = product_strength.lower().strip()
        if strength == "light" and ps in ("strong", "intense", "powerful"):
            return WRONG_STRENGTH_PENALTY
        if strength == "strong" and ps in ("light", "soft", "mild"):
            return WRONG_STRENGTH_PENALTY
    return 0


def _missing_metadata_penalty(product: Mapping[str, Any]) -> int:
    """Penalize products with data field but no usable fragrance attributes.

    Products without a data field at all are not penalized
    (they may be minimal test fixtures or legacy entries).
    """
    raw_data = product.get("data")
    if not raw_data:
        return 0
    attrs = get_product_attributes(product)
    has_data = any(v for v in attrs.values() if v)
    if not has_data:
        return MISSING_METADATA_PENALTY
    return 0


def _has_disliked_note(
    product: Mapping[str, Any],
    disliked_notes: list[str],
) -> bool:
    """Check if a product contains any note the user dislikes."""
    if not disliked_notes:
        return False
    attrs = get_product_attributes(product)
    all_notes = []
    for key in ("notes_top", "notes_middle", "notes_base"):
        notes = attrs.get(key)
        if notes:
            all_notes.extend(str(n).lower() for n in notes)
    scent_family = attrs.get("scent_family")
    if scent_family and isinstance(scent_family, list):
        all_notes.extend(s.lower() for s in scent_family)
    notes_text = " ".join(all_notes)
    for disliked in disliked_notes:
        if disliked.lower() in notes_text:
            return True
    return False


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
    compliment: bool = False,
    max_price_in_results: float = 1.0,
    already_recommended: bool = False,
    disliked_notes: list[str] | None = None,
    blind_buy: bool = False,
    strength: str | None = None,
    nuanced: Any = None,
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

    # Exact product name matching (with brand stripping)
    if product_name and query_text:
        query_words = query_text.split()

        if product_name == query_text:
            score += EXACT_NAME_WEIGHT
        elif len(query_words) > 1 and f" {query_text} " in f" {product_name} ":
            score += int(EXACT_NAME_WEIGHT * 0.8)

        # Normalized exact match: strip punctuation, collapse spaces
        norm_query = _normalize_for_exact_match(query_text)
        norm_pname = _normalize_for_exact_match(product_name)
        if norm_pname == norm_query:
            score += EXACT_NAME_WEIGHT

        # Combined name+brand match
        combined = f"{product_name} {product_brand}"
        norm_combined = _normalize_for_exact_match(combined)
        if norm_combined == norm_query:
            score += EXACT_NAME_WEIGHT

    # Brand match
    if brand and brand.lower() in product_brand:
        score += BRAND_WEIGHT

    # Category match
    if category and category.lower() in product_category:
        score += CATEGORY_WEIGHT

    # Gender match (token-based, using shared gender word constants)
    if gender:
        product_words = _tokenize(product_text)

        if gender == "male" and product_words & MALE_WORDS or gender == "female" and product_words & FEMALE_WORDS:
            score += GENDER_WEIGHT

    # Wrong gender penalty
    score += _gender_penalty(product_text, gender)

    # Budget
    if budget is not None:
        if _matches_budget(product, budget):
            score += BUDGET_WEIGHT
        else:
            score += OVER_BUDGET_PENALTY

    # Combo handling (token-based)
    is_combo = _is_combo_product(product)

    if combo_requested and is_combo:
        score += COMBO_MATCH_WEIGHT
    elif not combo_requested and is_combo:
        penalty = LUXURY_COMBO_PENALTY if luxury else UNREQUESTED_COMBO_PENALTY
        score += penalty

    # Metadata-based matching (boost if actual metadata exists)
    if _matches_occasion(product, occasion):
        score += OCCASION_WEIGHT
    # Occasion-specific scent profiling (boost/penalize based on occasion-appropriate scents)
    if occasion:
        score += _occasion_specific_score(product, occasion)
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

    # Compliment intent: boost premium brands + products with performance data
    if compliment:
        product_brand_lower = _text(product.get("brand"))
        for brand_name in PREMIUM_BRANDS:
            if brand_name in product_brand_lower:
                score += COMPLIMENT_PREMIUM_BOOST
                break
        attrs = get_product_attributes(product)
        if attrs.get("performance") or attrs.get("longevity") or attrs.get("sillage"):
            score += COMPLIMENT_PERFORMANCE_BOOST
        score += _premium_brand_boost(product, True)

    # Popularity boost (only from structured data, never from description)
    attrs = get_product_attributes(product)
    if attrs.get("authenticity") or _matches_performance(product, "compliment"):
        score += POPULARITY_WEIGHT

    # ---- New scoring features ----

    # Diversity penalty: penalize already-recommended products
    if already_recommended:
        score += ALREADY_RECOMMENDED_PENALTY

    # Negative recommendation: penalize owned products
    product_id = product.get("id", "")
    if already_recommended and product_id:
        # Heavy penalty for anything the user already owns or was told about
        score += OWNED_PRODUCT_PENALTY

    # Negative recommendation: penalize disliked notes
    if disliked_notes and _has_disliked_note(product, disliked_notes):
            score += DISLIKED_NOTE_PENALTY

    # Blind-buy mode: boost versatile, mass-appealing products
    if blind_buy:
        attrs = get_product_attributes(product)
        scent_family = attrs.get("scent_family")

        # Boost versatile scent profiles (fresh, clean, aquatic — safe for most people)
        if scent_family and isinstance(scent_family, list):
            sf_text = " ".join(s.lower() for s in scent_family)
            versatile_keywords = {"fresh", "clean", "citrus", "aquatic", "aromatic"}
            if any(kw in sf_text for kw in versatile_keywords):
                score += BLIND_BUY_VERSATILITY_BOOST

        # Boost products with multiple occasions (versatile)
        occasion_list = attrs.get("occasion")
        if occasion_list and isinstance(occasion_list, list) and len(occasion_list) >= 2:
            score += BLIND_BUY_MULTI_OCCASION_BOOST

        # Boost premium brands (safer blind buys — better quality reputation)
        product_brand = _text(product.get("brand"))
        if any(brand in product_brand for brand in PREMIUM_BRANDS):
            score += BLIND_BUY_PREMIUM_BOOST

        # Boost mid-range priced products (safer blind buys — not too cheap, not too expensive)
        try:
            price = float(product.get("price", 0))
        except (TypeError, ValueError):
            price = 0
        if 1000 <= price <= 3000:
            score += BLIND_BUY_MASS_APPEAL_BOOST

        # Penalize heavy winter-oriented scents (not ideal for year-round use in Bangladesh)
        if scent_family and isinstance(scent_family, list):
            sf_text = " ".join(s.lower() for s in scent_family)
            winter_keywords = {"gourmand", "heavy", "oud", "animalic", "leather", "smoky", "incense"}
            if any(kw in sf_text for kw in winter_keywords):
                score += BLIND_BUY_WINTER_PENALTY

    # Strength preference matching
    if strength:
        score += _matches_strength(product, strength)

    # Missing metadata penalty
    score += _missing_metadata_penalty(product)

    # Nuanced request scoring
    if nuanced is not None and hasattr(nuanced, "is_empty") and not nuanced.is_empty():
        score = _apply_nuanced_scoring(product, score, nuanced)

    # Field-aware keyword relevance
    score += _keyword_score(product, tokens)

    return score


def _apply_nuanced_scoring(
    product: Mapping[str, Any],
    score: int,
    nuanced: Any,
) -> int:
    """Apply nuanced request weights to product score (mutates score in-place)."""
    # Use a local reference since we're modifying the outer scope via return
    # Actually we return score, so let's just calculate an extra
    extra = 0
    attrs = get_product_attributes(product)
    scent_family = attrs.get("scent_family")
    sf_text = " ".join(s.lower() for s in scent_family) if scent_family and isinstance(scent_family, list) else ""

    # Sweetness
    if nuanced.sweetness > 0 and ("sweet" in sf_text or "gourmand" in sf_text or "vanilla" in sf_text):
            extra += int(15 * nuanced.sweetness)

    # Freshness
    if nuanced.freshness > 0:
        fresh_keywords = {"fresh", "aquatic", "marine", "citrus", "aromatic", "green"}
        if any(kw in sf_text for kw in fresh_keywords):
            extra += int(15 * nuanced.freshness)

    # Low citrus
    if nuanced.citrus <= 0.3 and nuanced.citrus > 0 and "citrus" not in sf_text:
            extra += 10

    # Masculinity
    if nuanced.masculinity > 0:
        cat = _text(product.get("category"))
        if nuanced.masculinity > 0.7:
            if "men" in cat or "male" in cat:
                extra += 15
        elif "unisex" in cat or "women" in cat:
            extra += 10

    # Elegance
    if nuanced.elegance > 0.5:
        elegant_keywords = {"floral", "powdery", "aldehydic", "iris", "violet"}
        if any(kw in sf_text for kw in elegant_keywords):
            extra += 15
        product_brand = _text(product.get("brand"))
        for brand in PREMIUM_BRANDS:
            if brand in product_brand:
                extra += 10

    # Luxury/expensive smelling
    if nuanced.luxury_level > 0.5:
        product_brand = _text(product.get("brand"))
        for brand in PREMIUM_BRANDS:
            if brand in product_brand:
                extra += int(LUXURY_WEIGHT * nuanced.luxury_level)

    # Versatility
    if nuanced.versatility > 0.5:
        versatile_keywords = {"fresh", "clean", "citrus", "aromatic", "aquatic", "light"}
        if any(kw in sf_text for kw in versatile_keywords):
            extra += 15

    # Compliment factor
    if nuanced.compliment_factor > 0.5 and (attrs.get("performance") or attrs.get("longevity") or attrs.get("sillage")):
            extra += 20

    # Price perception - "expensive smelling"
    if nuanced.price_perception == "expensive":
        product_brand = _text(product.get("brand"))
        for brand in PREMIUM_BRANDS:
            if brand in product_brand:
                extra += 25
        try:
            price = float(product.get("price", 0))
            if price >= 2000:
                extra += 15
        except (TypeError, ValueError):
            pass

    return score + extra


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
    compliment: bool = False,
    already_recommended_ids: set[str] | None = None,
    disliked_notes: list[str] | None = None,
    blind_buy: bool = False,
    strength: str | None = None,
    nuanced: Any = None,
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
    compliment = (
        compliment
        if compliment is not None
        else __import__("app.filters", fromlist=["detect_compliment"]).detect_compliment(query)
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
        product_id = str(product.get("id", ""))
        already_rec = already_recommended_ids is not None and product_id in already_recommended_ids
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
            compliment=compliment,
            max_price_in_results=max_price_in_results,
            already_recommended=already_rec,
            disliked_notes=disliked_notes,
            blind_buy=blind_buy,
            strength=strength,
            nuanced=nuanced,
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

    ranked = [dict(product) for _, _, product in scored[:max_results]]

    # Performance-based re-sort: when user asks for longest lasting, strongest,
    # or best projection, reorder by the actual attribute value.
    if performance:
        ranked = _sort_by_performance(ranked, performance)

    return ranked
