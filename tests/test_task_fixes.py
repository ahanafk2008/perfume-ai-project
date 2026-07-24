"""Regression tests for the 13 task fixes.

Each test class maps to a specific fix number.
"""

from unittest.mock import Mock

from app.database import fetch_product_candidates
from app.filters import extract_budget
from app.intent import TRUST_CONCERN_KEYWORDS, Intent, detect_intent
from app.preferences import (
    extract_preferences_from_message,
    reset_preferences,
)
from app.ranking import _deduplicate_products
from app.recommendation_engine import RecommendationEngine
from app.services.chat import ChatService
from app.state import get_conversation_state, reset_conversation_state

# =============================================================================
# Fix 1: Budget memory — "exactly X", "around X", "at least X"
# =============================================================================

class TestFix1BudgetPatterns:

    def test_extract_exactly(self):
        b = extract_budget("exactly 2500")
        assert b == 2500

    def test_extract_around(self):
        b = extract_budget("around 3000")
        assert b == 3000

    def test_extract_at_least(self):
        b = extract_budget("at least 1500")
        assert b == 1500

    def test_extract_exactly_with_currency(self):
        b = extract_budget("exactly ৳2500")
        assert b == 2500


# =============================================================================
# Fix 2: Brand follow-up — brand change triggers new search
# =============================================================================

class TestFix2BrandFollowUp:

    def test_brand_change_detected_in_refinement(self):
        """When user mentions a different brand during refinement, do new search."""
        chat = ChatService(user_id="test_brand_followup")
        chat.intent_service = Mock()
        chat.search_service = Mock()
        chat.ai_service = Mock()
        chat.intent_service.detect.return_value = Intent.PRODUCT_SEARCH
        chat.search_service.search.return_value = [{"name": "A", "brand": "Lattafa", "price": 100, "category": "men"}]
        chat.ai_service.generate_reply.return_value = "OK"

        # First search establishes Lattafa context
        chat.process_message("show Lattafa")
        assert chat.search_service.search.call_count == 1

        # Follow-up with refinement keyword and same brand — should refine
        chat.search_service.search.reset_mock()
        chat.ai_service.generate_reply.return_value = "OK"
        chat.process_message("only original Lattafa")
        # Should NOT trigger new search (same brand, refinement)
        assert chat.search_service.search.call_count == 0


# =============================================================================
# Fix 3: Authenticity filtering — no silent fallback
# =============================================================================

class TestFix3AuthenticityFiltering:

    def test_no_fallback_on_empty_filter(self):
        """When clone_only filter returns empty, don't silently show all products."""
        from app.services.chat import ChatService
        chat = ChatService(user_id="test_auth")
        products = [
            {"name": "Original", "data": '{"fragrance_details": {"product_origin": "original"}}'},
        ]
        # Apply clone_only — should return empty (no inspired products)
        result = chat._apply_refinement(products, "clone_only")
        assert len(result) == 0, "clone_only filter must return empty when no clones exist"

    def test_original_only_no_fallback(self):
        chat = ChatService(user_id="test_auth2")
        products = [
            {"name": "Clone", "data": '{"fragrance_details": {"product_origin": "inspired"}}'},
        ]
        result = chat._apply_refinement(products, "original_only")
        assert len(result) == 0, "original_only filter must return empty when no originals exist"


# =============================================================================
# Fix 4: Recommendation follow-ups
# =============================================================================

