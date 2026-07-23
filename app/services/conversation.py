"""Conversation response service."""

from app.intent import Intent


class ConversationService:
    """Handles fixed conversation responses and product context memory."""

    def __init__(self):
        self.last_product: dict | None = None
        self.last_product_name: str | None = None
        self.last_search_products: list[dict] = []
        self.last_filters: dict = {}

    def handle(self, intent: Intent) -> str | None:
        """Return response if this intent is handled here."""

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

        if intent == Intent.DELIVERY:
            return "\nAI:\nYes, we provide delivery service."

        if intent == Intent.PAYMENT:
            return (
                "\nAI:\n"
                "We accept available payment methods. "
                "Please contact Scent Of Time for payment details."
            )

        if intent == Intent.LOCATION:
            return (
                "\nAI:\n"
                "Please contact Scent Of Time for our store location."
            )

        if intent == Intent.STORE_INFO:
            return (
                "\nAI:\n"
                "We sell perfumes and fragrance-related products. 😊\n\n"
                "We offer a variety of brands and fragrances for different budgets.\n\n"
                "Tell me:\n"
                "• Your budget\n"
                "• A brand name\n"
                "• A fragrance type\n\n"
                "I'll help you find the best matching products."
            )

        if intent == Intent.ORDER:
            return (
                "\nAI:\n"
                "Great! I can help you place your order. 😊\n\n"
                "Please provide:\n"
                "• Perfume name\n"
                "• Your name\n"
                "• Phone number\n"
                "• Delivery address"
            )

        return None

    def store_product_context(self, products: list[dict], query: str = ""):
        """Store the last searched products and extract single product if available."""
        if products:
            self.last_search_products = products
            # Store the first/most relevant product as the primary context
            self.last_product = products[0] if products else None
            self.last_product_name = self.last_product.get("name") if self.last_product else None
        else:
            self.last_search_products = []
            self.last_product = None
            self.last_product_name = None

    def get_last_product(self) -> dict | None:
        """Get the last mentioned product."""
        return self.last_product

    def get_last_product_name(self) -> str | None:
        """Get the last mentioned product name."""
        return self.last_product_name

    def get_last_search_products(self) -> list[dict]:
        """Get all products from the last search."""
        return self.last_search_products

    def clear_product_context(self):
        """Clear stored product context."""
        self.last_product = None
        self.last_product_name = None
        self.last_search_products = []
        self.last_filters = {}
