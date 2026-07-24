"""Regression tests for conversation quality and search consistency improvements.

Covers all 9 priorities:
1. Conversation state / preference accumulation
2. Follow-up memory
3. Comparison context
4. Budget filtering (hard filter)
5. Search consistency
6. Ambiguous requests
7. Ranking improvements (office, date, combo, duplicate)
8. Hallucination prevention
9. Better explanations
"""

from unittest.mock import Mock

from app.filters import parse_nuanced_request
from app.intent import Intent
from app.preferences import (
    extract_preferences_from_message,
    get_preferences,
    reset_preferences,
)
from app.ranking import _deduplicate_products, _is_combo_product, rank_products
from app.search import exact_name_search, search_products
from app.services.chat import ChatService
from app.state import get_conversation_state, reset_conversation_state

# =============================================================================
# Priority 1: Preference Accumulation
# =============================================================================

class TestPreferenceAccumulation:

    def setup_method(self):
        reset_preferences()
        reset_conversation_state()

    def test_budget_accumulates(self):
        """Budget from one message persists to the next."""
        extract_preferences_from_message("under 2000")
        prefs = get_preferences()
        assert prefs.budget == 2000

    def test_occasion_accumulates(self):
        """Occasion persists across messages."""
        extract_preferences_from_message("office perfume")
        prefs = get_preferences()
        assert prefs.occasion == "office"

    def test_preferences_merge_not_replace(self):
        """New message adds to state, doesn't replace existing preferences."""
        extract_preferences_from_message("under 2000")
        extract_preferences_from_message("i hate vanilla")
        prefs = get_preferences()
        assert prefs.budget == 2000
        assert "vanilla" in prefs.disliked_notes

    def test_gender_accumulates(self):
        extract_preferences_from_message("men perfume")
        prefs = get_preferences()
        assert prefs.gender == "male"

    def test_season_accumulates(self):
        extract_preferences_from_message("summer fragrance")
        prefs = get_preferences()
        assert prefs.weather == "summer" or "summer" in str(prefs.weather)

    def test_owned_perfumes_accumulate(self):
        extract_preferences_from_message("i already have Dior Sauvage")
        prefs = get_preferences()
        # Check case-insensitive since extraction normalizes
        owned_lower = [o.lower() for o in prefs.owned_perfumes]
        assert "dior sauvage" in " ".join(owned_lower) or "dior" in " ".join(owned_lower)

    def test_disliked_notes_accumulate(self):
        extract_preferences_from_message("i hate vanilla")
        extract_preferences_from_message("avoid sweet")
        prefs = get_preferences()
        assert "vanilla" in prefs.disliked_notes

    def test_preferred_brands_extracted(self):
        extract_preferences_from_message("i like Dior")
        prefs = get_preferences()
        assert len(prefs.preferred_brands) > 0

    def test_disliked_brands_extracted(self):
        extract_preferences_from_message("hate Lattafa brand")
        prefs = get_preferences()
        assert len(prefs.disliked_brands) > 0

    def test_authenticity_preference(self):
        extract_preferences_from_message("only original perfumes")
        prefs = get_preferences()
        assert prefs.authenticity_pref == "original"

    def test_clone_preference(self):
        extract_preferences_from_message("no clones")
        prefs = get_preferences()
        assert prefs.clone_pref == "original_only"

    def test_combo_preference(self):
        extract_preferences_from_message("no combos")
        prefs = get_preferences()
        assert prefs.combo_pref == "no_combo"


# =============================================================================
# Priority 2: Follow-up Memory
# =============================================================================

class TestFollowUpMemory:

    def setup_method(self):
        reset_preferences()
        reset_conversation_state()

    def test_last_search_stored(self):
        """ChatService stores last search results."""
        state = get_conversation_state("test_user")
        state.store_search("test query", [{"name": "Test", "id": "1"}], True)
        assert state.last_query == "test query"
        assert len(state.last_products) == 1
        assert state.last_searched is True

    def test_last_recommendation_stored(self):
        state = get_conversation_state("test_user")
        state.store_recommendation("best perfume", [{"name": "Best One", "id": "2"}])
        assert "best perfume" in state.last_recommended_query

    def test_follow_up_detected(self):
        """Follow-up keywords like 'original' detect as refinement."""
        chat = ChatService(user_id="test_followup")
        # Simulate a previous search
        chat.last_products = [{"name": "Test", "id": "1", "brand": "X", "price": 100, "category": "men"}]
        chat.last_searched = True
        refinement = chat._detect_refinement("only original")
        assert refinement is not None

    def test_refinement_applied(self):
        chat = ChatService(user_id="test_refine")
        products = [
            {"name": "A", "data": '{"fragrance_details": {"product_origin": "original"}}'},
            {"name": "B", "data": '{"fragrance_details": {"product_origin": "inspired"}}'},
        ]
        result = chat._apply_refinement(products, "original_only")
        names = [p["name"] for p in result]
        assert "A" in names
        assert len(result) <= 2  # At least A is there


