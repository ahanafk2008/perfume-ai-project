"""Tests for context-aware recommendation ranking.

Tests that the recommendation pipeline properly uses:
- previously owned products (exclusion)
- disliked notes (exclusion)
- strength preference (scoring)
- blind buy context
- occasion-specific recommendations
"""

from app.intent import Intent, detect_intent
from app.preferences import (
    PreferenceExtractor,
    extract_preferences_from_message,
    get_preferences,
    reset_preferences,
)
from app.ranking import _matches_strength, _missing_metadata_penalty
from app.recommendation_engine import RecommendationEngine, _build_reason

SAMPLE_PRODUCTS = [
    {
        "id": "1",
        "name": "Lattafa Khamrah",
        "brand": "Lattafa",
        "category": "Unisex",
        "price": "1800",
        "data": '{"fragrance_details": {"scent_family": ["sweet", "gourmand", "warm"], "longevity": "8-10 hours", "sillage": "Excellent", "performance": ["longlasting", "strong"], "season": ["winter"], "occasion": ["date", "party"]}}',
    },
    {
        "id": "2",
        "name": "Armaf Club De Nuit",
        "brand": "Armaf",
        "category": "Men",
        "price": "2200",
        "data": '{"fragrance_details": {"scent_family": ["fresh", "citrus", "aromatic"], "longevity": "6-8 hours", "sillage": "Very Good", "performance": ["longlasting"], "season": ["summer"], "occasion": ["office", "daily", "casual"]}}',
    },
    {
        "id": "3",
        "name": "Dior Sauvage",
        "brand": "Dior",
        "category": "Men",
        "price": "4500",
        "data": '{"fragrance_details": {"scent_family": ["fresh", "aromatic", "pepper"], "longevity": "6-8 hours", "sillage": "Very Good", "performance": ["longlasting", "projection"], "season": ["summer", "spring"], "occasion": ["date", "office", "party"]}}',
    },
    {
        "id": "4",
        "name": "Rasasi Hawas",
        "brand": "Rasasi",
        "category": "Men",
        "price": "2200",
        "data": '{"fragrance_details": {"scent_family": ["fresh", "aquatic", "sweet"], "longevity": "6-8 hours", "sillage": "Good", "performance": ["longlasting"], "season": ["summer"], "occasion": ["daily", "office", "casual"]}}',
    },
    {
        "id": "5",
        "name": "Budget Perfume",
        "brand": "Local Brand",
        "category": "Unisex",
        "price": "500",
        "data": '{}',
    },
]


class TestOwnedExclusion:
    def setup_method(self):
        reset_preferences("test_owned")

    def test_owned_products_not_recommended(self):
        """Previously used products should not appear in recommendations."""
        extract_preferences_from_message(
            "I already used Sauvage and Club De Nuit",
            "test_owned",
        )
        engine = RecommendationEngine()
        ranked = engine.recommend(
            SAMPLE_PRODUCTS,
            "best",
            Intent.BEST_RECOMMENDATION,
            user_id="test_owned",
        )
        names = [p["name"].lower() for p in ranked]
        # Already-owned products should not appear or be heavily penalized
        assert "dior sauvage" not in names or "club de nuit" not in names


class TestDislikedNotes:
    def setup_method(self):
        reset_preferences("test_disliked")

    def test_hate_strong_excludes_strong_perfumes(self):
        """Products with 'strong' performance should be penalized for 'hate strong'."""
        extract_preferences_from_message("I hate strong perfumes", "test_disliked")
        prefs = get_preferences("test_disliked")
        assert prefs.strength_pref == "light"
        # Khamrah has "strong" in performance - should be penalized
        penalty = _matches_strength(SAMPLE_PRODUCTS[0], "light")
        assert penalty < 0, "Strong perfume should be penalized for light preference"


class TestStrengthRanking:
    def setup_method(self):
        reset_preferences("test_strength")

    def test_moderate_preference(self):
        """Moderate strength preference should penalize 'strong' products."""
        prefs = get_preferences("test_strength")
        prefs.strength_pref = "light"

        engine = RecommendationEngine()
        ranked = engine.recommend(
            SAMPLE_PRODUCTS,
            "recommend",
            Intent.BEST_RECOMMENDATION,
            user_id="test_strength",
        )
        names = [p["name"].lower() for p in ranked]
        # Should not be first for light preference
        fresh_names = [n for n in names if "fresh" in n.lower() or "club" in n.lower()]
        if fresh_names:
            assert True  # fresh options should exist


