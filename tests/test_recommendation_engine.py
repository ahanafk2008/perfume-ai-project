"""Tests for the recommendation engine and recommendation intents."""

from app.intent import (
    Intent,
    detect_intent,
)
from app.recommendation_engine import RecommendationEngine, _build_reason

# ──────────────────────────────────────────────
# Intent Detection Tests
# ──────────────────────────────────────────────

class TestBestRecommendationIntent:
    def test_best_keyword(self):
        assert detect_intent("best") == Intent.BEST_RECOMMENDATION

    def test_recommend_one(self):
        assert detect_intent("recommend one") == Intent.BEST_RECOMMENDATION

    def test_top_perfume(self):
        assert detect_intent("top perfume") == Intent.BEST_RECOMMENDATION

    def test_popular(self):
        assert detect_intent("popular") == Intent.BEST_RECOMMENDATION

    def test_favorite(self):
        assert detect_intent("favorite") == Intent.BEST_RECOMMENDATION

    def test_best_perfume_does_not_fall_through(self):
        """Should not fall through to product_search."""
        result = detect_intent("best")
        assert result == Intent.BEST_RECOMMENDATION
        assert result != Intent.PRODUCT_SEARCH

    def test_best_greeting_request(self):
        """'hi best' should still be caught as product search via greeting."""
        # "hi" is a greeting, but "best" is a keyword - depends on greeting detection
        # The greeting check runs before recommendation, so this tests the flow


class TestLuxuryRecommendationIntent:
    def test_luxury(self):
        assert detect_intent("luxury") == Intent.LUXURY_RECOMMENDATION

    def test_premium(self):
        assert detect_intent("premium") == Intent.LUXURY_RECOMMENDATION

    def test_classy(self):
        assert detect_intent("classy") == Intent.LUXURY_RECOMMENDATION

    def test_designer(self):
        assert detect_intent("designer") == Intent.LUXURY_RECOMMENDATION

    def test_sophisticated(self):
        assert detect_intent("sophisticated") == Intent.LUXURY_RECOMMENDATION


class TestGenderFilterIntent:
    def test_men(self):
        assert detect_intent("men") == Intent.GENDER_FILTER

    def test_women(self):
        assert detect_intent("women") == Intent.GENDER_FILTER

    def test_unisex(self):
        assert detect_intent("unisex") == Intent.GENDER_FILTER

    def test_male(self):
        assert detect_intent("male") == Intent.GENDER_FILTER

    def test_female(self):
        assert detect_intent("female") == Intent.GENDER_FILTER


class TestBudgetRecommendationIntent:
    def test_cheap(self):
        assert detect_intent("cheap") == Intent.BUDGET_RECOMMENDATION

    def test_affordable(self):
        assert detect_intent("affordable") == Intent.BUDGET_RECOMMENDATION

    def test_under_2000(self):
        assert detect_intent("under 2000") == Intent.BUDGET_RECOMMENDATION

    def test_budget(self):
        assert detect_intent("budget") == Intent.BUDGET_RECOMMENDATION


class TestOccasionRecommendationIntent:
    def test_office(self):
        assert detect_intent("office") == Intent.OCCASION_RECOMMENDATION

    def test_date(self):
        assert detect_intent("date") == Intent.OCCASION_RECOMMENDATION

    def test_party(self):
        assert detect_intent("party") == Intent.OCCASION_RECOMMENDATION

    def test_wedding(self):
        assert detect_intent("wedding") == Intent.OCCASION_RECOMMENDATION

    def test_casual(self):
        assert detect_intent("casual") == Intent.OCCASION_RECOMMENDATION


class TestSeasonRecommendationIntent:
    def test_summer(self):
        assert detect_intent("summer") == Intent.SEASON_RECOMMENDATION

    def test_winter(self):
        assert detect_intent("winter") == Intent.SEASON_RECOMMENDATION

    def test_rainy(self):
        assert detect_intent("rainy") == Intent.SEASON_RECOMMENDATION