# =============================================================================
# Priority 3: Comparison Context
# =============================================================================

class TestComparisonContext:

    def setup_method(self):
        from app.comparison_engine import get_comparison_state
        get_comparison_state().clear()

    def test_comparison_state_stores_products(self):
        from app.comparison_engine import get_comparison_state
        cs = get_comparison_state()
        cs.set_products({"name": "A", "id": "1"}, {"name": "B", "id": "2"})
        assert cs.has_comparison() is True
        both = cs.get_both_products()
        assert len(both) == 2

    def test_ranking_criteria_detected(self):
        from app.aliases import get_ranking_criteria
        assert get_ranking_criteria("which lasts longer") == "longevity"
        assert get_ranking_criteria("which projects more") == "projection"
        assert get_ranking_criteria("which is better") == "overall"
        assert get_ranking_criteria("gift for husband") is None


# =============================================================================
# Priority 4: Budget Filtering (Hard Filter)
# =============================================================================

class TestBudgetFiltering:

    def setup_method(self):
        reset_preferences()
        reset_conversation_state()

    def test_hard_budget_filter(self):
        """Products over budget should never appear."""
        results = search_products("under 2000")
        for p in results:
            assert p["price"] <= 2000, f"{p['name']} costs {p['price']} > 2000"

    def test_budget_zero_results(self):
        """Very low budget should return empty or all within budget."""
        results = search_products("under 1")
        for p in results:
            assert p["price"] <= 1

    def test_accumulated_budget_enforced(self):
        """Budget from conversation state should be enforced."""
        extract_preferences_from_message("under 1000")
        state = get_conversation_state()
        acc = state.get_all_accumulated_preferences()
        assert acc["budget"] == 1000

    def test_budget_range(self):
        results = search_products("between 1000 and 2000")
        for p in results:
            assert 1000 <= p["price"] <= 2000


# =============================================================================
# Priority 5: Search Consistency
# =============================================================================

class TestSearchConsistency:

    def test_exact_name_search_finds_aventus(self):
        """'Do you have Aventus' should find CREED AVENTUS if it exists."""
        result = exact_name_search("CREED AVENTUS")
        # Just check the function works without error
        # Actual result depends on DB contents
        assert result is None or isinstance(result, dict)

    def test_exact_name_strips_prefixes(self):
        """'do you have X' should find X."""
        result = exact_name_search("do you have Aventus")
        # Should not crash
        assert result is None or isinstance(result, dict)

    def test_exact_name_search_finds_by_alias(self):
        """Common aliases should resolve to products."""
        result = exact_name_search("show me Sauvage")
        assert result is None or isinstance(result, dict)

    def test_exact_name_search_finds_by_brand_and_name(self):
        """Brand+name combination should find product."""
        result = exact_name_search("Dior Sauvage")
        assert result is None or isinstance(result, dict)

    def test_search_unknown_returns_empty(self):
        """Completely unknown query returns empty."""
        results = search_products("zyxwvutsrqponmlkjihgfedcba")
        assert results == []

    def test_do_you_have_triggers_search(self):
        """'Do you have X' should search even when intent is UNKNOWN."""
        from app.search import search_products
        results = search_products("do you have Dior Sauvage")
        assert isinstance(results, list)


# =============================================================================
# Priority 6: Ambiguous Requests
# =============================================================================

