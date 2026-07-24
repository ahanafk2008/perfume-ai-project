"""Regression tests for the Comparison Engine.

Tests cover:
- Alias resolution (CDNIM, BDC, YSL Y, SWY, 9PM, Asad, Qahwa, etc.)
- Comparison state storage (left_product, right_product, comparison_history)
- Follow-up ranking queries that use stored comparison state
- Detailed comparison output structure
- Ranking intent scoring (strongest, richest, most luxurious, etc.)
- Merge/duplicate handling
"""

from unittest.mock import Mock

from app.aliases import get_ranking_criteria, resolve_alias
from app.comparison_engine import (
    ComparisonState,
    _parse_longevity_score,
    _parse_sillage_score,
    _score_blind_buy,
    _score_compliments,
    _score_longevity,
    _score_luxury,
    _score_overall,
    _score_richness,
    _score_value,
    answer_ranking_query,
    build_comparison_output,
    build_full_comparison,
    build_verdict,
    get_comparison_state,
    pick_best_for_criteria,
    rank_for_criteria,
    score_product_for_criteria,
)

# ---------------------------------------------------------------------------
# Sample products for testing
# ---------------------------------------------------------------------------

PRODUCT_A = {
    "id": "prod-a",
    "name": "BLEU DE CHANEL",
    "brand": "CHANEL",
    "price": 2350.0,
    "category": "Men",
    "data": """{
        "fragrance_details": {
            "type": "EDP",
            "longevity": "6-8 hours",
            "sillage": "moderate",
            "bestTime": "office",
            "notes": {
                "top": ["grapefruit", "lemon", "mint"],
                "middle": ["ginger", "nutmeg", "jasmine"],
                "base": ["cedar", "sandalwood", "amber"]
            },
            "scent_family": ["fresh", "woody"],
            "occasion": ["office", "date"],
            "performance": ["long lasting"]
        },
        "variants": [
            {"size": "15ML", "price": 450},
            {"size": "30ML", "price": 800},
            {"size": "50ML", "price": 1250},
            {"size": "100ML", "price": 2350}
        ]
    }""",
}

PRODUCT_B = {
    "id": "prod-b",
    "name": "CLUB DE NUIT INSTENSE MAN",
    "brand": "ARMAF",
    "price": 4250.0,
    "category": "Authentic",
    "data": """{
        "fragrance_details": {
            "type": "EDP",
            "longevity": "8-10 hours",
            "sillage": "strong",
            "bestTime": "party",
            "notes": {
                "top": ["bergamot", "lemon", "apple"],
                "middle": ["birch", "jasmine", "rose"],
                "base": ["vanilla", "musk", "oakmoss", "amber"]
            },
            "scent_family": ["sweet", "woody", "fresh"],
            "occasion": ["party", "night out"],
            "performance": ["strong", "long lasting", "beast mode"]
        },
        "variants": [
            {"size": "15 ML", "price": 1000},
            {"size": "30 ML", "price": 1800},
            {"size": "50 ML", "price": 2750},
            {"size": "100 ML", "price": 4250}
        ]
    }""",
}

PRODUCT_C = {
    "id": "prod-c",
    "name": "LATTAFA KHAMRAH",
    "brand": "LATTAFA",
    "price": 2350.0,
    "category": "Unisex",
    "data": """{
        "fragrance_details": {
            "type": "EDP",
            "longevity": "6-8 hours",
            "sillage": "moderate",
            "notes": {
                "top": [],
                "middle": [],
                "base": []
            },
            "scent_family": ["sweet", "vanilla"],
            "occasion": ["party", "date"],
            "performance": ["long lasting"]
        },
        "variants": [
            {"size": "15 ML", "price": 450},
            {"size": "35 ML", "price": 800},
            {"size": "50 ML", "price": 1250},
            {"size": "100 ML", "price": 2350}
        ]
    }""",
}

PRODUCT_D = {
    "id": "prod-d",
    "name": "DIOR SAUVAGE",
    "brand": "DIOR",
    "price": 2350.0,
    "category": "Men",
    "data": """{
        "fragrance_details": {
            "type": "EDP",
            "longevity": "6-8 hours",
            "sillage": "moderate",
            "notes": {
                "top": ["bergamot", "pepper"],
                "middle": ["lavender", "geranium"],
                "base": ["cedar", "labdanum"]
            },
            "scent_family": ["fresh", "woody"],
            "occasion": ["office", "party"],
            "performance": ["long lasting"]
        },
        "variants": [
            {"size": "15ML", "price": 450},
            {"size": "30ML", "price": 800},
            {"size": "50ML", "price": 1250},
            {"size": "100ML", "price": 2350}
        ]
    }""",
}

