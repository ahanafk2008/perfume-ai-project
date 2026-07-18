"""Chat orchestration service."""

import logging

from app.faq import get_faq_answer
from app.intent import Intent
from app.services.ai import AIService
from app.services.conversation import ConversationService
from app.services.intent import IntentService
from app.services.search import SearchService

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates intent detection, product search, and AI interaction."""

    def __init__(
        self,
        intent_service: IntentService | None = None,
        search_service: SearchService | None = None,
        ai_service: AIService | None = None,
        conversation_service: ConversationService | None = None,
    ):
        self.intent_service = (
            intent_service if intent_service is not None else IntentService()
        )

        self.search_service = (
            search_service if search_service is not None else SearchService()
        )

        self.ai_service = (
            ai_service if ai_service is not None else AIService()
        )

        self.conversation_service = (
            conversation_service
            if conversation_service is not None
            else ConversationService()
        )

    def process_message(self, user_input: str) -> str:
        """Process a single user message and return the assistant's reply."""

        if not user_input:
            return "Type something."

        # FAQ responses
        faq_answer = get_faq_answer(user_input)
        if faq_answer:
            return f"\nAI:\n{faq_answer}"

        # Detect intent
        intent = self.intent_service.detect(user_input)
        logger.debug("Detected intent: %s", intent)

        # Fixed conversation responses
        conversation_reply = self.conversation_service.handle(intent)
        if conversation_reply:
            return conversation_reply

        # Search products
        products = []
        searched = False

        if intent != Intent.UNKNOWN:
            searched = True
            products = self.search_service.search(user_input)
            logger.debug("Found %d products", len(products))

        # Generate AI response
        reply, _ = self.ai_service.generate_reply(
            user_input,
            products,
            searched,
        )

        # Format product list (optional for CLI)
        if products:
            product_lines = [
                (
                    f"{product['name']} | "
                    f"{product['brand']} | "
                    f"{product['category']} | "
                    f"৳{product['price']}"
                )
                for product in products
            ]

            product_list = "\n".join(product_lines)

            return (
                f"\nProducts found:\n"
                f"{product_list}\n\n"
                f"AI:\n{reply}"
            )

        return f"\nAI:\n{reply}"