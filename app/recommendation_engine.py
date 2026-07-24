"""Recommendation engine for perfume products.

Reuses the existing ranking.py scoring system rather than duplicating
scoring logic. Supports intent-based recommendations:
- best, luxury, gender, budget, occasion, season, style, gift

Always returns ranking_reason alongside products so the AI can explain
why each product was recommended.
"""

from __future__ import annotations

import logging
from typing import Any

from app.filters import (
    detect_gender,
    detect_occasion,
    detect_scent,
    detect_season,
    extract_budget,
)
from app.intent import Intent
from app.product_attrs import get_product_attributes
from app.ranking import rank_products

logger = logging.getLogger(__name__)


def _text(value: Any) -> str:
    return str(value or "").lower().strip()


def _get_product_origin(product: dict[str, Any]) -> str:
    """Get product origin safely - never hallucinate.

    Returns 'original', 'inspired', or 'unknown'.
    """
    attrs = get_product_attributes(product)
    origin = attrs.get("product_origin")
    if origin and isinstance(origin, str):
        o = origin.strip().lower()
        if o in ("original", "inspired", "unknown"):
            return o
    return "unknown"


def _get_season(product: dict[str, Any]) -> str | None:
    """Get season info from product attributes."""
    attrs = get_product_attributes(product)
    season = attrs.get("season")
    if season and isinstance(season, list) and season:
        return season[0].lower()
    # fallback to best_time for backward compatibility
    best_time = _text(attrs.get("best_time") or "")
    if best_time:
        if any(w in best_time for w in ("summer", "spring", "hot")):
            return "summer"
        if any(w in best_time for w in ("winter", "cold", "fall", "autumn")):
            return "winter"
    return None


def _get_occasion(product: dict[str, Any]) -> list[str]:
    """Get occasion tags from product attributes."""
    attrs = get_product_attributes(product)
    occasion = attrs.get("occasion")
    if occasion and isinstance(occasion, list):
        return [o.lower() for o in occasion if o]
    return []


def _get_style(product: dict[str, Any]) -> list[str]:
    """Get style/scent family from product attributes."""
    attrs = get_product_attributes(product)
    scent_family = attrs.get("scent_family")
    if scent_family and isinstance(scent_family, list):
        return [s.lower() for s in scent_family if s]
    return []


def _get_performance(product: dict[str, Any]) -> list[str]:
    """Get performance tags from product attributes."""
    attrs = get_product_attributes(product)
    perf = attrs.get("performance")
    if perf and isinstance(perf, list):
        return [p.lower() for p in perf if p]
    return []