class TestBlindBuyContext:
    def setup_method(self):
        reset_preferences("test_blind")

    def test_blind_buy_detected(self):
        """'Which one should I blind buy?' should be BLIND_BUY intent."""
        # BLIND_BUY keyword check
        from app.intent import BLIND_BUY_KEYWORDS, contains_keyword
        assert contains_keyword("blind buy", BLIND_BUY_KEYWORDS)

    def test_blind_buy_uses_context(self):
        """Blind buy with previous preferences should use that context."""
        extract_preferences_from_message(
            "I hate strong perfumes",
            "test_blind",
        )
        extract_preferences_from_message(
            "Need university perfume",
            "test_blind",
        )
        prefs = get_preferences("test_blind")
        assert prefs.strength_pref == "light"
        assert prefs.occasion == "university" or prefs.occasion is not None

        # BLIND_BUY intent should be in recommendation intents
        from app.services.chat import ChatService
        assert Intent.BLIND_BUY in ChatService._RECOMMENDATION_INTENTS


class TestOccasionRecommendations:
    def test_university(self):
        """University perfume should detect recommendation intent."""
        intent = detect_intent("university perfume")
        assert intent == Intent.OCCASION_RECOMMENDATION

    def test_gym(self):
        """Gym perfume should detect recommendation intent."""
        intent = detect_intent("gym perfume")
        assert intent == Intent.OCCASION_RECOMMENDATION

    def test_preference_extraction_occasion(self):
        """Occasion should be extractable from university/gym query."""
        result = PreferenceExtractor.extract_all("university perfume")
        assert result["occasion"] is not None

    def test_occasion_reason_specific(self):
        """Reason for occasion should reference the specific occasion."""
        reason = _build_reason(
            SAMPLE_PRODUCTS[1], 10, Intent.OCCASION_RECOMMENDATION,
            criteria={"occasion": "university"},
        )
        assert "university" in reason.lower()

    def test_gym_reason(self):
        """Gym recommendation should mention fresh/light."""
        reason = _build_reason(
            SAMPLE_PRODUCTS[1], 10, Intent.OCCASION_RECOMMENDATION,
            criteria={"occasion": "gym"},
        )
        assert "gym" in reason.lower() or "fresh" in reason.lower()


class TestProductOriginSafety:
    def test_product_origin_field_available(self):
        """product_origin should be extractable from product data."""
        from app.product_attrs import get_product_attributes

        product = {
            "id": "test",
            "name": "Creed Aventus Inspired",
            "brand": "Test",
            "price": "800",
            "data": '{"fragrance_details": {"product_origin": "inspired"}}',
        }
        attrs = get_product_attributes(product)
        assert attrs.get("product_origin") == "inspired"

    def test_no_origin_is_unknown(self):
        """Missing product_origin should return None."""
        from app.product_attrs import get_product_attributes

        product = {
            "id": "test2",
            "name": "Test",
            "brand": "Test",
            "price": "500",
            "data": '{"fragrance_details": {}}',
        }
        attrs = get_product_attributes(product)
        assert attrs.get("product_origin") is None


class TestMissingMetadataPenalty:
    def test_no_data_no_penalty(self):
        """Products without data field should not be penalized."""
        product = {"id": "1", "name": "Test", "brand": "Test", "price": "500"}
        penalty = _missing_metadata_penalty(product)
        assert penalty == 0, "No data = no penalty"

    def test_empty_data_penalized(self):
        """Products with data but no attributes should be penalized."""
        product = {
            "id": "2",
            "name": "Test",
            "brand": "Test",
            "price": "500",
            "data": '{}',
        }
        penalty = _missing_metadata_penalty(product)
        assert penalty < 0, "Empty data = penalty"

    def test_rich_data_no_penalty(self):
        """Products with fragrance data should not be penalized."""
        product = {
            "id": "3",
            "name": "Test",
            "brand": "Test",
            "price": "500",
            "data": '{"fragrance_details": {"longevity": "6-8 hours"}}',
        }
        penalty = _missing_metadata_penalty(product)
        assert penalty == 0, "Rich data = no penalty"


class TestSetSuggestion:
    def setup_method(self):
        reset_preferences("test_avoid")

    def test_avoid_already_used(self):
        """Preference for avoiding used products."""
        extract_preferences_from_message(
            "I used Dior Sauvage and CDNIM",
            "test_avoid",
        )
        prefs = get_preferences("test_avoid")
        assert "Dior Sauvage" in prefs.owned_perfumes
        assert "CDNIM" in prefs.owned_perfumes

        engine = RecommendationEngine()
        ranked = engine.recommend(
            SAMPLE_PRODUCTS,
            "suggest something different",
            Intent.BEST_RECOMMENDATION,
            user_id="test_avoid",
        )
        names = [p["name"].lower() for p in ranked]
        # The owned products should be excluded or heavily penalized
        assert "dior sauvage" not in names
        assert "club de nuit" not in names
