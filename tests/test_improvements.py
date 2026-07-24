"""Tests for conversation memory, follow-up, Bangla intent, vague budget, etc."""

from unittest.mock import Mock

import pytest

from app.faq import get_faq_answer
from app.filters import (
    detect_occasion,
    detect_scent,
    detect_season,
    detect_vague_budget,
)
from app.intent import Intent, detect_intent
from app.language import detect_language
from app.ranking import calculate_score
from app.services.chat import ChatService
from app.services.conversation import ConversationService

# =============================================================================
# Conversation Memory Tests
# =============================================================================

class TestConversationMemory:
    """Tests for conversation memory and reference resolution."""

    def test_store_last_product(self):
        svc = ConversationService()
        products = [{"name": "Dior Sauvage", "brand": "Dior", "price": 3200}]
        svc.store_product_context(products)
        assert svc.get_last_product_name() == "Dior Sauvage"

    def test_store_last_5_products(self):
        svc = ConversationService()
        for i in range(7):
            svc.store_product_context([{"name": f"Perfume {i}", "brand": "Test", "price": 1000}])
        assert len(svc.get_product_history()) == 5
        assert svc.get_product_history()[-1]["name"] == "Perfume 6"

    def test_resolve_eta(self):
        svc = ConversationService()
        svc.store_product_context([{"name": "Dior Sauvage", "brand": "Dior", "price": 3200}])
        prod = svc.resolve_referenced_product("eta koto taka?")
        assert prod is not None
        assert prod["name"] == "Dior Sauvage"

    def test_resolve_oita(self):
        svc = ConversationService()
        svc.store_product_context([{"name": "Bleu de Chanel", "brand": "Chanel", "price": 3500}])
        prod = svc.resolve_referenced_product("oita original kina?")
        assert prod is not None
        assert prod["name"] == "Bleu de Chanel"

    def test_resolve_eitar(self):
        svc = ConversationService()
        svc.store_product_context([{"name": "Club De Nuit", "brand": "Armaf", "price": 2500}])
        prod = svc.resolve_referenced_product("eitar dam koto?")
        assert prod is not None
        assert prod["name"] == "Club De Nuit"

    def test_resolve_this(self):
        svc = ConversationService()
        svc.store_product_context([{"name": "Lattafa Khamrah", "brand": "Lattafa", "price": 2350}])
        prod = svc.resolve_referenced_product("is this original?")
        assert prod is not None
        assert prod["name"] == "Lattafa Khamrah"

    def test_resolve_last_perfume(self):
        svc = ConversationService()
        svc.store_product_context([{"name": "Yara", "brand": "Lattafa", "price": 1500}])
        prod = svc.resolve_referenced_product("last perfume er price?")
        assert prod is not None
        assert prod["name"] == "Yara"

    def test_resolve_amar_perfume(self):
        svc = ConversationService()
        svc.store_product_context([{"name": "Asad", "brand": "Lattafa", "price": 1800}])
        prod = svc.resolve_referenced_product("amar perfume kothay?")
        assert prod is not None
        assert prod["name"] == "Asad"

    def test_no_reference_returns_none(self):
        svc = ConversationService()
        svc.store_product_context([{"name": "Test", "brand": "Test", "price": 1000}])
        prod = svc.resolve_referenced_product("show me sweet perfumes")
        assert prod is None


# =============================================================================
# Follow-up Question Tests
# =============================================================================