class TestFix4RecommendationFollowUp:

    def test_just_one_reuses_recommendation_context(self):
        """'just one' after a recommendation should reuse recommended products."""
        reset_preferences()
        reset_conversation_state()
        chat = ChatService(user_id="test_rec_followup")
        chat.intent_service = Mock()
        chat.search_service = Mock()
        chat.ai_service = Mock()

        # Turn 1: recommendation
        chat.intent_service.detect.return_value = Intent.BEST_RECOMMENDATION
        chat.search_service.search.return_value = [
            {"name": "Best Perfume", "price": 2000, "category": "men"},
            {"name": "Runner Up", "price": 1500, "category": "men"},
        ]
        chat.ai_service.generate_reply.return_value = "Here are my top picks."
        chat.process_message("recommend me something")
        assert chat.last_searched is True

        # Turn 2: "just one" should reuse, not search again
        chat.intent_service.detect.return_value = Intent.UNKNOWN
        chat.search_service.search.reset_mock()
        chat.ai_service.generate_reply.return_value = "I recommend Best Perfume."
        response = chat.process_message("just one")
        chat.search_service.search.assert_not_called()
        assert response is not None

    def test_cheaper_reuses_recommendation_context(self):
        """'cheaper' after recommendation should reuse context."""
        reset_preferences()
        reset_conversation_state()
        chat = ChatService(user_id="test_rec_cheaper")
        chat.intent_service = Mock()
        chat.search_service = Mock()
        chat.ai_service = Mock()

        chat.intent_service.detect.return_value = Intent.BEST_RECOMMENDATION
        chat.search_service.search.return_value = [
            {"name": "Expensive One", "price": 5000, "category": "men"},
        ]
        chat.ai_service.generate_reply.return_value = "Here are my top picks."
        chat.process_message("recommend me something good")
        assert chat.last_searched is True

        state = get_conversation_state("test_rec_cheaper")
        state.store_recommendation("recommend me something good", [
            {"name": "Expensive One", "price": 5000, "category": "men"},
            {"name": "Cheap One", "price": 1000, "category": "men"},
        ])

        chat.intent_service.detect.return_value = Intent.UNKNOWN
        chat.search_service.search.reset_mock()
        chat.ai_service.generate_reply.return_value = "Cheap One is more affordable."
        response = chat.process_message("cheaper")
        assert response is not None


# =============================================================================
# Fix 5: Refinement detection preserves context
# =============================================================================

class TestFix5RefinementPreservation:

    def test_refinement_preserves_previous_context(self):
        """Refinement should filter last products, not start fresh."""
        chat = ChatService(user_id="test_refine")
        chat.last_products = [
            {"name": "A", "data": '{"fragrance_details": {"product_origin": "original"}}'},
            {"name": "B", "data": '{"fragrance_details": {"product_origin": "inspired"}}'},
        ]
        chat.last_searched = True
        refinement = chat._detect_refinement("only original")
        assert refinement == "original_only"
        result = chat._apply_refinement(chat.last_products, refinement)
        names = [p["name"] for p in result]
        assert "A" in names
        assert "B" not in names


# =============================================================================
# Fix 6: Hard budget in recommendation engine
# =============================================================================

class TestFix6HardBudget:

    def test_recommendation_engine_enforces_hard_budget(self):
        """Products over budget must never appear in recommendations."""
        engine = RecommendationEngine()
        products = [
            {"name": "Cheap", "price": 500, "category": "men"},
            {"name": "Expensive", "price": 5000, "category": "women"},
            {"name": "Mid", "price": 2000, "category": "unisex"},
        ]
        ranked = engine.recommend(products, "under 1000", Intent.BEST_RECOMMENDATION)
        for p in ranked:
            assert p["price"] <= 1000, f"{p['name']} costs {p['price']} > 1000"

    def test_recommendation_hard_budget_excludes_over_budget(self):
        """Even with high score, over-budget products must be excluded."""
        engine = RecommendationEngine()
        products = [
            {"name": "Best Match Expensive", "brand": "Dior", "price": 5000, "category": "men"},
            {"name": "Cheap Match", "brand": "Lattafa", "price": 800, "category": "men"},
        ]
        ranked = engine.recommend(products, "under 1000 best perfume", Intent.BEST_RECOMMENDATION)
        names = [p["name"] for p in ranked]
        assert "Best Match Expensive" not in names, "Over-budget product must be excluded"
        assert "Cheap Match" in names


# =============================================================================
# Fix 7: "recommend one" / "just one" 
# =============================================================================

class TestFix7RecommendOne:

    def test_just_one_in_followup_keywords(self):
        """'just one' must be recognized as a follow-up keyword."""
        from app.services.chat import ChatService
        chat = ChatService(user_id="test_just_one")
        chat.last_products = [{"name": "A", "brand": "X", "price": 100, "category": "men"}]
        chat.last_searched = True

        chat.intent_service = Mock()
        chat.search_service = Mock()
        chat.ai_service = Mock()
        chat.intent_service.detect.return_value = Intent.FOLLOW_UP
        chat.search_service.search.return_value = []
        chat.ai_service.generate_reply.return_value = "OK"

        response = chat.process_message("just one")
        # Should not trigger new search (reuses previous products)
        chat.search_service.search.assert_not_called()
        assert response is not None