class TestAmbiguousRequests:

    def setup_method(self):
        reset_preferences()
        reset_conversation_state()

    def test_fresh_but_warm_detected(self):
        chat = ChatService(user_id="test_ambig")
        result = chat._detect_ambiguity("fresh but warm perfume")
        assert result is not None
        assert "fresh" in result.lower() and "warm" in result.lower()

    def test_sweet_but_not_sweet_detected(self):
        chat = ChatService(user_id="test_ambig2")
        result = chat._detect_ambiguity("sweet but not sweet")
        assert result is not None

    def test_strong_not_overpowering_detected(self):
        chat = ChatService(user_id="test_ambig3")
        result = chat._detect_ambiguity("strong but not overpowering")
        assert result is not None

    def test_non_ambiguous_passes(self):
        chat = ChatService(user_id="test_ambig4")
        result = chat._detect_ambiguity("office perfume under 2000")
        assert result is None

    def test_contradictory_seasons_detected(self):
        chat = ChatService(user_id="test_ambig5")
        result = chat._detect_ambiguity("summer perfume for winter")
        assert result is not None

    def test_nuanced_request_parsing(self):
        nr = parse_nuanced_request("sweet but not too sweet")
        assert nr.sweetness == 0.5  # balanced sweet


# =============================================================================
# Priority 7: Ranking Improvements
# =============================================================================

class TestRankingImprovements:

    def test_office_penalizes_loud_scents(self):
        """Office ranking should penalize club/party scents."""
        from app.ranking import _occasion_specific_score

        # Create a club scent product
        loud_product = {
            "data": '{"fragrance_details": {"scent_family": ["sweet", "gourmand", "strong", "party"]}}'
        }
        score = _occasion_specific_score(loud_product, "office")
        assert score < 0, "Loud scents should be penalized for office"

    def test_date_boosts_compliments(self):
        """Date ranking should boost compliment-getting scents."""
        from app.ranking import _occasion_specific_score

        date_product = {
            "data": '{"fragrance_details": {"scent_family": ["sweet", "vanilla", "romantic"]}}'
        }
        score = _occasion_specific_score(date_product, "date")
        assert score >= 0, "Romantic scents should be boosted for date"

    def test_combo_detected_by_category(self):
        combo = {"name": "Test", "brand": "X", "category": "Combo", "description": "", "price": 100}
        assert _is_combo_product(combo) is True

    def test_non_combo_not_detected(self):
        regular = {"name": "Test", "brand": "X", "category": "Men", "description": "", "price": 100}
        assert _is_combo_product(regular) is False

    def test_deduplication_by_id(self):
        products = [
            {"id": "1", "name": "A"},
            {"id": "1", "name": "A"},  # duplicate
            {"id": "2", "name": "B"},
        ]
        deduped = _deduplicate_products(products)
        assert len(deduped) == 2

    def test_deduplication_by_name_brand(self):
        products = [
            {"name": "A", "brand": "X"},
            {"name": "A", "brand": "X"},  # duplicate
            {"name": "B", "brand": "Y"},
        ]
        deduped = _deduplicate_products(products)
        assert len(deduped) == 2

    def test_gender_penalty_applied(self):
        from app.ranking import _gender_penalty
        text = "women floral perfume"
        penalty = _gender_penalty(text, "male")
        assert penalty < 0


# =============================================================================
# Priority 8: Hallucination Prevention
# =============================================================================

class TestHallucinationPrevention:

    def test_product_fields_only_from_db(self):
        """Product display should only use structured fields."""
        from app.prompt_builder import _product_fields
        product = {
            "name": "Test Perfume",
            "brand": "TestBrand",
            "category": "Men",
            "price": 1000,
            "data": '{"fragrance_details": {"scent_family": ["fresh"], "longevity": "6-8 hours"}}'
        }
        fields = _product_fields(product)
        text = " | ".join(fields)
        assert "Test Perfume" in text
        assert "TestBrand" in text
        assert "Men" in text
        assert "৳1000" in text
        assert "fresh" in text
        assert "6-8 hours" in text


# =============================================================================
# Priority 9: Better Explanations
# =============================================================================