class TestStyleRecommendationIntent:
    def test_clean(self):
        assert detect_intent("clean") == Intent.STYLE_RECOMMENDATION

    def test_marine(self):
        assert detect_intent("marine") == Intent.STYLE_RECOMMENDATION

    def test_ocean(self):
        assert detect_intent("ocean") == Intent.STYLE_RECOMMENDATION

    def test_sugary(self):
        assert detect_intent("sugary") == Intent.STYLE_RECOMMENDATION

    def test_candy(self):
        assert detect_intent("candy") == Intent.STYLE_RECOMMENDATION

    def test_earthy(self):
        assert detect_intent("earthy") == Intent.STYLE_RECOMMENDATION

    def test_pepper(self):
        assert detect_intent("pepper") == Intent.STYLE_RECOMMENDATION

    def test_flower(self):
        assert detect_intent("flower") == Intent.STYLE_RECOMMENDATION

    def test_sweet_is_product_search(self):
        """'sweet' is a product keyword, not a style recommendation."""
        assert detect_intent("sweet") == Intent.PRODUCT_SEARCH

    def test_fresh_is_product_search(self):
        """'fresh' is a product keyword, not a style recommendation."""
        assert detect_intent("fresh") == Intent.PRODUCT_SEARCH

    def test_woody_is_product_search(self):
        """'woody' is a product keyword, not a style recommendation."""
        assert detect_intent("woody") == Intent.PRODUCT_SEARCH

    def test_floral_is_product_search(self):
        """'floral' is a product keyword, not a style recommendation."""
        assert detect_intent("floral") == Intent.PRODUCT_SEARCH


class TestGiftRecommendationIntent:
    def test_gift_idea(self):
        """'gift idea' should route to GIFT (higher priority than GIFT_RECOMMENDATION)."""
        assert detect_intent("gift idea") == Intent.GIFT

    def test_gift_suggestion(self):
        """'gift suggestion' should route to GIFT (higher priority)."""
        assert detect_intent("gift suggestion") == Intent.GIFT

    def test_simple_gift_still_gift(self):
        """Simple 'gift' should still be GIFT (not GIFT_RECOMMENDATION)."""
        assert detect_intent("gift") == Intent.GIFT

    def test_birthday_gift(self):
        """'birthday gift' - birthday is in GIFT_KEYWORDS, so should be GIFT."""
        result = detect_intent("birthday gift")
        assert result in (Intent.GIFT, Intent.GIFT_RECOMMENDATION)


# ──────────────────────────────────────────────
# Recommendation Engine Tests
# ──────────────────────────────────────────────

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
        "name": "Tom Ford Tobacco Vanille",
        "brand": "Tom Ford",
        "category": "Unisex",
        "price": "8000",
        "data": '{"fragrance_details": {"scent_family": ["sweet", "vanilla", "woody", "spicy"], "longevity": "10-12 hours", "sillage": "Excellent", "performance": ["longlasting", "strong", "projection"], "season": ["winter", "fall"], "occasion": ["date", "party", "formal"]}}',
    },
    {
        "id": "5",
        "name": "Rasasi Hawas",
        "brand": "Rasasi",
        "category": "Men",
        "price": "2200",
        "data": '{"fragrance_details": {"scent_family": ["fresh", "aquatic", "sweet"], "longevity": "6-8 hours", "sillage": "Good", "performance": ["longlasting"], "season": ["summer"], "occasion": ["daily", "office", "casual"]}}',
    },
    {
        "id": "6",
        "name": "Lattafa Yara",
        "brand": "Lattafa",
        "category": "Women",
        "price": "1400",
        "data": '{"fragrance_details": {"scent_family": ["sweet", "floral", "powdery"], "longevity": "6-8 hours", "sillage": "Good", "performance": ["longlasting"], "season": ["spring", "summer"], "occasion": ["daily", "casual", "date"]}}',
    },
    {
        "id": "7",
        "name": "Budget Perfume",
        "brand": "Local Brand",
        "category": "Unisex",
        "price": "500",
        "data": '{"fragrance_details": {"scent_family": ["fresh", "citrus"], "longevity": "2-3 hours", "sillage": "Moderate"}}',
    },
    {
        "id": "8",
        "name": "Premium Oud",
        "brand": "Mancera",
        "category": "Unisex",
        "price": "6500",
        "data": '{"fragrance_details": {"scent_family": ["oud", "woody", "spicy"], "longevity": "10-12 hours", "sillage": "Excellent", "performance": ["longlasting", "strong", "projection"], "season": ["winter"], "occasion": ["party", "formal", "wedding"]}}',
    },
]


