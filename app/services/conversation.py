"""Conversation response service."""

import re

from app.intent import Intent

# Reference pronouns that resolve to the last discussed product
_REFERENCE_PATTERNS = {
    "eta",
    "eitar",
    "oita",
    "oi ta",
    "ei ta",
    "ei tao",
    "eituku",
    "amar perfume",
    "last perfume",
    "previous perfume",
    "this",
    "that",
    "it",
    "this perfume",
    "that perfume",
    "the perfume",
    "eta perfume",
    "oita perfume",
    "seta",
    "shei ta",
    "shei perfume",
    "agor ta",
    "agor perfume",
}


class ConversationService:
    """Handles fixed conversation responses and product context memory."""

    def __init__(self):
        self.last_product: dict | None = None
        self.last_product_name: str | None = None
        self.last_search_products: list[dict] = []
        self.last_filters: dict = {}
        self._product_history: list[dict] = []
        self._product_history_names: list[str] = []

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

        if intent == Intent.BEGINNER:
            return (
                "\nAI:\n"
                "No problem! Let me guide you through the basics.\n\n"
                "Perfumes generally fall into these scent families:\n"
                "• Fresh — clean, citrus, aquatic (great for summer/office)\n"
                "• Sweet/Gourmand — vanilla, caramel, dessert-like\n"
                "• Woody — cedar, sandalwood, vetiver (warm, earthy)\n"
                "• Floral — rose, jasmine, lavender (romantic, elegant)\n"
                "• Oriental/Spicy — amber, spices, incense (warm, rich)\n\n"
                "Tell me what sounds interesting to you, or your budget, "
                "and I'll recommend something perfect for a beginner!"
            )

        if intent == Intent.COLLECTION_BUILDER:
            return (
                "\nAI:\n"
                "I'll help you build a balanced collection covering different occasions! 😊\n\n"
                "Tell me:\n"
                "• Your budget range\n"
                "• How many perfumes you want\n"
                "• Any scent preferences\n\n"
                "I'll make sure each one serves a different purpose."
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
            return "\nAI:\nDelivery typically takes 2-4 business days within Bangladesh. Please contact Scent Of Time for specific delivery timeframes."

        if intent == Intent.PAYMENT:
            return (
                "\nAI:\n"
                "We accept Cash on Delivery (COD) and other available payment methods. "
                "Please contact Scent Of Time to confirm COD availability in your area."
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
        """Store the last searched products and build product history."""
        if products:
            self.last_search_products = products
            self.last_product = products[0] if products else None
            self.last_product_name = self.last_product.get("name") if self.last_product else None

            for p in products:
                name = p.get("name") or ""
                if name and name not in self._product_history_names:
                    self._product_history_names.append(name)
                    self._product_history.append(p)

            self._product_history = self._product_history[-5:]
            self._product_history_names = self._product_history_names[-5:]
        else:
            self.last_search_products = []
            self.last_product = None
            self.last_product_name = None

    def resolve_referenced_product(self, query: str) -> dict | None:
        """Resolve a pronoun reference like 'eta', 'oita', 'this', 'that' to the actual product."""
        if not self._product_history:
            return None
        q = query.lower().strip()
        q_clean = re.sub(r"[?।!,]", "", q).strip()
        words = set(q_clean.split())

        if words & _REFERENCE_PATTERNS:
            return self._product_history[-1]

        for phrase in sorted(_REFERENCE_PATTERNS, key=len, reverse=True):
            if " " in phrase and phrase in q_clean:
                return self._product_history[-1]

        return None

    def resolve_referenced_product_name(self, query: str) -> str | None:
        """Resolve reference and return the product name."""
        prod = self.resolve_referenced_product(query)
        return prod.get("name") if prod else None

    def get_last_product(self) -> dict | None:
        """Get the last mentioned product."""
        return self.last_product

    def get_last_product_name(self) -> str | None:
        """Get the last mentioned product name."""
        return self.last_product_name

    def get_last_search_products(self) -> list[dict]:
        """Get all products from the last search."""
        return self.last_search_products

    def get_product_history(self) -> list[dict]:
        """Get the list of last 5 discussed products."""
        return list(self._product_history)

    def clear_product_context(self):
        """Clear stored product context."""
        self.last_product = None
        self.last_product_name = None
        self.last_search_products = []
        self.last_filters = {}
        self._product_history = []
        self._product_history_names = []
