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

        self.previous_intent: Intent | None = None

    def process_message(self, user_input: str) -> str:
        """Process a single user message and return the assistant's reply."""

        if not user_input:
            return "Type something."

        # Detect intent (with previous-turn context for follow-ups).
        intent = self.intent_service.detect(
            user_input,
            previous_intent=self.previous_intent,
        )
        logger.debug("Detected intent: %s", intent)
        self.previous_intent = intent

        # Fixed conversation responses (greetings, thanks, FAQ, etc.).
        # If this returns a reply, that intent is fully handled and we
        # never reach the search step below.
        conversation_reply = self.conversation_service.handle(intent)
        if conversation_reply:
            return conversation_reply

        # Keyword-only FAQ topics that do not have a dedicated Intent
        # (exchange, return, contact, business hours, etc.). Run after
        # ConversationService so intents with handlers are authoritative
        # and FAQ never double-answers them.
        faq_answer = get_faq_answer(user_input)
        if faq_answer:
            return f"\nAI:\n{faq_answer}"

        # Search products.
        #
        # IMPORTANT: this is intentionally NOT gated on
        # `intent != Intent.UNKNOWN`. Intent detection is keyword-based
        # and can never cover every way a customer phrases a product
        # query (an unlisted brand, a typo, unusual wording). Any of
        # those can legitimately fall through to Intent.UNKNOWN even
        # though the customer is clearly asking about products.
        # Everything that reaches this point has already had a chance
        # to short-circuit above (greetings, FAQ, store info, etc. all
        # return early via conversation_service), so it's always worth
        # attempting a real search here. ChatService owns this
        # decision; SearchService decides what (if anything) matches,
        # and PromptBuilder only formats whatever it's given.
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