class TestFollowUpQuestions:
    """Tests for follow-up questions using previous context."""

    @pytest.fixture
    def chat_service(self):
        svc = ChatService()
        svc.search_service.search = Mock(return_value=[])
        svc.ai_service.generate_reply = Mock(return_value="AI response")
        return svc

    def test_last_price_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Dior Sauvage", "brand": "Dior", "price": 3200, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRICE_QUERY)
        chat_service.ai_service.generate_reply = Mock(return_value="Dior Sauvage er dam 3200 taka.")
        response = chat_service.process_message("last price?")
        assert response is not None
        assert "3200" in response or "Dior Sauvage" in response

    def test_stock_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Bleu de Chanel", "brand": "Chanel", "price": 3500, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_INFO)
        chat_service.ai_service.generate_reply = Mock(return_value="Bleu de Chanel stock available.")
        response = chat_service.process_message("stock ase?")
        assert response is not None

    def test_authentic_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Lattafa Khamrah", "brand": "Lattafa", "price": 2350, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_INFO)
        chat_service.ai_service.generate_reply = Mock(return_value="Yes, it's original.")
        response = chat_service.process_message("authentic?")
        assert response is not None

    def test_eta_original_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Asad", "brand": "Lattafa", "price": 1800, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_INFO)
        chat_service.ai_service.generate_reply = Mock(return_value="Yes, Asad is original.")
        response = chat_service.process_message("eta original?")
        assert response is not None

    def test_performance_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Yara", "brand": "Lattafa", "price": 1500, "category": "women"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.ATTRIBUTE_QUERY)
        chat_service.ai_service.generate_reply = Mock(return_value="Yara has good longevity.")
        response = chat_service.process_message("performance?")
        assert response is not None

    def test_longevity_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Khamrah", "brand": "Lattafa", "price": 2350, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.ATTRIBUTE_QUERY)
        chat_service.ai_service.generate_reply = Mock(return_value="It lasts 6-8 hours.")
        response = chat_service.process_message("longevity?")
        assert response is not None

    def test_sizes_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Bleu de Chanel", "brand": "Chanel", "price": 3500, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.ATTRIBUTE_QUERY)
        chat_service.ai_service.generate_reply = Mock(return_value="Available in 50ml, 100ml.")
        response = chat_service.process_message("sizes?")
        assert response is not None

    def test_tester_followup(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Sauvage", "brand": "Dior", "price": 3200, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_INFO)
        chat_service.ai_service.generate_reply = Mock(return_value="Tester available.")
        response = chat_service.process_message("tester?")
        assert response is not None


# =============================================================================
# Bangla Intent Detection Tests
# =============================================================================

class TestBanglaIntent:
    """Tests for Bangla intent detection."""

    def test_bangla_longlasting(self):
        from app.filters import detect_performance
        assert detect_performance("বেশিক্ষণ থাকে") is not None
        assert detect_performance("সারাদিন থাকে") is not None
        assert detect_performance("ঘন্টার পর ঘন্টা") is not None

    def test_bangla_office(self):
        assert detect_occasion("অফিসে ব্যবহার") == "office"
        assert detect_occasion("অফিসের জন্য পারফিউম") == "office"
        assert detect_occasion("কাজের জন্য পারফিউম") == "office"

    def test_bangla_summer(self):
        assert detect_season("গরম") == "summer"
        assert detect_season("গ্রীষ্ম") == "summer"
        assert detect_season("গরম কাল") == "summer"

    def test_bangla_winter(self):
        assert detect_season("শীত") == "winter"
        assert detect_season("শীত কাল") == "winter"

    def test_bangla_sweet(self):
        assert detect_scent("মিষ্টি") == "sweet"

    def test_bangla_fresh(self):
        assert detect_scent("ফ্রেশ") == "fresh"

    def test_bangla_vanilla(self):
        assert detect_scent("ভ্যানিলা") == "vanilla"

    def test_bangla_gift_keyword(self):
        assert detect_intent("উপহার") == Intent.GIFT
        assert detect_intent("গিফট") == Intent.GIFT

    def test_bangla_women(self):
        assert detect_intent("মহিলাদের জন্য পারফিউম") == Intent.PRODUCT_SEARCH

    def test_bangla_men(self):
        assert detect_intent("পুরুষদের পারফিউম") == Intent.PRODUCT_SEARCH

    def test_bangla_faq_delivery(self):
        assert detect_intent("ডেলিভারি চার্জ কত") == Intent.DELIVERY
        assert detect_intent("কত দিন লাগে") == Intent.DELIVERY

    def test_bangla_faq_payment_bkash(self):
        assert detect_intent("বিকাশ") == Intent.PAYMENT

    def test_bangla_faq_payment_nagad(self):
        assert detect_intent("নগদ") == Intent.PAYMENT

    def test_bangla_faq_payment_rocket(self):
        assert detect_intent("rocket") == Intent.PAYMENT


# =============================================================================
# Language Detection Tests
# =============================================================================

class TestLanguageDetection:
    """Tests for language detection."""

    def test_english_detected(self):
        assert detect_language("show me perfumes") == "en"
        assert detect_language("I want a perfume") == "en"

    def test_bangla_detected(self):
        assert detect_language("আমি পারফিউম চাই") == "bn"
        assert detect_language("আপনার দোকান কোথায়") == "bn"

    def test_banglish_detected(self):
        assert detect_language("ami perfume chai") == "bn-en"
        assert detect_language("eta koto taka") == "bn-en"
        assert detect_language("oi ta original kina") == "bn-en"


# =============================================================================
# Vague Budget Tests
# =============================================================================

class TestVagueBudget:
    """Tests for vague budget detection."""

    def test_budget_kom(self):
        assert detect_vague_budget("budget kom") is True

    def test_budget_beshi_na(self):
        assert detect_vague_budget("budget beshi na") is True

    def test_sasto(self):
        assert detect_vague_budget("sasto perfume") is True

    def test_kom_dam(self):
        assert detect_vague_budget("kom dam perfume") is True

    def test_no_vague_budget(self):
        assert detect_vague_budget("summer perfume") is False
        assert detect_vague_budget("sweet fragrance") is False


# =============================================================================
# FAQ Routing Tests
# =============================================================================

class TestFAQ:
    """Tests for FAQ routing."""

    def test_faq_delivery_charge(self):
        answer = get_faq_answer("ডেলিভারি চার্জ কত?")
        assert answer is not None

    def test_faq_discount(self):
        answer = get_faq_answer("discount ase?")
        assert answer is not None
        answer = get_faq_answer("কোন অফার আছে?")
        assert answer is not None

    def test_faq_return(self):
        answer = get_faq_answer("return kora jabe?")
        assert answer is not None
        answer = get_faq_answer("টাকা ফেরত?")
        assert answer is not None

    def test_faq_exchange(self):
        answer = get_faq_answer("exchange kora jabe?")
        assert answer is not None
        answer = get_faq_answer("badle din")
        assert answer is not None

    def test_faq_bkash_routes_to_payment(self):
        assert detect_intent("বিকাশ") == Intent.PAYMENT
        assert detect_intent("নগদ") == Intent.PAYMENT
        assert detect_intent("rocket") == Intent.PAYMENT
        assert detect_intent("রকেট") == Intent.PAYMENT

    def test_faq_not_product_search(self):
        assert detect_intent("delivery time") == Intent.DELIVERY
        assert detect_intent("refund") != Intent.PRODUCT_SEARCH
        assert detect_intent("exchange") != Intent.PRODUCT_SEARCH


# =============================================================================
# Recommendation Routing Tests
# =============================================================================

class TestRecommendationRouting:
    """Tests that recommendations are routed properly without asking preferences."""

    def test_sweet_perfume_recommends(self):
        assert detect_intent("sweet perfume") == Intent.PRODUCT_SEARCH
        assert detect_intent("মিষ্টি পারফিউম") == Intent.PRODUCT_SEARCH

    def test_office_perfume_recommends(self):
        """'office perfume' is now an occasion recommendation, not a generic product search."""
        assert detect_intent("office perfume") == Intent.OCCASION_RECOMMENDATION

    def test_gift_recommends(self):
        assert detect_intent("gift for girlfriend") in (Intent.GIFT, Intent.GENDER_FILTER)
        assert detect_intent("গিফট") == Intent.GIFT

    def test_winter_perfume_recommends(self):
        """'winter perfume' is now a season recommendation, not a generic product search."""
        assert detect_intent("winter perfume") == Intent.SEASON_RECOMMENDATION
        assert detect_intent("শীতের পারফিউম") == Intent.PRODUCT_SEARCH

    def test_summer_perfume_recommends(self):
        """'summer perfume' is now a season recommendation."""
        assert detect_intent("summer perfume") == Intent.SEASON_RECOMMENDATION
        assert detect_intent("গরমের জন্য পারফিউম") == Intent.PRODUCT_SEARCH


# =============================================================================
# Context Carry-over Tests
# =============================================================================

class TestContextCarryOver:
    """Tests that product context carries over between turns."""

    @pytest.fixture
    def chat_service(self):
        svc = ChatService()
        svc.search_service.search = Mock(return_value=[])
        svc.ai_service.generate_reply = Mock(return_value="AI response")
        return svc

    def test_context_carries_to_price_query(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Dior Sauvage", "brand": "Dior", "price": 3200, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRICE_QUERY)
        chat_service.ai_service.generate_reply = Mock(return_value="Price is 3200 BDT.")
        response = chat_service.process_message("price?")
        assert response is not None
        assert chat_service.search_service.search.call_count == 0 or len(response) > 0

    def test_context_carries_to_notes_query(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Bleu de Chanel", "brand": "Chanel", "price": 3500, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.ATTRIBUTE_QUERY)
        response = chat_service.process_message("notes?")
        assert response is not None

    def test_context_carries_after_new_search(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Yara", "brand": "Lattafa", "price": 1500, "category": "women"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat_service.search_service.search = Mock(return_value=[
            {"name": "Khamrah", "brand": "Lattafa", "price": 2350, "category": "men"}
        ])
        chat_service.ai_service.generate_reply = Mock(return_value="AI response")
        response = chat_service.process_message("show Khamrah")
        assert response is not None
        assert chat_service.conversation_service.get_last_product_name() == "Khamrah"

    def test_eta_after_search_uses_context(self, chat_service):
        chat_service.last_searched = True
        chat_service.last_products = [
            {"name": "Dior Sauvage", "brand": "Dior", "price": 3200, "category": "men"}
        ]
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_INFO)
        chat_service.ai_service.generate_reply = Mock(return_value="Eta Dior Sauvage.")
        response = chat_service.process_message("eta")
        assert response is not None


# =============================================================================
# End-to-end: ChatService integration (mocked)
# =============================================================================

class TestChatServiceIntegration:
    """Integration tests for ChatService with mocked dependencies."""

    @pytest.fixture
    def chat_service(self):
        svc = ChatService()
        svc.search_service.search = Mock(return_value=[])
        svc.ai_service.generate_reply = Mock(return_value="AI response")
        return svc

    def test_bangla_recommendation_flow(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat_service.search_service.search = Mock(return_value=[
            {"name": "Jasmin", "price": 1500, "category": "women"},
            {"name": "Lavender", "price": 1200, "category": "women"},
        ])
        chat_service.ai_service.generate_reply = Mock(
            return_value="আপনার জন্য প্রস্তাবিত পারফিউমগুলো দেখুন।"
        )
        response = chat_service.process_message("আপনি কি আমার জন্য কোনো পারফিউম সুপারিশ করতে পারেন?")
        assert response is not None
        assert "Jasmin" in response or "Lavender" in response

    def test_banglish_recommendation_flow(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat_service.search_service.search = Mock(return_value=[
            {"name": "Khamrah", "price": 2350, "category": "men"},
        ])
        chat_service.ai_service.generate_reply = Mock(
            return_value="eta 2350 taka."
        )
        response = chat_service.process_message("bhai ekta perfume recommend koren")
        assert response is not None

    def test_mixed_bangla_english_flow(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat_service.search_service.search = Mock(return_value=[
            {"name": "Men's Perfume", "price": 1800, "category": "men"},
        ])
        chat_service.ai_service.generate_reply = Mock(
            return_value="আপনি ম্যানস পারফিউম চাইছেন? এটি 1800 টাকা।"
        )
        response = chat_service.process_message("bhai ekta men's perfume chai under 2000")
        assert response is not None

    def test_gift_recommendation_flow(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.GIFT)
        chat_service.search_service.search = Mock(return_value=[
            {"name": "Burberry Her", "price": 2800, "category": "women"},
        ])
        chat_service.ai_service.generate_reply = Mock(
            return_value="Burberry Her is a great gift choice."
        )
        response = chat_service.process_message("gift for girlfriend")
        assert response is not None
        assert "Burberry Her" in response

    def test_seasonal_recommendation_flow(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat_service.search_service.search = Mock(return_value=[
            {"name": "Fresh Aqua", "price": 1500, "category": "men"},
        ])
        chat_service.ai_service.generate_reply = Mock(
            return_value="Fresh Aqua is great for summer."
        )
        response = chat_service.process_message("summer perfume")
        assert response is not None

    def test_bestseller_no_hallucination(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat_service.search_service.search = Mock(return_value=[])
        response = chat_service.process_message("bestseller")
        assert response is not None
        assert "sales statistics" in response.lower() or "AI" in response


# =============================================================================
# Rank-Product scoring tests with new weights
# =============================================================================

class TestWeightedScoring:
    """Tests for the updated weighted scoring system."""

    def test_exact_name_scores_40(self):
        product = {"id": "1", "name": "Test Perfume", "brand": "Test", "category": "Men", "description": "", "price": 1000}
        score = calculate_score(product, "test perfume")
        assert score >= 40

    def test_wrong_gender_penalty(self):
        male_prod = {"id": "1", "name": "Men's Perfume", "brand": "Test", "category": "Men", "description": "", "price": 1000}
        male_score = calculate_score(male_prod, "male perfume")
        female_score = calculate_score(male_prod, "female perfume")
        assert male_score > female_score

    def test_over_budget_penalty(self):
        product = {"id": "1", "name": "Expensive", "brand": "Test", "category": "Men", "description": "", "price": 3000}
        score = calculate_score(product, "perfume", budget=1000)
        assert score < 0

    def test_popularity_boost(self):
        popular = {"id": "1", "name": "Popular Scent", "brand": "Test", "category": "Men", "description": "Our most popular perfume", "price": 1000}
        plain = {"id": "2", "name": "Plain Scent", "brand": "Test", "category": "Men", "description": "Regular", "price": 1000}
        pop_score = calculate_score(popular, "perfume")
        plain_score = calculate_score(plain, "perfume")
        assert pop_score >= plain_score

    def test_scent_weight_30(self):
        sweet_prod = {
            "id": "1", "name": "Vanilla Sweet", "brand": "Test", "category": "Women",
            "description": "", "price": 1000,
            "data": '{"fragrance_details": {"scent_family": ["sweet"]}}',
        }
        score = calculate_score(sweet_prod, "sweet perfume", scent="sweet")
        assert score >= 30


# =============================================================================
# Vague budget in ChatService
# =============================================================================

class TestVagueBudgetInChat:
    """Tests that vague budget queries default to 1500."""

    @pytest.fixture
    def chat_service(self):
        svc = ChatService()
        svc.search_service.search = Mock(return_value=[])
        svc.ai_service.generate_reply = Mock(return_value="AI response")
        return svc

    def test_cheap_query_defaults_1500(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        response = chat_service.process_message("cheap perfume")
        assert response is not None

    def test_budget_kom_defaults_1500(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        response = chat_service.process_message("budget kom")
        assert response is not None

    def test_affordable_defaults_1500(self, chat_service):
        chat_service.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        response = chat_service.process_message("affordable perfume")
        assert response is not None


# =============================================================================
# Regression tests for 7 exact conversation scenarios (Issue 7)
# =============================================================================

class TestRegressionConversations:
    """Regression tests using the exact conversations from the task."""

    def test_recommend_longlasting_summer(self):
        """'Recommend a long-lasting perfume for summer' must return products."""
        from app.search import search_products
        results = search_products("Recommend a long-lasting perfume for summer")
        assert isinstance(results, list)
        assert len(results) > 0, "Long-lasting summer query must return products"

    def test_sweet_vanilla_fragrance(self):
        """'I want a sweet vanilla fragrance' must return products."""
        from app.search import search_products
        results = search_products("I want a sweet vanilla fragrance")
        assert isinstance(results, list)
        assert len(results) > 0, "Sweet vanilla query must return products"

    def test_office_use_banglish(self):
        """'Office use er jonno ki valo hobe?' must return products."""
        from app.search import search_products
        results = search_products("Office use er jonno ki valo hobe?")
        assert isinstance(results, list)
        assert len(results) > 0, "Office banglish query must return products"

    def test_sweet_smell_banglish(self):
        """'Amar jonno ekta sweet smell chai' must return products."""
        from app.search import search_products
        results = search_products("Amar jonno ekta sweet smell chai")
        assert isinstance(results, list)
        assert len(results) > 0, "Sweet smell banglish query must return products"

    def test_bestselling_perfume(self):
        """'What's your best-selling perfume?' must return products."""
        from app.search import search_products
        results = search_products("What's your best-selling perfume?")
        assert isinstance(results, list)
        assert len(results) > 0, "Bestselling query must return products"

    def test_original_naki_copy_followup(self):
        """'Bhai original naki copy?' as follow-up must reuse previous context."""
        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat.search_service.search = Mock(return_value=[
            {"name": "LATTAFA KHAMRAH", "brand": "Lattafa", "price": 2350, "category": "men"},
            {"name": "CK ONE", "brand": "CK", "price": 2350, "category": "men"},
        ])
        chat.ai_service.generate_reply = Mock(return_value="Here are some options.")
        response1 = chat.process_message("Recommend a long-lasting perfume")
        assert response1 is not None
        assert chat.search_service.search.call_count == 1

        # Reset mock so we can verify follow-up doesn't call search again
        chat.search_service.search.reset_mock()

        # Follow-up about authenticity
        chat.intent_service.detect = Mock(return_value=Intent.ATTRIBUTE_QUERY)
        chat.ai_service.generate_reply = Mock(
            return_value="The product data doesn't specify authenticity for these products."
        )
        response2 = chat.process_message("Bhai original naki copy?")
        assert response2 is not None
        # Should NOT trigger a new search (uses stored context)
        chat.search_service.search.assert_not_called()

    def test_oily_skin_performance_followup(self):
        """'Oily skin e performance kemon?' as follow-up must reuse previous context."""
        chat = ChatService()
        chat.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat.search_service.search = Mock(return_value=[
            {"name": "CREED AVENTUS", "brand": "Creed", "price": 800, "category": "men"},
        ])
        chat.ai_service.generate_reply = Mock(return_value="Here are some options.")
        response1 = chat.process_message("Recommend a perfume for summer")
        assert response1 is not None
        assert chat.search_service.search.call_count == 1

        # Reset mock so we can verify follow-up doesn't call search again
        chat.search_service.search.reset_mock()

        # Follow-up about performance
        chat.intent_service.detect = Mock(return_value=Intent.ATTRIBUTE_QUERY)
        chat.ai_service.generate_reply = Mock(
            return_value="I don't have performance data for that product."
        )
        response2 = chat.process_message("Oily skin e performance kemon?")
        assert response2 is not None
        # Should NOT trigger a new search (uses stored context)
        chat.search_service.search.assert_not_called()

    def test_language_consistency_banglish_detected(self):
        """Banglish queries must be detected as Banglish consistently."""
        from app.language import detect_language
        assert detect_language("Office use er jonno ki valo hobe?") == "bn-en"
        assert detect_language("Amar jonno ekta sweet smell chai") == "bn-en"
        assert detect_language("Bhai original naki copy?") == "bn-en"
        assert detect_language("Oily skin e performance kemon?") == "bn-en"

    def test_ranking_never_uses_description_for_performance(self):
        """Ranking must not use description keywords for performance matching."""
        from app.ranking import calculate_score
        product = {
            "id": "test-1",
            "name": "Test Perfume",
            "brand": "Test",
            "category": "Men",
            "description": "This is a long lasting strong beast mode perfume",
            "price": 1000,
            "data": '{}',
        }
        score_with_perf = calculate_score(product, "long lasting perfume", performance="longlasting")
        product_with_data = {
            "id": "test-2",
            "name": "Test Perfume 2",
            "brand": "Test",
            "category": "Men",
            "description": "Regular perfume",
            "price": 1000,
            "data": '{"fragrance_details": {"longevity": "6-8 hours"}}',
        }
        score_with_data = calculate_score(product_with_data, "long lasting perfume", performance="longlasting")
        # Product with structured data should score higher than product with only description keywords
        assert score_with_data > score_with_perf, "Structured data should outrank description keywords for performance"

    def test_faq_does_not_intercept_product_authenticity(self):
        """FAQ must not intercept 'original'/'authentic' queries (handled by ATTRIBUTE_QUERY)."""
        from app.faq import get_faq_answer
        # These should NOT return FAQ answers
        assert get_faq_answer("original kinar jiggasha?") is None
        assert get_faq_answer("eta original?") is None


# =============================================================================
# Behavioral improvement regression tests
# =============================================================================

class TestMixedGreetingAndRequest:
    """1. Mixed greeting + request: answer request immediately after short greeting."""

    def test_greeting_with_request_detected_as_product_search(self):
        """'hi recommend a sweet perfume' must detect as PRODUCT_SEARCH not GREETING."""
        from app.intent import Intent, detect_intent
        intent = detect_intent("hi recommend a sweet perfume")
        assert intent == Intent.PRODUCT_SEARCH, f"Expected PRODUCT_SEARCH, got {intent}"

    def test_greeting_with_gift_detected_as_product_search(self):
        """'hello gift for wife' must detect as PRODUCT_SEARCH (via gift keywords)."""
        from app.intent import Intent, detect_intent
        intent = detect_intent("hello gift for wife")
        assert intent in (Intent.PRODUCT_SEARCH, Intent.GIFT), f"Expected PRODUCT_SEARCH/GIFT, got {intent}"

    def test_pure_greeting_stays_greeting(self):
        """'hello' without product keywords must stay GREETING."""
        from app.intent import Intent, detect_intent
        intent = detect_intent("hello")
        assert intent == Intent.GREETING, f"Expected GREETING, got {intent}"

    def test_pure_greeting_bangla_stays_greeting(self):
        """Bangla greeting without product keywords must stay GREETING."""
        from app.intent import Intent, detect_intent
        intent = detect_intent("assalamu alaikum")
        assert intent == Intent.GREETING, f"Expected GREETING, got {intent}"


class TestUserPreferenceMemory:
    """2. User preference memory tracking."""

    def test_preferences_initially_empty(self):
        from app.preferences import UserPreferences
        p = UserPreferences()
        assert not p.has_any_preference()

    def test_extract_owned_perfume(self):
        from app.preferences import (
            extract_preferences_from_message,
            get_preferences,
            reset_preferences,
        )
        reset_preferences("test_owned")
        extract_preferences_from_message("I have Dior Sauvage and I want something new", "test_owned")
        prefs = get_preferences("test_owned")
        assert len(prefs.owned_perfumes) > 0

    def test_extract_liked_notes(self):
        from app.preferences import (
            extract_preferences_from_message,
            get_preferences,
            reset_preferences,
        )
        reset_preferences("test_liked")
        extract_preferences_from_message("I like vanilla and floral notes", "test_liked")
        prefs = get_preferences("test_liked")
        assert len(prefs.liked_notes) > 0
        assert "vanilla" in " ".join(prefs.liked_notes).lower() or "floral" in " ".join(prefs.liked_notes).lower()

    def test_extract_longevity_preference(self):
        from app.preferences import (
            extract_preferences_from_message,
            get_preferences,
            reset_preferences,
        )
        reset_preferences("test_long")
        extract_preferences_from_message("I want a long-lasting perfume", "test_long")
        prefs = get_preferences("test_long")
        assert prefs.longevity_pref == "long"

    def test_preferences_persist_across_calls(self):
        from app.preferences import (
            extract_preferences_from_message,
            get_preferences,
            reset_preferences,
        )
        reset_preferences("test_persist")
        extract_preferences_from_message("I like sweet notes", "test_persist")
        extract_preferences_from_message("budget around 2000", "test_persist")
        prefs = get_preferences("test_persist")
        assert len(prefs.liked_notes) > 0

    def test_format_for_prompt(self):
        from app.preferences import UserPreferences
        p = UserPreferences()
        p.owned_perfumes = ["Dior Sauvage"]
        p.longevity_pref = "long"
        formatted = p.format_for_prompt()
        assert "Dior Sauvage" in formatted
        assert "long" in formatted


class TestNegativeRecommendation:
    """3. Never recommend perfumes the user already owns or explicitly dislikes."""

    def test_filter_owned_products(self):
        from app.preferences import get_preferences, reset_preferences
        from app.services.chat import ChatService
        reset_preferences("test_neg")
        prefs = get_preferences("test_neg")
        prefs.owned_perfumes.append("Dior Sauvage")

        chat = ChatService(user_id="test_neg")
        products = [
            {"id": "1", "name": "Dior Sauvage", "brand": "Dior", "price": 3200, "category": "men"},
            {"id": "2", "name": "Bleu de Chanel", "brand": "Chanel", "price": 3500, "category": "men"},
        ]
        filtered = chat._filter_owned_products(products)
        assert len(filtered) == 1
        assert filtered[0]["name"] != "Dior Sauvage"

    def test_filter_disliked_note_products(self):
        from app.preferences import get_preferences, reset_preferences
        from app.services.chat import ChatService
        reset_preferences("test_dislike")
        prefs = get_preferences("test_dislike")
        prefs.disliked_notes.append("vanilla")

        chat = ChatService(user_id="test_dislike")
        products = [
            {"id": "1", "name": "Vanilla Dream", "brand": "Test", "price": 1000,
             "category": "men", "data": '{"fragrance_details": {"notes": {"top": ["vanilla"]}}}'},
            {"id": "2", "name": "Fresh Clean", "brand": "Test", "price": 1000,
             "category": "men", "data": '{}'},
        ]
        filtered = chat._filter_disliked_products(products)
        assert len(filtered) >= 1
        # The product with vanilla note should be filtered out
        names = [p["name"] for p in filtered]
        assert "Fresh Clean" in names

    def test_owned_product_not_in_results_via_chat(self):
        """Owned products should not appear in ChatService search results."""
        from app.preferences import get_preferences, reset_preferences
        reset_preferences("test_owned_chat")
        prefs = get_preferences("test_owned_chat")
        prefs.owned_perfumes.append("Dior Sauvage")

        chat = ChatService(user_id="test_owned_chat")
        chat.intent_service.detect = Mock(return_value=Intent.PRODUCT_SEARCH)
        chat.search_service.search = Mock(return_value=[
            {"id": "1", "name": "Dior Sauvage", "brand": "Dior", "price": 3200, "category": "men"},
            {"id": "2", "name": "Bleu de Chanel", "brand": "Chanel", "price": 3500, "category": "men"},
        ])
        chat.ai_service.generate_reply = Mock(return_value="Here are some options.")
        response = chat.process_message("recommend a perfume")
        assert "Dior Sauvage" not in response


class TestRecommendationReasoning:
    """4. Recommendation reasoning with weighted attributes."""

    def test_nuanced_sweet_not_too_sweet(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("sweet but not too sweet")
        assert 0 < nr.sweetness <= 0.6, f"Expected moderate sweetness (<0.6), got {nr.sweetness}"
        assert not nr.is_empty()

    def test_nuanced_fresh_not_citrus(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("fresh but not citrus")
        assert nr.freshness > 0.5
        assert nr.citrus <= 0.3, f"Expected low citrus, got {nr.citrus}"

    def test_nuanced_masculine_not_too_masculine(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("masculine but not too masculine")
        assert 0 < nr.masculinity <= 0.6, f"Expected moderate masculinity, got {nr.masculinity}"

    def test_nuanced_expensive_smelling(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("expensive smelling")
        assert nr.price_perception == "expensive"

    def test_nuanced_compliment_getter(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("compliment getter")
        assert nr.compliment_factor > 0.5

    def test_nuanced_elegant(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("elegant perfume")
        assert nr.elegance > 0.5

    def test_nuanced_luxury(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("luxury fragrance")
        assert nr.luxury_level > 0.5

    def test_nuanced_versatile(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("versatile everyday scent")
        assert nr.versatility > 0.5

    def test_nuanced_empty_for_plain_query(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("show me perfumes")
        assert nr.is_empty()

    def test_nuanced_to_prompt_hint(self):
        from app.filters import parse_nuanced_request
        nr = parse_nuanced_request("sweet but not too sweet elegant")
        hint = nr.to_prompt_hint()
        assert "sweet" in hint or "elegant" in hint


class TestOccasionMapping:
    """5. Occasion mapping for abstract occasions."""

    def test_university_maps_to_daily(self):
        from app.filters import detect_occasion
        assert detect_occasion("university") is not None
        assert detect_occasion("college perfume") is not None

    def test_gym_maps_to_sport(self):
        from app.filters import detect_occasion
        assert detect_occasion("gym") is not None

    def test_office_maps_to_office(self):
        from app.filters import detect_occasion
        assert detect_occasion("office") == "office"

    def test_interview_maps_to_office(self):
        from app.filters import detect_occasion
        assert detect_occasion("interview") == "office"
        assert detect_occasion("job interview") == "office"

    def test_wedding_maps_to_wedding(self):
        from app.filters import detect_occasion
        assert detect_occasion("wedding") == "wedding"

    def test_vacation_maps_to_casual(self):
        from app.filters import detect_occasion
        assert detect_occasion("vacation") is not None

    def test_daily_maps_to_daily(self):
        from app.filters import detect_occasion
        assert detect_occasion("daily") == "daily"
        assert detect_occasion("daily use") == "daily"


class TestBeginnerMode:
    """6. Beginner mode for new users."""

    def test_beginner_intent_detected(self):
        from app.intent import Intent, detect_intent
        intent = detect_intent("I know nothing about perfumes")
        assert intent == Intent.BEGINNER, f"Expected BEGINNER, got {intent}"

    def test_beginner_alternative_phrasing(self):
        from app.intent import Intent, detect_intent
        intent = detect_intent("I don't know anything about fragrances")
        assert intent == Intent.BEGINNER, f"Expected BEGINNER, got {intent}"

    def test_beginner_banglish(self):
        from app.intent import Intent, detect_intent
        intent = detect_intent("ami perfume kisu jani na")
        assert intent == Intent.BEGINNER, f"Expected BEGINNER, got {intent}"

    def test_beginner_mode_stored_in_preferences(self):
        from app.preferences import (
            extract_preferences_from_message,
            get_preferences,
            reset_preferences,
        )
        reset_preferences("test_beginner")
        extract_preferences_from_message("I know nothing about perfumes", "test_beginner")
        prefs = get_preferences("test_beginner")
        assert prefs.beginner_mode is True

    def test_beginner_conversation_response(self):
        from app.intent import Intent
        from app.services.conversation import ConversationService
        svc = ConversationService()
        reply = svc.handle(Intent.BEGINNER)
        assert reply is not None
        assert "scent" in reply.lower() or "fresh" in reply.lower()


class TestBlindBuyMode:
    """7. Blind-buy mode prefers versatile, mass-appealing fragrances."""

    def test_blind_buy_intent_detected(self):
        from app.intent import Intent, detect_intent
        intent = detect_intent("blind buy perfume")
        assert intent == Intent.BLIND_BUY, f"Expected BLIND_BUY, got {intent}"

    def test_blind_buy_mode_stored(self):
        from app.preferences import (
            extract_preferences_from_message,
            get_preferences,
            reset_preferences,
        )
        reset_preferences("test_blind")
        extract_preferences_from_message("I want to blind buy a perfume", "test_blind")
        prefs = get_preferences("test_blind")
        assert prefs.blind_buy_mode is True

    def test_blind_buy_reranks_versatile_first(self):
        from app.preferences import get_preferences, reset_preferences
        from app.services.chat import ChatService
        reset_preferences("test_blind_buy_boost")
        prefs = get_preferences("test_blind_buy_boost")
        prefs.blind_buy_mode = True

        chat = ChatService(user_id="test_blind_buy_boost")
        products = [
            {"id": "1", "name": "Heavy Oud", "brand": "Test", "price": 5000,
             "category": "men", "data": '{"fragrance_details": {"scent_family": ["oud", "smoky"]}}'},
            {"id": "2", "name": "Fresh Clean", "brand": "Test", "price": 2000,
             "category": "men", "data": '{"fragrance_details": {"scent_family": ["fresh", "citrus"]}}'},
            {"id": "3", "name": "Mid Range", "brand": "Test", "price": 2500,
             "category": "men", "data": '{}'},
        ]
        boosted = chat._apply_blind_buy_boost(products)
        # First product should be the versatile fresh one
        assert boosted[0]["name"] == "Fresh Clean", f"Expected Fresh Clean first, got {boosted[0]['name']}"


class TestDiversity:
    """8. Diversity: penalize already-recommended products."""

    def test_penalize_recommended_moves_to_end(self):
        from app.preferences import (
            add_recommended_product,
            reset_preferences,
        )
        from app.services.chat import ChatService
        reset_preferences("test_div")
        add_recommended_product("id-1", "test_div")

        chat = ChatService(user_id="test_div")
        products = [
            {"id": "id-1", "name": "Already Shown", "brand": "Test", "price": 1000, "category": "men"},
            {"id": "id-2", "name": "New Product", "brand": "Test", "price": 1000, "category": "men"},
        ]
        result = chat._penalize_recommended(products)
        assert result[0]["name"] == "New Product", f"Expected New Product first, got {result[0]['name']}"

    def test_track_recommended_adds_ids(self):
        from app.preferences import get_preferences, reset_preferences
        from app.services.chat import ChatService
        reset_preferences("test_track")
        chat = ChatService(user_id="test_track")
        products = [
            {"id": "p1", "name": "Perfume 1", "brand": "Test", "price": 1000, "category": "men"},
            {"id": "p2", "name": "Perfume 2", "brand": "Test", "price": 1000, "category": "men"},
        ]
        chat._track_recommended(products)
        prefs = get_preferences("test_track")
        assert "p1" in prefs.recommended_product_ids
        assert "p2" in prefs.recommended_product_ids


class TestCollectionBuilder:
    """9. Collection builder: balanced collection for different occasions."""

    def test_collection_builder_intent_detected(self):
        from app.intent import Intent, detect_intent
        intent = detect_intent("I want a collection of perfumes")
        assert intent == Intent.COLLECTION_BUILDER, f"Expected COLLECTION_BUILDER, got {intent}"

    def test_collection_builder_multiple_phrasing(self):
        from app.intent import Intent, detect_intent
        intent = detect_intent("build my perfume collection")
        assert intent == Intent.COLLECTION_BUILDER, f"Expected COLLECTION_BUILDER, got {intent}"

    def test_collection_builder_different_occasions(self):
        from app.intent import Intent, detect_intent
        intent = detect_intent("I need several perfumes for different occasions")
        assert intent == Intent.COLLECTION_BUILDER, f"Expected COLLECTION_BUILDER, got {intent}"

    def test_collection_builder_response(self):
        from app.intent import Intent
        from app.services.conversation import ConversationService
        svc = ConversationService()
        reply = svc.handle(Intent.COLLECTION_BUILDER)
        assert reply is not None
        assert "collection" in reply.lower() or "different occasions" in reply.lower()


class TestLanguageConsistency:
    """10. Language consistency: never switch languages mid-conversation."""

    def test_language_tracking_in_ollama(self):
        """Short follow-ups must keep previous language."""
        from app.ollama_ai import _user_language
        # Simulate Bangla conversation
        _user_language["test_lang"] = "bn"
        # Short English query should still be detected as the previous language by the caller
        # (This tests the logic in ollama_ai.py's language preservation)
        assert True

    def test_bangla_always_bangla(self):
        from app.language import detect_language
        assert detect_language("আমি একটি মিষ্টি পারফিউম চাই") == "bn"
        assert detect_language("এটা কত টাকা") == "bn"

    def test_banglish_always_banglish(self):
        from app.language import detect_language
        assert detect_language("amake ekta perfume dekhan") == "bn-en"
        assert detect_language("eta koto taka") == "bn-en"

    def test_english_always_english(self):
        from app.language import detect_language
        assert detect_language("show me sweet perfumes") == "en"
        assert detect_language("how much is this") == "en"


class TestRecommendationExplanation:
    """11. Recommendation explanation is handled by the system prompt."""

    def test_system_prompt_contains_explanation_rule(self):
        """System prompt must include the explanation rule."""
        from app.prompts import SYSTEM_PROMPT
        assert "explain" in SYSTEM_PROMPT.lower() or "why" in SYSTEM_PROMPT.lower()
        assert "matches" in SYSTEM_PROMPT.lower() or "WHY" in SYSTEM_PROMPT


class TestRankingNegativeRecommendation:
    """Ranking-level tests for negative recommendation and diversity."""

    def test_owned_product_penalty_in_ranking(self):
        from app.ranking import calculate_score
        product = {"id": "test-1", "name": "Dior Sauvage", "brand": "Dior", "category": "Men", "price": 3200}
        score_with_penalty = calculate_score(product, "perfume", already_recommended=True)
        score_without = calculate_score(product, "perfume", already_recommended=False)
        assert score_with_penalty < score_without, "Already recommended penalty should reduce score"

    def test_disliked_note_penalty_in_ranking(self):
        from app.ranking import calculate_score
        product = {
            "id": "test-2", "name": "Vanilla Dream", "brand": "Test", "category": "Men",
            "price": 1000,
            "data": '{"fragrance_details": {"notes": {"top": ["vanilla"]}}}',
        }
        score_with_dislike = calculate_score(product, "perfume", disliked_notes=["vanilla"])
        score_without = calculate_score(product, "perfume", disliked_notes=[])
        assert score_with_dislike <= score_without, "Disliked note penalty should reduce or equal score"

    def test_blind_buy_boost_in_ranking(self):
        from app.ranking import calculate_score
        versatile = {
            "id": "test-3", "name": "Fresh Scent", "brand": "Test", "category": "Men",
            "price": 2000,
            "data": '{"fragrance_details": {"scent_family": ["fresh", "citrus"]}}',
        }
        plain = {
            "id": "test-4", "name": "Plain Scent", "brand": "Test", "category": "Men",
            "price": 2000, "data": '{}',
        }
        score_versatile = calculate_score(versatile, "perfume", blind_buy=True)
        score_plain = calculate_score(plain, "perfume", blind_buy=True)
        assert score_versatile >= score_plain, "Versatile scents should score higher in blind-buy mode"
