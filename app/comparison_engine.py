"""Comparison engine for perfume products.

Stores comparison state (left_product, right_product, comparison_history),
produces detailed structured comparison output, and handles follow-up
ranking intents via recommendation scoring (not keyword search).
"""

from __future__ import annotations

import re
from typing import Any

from app.product_attrs import get_product_attributes

# Ranking criteria weights for scoring
LONGEVITY_WEIGHT = 50
PROJECTION_WEIGHT = 40
RICHNESS_WEIGHT = 30
LUXURY_WEIGHT = 50
COMPLIMENTS_WEIGHT = 30
BLIND_BUY_WEIGHT = 40
VALUE_WEIGHT = 25
VERSATILITY_WEIGHT = 35

PREMIUM_BRANDS: set[str] = {
    "dior", "tom ford", "tomford", "gucci", "prada", "versace",
    "armani", "giorgio armani", "burberry", "carolina herrera",
    "chanel", "ysl", "yves saint laurent", "louis vuitton",
    "dolce & gabbana", "bvlgari", "bulgari", "paco rabanne",
    "hugo boss", "calvin klein", "givenchy", "valentino",
    "lacoste", "montblanc", "hermes", "jo malone", "mugler",
    "mancera", "montale", "parfums de marly", "creed",
    "initio", "amouage", "roja", "byredo", "le labo",
    "diptyque", "kilian", "lattafa", "armaf", "rasasi",
    "afnan", "maison francis kurkdjian",
}


def _text(value: Any) -> str:
    return str(value or "").lower().strip()


def _extract_size_prices(product: dict[str, Any]) -> list[tuple[str, float]]:
    try:
        import json
        raw = product.get("data")
        data = json.loads(raw) if isinstance(raw, str) else (raw or {})
        variants = data.get("variants") or []
        size_prices = []
        for v in variants:
            size = str(v.get("size", "")).strip()
            try:
                price = float(v.get("price", 0))
            except (TypeError, ValueError):
                continue
            if size and price > 0:
                size_prices.append((size, price))
        return size_prices
    except (ValueError, TypeError, AttributeError):
        return []


def _parse_longevity_score(product: dict[str, Any]) -> float:
    attrs = get_product_attributes(product)
    lo = _text(attrs.get("longevity") or "")
    if not lo:
        return 5.0
    m = re.search(r"(\d+)\s*[-to]+\s*(\d+)", lo)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2.0
    m = re.search(r"(\d+(?:\.\d+)?)", lo)
    if m:
        return float(m.group(1))
    ranking = {"excellent": 10, "very good": 8, "good": 6, "moderate": 4, "weak": 2}
    for kw, val in ranking.items():
        if kw in lo:
            return val
    return 5.0


def _parse_sillage_score(product: dict[str, Any]) -> float:
    attrs = get_product_attributes(product)
    si = _text(attrs.get("sillage") or "")
    if not si:
        return 5.0
    m = re.search(r"(\d+)\s*[-to]+\s*(\d+)", si)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2.0
    m = re.search(r"(\d+(?:\.\d+)?)", si)
    if m:
        return float(m.group(1))
    ranking = {"excellent": 10, "very good": 8, "good": 6, "moderate": 4, "weak": 2, "poor": 1}
    for kw, val in ranking.items():
        if kw in si:
            return val
    return 5.0


def _is_premium_brand(product: dict[str, Any]) -> bool:
    brand = _text(product.get("brand"))
    return any(pb in brand for pb in PREMIUM_BRANDS)


def _get_scent_family(product: dict[str, Any]) -> str:
    attrs = get_product_attributes(product)
    sf = attrs.get("scent_family")
    if sf and isinstance(sf, list):
        return ", ".join(sf)
    return "N/A"


def _get_occasion(product: dict[str, Any]) -> str:
    attrs = get_product_attributes(product)
    oc = attrs.get("occasion")
    if oc and isinstance(oc, list):
        return ", ".join(oc)
    return "N/A"


def _get_performance_tags(product: dict[str, Any]) -> str:
    attrs = get_product_attributes(product)
    pf = attrs.get("performance")
    if pf and isinstance(pf, list):
        return ", ".join(pf)
    return "N/A"


def _get_longevity_text(product: dict[str, Any]) -> str:
    attrs = get_product_attributes(product)
    lo = attrs.get("longevity")
    return lo or "N/A"


def _get_projection_text(product: dict[str, Any]) -> str:
    attrs = get_product_attributes(product)
    si = attrs.get("sillage")
    return si or "N/A"