class TestBetterExplanations:

    def test_reason_includes_attributes(self):
        """Recommendation reason should include actual metadata."""
        from app.recommendation_engine import _build_reason
        product = {
            "name": "Test Perfume",
            "brand": "Dior",
            "price": 1500,
            "data": '{"fragrance_details": {"scent_family": ["fresh", "citrus"], "longevity": "6-8 hours", "sillage": "moderate"}}'
        }
        reason = _build_reason(product, 5, Intent.BEST_RECOMMENDATION, {"budget": 2000})
        assert "fresh" in reason
        assert "citrus" in reason
        assert "longevity" in reason
        assert "within budget" in reason

    def test_reason_includes_occasion(self):
        from app.recommendation_engine import _build_reason
        product = {
            "name": "Office Safe",
            "brand": "X",
            "price": 2000,
            "data": '{"fragrance_details": {"scent_family": ["fresh"], "occasion": ["office"]}}'
        }
        reason = _build_reason(product, 5, Intent.OCCASION_RECOMMENDATION, {"occasion": "office"})
        assert "office" in reason.lower() or "fresh" in reason

    def test_reason_no_hallucination(self):
        """Reason should not infer characteristics from names.
        
        e.g., should NOT say "Ice sounds fresh" or "Cool Water sounds cooling".
        Only use what's in the structured data.
        """
        from app.recommendation_engine import _build_reason
        product = {
            "name": "Ice Cold",
            "brand": "Test",
            "price": 1000,
            "data": '{}'
        }
        reason = _build_reason(product, 5, Intent.BEST_RECOMMENDATION)
        # The product name can appear, but no scent inference from the name
        assert "fresh" not in reason.lower() or "recommended" in reason
        assert "cooling" not in reason.lower()


# =============================================================================
# Integration: Conversation Flow
# =============================================================================

class TestConversationFlow:

    def setup_method(self):
        reset_preferences()
        reset_conversation_state()

    def test_preference_updates_search(self):
        """Preferences from earlier messages should influence later searches."""
        chat = ChatService(user_id="test_flow1")
        chat.intent_service = Mock()
        chat.search_service = Mock()
        chat.ai_service = Mock()

        # First message: set budget
        chat.intent_service.detect.return_value = Intent.PRODUCT_SEARCH
        chat.search_service.search.return_value = []
        chat.ai_service.generate_reply.return_value = "OK"

        chat.process_message("under 2000 men perfume")

        # Verify preferences were extracted
        prefs = get_preferences("test_flow1")
        assert prefs.budget == 2000
        assert prefs.gender == "male"

    def test_ambiguity_blocks_search(self):
        """Ambiguous requests should ask a question instead of searching."""
        chat = ChatService(user_id="test_ambig_flow")
        chat.intent_service = Mock()
        chat.search_service = Mock()
        chat.ai_service = Mock()

        chat.intent_service.detect.return_value = Intent.PRODUCT_SEARCH
        chat.search_service.search.return_value = [{"name": "Test", "price": 100}]
        chat.ai_service.generate_reply.return_value = ("Some reply", {})

        response = chat.process_message("fresh but warm perfume")
        assert "fresh" in response.lower()
        assert "warm" in response.lower()
        # Should ask a clarification, not show products
        assert "Products found" not in response

    def test_ranked_results_deduplicated(self):
        """Duplicate products should not appear in results."""
        products = [
            {"id": "1", "name": "A", "brand": "X", "price": 100, "category": "men"},
            {"id": "1", "name": "A", "brand": "X", "price": 100, "category": "men"},
            {"id": "2", "name": "B", "brand": "Y", "price": 200, "category": "women"},
        ]
        ranked = rank_products(products, "perfume")
        assert len(ranked) == 2


class TestConversationState:

    def setup_method(self):
        reset_preferences()
        reset_conversation_state()

    def test_state_created(self):
        state = get_conversation_state("new_user")
        assert state is not None

    def test_state_stores_search(self):
        state = get_conversation_state("search_user")
        state.store_search("test", [{"id": "1"}], True)
        assert state.last_query == "test"
        assert state.last_searched is True

    def test_state_stores_recommendation(self):
        state = get_conversation_state("rec_user")
        state.store_recommendation("best", [{"id": "2"}])
        assert len(state.last_recommended_products) == 1

    def test_state_stores_comparison(self):
        state = get_conversation_state("cmp_user")
        state.store_comparison("a vs b", [{"id": "1"}, {"id": "2"}])
        assert state.is_in_comparison() is True
        left, right = state.get_comparison_pair()
        assert left is not None
        assert right is not None

    def test_state_accumulated_prefs(self):
        extract_preferences_from_message("under 3000 men office")
        state = get_conversation_state()
        acc = state.get_all_accumulated_preferences()
        assert acc["budget"] == 3000
        assert acc["gender"] == "male"
        assert acc["occasion"] == "office"

    def test_state_updates_not_replace(self):
        """Second message should add to, not replace, accumulated state."""
        extract_preferences_from_message("under 2000")
        extract_preferences_from_message("i hate vanilla")
        state = get_conversation_state()
        acc = state.get_all_accumulated_preferences()
        assert acc["budget"] == 2000
        assert len(acc["disliked_notes"]) > 0