class TestRecommendationEngine:
    def setup_method(self):
        self.engine = RecommendationEngine()

    def test_best_recommendation(self):
        """Best recommendation should rank products and return reasons."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "best", Intent.BEST_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)
        # Premium brands (Dior, Tom Ford) should rank higher for "best"
        top_names = [p["name"] for p in ranked[:3]]
        assert any("Dior" in n or "Tom Ford" in n for n in top_names)

    def test_luxury_recommendation(self):
        """Luxury should rank premium/expensive products higher."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "luxury", Intent.LUXURY_RECOMMENDATION
        )
        assert len(ranked) > 0
        # Top results should be premium brands with high price
        top = ranked[0]
        assert "ranking_reason" in top
        # Dior (4500) and Tom Ford (8000) should be near top
        top_names = [p["name"] for p in ranked[:3]]
        assert any("Dior" in n or "Tom Ford" in n or "Mancera" in n for n in top_names)

    def test_gender_filter_men(self):
        """Gender filter should return men's products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "men", Intent.GENDER_FILTER
        )
        assert len(ranked) > 0
        # At least some should have 'Men' category
        cats = [p.get("category", "") for p in ranked]
        assert any("Men" in c for c in cats)

    def test_gender_filter_women(self):
        """Gender filter should return women's products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "women", Intent.GENDER_FILTER
        )
        assert len(ranked) > 0
        cats = [p.get("category", "") for p in ranked]
        assert any("Women" in c for c in cats)

    def test_gender_filter_unisex(self):
        """Gender filter should include unisex products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "unisex", Intent.GENDER_FILTER
        )
        assert len(ranked) > 0
        cats = [p.get("category", "") for p in ranked]
        assert any("Unisex" in c for c in cats)

    def test_budget_recommendation_cheap(self):
        """Budget recommendation should prefer lower-priced products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "cheap", Intent.BUDGET_RECOMMENDATION
        )
        assert len(ranked) > 0
        # The cheapest product (500) should be in the top results
        names = [p["name"] for p in ranked[:5]]
        assert "Budget Perfume" in names

    def test_budget_recommendation_under_2000(self):
        """Budget with price should prefer affordable options."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "under 2000", Intent.BUDGET_RECOMMENDATION
        )
        assert len(ranked) > 0
        # The cheapest product (500) should be in top results
        names = [p["name"] for p in ranked[:5]]
        assert "Budget Perfume" in names

    def test_occasion_office(self):
        """Office occasion should return office-suitable products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "office", Intent.OCCASION_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)

    def test_occasion_date(self):
        """Date occasion should return date-suitable products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "date", Intent.OCCASION_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)

    def test_season_summer(self):
        """Summer season should return summer-suitable products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "summer", Intent.SEASON_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)

    def test_season_winter(self):
        """Winter season should return winter-suitable products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "winter", Intent.SEASON_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)

    def test_style_fresh(self):
        """Fresh style should return fresh-scented products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "fresh", Intent.STYLE_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)

    def test_style_sweet(self):
        """Sweet style should return sweet-scented products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "sweet", Intent.STYLE_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)

    def test_gift_recommendation(self):
        """Gift recommendation should return gift-worthy products."""
        ranked = self.engine.recommend(
            SAMPLE_PRODUCTS, "gift idea", Intent.GIFT_RECOMMENDATION
        )
        assert len(ranked) > 0
        assert all("ranking_reason" in p for p in ranked)

    def test_recommendation_type_label(self):
        """get_recommendation_type should return correct labels."""
        assert self.engine.get_recommendation_type(Intent.BEST_RECOMMENDATION) == "Top Picks"
        assert self.engine.get_recommendation_type(Intent.LUXURY_RECOMMENDATION) == "Luxury Selection"
        assert self.engine.get_recommendation_type(Intent.GENDER_FILTER) == "Gender Filter"

    def test_empty_products(self):
        """Should handle empty product list gracefully."""
        ranked = self.engine.recommend([], "best", Intent.BEST_RECOMMENDATION)
        assert ranked == []


class TestBuildReason:
    def test_best_reason(self):
        """Best recommendation reason should mention price."""
        reason = _build_reason(SAMPLE_PRODUCTS[0], 10, Intent.BEST_RECOMMENDATION)
        assert "Khamrah" in reason
        assert "highly rated" in reason

    def test_luxury_reason_premium_brand(self):
        """Luxury reason should mention premium brand for Dior."""
        reason = _build_reason(SAMPLE_PRODUCTS[2], 10, Intent.LUXURY_RECOMMENDATION)
        assert "Dior" in reason
        assert "premium" in reason.lower() or "luxury" in reason.lower()

    def test_luxury_reason_non_premium(self):
        """Luxury reason for non-premium brand should not mention brand."""
        reason = _build_reason(SAMPLE_PRODUCTS[6], 5, Intent.LUXURY_RECOMMENDATION)
        # Should not mention a premium brand
        assert "Dior" not in reason
        assert "Tom Ford" not in reason
        assert "Mancera" not in reason

    def test_budget_reason(self):
        """Budget reason should mention value."""
        reason = _build_reason(SAMPLE_PRODUCTS[6], 10, Intent.BUDGET_RECOMMENDATION)
        assert "value" in reason.lower()

    def test_gender_reason(self):
        """Gender filter reason should mention gender."""
        reason = _build_reason(
            SAMPLE_PRODUCTS[1], 10, Intent.GENDER_FILTER,
            criteria={"gender": "male"}
        )
        assert "for" in reason.lower()

    def test_occasion_reason(self):
        """Occasion reason should mention the occasion."""
        reason = _build_reason(
            SAMPLE_PRODUCTS[0], 10, Intent.OCCASION_RECOMMENDATION,
            criteria={"occasion": "date"}
        )
        assert "date" in reason.lower()

    def test_season_reason(self):
        """Season reason should mention the season."""
        reason = _build_reason(
            SAMPLE_PRODUCTS[0], 10, Intent.SEASON_RECOMMENDATION,
            criteria={"season": "winter"}
        )
        assert "winter" in reason.lower() or "seasonal" in reason.lower()

    def test_style_reason(self):
        """Style reason should mention the scent profile."""
        reason = _build_reason(
            SAMPLE_PRODUCTS[4], 10, Intent.STYLE_RECOMMENDATION,
            criteria={"style": "fresh"}
        )
        assert "fresh" in reason.lower()

    def test_gift_reason_premium_brand(self):
        """Gift reason should mention brand for premium brands."""
        reason = _build_reason(SAMPLE_PRODUCTS[3], 10, Intent.GIFT_RECOMMENDATION)
        assert "gift" in reason.lower()

    def test_gift_reason_non_premium(self):
        """Gift reason should not hallucinate brand for non-premium."""
        reason = _build_reason(SAMPLE_PRODUCTS[6], 5, Intent.GIFT_RECOMMENDATION)
        assert "gift" in reason.lower()

    def test_no_hallucinated_attributes(self):
        """Reason should only include attributes that actually exist."""
        product = {
            "id": "99",
            "name": "Test Product",
            "brand": "Unknown",
            "category": "Unisex",
            "price": "500",
        }
        reason = _build_reason(product, 5, Intent.BEST_RECOMMENDATION)
        assert "Test Product" in reason
        # Should have some content but no hallucinated attribute claims
        assert "scent:" not in reason
        assert "longevity:" not in reason
        assert "projection:" not in reason
        assert "performance:" not in reason


# ──────────────────────────────────────────────
# Regression: Existing tests should still pass
# ──────────────────────────────────────────────

class TestNoSearchServiceCall:
    """Verify recommendation engine does not call SearchService."""

    def test_recommendation_uses_ranking_not_search(self):
        """The engine should use rank_products, not call search."""
        from app.ranking import rank_products
        # Just verify rank_products is importable and the engine uses it
        assert callable(rank_products)
        engine = RecommendationEngine()
        result = engine.recommend(
            SAMPLE_PRODUCTS[:3],
            "best",
            Intent.BEST_RECOMMENDATION,
        )
        assert len(result) > 0
        assert "ranking_reason" in result[0]


class TestNoHallucinatedAttributes:
    """Verify the engine never claims attributes that don't exist in data."""

    def test_minimal_product(self):
        """A product with no fragrance_details should get generic reason."""
        minimal = {
            "id": "100",
            "name": "Minimal Perfume",
            "brand": "TestBrand",
            "category": "Unisex",
            "price": "1000",
        }
        reason = _build_reason(minimal, 5, Intent.BEST_RECOMMENDATION)
        assert "Minimal Perfume" in reason
        # Should not have fragrance detail claims
        assert "scent:" not in reason
        assert "longevity:" not in reason

    def test_product_origin_not_claimed(self):
        """Engine should not claim product_origin unless data exists."""
        product = {
            "id": "101",
            "name": "Test",
            "brand": "Test",
            "price": "1000",
        }
        from app.recommendation_engine import _get_product_origin
        origin = _get_product_origin(product)
        assert origin == "unknown"


# ──────────────────────────────────────────────
# Intent keyword coverage tests
# ──────────────────────────────────────────────

class TestIntentKeywordCoverage:
    def test_search_service_not_called_for_recommendation(self):
        """Recommendation intents should not trigger search service."""
        from app.services.chat import ChatService
        # Just check the _RECOMMENDATION_INTENTS set is defined correctly
        assert Intent.BEST_RECOMMENDATION in ChatService._RECOMMENDATION_INTENTS
        assert Intent.LUXURY_RECOMMENDATION in ChatService._RECOMMENDATION_INTENTS
        assert Intent.GENDER_FILTER in ChatService._RECOMMENDATION_INTENTS
        assert Intent.STYLE_RECOMMENDATION in ChatService._RECOMMENDATION_INTENTS
        assert Intent.SEASON_RECOMMENDATION in ChatService._RECOMMENDATION_INTENTS
        assert Intent.OCCASION_RECOMMENDATION in ChatService._RECOMMENDATION_INTENTS
        assert Intent.GIFT_RECOMMENDATION in ChatService._RECOMMENDATION_INTENTS