def _get_type(product: dict[str, Any]) -> str:
    attrs = get_product_attributes(product)
    t = attrs.get("type")
    return t or "EDP (assumed)"


def _get_variants_text(product: dict[str, Any]) -> str:
    sp = _extract_size_prices(product)
    if sp:
        return ", ".join(f"{s} (৳{int(p)})" for s, p in sp)
    price = product.get("price")
    return f"৳{price}" if price else "N/A"


def _get_price_range(product: dict[str, Any]) -> str:
    sp = _extract_size_prices(product)
    if sp:
        prices = [p for _, p in sp]
        return f"৳{int(min(prices))} - ৳{int(max(prices))}"
    price = product.get("price")
    return f"৳{price}" if price else "N/A"


def _get_notes_text(product: dict[str, Any]) -> str:
    attrs = get_product_attributes(product)
    parts = []
    for label, key in [("Top", "notes_top"), ("Middle", "notes_middle"), ("Base", "notes_base")]:
        notes = attrs.get(key)
        if notes and isinstance(notes, list) and notes:
            parts.append(f"{label}: {', '.join(notes)}")
    return " | ".join(parts) if parts else "N/A"


def _score_compliments(product: dict[str, Any]) -> float:
    score = 0.0
    attrs = get_product_attributes(product)
    if attrs.get("performance"):
        score += 10
    if attrs.get("longevity"):
        score += 10
    if attrs.get("sillage"):
        score += 10
    scent_family = attrs.get("scent_family")
    if scent_family and isinstance(scent_family, list):
        popular_keywords = {"sweet", "fresh", "vanilla", "floral"}
        sf_text = " ".join(s.lower() for s in scent_family)
        for kw in popular_keywords:
            if kw in sf_text:
                score += 5
    if _is_premium_brand(product):
        score += 10
    return score


def _score_richness(product: dict[str, Any]) -> float:
    score = 0.0
    attrs = get_product_attributes(product)
    scent_family = attrs.get("scent_family")
    if scent_family and isinstance(scent_family, list):
        rich_keywords = {"sweet", "vanilla", "woody", "amber", "oriental", "gourmand", "spicy", "warm"}
        sf_text = " ".join(s.lower() for s in scent_family)
        for kw in rich_keywords:
            if kw in sf_text:
                score += 10
        score += len(scent_family) * 5
    notes_count = 0
    for key in ("notes_top", "notes_middle", "notes_base"):
        notes = attrs.get(key)
        if notes and isinstance(notes, list):
            notes_count += len(notes)
    score += notes_count * 2
    if _is_premium_brand(product):
        score += 15
    return score


def _score_luxury(product: dict[str, Any]) -> float:
    score = 0.0
    if _is_premium_brand(product):
        score += 40
    try:
        price = float(product.get("price", 0))
        if price >= 3000:
            score += 30
        elif price >= 2000:
            score += 15
        elif price >= 1000:
            score += 5
    except (TypeError, ValueError):
        pass
    return score


def _score_blind_buy(product: dict[str, Any]) -> float:
    score = 0.0
    attrs = get_product_attributes(product)
    scent_family = attrs.get("scent_family")
    if scent_family and isinstance(scent_family, list):
        sf_text = " ".join(s.lower() for s in scent_family)
        safe_keywords = {"fresh", "clean", "citrus", "aquatic", "aromatic", "light"}
        for kw in safe_keywords:
            if kw in sf_text:
                score += 10
        polarizing_keywords = {"oud", "animalic", "leather", "smoky", "incense"}
        for kw in polarizing_keywords:
            if kw in sf_text:
                score -= 20
    try:
        price = float(product.get("price", 0))
        if 1000 <= price <= 2500:
            score += 20
        elif price < 1000:
            score += 10
    except (TypeError, ValueError):
        pass
    if _is_premium_brand(product):
        score += 10
    return score


def _score_value(product: dict[str, Any]) -> float:
    score = 0.0
    try:
        price = float(product.get("price", 0))
        if price <= 1000:
            score += 30
        elif price <= 2000:
            score += 20
        elif price <= 3000:
            score += 10
    except (TypeError, ValueError):
        pass
    sp = _extract_size_prices(product)
    if len(sp) >= 4:
        score += 10
    if _get_performance_tags(product) != "N/A":
        score += 10
    return score


def _score_versatility(product: dict[str, Any]) -> float:
    score = 0.0
    attrs = get_product_attributes(product)
    scent_family = attrs.get("scent_family")
    if scent_family and isinstance(scent_family, list):
        sf_text = " ".join(s.lower() for s in scent_family)
        versatile = {"fresh", "clean", "citrus", "aquatic", "aromatic", "light", "woody"}
        for kw in versatile:
            if kw in sf_text:
                score += 10
    occasion = attrs.get("occasion")
    if occasion and isinstance(occasion, list):
        score += len(occasion) * 8
    return score