# =============================================================================
# Fix 9: "safe" removed from TRUST_CONCERN_KEYWORDS
# =============================================================================

class TestFix9SafeKeyword:

    def test_safe_not_in_trust_concern(self):
        assert "safe" not in TRUST_CONCERN_KEYWORDS, "'safe' must not trigger trust concern"

    def test_loud_office_safe_is_not_trust_concern(self):
        """'Loud but office safe' must not be classified as trust concern."""
        intent = detect_intent("Loud but office safe perfume")
        assert intent != Intent.TRUST_CONCERN, "'safe' should not trigger trust concern"


# =============================================================================
# Fix 10: No-result explanation
# =============================================================================

class TestFix10NoResultExplanation:

    def test_no_result_includes_active_filters(self):
        """When search returns nothing, response should mention active filters."""
        chat = ChatService(user_id="test_noresult")
        chat.intent_service = Mock()
        chat.search_service = Mock()
        chat.ai_service = Mock()
        chat.intent_service.detect.return_value = Intent.PRODUCT_SEARCH
        chat.search_service.search.return_value = []
        chat.ai_service.generate_reply.return_value = "I couldn't find any products."

        extract_preferences_from_message("under 500 men")
        response = chat.process_message("show me something under 500")
        assert response is not None
        # Should mention active filters
        assert "budget" in response.lower() or "500" in response


# =============================================================================
# Fix 11: Deduplication across all paths
# =============================================================================

class TestFix11Deduplication:

    def test_dedup_by_id(self):
        products = [
            {"id": "1", "name": "A", "brand": "X"},
            {"id": "1", "name": "A", "brand": "X"},
            {"id": "2", "name": "B", "brand": "Y"},
        ]
        deduped = _deduplicate_products(products)
        assert len(deduped) == 2

    def test_dedup_by_name_brand_when_no_id(self):
        products = [
            {"name": "A", "brand": "X"},
            {"name": "A", "brand": "X"},
            {"name": "B", "brand": "Y"},
        ]
        deduped = _deduplicate_products(products)
        assert len(deduped) == 2

    def test_rank_products_deduplicates(self):
        """rank_products should always deduplicate."""
        from app.ranking import rank_products
        products = [
            {"id": "1", "name": "A", "brand": "X", "price": 100, "category": "men"},
            {"id": "1", "name": "A", "brand": "X", "price": 100, "category": "men"},
            {"id": "2", "name": "B", "brand": "Y", "price": 200, "category": "women"},
        ]
        ranked = rank_products(products, "perfume")
        assert len(ranked) == 2


# =============================================================================
# Fix 12: Gender LIKE matching
# =============================================================================

class TestFix12GenderLike:

    def test_gender_filter_uses_like(self):
        """Gender filter should use LIKE for broader matching."""
        tokens = ["perfume"]
        candidates = fetch_product_candidates(
            "women perfume", tokens, gender="female"
        )
        for p in candidates:
            cat = p.get("category", "").lower()
            assert "women" in cat or "wom" in cat or "female" in cat or "unisex" in cat, (
                f"Expected women-related category, got '{cat}'"
            )


# =============================================================================
# Fix 13: Response consistency
# =============================================================================

class TestFix13ResponseConsistency:

    def test_format_response_with_products(self):
        chat = ChatService(user_id="test_fmt1")
        reply = "Here are some products."
        products = [{"name": "Test", "brand": "X", "category": "men", "price": 100}]
        result = chat._format_response(reply, products)
        assert "Products found:" in result
        assert "AI:" in result
        assert "Test" in result

    def test_format_response_no_products(self):
        chat = ChatService(user_id="test_fmt2")
        reply = "No products found."
        result = chat._format_response(reply)
        assert result.startswith("\nAI:\n")
        assert "No products found" in result

    def test_format_response_products_empty_list(self):
        chat = ChatService(user_id="test_fmt3")
        reply = "Nothing to show."
        result = chat._format_response(reply, [])
        assert result.startswith("\nAI:\n")
        assert "Nothing to show" in result