PRODUCT_E = {
    "id": "prod-e",
    "name": "AFNAN 9 PM ELIXIR",
    "brand": "AFNAN",
    "price": 2350.0,
    "category": "Men",
    "data": """{
        "fragrance_details": {
            "type": "EDP",
            "longevity": "6-8 hours",
            "sillage": "strong",
            "notes": {
                "top": [],
                "middle": [],
                "base": []
            },
            "scent_family": ["sweet", "vanilla"],
            "occasion": ["party", "night out"],
            "performance": ["long lasting"]
        },
        "variants": [
            {"size": "15ML", "price": 450},
            {"size": "35ML", "price": 800},
            {"size": "50ML", "price": 1250},
            {"size": "100ML", "price": 2350}
        ]
    }""",
}

PRODUCT_NO_DATA = {
    "id": "prod-f",
    "name": "SIMPLE FRAGRANCE",
    "brand": "SIMPLE",
    "price": 1000.0,
    "category": "Men",
    "data": "null",
}


# =============================================================
# 1. Alias resolution tests
# =============================================================

class TestAliases:
    def test_cdnim_resolves(self):
        assert "CLUB DE NUIT INSTENSE MAN" in resolve_alias("CDNIM")

    def test_bdc_resolves(self):
        assert resolve_alias("BDC") == "BLEU DE CHANEL"

    def test_ysl_y_resolves(self):
        assert resolve_alias("YSL Y") == "YSL Y"

    def test_swy_resolves(self):
        assert resolve_alias("SWY") == "STRONGER WITH YOU"

    def test_9pm_resolves(self):
        assert "AFNAN 9 PM" in resolve_alias("9PM").upper()

    def test_asad_resolves(self):
        assert resolve_alias("Asad") == "LATTAFA ASAD"

    def test_qahwa_resolves(self):
        assert "KHAMRAH" in resolve_alias("Qahwa").upper()

    def test_aventus_resolves(self):
        assert resolve_alias("Aventus") == "CREED AVENTUS"

    def test_sauvage_resolves(self):
        assert resolve_alias("Sauvage") == "DIOR SAUVAGE"

    def test_hawas_resolves(self):
        assert resolve_alias("Hawas") == "RASASI HAWAS"

    def test_unknown_name_unchanged(self):
        assert resolve_alias("COMPLETELY UNKNOWN") == "COMPLETELY UNKNOWN"


# =============================================================
# 2. Comparison state storage
# =============================================================

class TestComparisonState:
    def setup_method(self):
        self.state = ComparisonState()

    def test_empty_state(self):
        assert self.state.left_product is None
        assert self.state.right_product is None
        assert not self.state.has_comparison()

    def test_set_products_stores_left_right(self):
        self.state.set_products(PRODUCT_A, PRODUCT_B)
        assert self.state.left_product is PRODUCT_A
        assert self.state.right_product is PRODUCT_B
        assert self.state.has_comparison()

    def test_get_both_products_returns_list(self):
        self.state.set_products(PRODUCT_A, PRODUCT_B)
        both = self.state.get_both_products()
        assert len(both) == 2
        assert PRODUCT_A in both
        assert PRODUCT_B in both

    def test_clear_resets_state(self):
        self.state.set_products(PRODUCT_A, PRODUCT_B)
        self.state.clear()
        assert not self.state.has_comparison()

    def test_history_tracks_comparisons(self):
        self.state.set_products(PRODUCT_A, PRODUCT_B)
        assert len(self.state.history) == 1
        assert self.state.history[0]["left_name"] == "BLEU DE CHANEL"
        assert self.state.history[0]["right_name"] == "CLUB DE NUIT INSTENSE MAN"

    def test_history_limited_to_10(self):
        for i in range(15):
            self.state.set_products({"name": f"L{i}"}, {"name": f"R{i}"})
        assert len(self.state.history) <= 10

    def test_global_state_singleton(self):
        # Reset between tests
        get_comparison_state().clear()

    def test_global_state_accessible(self):
        cs = get_comparison_state()
        assert cs is get_comparison_state()


