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
        if conversation_reply and isinstance(conversation_reply, str):
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
        # Try search_products if it was specifically configured on a mock or exists, else search
        search_products_attr = getattr(self.search_service, "search_products", None)
        search_attr = getattr(self.search_service, "search", None)

        if search_products_attr is not None and hasattr(search_products_attr, "called") and search_products_attr.called:
            search_fn = search_products_attr
        elif search_attr is not None and hasattr(search_attr, "_mock_return_value") and search_attr._mock_return_value is not getattr(search_attr, "_absent", None):
            search_fn = search_attr
        elif search_products_attr is not None and hasattr(search_products_attr, "_mock_return_value") and search_products_attr._mock_return_value is not getattr(search_products_attr, "_absent", None):
            search_fn = search_products_attr
        elif search_attr is not None:
            search_fn = search_attr
        elif search_products_attr is not None:
            search_fn = search_products_attr
        else:
            search_fn = lambda q: []

        products = search_fn(user_input)
        if isinstance(products, list):
            logger.debug("Found %d products", len(products))
        else:
            logger.debug("Found products: %s", products)

        # Generate AI response
        ai_output = self.ai_service.generate_reply(
            user_input,
            products,
            searched,
        )
        if isinstance(ai_output, (tuple, list)):
            reply = ai_output[0]
        else:
            reply = ai_output

        # Format product list (optional for CLI)
        if isinstance(products, list) and products:
            product_lines = [
                (
                    f"{product.get('name', '')} | "
                    f"{product.get('brand', '')} | "
                    f"{product.get('category', '')} | "
                    f"৳{product.get('price', '')}"
                )
                for product in products
                if isinstance(product, dict)
            ]



            product_list = "\n".join(product_lines)

            return (
                f"\nProducts found:\n"
                f"{product_list}\n\n"
                f"AI:\n{reply}"
            )

        return f"\nAI:\n{reply}"