def _build_reason(
    product: dict[str, Any],
    score: int,
    intent: Intent,
    criteria: dict[str, Any] | None = None,
) -> str:
    """Build a human-readable ranking reason for a product.

    Only uses attributes that actually exist in the database.
    Never hallucinates.
    """
    name = product.get("name", "Unknown")
    brand = product.get("brand", "")
    price = product.get("price", 0)

    reasons = []

    # Intent-specific explanations
    if intent == Intent.BEST_RECOMMENDATION:
        try:
            p = int(price)
            reasons.append(f"highly rated option at ৳{p}")
        except (TypeError, ValueError):
            reasons.append("highly rated option")

    elif intent == Intent.LUXURY_RECOMMENDATION:
        if brand and any(pb in _text(brand) for pb in _PREMIUM_BRANDS):
            reasons.append(f"premium {brand} brand")
        try:
            p = int(price)
            if p >= 2000:
                reasons.append(f"luxury tier at ৳{p}")
        except (TypeError, ValueError):
            pass

    elif intent == Intent.BUDGET_RECOMMENDATION:
        try:
            p = int(price)
            reasons.append(f"great value at ৳{p}")
        except (TypeError, ValueError):
            reasons.append("great value")

    elif intent == Intent.GENDER_FILTER:
        gender = criteria.get("gender", "") if criteria else ""
        if gender:
            reasons.append(f"for {gender}")
        else:
            cat = product.get("category", "")
            reasons.append(f"{cat} category")

    elif intent == Intent.OCCASION_RECOMMENDATION:
        occ = criteria.get("occasion", "") if criteria else ""
        if occ:
            occasion_labels = {
                "office": "office friendly",
                "professional": "office friendly",
                "university": "clean and affordable for university",
                "gym": "fresh and light for gym",
                "party": "memorable for parties",
                "club": "memorable for parties",
                "date": "compliment-getting for date night",
                "wedding": "special occasion wear",
                "daily": "versatile daily wear",
                "casual": "casual everyday",
                "formal": "elegant formal",
            }
            label = occasion_labels.get(occ.lower(), f"great for {occ}")
            reasons.append(label)
        else:
            reasons.append("versatile choice")

    elif intent == Intent.SEASON_RECOMMENDATION:
        season = criteria.get("season", "") if criteria else ""
        if season:
            reasons.append(f"ideal for {season}")
        else:
            reasons.append("seasonal choice")

    elif intent == Intent.STYLE_RECOMMENDATION:
        style = criteria.get("style", "") if criteria else ""
        if style:
            reasons.append(f"{style} scent profile")
        else:
            reasons.append("great scent profile")

    elif intent == Intent.GIFT_RECOMMENDATION:
        if brand and any(pb in _text(brand) for pb in _PREMIUM_BRANDS):
            reasons.append(f"prestige {brand} gift")
        else:
            reasons.append("great gift option")

    # Attribute-based reasons (only if data exists)
    attrs = get_product_attributes(product)
    sf = attrs.get("scent_family")
    if sf and isinstance(sf, list) and sf:
        reasons.append(f"scent: {', '.join(sf[:3])}")

    perf = attrs.get("performance")
    if perf and isinstance(perf, list) and perf:
        tags = [p for p in perf if p]
        if tags:
            reasons.append(f"performance: {', '.join(tags[:2])}")

    lo = attrs.get("longevity")
    if lo:
        reasons.append(f"longevity: {lo}")

    si = attrs.get("sillage")
    if si:
        reasons.append(f"projection: {si}")

    # Occasion-specific benefits based on actual metadata
    occ = attrs.get("occasion")
    if occ and isinstance(occ, list):
        occ_labels = ', '.join(occ[:2])
        if occ_labels:
            reasons.append(f"good for {occ_labels}")

    # Price-based reasons
    try:
        p = float(price)
        budget = criteria.get("budget") if criteria else None
        if budget and p <= budget:
            reasons.append("within budget")
        if p <= 1000:
            reasons.append("great value")
    except (TypeError, ValueError):
        pass

    # Authenticity-based reasons
    origin = attrs.get("product_origin")
    if origin and isinstance(origin, str):
        o = origin.strip().lower()
        if o == "original":
            reasons.append("original product")
        elif o == "inspired":
            reasons.append("inspired version")

    # Build final reason string
    if reasons:
        reasons_text = "; ".join(reasons)
        return f"{name}: {reasons_text}."
    return f"{name}: recommended pick."


# Shared reference to premium brands from ranking.py
_PREMIUM_BRANDS: set[str] = {
    "dior", "tom ford", "tomford", "gucci", "prada", "versace",
    "armani", "giorgio armani", "burberry", "carolina herrera",
    "chanel", "ysl", "yves saint laurent", "louis vuitton",
    "dolce & gabbana", "bvlgari", "bulgari", "paco rabanne",
    "hugo boss", "calvin klein", "givenchy", "valentino",
    "lacoste", "montblanc", "hermes", "jo malone", "mugler",
    "mancera", "montale", "parfums de marly", "creed",
    "initio", "amouage", "roja", "byredo", "le labo",
    "diptyque", "kilian",
}