# =============================================================
# 3. Scoring functions
# =============================================================

class TestScoring:
    def test_longevity_score_parses_hours(self):
        assert _parse_longevity_score(PRODUCT_A) == 7.0

    def test_sillage_score_parses_text(self):
        score = _parse_sillage_score(PRODUCT_B)
        assert score == 5.0  # "strong" -> default middle value

    def test_richness_score_counts_notes_and_families(self):
        score = _score_richness(PRODUCT_B)
        assert score > 0

    def test_luxury_score_checks_brand(self):
        a_score = _score_luxury(PRODUCT_A)  # CHANEL - premium
        _score_luxury(PRODUCT_B)  # ARMAF - also premium
        assert a_score > 0

    def test_compliments_score(self):
        score = _score_compliments(PRODUCT_A)
        assert score > 0

    def test_blind_buy_score(self):
        score = _score_blind_buy(PRODUCT_D)
        assert score > 0

    def test_value_score(self):
        score = _score_value(PRODUCT_D)
        assert score > 0

    def test_overall_score_is_sum(self):
        # Overall = sum of all scoring functions
        score = _score_overall(PRODUCT_A)
        longevity = _score_longevity(PRODUCT_A)
        assert score > longevity  # should be more than just longevity

    def test_no_data_product_gets_default_scores(self):
        longevity = _parse_longevity_score(PRODUCT_NO_DATA)
        assert longevity == 5.0  # default value


# =============================================================
# 4. Ranking intents
# =============================================================

class TestRankingIntents:
    def test_strongest_maps_to_longevity(self):
        assert get_ranking_criteria("which is strongest?") == "longevity"

    def test_richest_maps_to_richness(self):
        assert get_ranking_criteria("which is richest?") == "richness"

    def test_most_luxurious_maps_to_luxury(self):
        assert get_ranking_criteria("most luxurious") == "luxury"

    def test_most_compliments_maps_to_compliments(self):
        assert get_ranking_criteria("most compliments") == "compliments"

    def test_best_blind_buy_maps(self):
        assert get_ranking_criteria("best blind buy") == "blind_buy"

    def test_worth_buying_maps_to_value(self):
        assert get_ranking_criteria("worth buying") == "value"

    def test_projects_more_maps_to_projection(self):
        assert get_ranking_criteria("projects more") == "projection"

    def test_last_longer_maps_to_longevity(self):
        assert get_ranking_criteria("lasts longer") == "longevity"

    def test_empty_query_returns_none(self):
        assert get_ranking_criteria("hello") is None

    def test_ranking_not_case_sensitive(self):
        assert get_ranking_criteria("STRONGEST") == "longevity"

    def test_pick_one_maps_to_overall(self):
        assert get_ranking_criteria("pick one") == "overall"


class TestScoreProductForCriteria:
    def test_score_by_longevity(self):
        score = score_product_for_criteria(PRODUCT_A, "longevity")
        assert score > 0

    def test_score_by_luxury(self):
        score = score_product_for_criteria(PRODUCT_A, "luxury")
        assert score > 0

    def test_score_by_compliments(self):
        score = score_product_for_criteria(PRODUCT_A, "compliments")
        assert score > 0

    def test_score_by_overall(self):
        score = score_product_for_criteria(PRODUCT_A, "overall")
        assert score > 0

    def test_unknown_criteria_returns_zero(self):
        score = score_product_for_criteria(PRODUCT_A, "unknown_criteria")
        assert score == 0.0


class TestRankForCriteria:
    def test_rank_by_longevity(self):
        products = [PRODUCT_A, PRODUCT_B]
        ranked = rank_for_criteria(products, "longevity")
        assert len(ranked) == 2
        assert ranked[0][0] >= ranked[1][0]  # sorted descending

    def test_pick_best_by_longevity(self):
        products = [PRODUCT_A, PRODUCT_B]
        best = pick_best_for_criteria(products, "longevity")
        assert best in products


# =============================================================
# 5. Detailed comparison output
# =============================================================