def _score_projection(product: dict[str, Any]) -> float:
    return _parse_sillage_score(product)


def _score_longevity(product: dict[str, Any]) -> float:
    return _parse_longevity_score(product)


def _score_overall(product: dict[str, Any]) -> float:
    return (
        _parse_longevity_score(product)
        + _parse_sillage_score(product)
        + _score_richness(product)
        + _score_luxury(product)
        + _score_compliments(product)
        + _score_blind_buy(product)
        + _score_value(product)
    )


_SCORING_FUNCTIONS: dict[str, tuple[Any, str]] = {
    "longevity": (_score_longevity, "Longevity Score"),
    "projection": (_score_projection, "Projection Score"),
    "richness": (_score_richness, "Richness Score"),
    "luxury": (_score_luxury, "Luxury Score"),
    "compliments": (_score_compliments, "Compliment Score"),
    "blind_buy": (_score_blind_buy, "Blind Buy Score"),
    "value": (_score_value, "Value Score"),
    "versatility": (_score_versatility, "Versatility Score"),
    "overall": (_score_overall, "Overall Score"),
}


class ComparisonState:
    """Stores the active comparison between two products."""

    def __init__(self):
        self.left_product: dict[str, Any] | None = None
        self.right_product: dict[str, Any] | None = None
        self.history: list[dict[str, Any]] = []

    def set_products(self, left: dict[str, Any] | None, right: dict[str, Any] | None):
        self.left_product = left
        self.right_product = right
        if left and right:
            self.history.append({"left": left, "right": right, "left_name": left.get("name"), "right_name": right.get("name")})
            self.history = self.history[-10:]

    def clear(self):
        self.left_product = None
        self.right_product = None

    def has_comparison(self) -> bool:
        return self.left_product is not None and self.right_product is not None

    def get_both_products(self) -> list[dict[str, Any]]:
        result = []
        if self.left_product:
            result.append(self.left_product)
        if self.right_product:
            result.append(self.right_product)
        return result


# Singleton instance for the app
_comparison_state = ComparisonState()


def get_comparison_state() -> ComparisonState:
    return _comparison_state


