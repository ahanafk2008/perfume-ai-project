"""Chat orchestration service."""

import logging
import re

from app.faq import get_faq_answer
from app.intent import Intent, contains_keyword, PRODUCT_KEYWORDS
from app.services.ai import AIService
from app.services.conversation import ConversationService
from app.services.intent import IntentService
from app.services.search import SearchService

logger = logging.getLogger(__name__)

# Lightweight semantic mapping for recommendation queries.
# Maps user keywords to database-friendly tags/keywords.
# ONLY maps to existing concepts; does NOT invent fragrance notes.
SEMANTIC_MAPPING: dict[str, str] = {
    "office": "professional fresh",
    "date night": "romantic",
    "sweet": "sweet gourmand",
    "summer": "fresh",
    "winter": "warm",
    "compliment": "popular",
    "work": "professional fresh",
    "professional": "professional fresh",
    "romantic": "romantic",
    "gourmand": "sweet gourmand",
    "casual": "fresh",
    "daily": "fresh",
    "everyday": "fresh",
    "formal": "warm",
    "party": "popular",
    "club": "popular",
    "gift": "popular",
}


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
        self.last_user_query: str = ""
        self.last_products: list[dict] = []
        self.last_searched: bool = False

    def _extract_product_names(self, user_input: str) -> list[str]:
        """Extract product names from user message using known patterns."""
        # Look for quoted names or capitalized multi-word sequences
        # that look like perfume names.
        names: list[str] = []

        # Quoted strings
        for quoted in re.findall(r'"([^"]+)"', user_input):
            names.append(quoted.strip())

        # Capitalized multi-word tokens (e.g. "Club De Nuit Intense Man")
        cap_matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", user_input)
        names.extend(cap_matches)

        # Clean up duplicates while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for n in names:
            if n and n not in seen:
                seen.add(n)
                unique.append(n)
        return unique

    def _apply_semantic_mapping(self, query: str) -> str:
        """Append mapped keywords for recommendation/orientation queries."""
        mapped_terms = []
        q = query.lower()
        for keyword, mapped in SEMANTIC_MAPPING.items():
            if keyword in q:
                mapped_terms.append(mapped)
        if mapped_terms:
            return query + " " + " ".join(mapped_terms)
        return query

    def _extract_price_range(self, query: str) -> tuple[int | None, int | None]:
        """Extract min_price and max_price from a range query like 'between 3000 and 5000'."""
        q = query.lower()
        min_price = None
        max_price = None

        # Pattern: "between X and Y" or "from X to Y"
        m = re.search(r"(?:between|from)\s+(\d+)\s+(?:and|to)\s+(\d+)", q)
        if m:
            min_price = int(m.group(1))
            max_price = int(m.group(2))
            return min_price, max_price

        # Pattern: "X to Y"
        m = re.search(r"(\d+)\s+to\s+(\d+)", q)
        if m:
            min_price = int(m.group(1))
            max_price = int(m.group(2))
            return min_price, max_price

        # Pattern: single max budget
        m = re.search(r"(?:under|below|upto|up to|max|maximum|budget)\s+(\d+)", q)
        if m:
            max_price = int(m.group(1))
            return min_price, max_price

        return min_price, max_price

    def _search_with_range(
        self,
        query: str,
        min_price: int | None,
        max_price: int | None,
    ) -> list[dict]:
        """Run search and enforce strict price range filtering."""
        products = self.search_service.search(query)
        if not isinstance(products, list):
            products = []

        if min_price is not None or max_price is not None:
            filtered = []
            for p in products:
                try:
                    price = float(p.get("price", 0))
                except (TypeError, ValueError):
                    continue
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue
                filtered.append(p)
            products = filtered
        return products

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

        # Fixed conversation responses.
        conversation_reply = self.conversation_service.handle(intent)
        if conversation_reply and isinstance(conversation_reply, str):
            return conversation_reply

        # Keyword-only FAQ topics.
        faq_answer = get_faq_answer(user_input)
        if faq_answer:
            return f"\nAI:\n{faq_answer}"

        # Determine whether we should reuse previous products for a
        # product-related follow-up (e.g. "which one lasts longer?").
        followup_product_intents = {
            Intent.PRODUCT_SEARCH,
            Intent.PRODUCT_DETAIL,
            Intent.PRODUCT_INFO,
            Intent.PRICE_QUERY,
            Intent.ATTRIBUTE_QUERY,
            Intent.COMPARISON_QUERY,
            Intent.ORDER,
            Intent.FOLLOW_UP,
        }
        # Broad follow-up keywords for conversational reuse.
        followup_keywords = {
            "which one",
            "which is best",
            "best one",
            "lasts longer",
            "longer",
            "better",
            "which should i buy",
            "which one should i buy",
            "compare",
            "comparison",
            "choose",
            "recommend one",
            "kon ta",
            "kun ta bhalo",
            "eituku",
            "ei tao",
            "kon ta bhalo",
            "kon ta valo",
            "kon one",
            "what about",
            "what is the price",
            "how much is",
            "how much does it cost",
            "notes",
            "how long",
            "is it original",
            "original",
            "authentic",
            "description",
            "details",
            "stock",
        }

        normalized_input = user_input.strip().lower()
        intent_is_followup = intent in followup_product_intents
        has_followup_keywords = contains_keyword(user_input, followup_keywords)

        # Reuse previous products when:
        # - intent is product-related
        # - user asks follow-up style keywords OR asks about the same product context
        # - we have previous search results
        reuse_previous_products = (
            intent_is_followup
            and has_followup_keywords
            and self.last_searched
            and self.last_products
        )

        logger.debug(
            "Reuse check | intent=%s | intent_is_followup=%s | has_followup_keywords=%s | last_searched=%s | last_products=%d | reuse=%s",
            intent,
            intent_is_followup,
            has_followup_keywords,
            self.last_searched,
            len(self.last_products),
            reuse_previous_products,
        )

        # Search products.
        searched = False
        products = []

        if reuse_previous_products:
            searched = self.last_searched
            products = self.last_products
        else:
            product_intents = (
                Intent.PRODUCT_SEARCH,
                Intent.PRODUCT_DETAIL,
                Intent.PRODUCT_INFO,
                Intent.PRICE_QUERY,
                Intent.ATTRIBUTE_QUERY,
                Intent.COMPARISON_QUERY,
                Intent.ORDER,
            )

            if intent in product_intents:
                searched = True
            elif intent == Intent.UNKNOWN and contains_keyword(user_input, PRODUCT_KEYWORDS):
                searched = True
            elif intent not in {
                Intent.GREETING,
                Intent.THANKS,
                Intent.GOODBYE,
                Intent.CASUAL,
                Intent.STORE_INFO,
                Intent.DELIVERY,
                Intent.PAYMENT,
                Intent.LOCATION,
                Intent.UNKNOWN,
            }:
                searched = True

            if searched:
                # Build search query with semantic mapping for recommendation/orientation queries.
                search_query = user_input
                if intent in {
                    Intent.PRODUCT_SEARCH,
                    Intent.PRODUCT_DETAIL,
                    Intent.PRODUCT_INFO,
                    Intent.PRICE_QUERY,
                    Intent.ATTRIBUTE_QUERY,
                    Intent.COMPARISON_QUERY,
                    Intent.ORDER,
                }:
                    search_query = self._apply_semantic_mapping(user_input)

                # Price range extraction and strict filtering
                min_price, max_price = self._extract_price_range(user_input)

                products = self._search_with_range(
                    search_query,
                    min_price,
                    max_price,
                )

                logger.debug("Found %d products", len(products))

        # Generate AI response
        ai_output = self.ai_service.generate_reply(
            user_input,
            products,
            searched,
        )

        # Update conversation memory (product context).
        self.last_user_query = user_input
        self.last_searched = searched
        if searched and isinstance(products, list):
            self.last_products = products
            # Store product context in ConversationService for follow-ups
            self.conversation_service.store_product_context(products, user_input)
        if isinstance(ai_output, (tuple, list)):
            reply = ai_output[0]
        else:
            reply = ai_output

        # Format product list (optional for CLI / integrations)
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