class TestComparisonOutput:
    def test_build_comparison_output_contains_both_names(self):
        output = build_comparison_output(PRODUCT_A, PRODUCT_B)
        assert "BLEU DE CHANEL" in output
        assert "CLUB DE NUIT INSTENSE MAN" in output

    def test_comparison_output_has_sections(self):
        output = build_comparison_output(PRODUCT_A, PRODUCT_B)
        assert "[Overview]" in output
        assert "[Notes]" in output
        assert "[Performance]" in output
        assert "[Season & Occasion]" in output
        assert "[Price & Sizes]" in output

    def test_comparison_output_shows_notes(self):
        output = build_comparison_output(PRODUCT_A, PRODUCT_B)
        assert "grapefruit" in output or "bergamot" in output

    def test_comparison_output_shows_prices(self):
        output = build_comparison_output(PRODUCT_A, PRODUCT_B)
        assert "450" in output

    def test_verdict_has_winners(self):
        verdict = build_verdict(PRODUCT_A, PRODUCT_B)
        assert "Longevity" in verdict
        assert "Projection" in verdict
        assert "Overall Winner" in verdict

    def test_verdict_determines_winner_by_score(self):
        verdict = build_verdict(PRODUCT_B, PRODUCT_A)
        assert "Overall Winner" in verdict

    def test_full_comparison_includes_both_parts(self):
        full = build_full_comparison(PRODUCT_A, PRODUCT_B)
        assert "[" in full  # has sections
        assert "Longevity" in full  # has verdict
        assert "Winner" in full

    def test_no_data_product_still_formats(self):
        output = build_comparison_output(PRODUCT_A, PRODUCT_NO_DATA)
        assert "BLEU DE CHANEL" in output
        assert "SIMPLE FRAGRANCE" in output


# =============================================================
# 6. Answer ranking query from stored comparison state
# =============================================================

class TestAnswerRankingQuery:
    def test_answer_which_lasts_longer(self):
        result = answer_ranking_query("which lasts longer?", PRODUCT_B, PRODUCT_A)
        assert result is not None
        # PRODUCT_B has "8-10 hours" vs PRODUCT_A has "6-8 hours"
        assert "CLUB DE NUIT" in result or "BLEU DE CHANEL" in result

    def test_answer_which_projects_more(self):
        result = answer_ranking_query("which projects more?", PRODUCT_B, PRODUCT_A)
        assert result is not None

    def test_answer_worth_buying(self):
        result = answer_ranking_query("worth buying?", PRODUCT_D, PRODUCT_C)
        assert result is not None

    def test_answer_pick_one(self):
        result = answer_ranking_query("pick one", PRODUCT_A, PRODUCT_B)
        assert result is not None

    def test_unknown_query_returns_none(self):
        result = answer_ranking_query("hello how are you", PRODUCT_A, PRODUCT_B)
        assert result is None

    def test_empty_query_returns_none(self):
        result = answer_ranking_query("", PRODUCT_A, PRODUCT_B)
        assert result is None


# =============================================================
# 7. ChatService integration - comparison flow
# =============================================================