def build_comparison_output(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Build a detailed structured comparison output between two products."""
    l_name = left.get("name", "Product A")
    r_name = right.get("name", "Product B")
    l_brand = left.get("brand", "N/A")
    r_brand = right.get("brand", "N/A")

    lines = []
    lines.append("=" * 60)
    lines.append(f"  COMPARISON: {l_name}  vs  {r_name}")
    lines.append("=" * 60)

    sections = [
        ("Overview", [
            ("Brand", l_brand, r_brand),
            ("Category", left.get("category", "N/A"), right.get("category", "N/A")),
            ("Type", _get_type(left), _get_type(right)),
        ]),
        ("Notes", [
            ("Notes", _get_notes_text(left), _get_notes_text(right)),
            ("Scent Family", _get_scent_family(left), _get_scent_family(right)),
        ]),
        ("Performance", [
            ("Longevity", _get_longevity_text(left), _get_longevity_text(right)),
            ("Projection/Sillage", _get_projection_text(left), _get_projection_text(right)),
            ("Performance Tags", _get_performance_tags(left), _get_performance_tags(right)),
        ]),
        ("Season & Occasion", [
            ("Season", _get_longevity_text(left), _get_longevity_text(right)),
            ("Occasion", _get_occasion(left), _get_occasion(right)),
        ]),
        ("Price & Sizes", [
            ("Price Range", _get_price_range(left), _get_price_range(right)),
            ("Available Sizes", _get_variants_text(left), _get_variants_text(right)),
        ]),
    ]

    for section_title, rows in sections:
        lines.append("")
        lines.append(f"  [{section_title}]")
        lines.append(f"  {'Feature':<25} {l_name:<30} {r_name:<30}")
        lines.append(f"  {'-'*25} {'-'*30} {'-'*30}")
        for feat, lval, rval in rows:
            l_short = str(lval)[:28] if lval else "N/A"
            r_short = str(rval)[:28] if rval else "N/A"
            lines.append(f"  {feat:<25} {l_short:<30} {r_short:<30}")

    return "\n".join(lines)


def build_verdict(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Build the verdict/best-for section of the comparison."""
    lines = []
    lines.append("")
    lines.append("-" * 60)
    lines.append("  VERDICT")
    lines.append("-" * 60)

    # Determine winners for each category
    longevity_l = _parse_longevity_score(left)
    longevity_r = _parse_longevity_score(right)
    proj_l = _parse_sillage_score(left)
    proj_r = _parse_sillage_score(right)
    richness_l = _score_richness(left)
    richness_r = _score_richness(right)
    luxury_l = _score_luxury(left)
    luxury_r = _score_luxury(right)
    value_l = _score_value(left)
    value_r = _score_value(right)
    blind_l = _score_blind_buy(left)
    blind_r = _score_blind_buy(right)

    def winner(l_score, r_score, l_name, r_name, label):
        if l_score > r_score:
            return f"  {label}: {l_name}"
        elif r_score > l_score:
            return f"  {label}: {r_name}"
        else:
            return f"  {label}: Tie"

    def highlight(l_score, r_score, l_name, r_name, label):
        if l_score > r_score:
            return f"  Best {label}: {l_name}"
        elif r_score > l_score:
            return f"  Best {label}: {r_name}"
        else:
            return f"  Best {label}: Tie"

    lines.append(highlight(longevity_l, longevity_r, left.get("name"), right.get("name"), "Longevity"))
    lines.append(highlight(proj_l, proj_r, left.get("name"), right.get("name"), "Projection"))
    lines.append(highlight(richness_l, richness_r, left.get("name"), right.get("name"), "Richness"))
    lines.append(highlight(luxury_l, luxury_r, left.get("name"), right.get("name"), "Luxury"))
    lines.append(highlight(blind_l, blind_r, left.get("name"), right.get("name"), "Blind Buy"))
    lines.append(highlight(value_l, value_r, left.get("name"), right.get("name"), "Value"))

    total_l = longevity_l + proj_l + richness_l + luxury_l + value_l
    total_r = longevity_r + proj_r + richness_r + luxury_r + value_r

    lines.append("")
    if total_l > total_r:
        lines.append(f"  Overall Winner: {left.get('name')}")
    elif total_r > total_l:
        lines.append(f"  Overall Winner: {right.get('name')}")
    else:
        lines.append("  Overall Winner: Tie")

    return "\n".join(lines)


def build_full_comparison(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Build the complete comparison output including verdict."""
    return build_comparison_output(left, right) + "\n" + build_verdict(left, right)


def score_product_for_criteria(product: dict[str, Any], criteria: str) -> float:
    """Score a product for a specific ranking criteria.
    
    This is recommendation SCORING, not keyword search.
    """
    if criteria in _SCORING_FUNCTIONS:
        fn, _ = _SCORING_FUNCTIONS[criteria]
        return fn(product)
    return 0.0


def rank_for_criteria(
    products: list[dict[str, Any]],
    criteria: str,
) -> list[tuple[float, dict[str, Any]]]:
    """Rank products by a scoring criteria. Returns list of (score, product) tuples sorted descending."""
    scored = [(score_product_for_criteria(p, criteria), p) for p in products]
    scored.sort(key=lambda x: -x[0])
    return scored


def pick_best_for_criteria(
    products: list[dict[str, Any]],
    criteria: str,
) -> dict[str, Any] | None:
    """Pick the best product for a given criteria."""
    ranked = rank_for_criteria(products, criteria)
    if ranked:
        return ranked[0][1]
    return None


def answer_ranking_query(
    query: str,
    left: dict[str, Any],
    right: dict[str, Any],
) -> str | None:
    """Answer a follow-up ranking question using stored comparison state."""
    from app.aliases import get_ranking_criteria

    criteria = get_ranking_criteria(query)
    if not criteria:
        return None

    l_score = score_product_for_criteria(left, criteria)
    r_score = score_product_for_criteria(right, criteria)

    l_name = left.get("name", "Product A")
    r_name = right.get("name", "Product B")

    _, label = _SCORING_FUNCTIONS.get(criteria, (None, "Score"))

    if l_score > r_score:
        return (
            f"Based on {label.lower()}, **{l_name}** wins!\n"
            f"  {l_name}: {l_score:.1f}\n"
            f"  {r_name}: {r_score:.1f}"
        )
    elif r_score > l_score:
        return (
            f"Based on {label.lower()}, **{r_name}** wins!\n"
            f"  {r_name}: {r_score:.1f}\n"
            f"  {l_name}: {l_score:.1f}"
        )
    else:
        return (
            f"Both are tied on {label.lower()} ({l_score:.1f} each). "
            f"It's a matter of personal preference!"
        )