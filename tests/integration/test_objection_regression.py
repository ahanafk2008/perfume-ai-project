"""Regression tests: customer objections must NOT trigger product search.

When a user raises a sales objection, price concern, trust issue, etc.,
the chatbot should respond like a sales representative, NOT a search engine.
"""

from unittest.mock import Mock

import pytest

from app.services.ai import AIService
from app.services.chat import ChatService
from app.services.intent import IntentService
from app.services.search import SearchService

OBJECTION_MESSAGES = [
    "Why is your price so high?",
    "Daraz is cheaper",
    "Another page sells cheaper",
    "Give me discount",
    "Last price?",
    "Free delivery?",
    "I won't buy unless you reduce price",
    "Convince me",
    "Why should I buy from you?",
    "I don't trust online shops",
]


@pytest.fixture
def real_intent_service():
    """Use the real intent detector (not mocked) to ensure correct routing."""
    return IntentService()


@pytest.fixture
def mock_search_service():
    search = Mock(spec=SearchService)
    return search


@pytest.fixture
def mock_ai_generator():
    ai = Mock(spec=AIService)
    ai.generate_reply.return_value = ("AI reply", {})
    return ai


@pytest.fixture
def conversation_service():
    from app.services.conversation import ConversationService
    return ConversationService()


@pytest.fixture
def chat_service(real_intent_service, mock_search_service, mock_ai_generator, conversation_service):
    return ChatService(
        intent_service=real_intent_service,
        search_service=mock_search_service,
        ai_service=mock_ai_generator,
        conversation_service=conversation_service,
    )


class TestObjectionsDoNotTriggerProductSearch:
    """Each of these objections should be handled WITHOUT calling SearchService."""

    @pytest.mark.parametrize("message", OBJECTION_MESSAGES)
    def test_no_search_for_objection(self, chat_service, mock_search_service, message):
        response = chat_service.process_message(message)
        mock_search_service.search.assert_not_called()
        assert response is not None
        assert "AI:" in response

    @pytest.mark.parametrize("message", OBJECTION_MESSAGES)
    def test_objection_response_is_sales_representative(self, chat_service, message):
        response = chat_service.process_message(message)
        # Should not contain product table headers
        assert "Products found:" not in response
        # Should feel like a human response
        assert len(response) > 20

    def test_regular_product_search_still_works(self, chat_service, mock_search_service):
        """Verify normal product search is NOT broken by the changes."""
        mock_search_service.search.return_value = [
            {"id": "1", "name": "Test Perfume", "price": "1500", "brand": "Test"}
        ]
        response = chat_service.process_message("Show me perfumes")
        mock_search_service.search.assert_called_once()
        assert "Products found:" in response

    def test_price_objection_with_product_name(self, chat_service, mock_search_service):
        """When user says 'Why is CDNIM expensive?', objection handler uses product name."""
        response = chat_service.process_message("Why is CDNIM expensive?")
        mock_search_service.search.assert_not_called()
        assert "CDNIM" in response