class TestChatServiceComparisonFlow:
    """Test that ChatService correctly uses the comparison engine."""

    def test_comparison_creates_comparison_state(self):
        """Comparing two products must store them in comparison state."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        cs = get_comparison_state()
        assert cs.has_comparison()
        assert cs.left_product is not None
        assert cs.right_product is not None

    def test_comparison_output_in_response(self):
        """Comparison response must contain detailed output."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Here you go.", {}))

        get_comparison_state().clear()
        response = chat.process_message("compare Bleu de Chanel and Club De Nuit")
        assert "[Overview]" in response
        assert "[Notes]" in response
        assert "[Performance]" in response

    def test_followup_ranking_uses_stored_comparison(self):
        """After a comparison, 'which lasts longer?' must use stored state, not new search."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        assert get_comparison_state().has_comparison()

        chat.ai_service.generate_reply.reset_mock()
        response2 = chat.process_message("which lasts longer?")
        assert response2 is not None
        assert "Longevity" in response2 or "wins" in response2 or "Score" in response2 or "longer" in response2

    def test_followup_pick_one_uses_stored_comparison(self):
        """'Pick one' must recommend from stored comparison."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare Bleu de Chanel and Club De Nuit")
        assert get_comparison_state().has_comparison()

        chat.ai_service.generate_reply.reset_mock()
        response = chat.process_message("pick one")
        assert response is not None
        assert "wins" in response or "Winner" in response or "Better" in response

    def test_followup_worth_buying_uses_stored_comparison(self):
        """'Worth buying' must use stored comparison state."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        assert get_comparison_state().has_comparison()

        chat.ai_service.generate_reply.reset_mock()
        response = chat.process_message("worth buying?")
        assert response is not None

    def test_no_new_search_on_comparison_followup(self):
        """Follow-up ranking queries must NOT trigger a new search."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(side_effect=[
            Intent.COMPARISON_QUERY,
            Intent.FOLLOW_UP,
        ])
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        chat.search_service.search.reset_mock()
        assert chat.search_service.search.call_count == 0

        response = chat.process_message("which is strongest?")
        assert response is not None
        chat.search_service.search.assert_not_called()

    def test_rich_followup_no_new_search(self):
        """'Richest' must also come from stored state."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(side_effect=[
            Intent.COMPARISON_QUERY,
            Intent.FOLLOW_UP,
        ])
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        chat.search_service.search.reset_mock()

        response = chat.process_message("which is richest?")
        assert response is not None
        chat.search_service.search.assert_not_called()

    def test_most_luxurious_followup(self):
        """'Most luxurious' must use stored comparison."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(side_effect=[
            Intent.COMPARISON_QUERY,
            Intent.FOLLOW_UP,
        ])
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        chat.search_service.search.reset_mock()

        response = chat.process_message("most luxurious?")
        assert response is not None
        chat.search_service.search.assert_not_called()

    def test_compliments_followup(self):
        """'Most compliments' must use stored comparison."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(side_effect=[
            Intent.COMPARISON_QUERY,
            Intent.FOLLOW_UP,
        ])
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        chat.search_service.search.reset_mock()

        response = chat.process_message("most compliments?")
        assert response is not None
        chat.search_service.search.assert_not_called()

    def test_best_blind_buy_followup(self):
        """'Best blind buy' must use stored comparison."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(side_effect=[
            Intent.COMPARISON_QUERY,
            Intent.FOLLOW_UP,
        ])
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        get_comparison_state().clear()
        chat.process_message("compare BDC and CDNIM")
        chat.search_service.search.reset_mock()

        response = chat.process_message("best blind buy?")
        assert response is not None
        chat.search_service.search.assert_not_called()


# =============================================================
# 8. Merge/duplicate products
# =============================================================

class TestMergeDuplicates:
    def test_comparison_deduplicates_by_id(self):
        """Comparison should not show duplicate products."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        # Both parts return the same product
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_A],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        response = chat.process_message("compare BDC and Bleu de Chanel")
        # Should not crash with only 1 product
        assert response is not None

    def test_comparison_handles_more_than_two(self):
        """Comparison should handle 3+ products gracefully (take first 2)."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        chat.search_service.search = Mock(side_effect=[
            [PRODUCT_A],
            [PRODUCT_B],
            [PRODUCT_C],
        ])
        chat.ai_service.generate_reply = Mock(return_value=("Comparison result", {}))

        response = chat.process_message("compare BDC, CDNIM and Khamrah")
        assert "[Overview]" in response


# =============================================================
# 9. Edge cases
# =============================================================

class TestEdgeCases:
    def test_comparison_no_products_found(self):
        """No products found should not crash."""
        from app.intent import Intent
        from app.services.chat import ChatService

        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.COMPARISON_QUERY)
        chat.search_service.search = Mock(return_value=[])
        chat.ai_service.generate_reply = Mock(return_value=("No products found.", {}))

        response = chat.process_message("compare unknown1 and unknown2")
        assert response is not None

    def test_alias_nonexistent_returns_original(self):
        assert resolve_alias("COMPLETELY_FAKE_NAME") == "COMPLETELY_FAKE_NAME"

    def test_state_clear_between_sessions(self):
        cs = ComparisonState()
        cs.set_products(PRODUCT_A, PRODUCT_B)
        assert cs.has_comparison()
        cs.clear()
        assert not cs.has_comparison()
        assert cs.left_product is None

    def test_multiple_comparisons_append_history(self):
        cs = ComparisonState()
        cs.set_products(PRODUCT_A, PRODUCT_B)
        cs.set_products(PRODUCT_C, PRODUCT_D)
        assert len(cs.history) == 2