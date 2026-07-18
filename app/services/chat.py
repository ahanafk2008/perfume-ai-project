"""Chat orchestration service."""

import logging

from app.faq import get_faq_answer
from app.intent import Intent
from app.services.intent import IntentService
from app.services.ai import AIService
from app.services.search import SearchService

logger = logging.getLogger(__name__)

class ChatService:
    """Orchestrates intent detection, product search, and AI interaction."""

    def __init__(
        self,
        intent_service: IntentService | None = None,
        search_service: SearchService | None = None,
        ai_service: AIService | None = None,
    ):
        self.ai_service = (
            ai_service if ai_service is not None else AIService()
        )

        self.intent_service = (
            intent_service if intent_service is not None else IntentService()
        )

        self.search_service = (
            search_service if search_service is not None else SearchService()
        )

    def process_message(self, user_input: str) -> str:
        """Process a single user message and return the assistant's reply."""
        
        if not user_input:
            return "Type something."

        intent = self.intent_service.detect(user_input)
        print(f"Detected intent: {intent}")

        if intent == Intent.GREETING:
            return (
                "\nAI:\n"
                "Hello! 👋\n\n"
                "Welcome to Scent Of Time.\n\n"
                "I can help you:\n"
                "• Recommend perfumes\n"
                "• Find perfumes within your budget\n"
                "• Suggest gifts\n"
                "• Compare fragrances\n"
                "• Answer product questions\n\n"
                "How can I help you today?"
            )

        if intent == Intent.THANKS:
            return (
                "\nAI:\n"
                "You're welcome! 😊\n"
                "If you need any perfume recommendations, just let me know."
            )

        if intent == Intent.GOODBYE:
            return (
                "\nAI:\n"
                "Thank you for visiting Scent Of Time.\n"
                "Have a wonderful day! 👋"
            )

        faq_answer = get_faq_answer(user_input)
        if faq_answer:
            return f"\nAI:\n{faq_answer}"

        if intent == Intent.DELIVERY:
            return "\nAI:\nYes, we provide delivery service."

        if intent == Intent.PAYMENT:
            return (
                "\nAI:\n"
                "We accept available payment methods. "
                "Please contact Scent Of Time for payment details."
            )

        if intent == Intent.LOCATION:
            return "\nAI:\nPlease contact Scent Of Time for our store location."

        if intent == Intent.ORDER:
            return (
                "\nAI:\n"
                "Great! I can help you place your order. 😊\n\n"
                "Please provide:\n"
                "• Perfume name\n"
                "• Your name\n"
                "• Phone number\n"
                "• Delivery address\n\n"
                "Once I have these details, we can proceed with your order."
            )

        if intent == Intent.UNKNOWN:
            products = self.search_service.search(user_input)
            print(f"Found {len(products)} products")
            reply, _ = self.ai_service.generate_reply(user_input, products)
            return f"\nAI:\n{reply}"

        # Product Search
        products = self.search_service.search(user_input)
        print(f'Found {len(products)} products')

        product_list_str = ""
        if products:
            product_list_str += "\nProducts found:\n"
            for product in products:
                product_list_str += (
                    f"{product['name']} | "
                    f"{product['brand']} | "
                    f"{product['category']} | "
                    f"৳{product['price']}\n"
                )

        reply, _ = self.ai_service.generate_reply(user_input, products)
        
        # We append the product list before the AI reply to match the previous CLI behavior exactly
        # where it printed the products, and then the AI reply.
        if product_list_str:
            return f"{product_list_str}\nAI:\n{reply}"
        
        return f"\nAI:\n{reply}"