class RecommendationEngine:
    """Handles recommendation queries using existing ranking system.

    Does NOT call SearchService. Receives pre-fetched products.
    """

    def recommend(
        self,
        products: list[dict[str, Any]],
        query: str,
        intent: Intent,
        *,
        max_results: int = 10,
        user_id: str = "cli",
    ) -> list[dict[str, Any]]:
        """Rank products by intent and return with ranking_reason.

        Uses rank_products() from ranking.py for scoring.
        """
        if not products:
            return []

        criteria: dict[str, Any] = {}

        # Extract filters from query
        gender = detect_gender(query)
        if gender:
            criteria["gender"] = gender

        budget = extract_budget(query)
        if budget:
            criteria["budget"] = budget

        occasion = detect_occasion(query)
        if occasion:
            criteria["occasion"] = occasion

        scent = detect_scent(query)
        if scent:
            criteria["style"] = scent

        season = detect_season(query)
        if season:
            criteria["season"] = season

        # Merge accumulated preferences from state
        from app.preferences import PreferenceExtractor, get_preferences
        prefs = get_preferences(user_id)
        strength = prefs.strength_pref or PreferenceExtractor.extract_strength(query)

        # Use accumulated budget if no explicit budget in query
        acc_budget = extract_budget(query)
        if acc_budget is None and prefs.budget is not None and ("budget" not in criteria or criteria.get("budget") is None):
            criteria["budget"] = prefs.budget

        # Build disliked_notes from preferences
        disliked_notes = list(prefs.disliked_notes) if prefs.disliked_notes else None

        # Build already_recommended_ids
        already_rec = set(prefs.recommended_product_ids) if prefs.recommended_product_ids else None

        # Owned product names for post-ranking filtering
        owned_names = [n.lower().strip() for n in prefs.owned_perfumes] if prefs.owned_perfumes else []

        # Map intent to ranking.py parameters
        recommendation = intent == Intent.BEST_RECOMMENDATION
        luxury = intent == Intent.LUXURY_RECOMMENDATION
        gift = intent in (Intent.GIFT_RECOMMENDATION, Intent.GIFT)
        cheap_intent = intent == Intent.BUDGET_RECOMMENDATION
        blind_buy = intent == Intent.BLIND_BUY or prefs.blind_buy_mode

        # Use accumulated preferences as fallbacks for any filter not in the current query
        acc_gender = criteria.get("gender") or prefs.gender
        acc_occasion = criteria.get("occasion") or prefs.occasion
        acc_season = criteria.get("season") or prefs.weather
        acc_style = criteria.get("style") or prefs.style

        # Pass accumulated budget if not explicitly in query
        if criteria.get("budget") is None and prefs.budget is not None:
            criteria["budget"] = prefs.budget

        ranked = rank_products(
            products,
            query,
            gender=acc_gender,
            budget=criteria.get("budget"),
            occasion=acc_occasion,
            scent=acc_style,
            season=acc_season,
            recommendation=recommendation,
            luxury=luxury,
            gift=gift,
            cheap_intent=cheap_intent,
            blind_buy=blind_buy,
            max_results=max_results,
            strength=strength,
            disliked_notes=disliked_notes,
            already_recommended_ids=already_rec,
        )

        # Hard budget filter: remove over-budget products regardless of score
        budget = criteria.get("budget")
        if budget is not None:
            ranked = [
                p for p in ranked
                if float(p.get("price", 0)) <= budget
            ]

        # Attach ranking reason to each product
        result = []
        for idx, product in enumerate(ranked):
            # Skip owned products (name match)
            if owned_names:
                pname = _text(product.get("name"))
                if pname and any(owned in pname or pname in owned for owned in owned_names):
                    continue
            # Calculate a simple score for reason generation
            score = max_results - idx
            reason = _build_reason(product, score, intent, criteria)
            product_copy = dict(product)
            product_copy["ranking_reason"] = reason
            result.append(product_copy)

        return result

    def get_recommendation_type(self, intent: Intent) -> str:
        """Return a display label for the recommendation type."""
        display_names = {
            Intent.BEST_RECOMMENDATION: "Top Picks",
            Intent.LUXURY_RECOMMENDATION: "Luxury Selection",
            Intent.GENDER_FILTER: "Gender Filter",
            Intent.BUDGET_RECOMMENDATION: "Budget Friendly",
            Intent.OCCASION_RECOMMENDATION: "Occasion Based",
            Intent.SEASON_RECOMMENDATION: "Seasonal Picks",
            Intent.STYLE_RECOMMENDATION: "Style Match",
            Intent.GIFT_RECOMMENDATION: "Gift Ideas",
            Intent.BLIND_BUY: "Blind Buy Picks",
        }
        return display_names.get(intent, "Recommendations")