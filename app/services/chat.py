"""Chat orchestration service."""

import logging
import re
import string
from typing import ClassVar

from app.aliases import get_ranking_criteria, resolve_alias
from app.comparison_engine import (
    answer_ranking_query,
    build_full_comparison,
    get_comparison_state,
)
from app.database import fetch_products
from app.faq import get_faq_answer
from app.filters import extract_budget
from app.intent import (
    COMPARISON_QUERY_KEYWORDS,
    PRODUCT_KEYWORDS,
    Intent,
    contains_keyword,
)
from app.objection_handler import handle_intent as handle_objection
from app.preferences import (
    add_recommended_product,
    extract_preferences_from_message,
    get_preferences,
    is_owned,
)
from app.recommendation_engine import RecommendationEngine
from app.search import exact_name_search
from app.services.ai import AIService
from app.services.conversation import ConversationService
from app.services.intent import IntentService
from app.services.search import SearchService
from app.state import get_conversation_state

logger = logging.getLogger(__name__)

# Lightweight semantic mapping for recommendation queries.
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
    "university": "fresh",
    "gym": "fresh aquatic",
    "interview": "professional fresh",
    "wedding": "romantic elegant",
    "vacation": "fresh casual",
}

# Reference pronouns that resolve to the last discussed product
_PRONOUN_REFERENCES = {
    "eta", "eitar", "oita", "oi ta", "ei ta", "ei tao", "eituku",
    "amar perfume", "last perfume", "previous perfume",
    "this", "that", "it",
    "this perfume", "that perfume", "the perfume",
    "seta", "shei ta", "shei perfume", "agor ta", "agor perfume",
}

# Vague budget keywords that default to 1500
_VAGUE_BUDGET_KEYWORDS = {
    "budget kom", "budget beshi na", "kom budget",
    "cheap", "affordable", "low budget", "sasto",
    "kom dam", "komdami", "budget e", "bekar",
}

# Sales-related keywords (best seller, popular, etc.)
_SALES_KEYWORDS = {
    "best seller", "best sellers", "bestseller",
    "most sold", "best selling", "bestselling",
    "best-selling", "best-sellers",
    "popular", "most popular",
    "top selling", "top seller", "top sellers",
    "top-selling", "top-seller",
    "most bought",
}

# Attribute queries that should resolve from stored product context
_PRODUCT_ATTRIBUTE_QUERIES = {
    "original", "authentic", "tester",
    "available", "stock", "stock ase",
    "performance", "longevity", "projection",
    "sizes", "size", "ml",
    "notes", "sillage",
    "last price", "price", "dam koto",
    "original kina", "eta original",
    "আসল", "এটা আসল", "কিনা",
    "tester ache", "original kinar",
}

# Single-recommendation keywords that should return exactly one product
_SINGLE_RECOMMENDATION_KEYWORDS = {
    "just one", "pick one", "recommend one", "only one",
    "single", "ekta", "ekti", "একটা", "একটি",
}

# Follow-up keywords that reuse previous recommendation context instead of fresh search
_RECOMMENDATION_FOLLOWUP_KEYWORDS = {
    "just one", "pick one", "recommend one", "another", "only one",
    "cheaper", "more expensive", "cheapest",
    "better one", "next option", "safest choice",
    "best blind buy", "your favorite",
    "kon ta", "kun ta bhalo", "seta", "oita",
}


class ChatService:
    """Orchestrates intent detection, product search, and AI interaction."""

    def __init__(
        self,
        intent_service: IntentService | None = None,
        search_service: SearchService | None = None,
        ai_service: AIService | None = None,
        conversation_service: ConversationService | None = None,
        user_id: str = "cli",
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
        self.user_id: str = user_id

    def _extract_product_names(self, user_input: str) -> list[str]:
        """Extract product names from user message using known patterns."""
        names: list[str] = []

        for quoted in re.findall(r'"([^"]+)"', user_input):
            names.append(quoted.strip())

        cap_matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", user_input)
        names.extend(cap_matches)

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

        m = re.search(r"(?:between|from)\s+[\u09f3]?\s*(\d+)\s+(?:and|to)\s+[\u09f3]?\s*(\d+)", q)
        if m:
            min_price = int(m.group(1))
            max_price = int(m.group(2))
            return min_price, max_price

        m = re.search(r"[\u09f3]?\s*(\d+)\s+to\s+[\u09f3]?\s*(\d+)", q)
        if m:
            min_price = int(m.group(1))
            max_price = int(m.group(2))
            return min_price, max_price

        m = re.search(r"(?:under|below|upto|up to|max|maximum|budget|within)\s+[\u09f3]?\s*(\d+)", q)
        if m:
            max_price = int(m.group(1))
            return min_price, max_price

        m = re.search(r"(?:less than|cheaper than)\s+[\u09f3]?\s*(\d+)", q)
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
        """Run search and enforce strict price range filtering.

        Budget is a HARD filter: products over budget are never returned.
        """
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
        else:
            # Even without explicit price range, still enforce accumulated budget
            # (already merged into max_price by caller, but guard here too)
            pass

        return products

    def _apply_refinement(self, products: list[dict], refinement: str) -> list[dict]:
        """Filter products based on refinement type."""
        if refinement == "original_only":
            filtered = []
            for p in products:
                from app.product_attrs import get_product_attributes
                attrs = get_product_attributes(p)
                origin = (attrs.get("product_origin") or "").lower().strip()
                if origin == "original" or not origin:
                    filtered.append(p)
            return filtered
        if refinement == "clone_only":
            filtered = []
            for p in products:
                from app.product_attrs import get_product_attributes
                attrs = get_product_attributes(p)
                origin = (attrs.get("product_origin") or "").lower().strip()
                if origin == "inspired":
                    filtered.append(p)
            return filtered
        if refinement == "no_combo":
            from app.ranking import _is_combo_product
            return [p for p in products if not _is_combo_product(p)]
        return products

    def _format_product_list(self, products: list[dict]) -> str:
        """Format product list for display."""
        lines = []
        for product in products:
            if isinstance(product, dict):
                lines.append(
                    f"{product.get('name', '')} | "
                    f"{product.get('brand', '')} | "
                    f"{product.get('category', '')} | "
                    f"৳{product.get('price', '')}"
                )
        return "\n".join(lines)

    def _has_vague_budget(self, query: str) -> bool:
        """Detect vague budget intent like 'budget kom', 'cheap', etc."""
        q = query.lower().strip()
        for phrase in _VAGUE_BUDGET_KEYWORDS:
            if phrase in q:
                return True
        return False

    def _is_sales_question(self, query: str) -> bool:
        """Detect if user is asking about best sellers or popular products."""
        q = query.lower().strip()
        for phrase in _SALES_KEYWORDS:
            if phrase in q:
                return True
        return False

    def _is_attribute_followup(self, query: str) -> bool:
        """Detect if query asks about a product attribute that should use stored context."""
        q = query.lower().strip()
        q_clean = re.sub(r"[?।!,]", "", q).strip()
        for phrase in _PRODUCT_ATTRIBUTE_QUERIES:
            if phrase in q_clean:
                return True
        return False

    def _build_comparison_table(self, products: list[dict]) -> str:
        """Build a markdown comparison table for 2+ products."""
        rows: list[str] = []
        headers = ["Feature"] + [p.get("name", f"Product {i+1}") for i, p in enumerate(products)]
        rows.append("| " + " | ".join(headers) + " |")
        rows.append("| " + " | ".join(["---"] * len(headers)) + " |")

        features = [
            ("Brand", lambda p: p.get("brand", "")),
            ("Category", lambda p: p.get("category", "")),
            ("Price", lambda p: f"৳{p.get('price', '')}"),
        ]

        for feat_name, extractor in features:
            vals = [extractor(p) for p in products]
            rows.append("| " + " | ".join([feat_name] + vals) + " |")

        return "\n".join(rows)

    def _handle_comparison(
        self,
        query: str,
        min_price: int | None,
        max_price: int | None,
    ) -> list[dict]:
        """Search for each product in a comparison query separately.

        Uses alias resolution and deduplicates by product ID.
        """
        q = query.lower().strip()

        for kw in sorted(COMPARISON_QUERY_KEYWORDS, key=len, reverse=True):
            q = q.replace(kw, "")
        q = re.sub(r"\s+", " ", q).strip()

        parts = re.split(r"\s+(?:and|vs|or|,\s*)\s+", q)
        parts = [p.strip() for p in parts if p.strip()]

        found: list[dict] = []
        seen_ids: set[str] = set()

        for part in parts:
            resolved = resolve_alias(part)
            results = self.search_service.search(resolved)
            if not results and resolved != part:
                results = self.search_service.search(part)
            if results:
                for p in results:
                    pid = p.get("id")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        found.append(p)

        if not found:
            return []

        if min_price is not None or max_price is not None:
            filtered = []
            for p in found:
                try:
                    price = float(p.get("price", 0))
                except (TypeError, ValueError):
                    continue
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue
                filtered.append(p)
            return filtered

        return found

    def _filter_owned_products(self, products: list[dict]) -> list[dict]:
        """Filter out products the user already owns."""
        prefs = get_preferences(self.user_id)
        if not prefs.owned_perfumes:
            return products
        filtered = []
        for p in products:
            name = p.get("name", "")
            if name and is_owned(name, self.user_id):
                logger.debug("Filtering out owned product: %s", name)
                continue
            filtered.append(p)
        return filtered

    def _filter_disliked_products(self, products: list[dict]) -> list[dict]:
        """Filter out products containing notes the user dislikes."""
        prefs = get_preferences(self.user_id)
        if not prefs.disliked_notes:
            return products
        from app.ranking import _has_disliked_note
        filtered = []
        for p in products:
            if _has_disliked_note(p, prefs.disliked_notes):
                name = p.get("name", "")
                logger.debug("Filtering out disliked product: %s", name)
                continue
            filtered.append(p)
        return filtered

    def _penalize_recommended(self, products: list[dict]) -> list[dict]:
        """Move already-recommended products to the end of the list."""
        prefs = get_preferences(self.user_id)
        if not prefs.recommended_product_ids:
            return products
        fresh = []
        repeated = []
        for p in products:
            pid = str(p.get("id", ""))
            name = str(p.get("name", ""))
            if pid in prefs.recommended_product_ids or any(name.lower() in rec_name.lower() for rec_name in prefs.owned_perfumes):
                repeated.append(p)
            else:
                fresh.append(p)
        return fresh + repeated

    def _apply_blind_buy_boost(self, products: list[dict]) -> list[dict]:
        """In blind-buy mode, prefer versatile/mass-appealing products."""
        prefs = get_preferences(self.user_id)
        if not prefs.blind_buy_mode:
            return products
        from app.product_attrs import get_product_attributes
        scored = []
        for p in products:
            score = 0
            attrs = get_product_attributes(p)
            scent_family = attrs.get("scent_family")
            if scent_family and isinstance(scent_family, list):
                sf_text = " ".join(s.lower() for s in scent_family)
                for kw in ("fresh", "clean", "citrus", "aquatic", "aromatic", "light"):
                    if kw in sf_text:
                        score += 10
            try:
                price = float(p.get("price", 0))
                if 1000 <= price <= 3000:
                    score += 15
            except (TypeError, ValueError):
                pass
            # Avoid polarizing notes
            if scent_family and isinstance(scent_family, list):
                sf_text = " ".join(s.lower() for s in scent_family)
                for kw in ("oud", "animalic", "leather", "smoky", "incense"):
                    if kw in sf_text:
                        score -= 20
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored]

    def _track_recommended(self, products: list[dict]) -> None:
        """Track product IDs as having been recommended."""
        for p in products:
            pid = str(p.get("id", ""))
            if pid:
                add_recommended_product(pid, self.user_id)

    def _get_all_products(self) -> list[dict]:
        """Get *all* products for recommendation ranking (broad fetch).

        Fetches all products directly from the database, then
        the recommendation engine scores them.
        """
        return fetch_products()

    def _format_response(self, reply: str, products: list[dict] | None = None) -> str:
        """Unified response formatter. All public-facing responses go through this."""
        if products:
            product_list = self._format_product_list(products)
            return (
                f"\nProducts found:\n"
                f"{product_list}\n\n"
                f"AI:\n{reply}"
            )
        return f"\nAI:\n{reply}"

    _RECOMMENDATION_INTENTS: ClassVar[set[Intent]] = {
        Intent.BEST_RECOMMENDATION,
        Intent.LUXURY_RECOMMENDATION,
        Intent.GENDER_FILTER,
        Intent.BUDGET_RECOMMENDATION,
        Intent.OCCASION_RECOMMENDATION,
        Intent.SEASON_RECOMMENDATION,
        Intent.STYLE_RECOMMENDATION,
        Intent.GIFT_RECOMMENDATION,
        Intent.BLIND_BUY,
        Intent.COLLECTION_BUILDER,
    }

    def _is_single_recommendation_query(self, query: str) -> bool:
        q = query.lower().strip()
        return any(kw in q for kw in _SINGLE_RECOMMENDATION_KEYWORDS)

    def _is_recommendation_followup(self, query: str) -> bool:
        q = query.lower().strip()
        return any(kw in q for kw in _RECOMMENDATION_FOLLOWUP_KEYWORDS)

    def _rerank_for_followup(self, products: list[dict], query: str) -> list[dict]:
        q = query.lower().strip()
        if "cheaper" in q or "cheapest" in q or "affordable" in q:
            products = sorted(products, key=lambda p: float(p.get("price", 0) or 0))
        elif "more expensive" in q:
            products = sorted(products, key=lambda p: -float(p.get("price", 0) or 0))
        elif "safest choice" in q or "safe" in q or "best blind buy" in q or "blind buy" in q:
            from app.comparison_engine import _score_blind_buy
            products = sorted(products, key=lambda p: -_score_blind_buy(p))
        return products

    def _build_collection(
        self,
        products: list[dict],
    ) -> list[dict]:
        """Build a diverse collection covering different occasions."""
        from app.product_attrs import get_product_attributes

        occasion_map = {
            "office": [],
            "party": [],
            "daily": [],
            "date": [],
            "sport": [],
        }

        for p in products:
            attrs = get_product_attributes(p)
            occ_list = attrs.get("occasion")
            assigned = False
            if occ_list and isinstance(occ_list, list):
                for o in occ_list:
                    ol = o.lower()
                    for key, value in occasion_map.items():
                        if key in ol:
                            value.append(p)
                            assigned = True
                            break
                    if assigned:
                        break
            if not assigned:
                occasion_map["daily"].append(p)

        collection = []
        seen_ids = set()
        for key in ["daily", "office", "party", "date", "sport"]:
            for p in occasion_map[key]:
                pid = p.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    collection.append(p)
                    break

        # Fill remaining slots with top-ranked products
        if len(collection) < 5:
            for p in products:
                pid = p.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    collection.append(p)
                if len(collection) >= 5:
                    break

        return collection[:5]

    def _handle_recommendation(
        self,
        user_input: str,
        intent: Intent,
    ) -> str | None:
        """Handle a recommendation intent.

        Returns a formatted response string, or None if the intent
        is not a recommendation.
        """
        if intent not in self._RECOMMENDATION_INTENTS:
            return None

        is_single = self._is_single_recommendation_query(user_input)
        is_followup = self._is_recommendation_followup(user_input)
        state = get_conversation_state(self.user_id)

        # If we have previous recommendations and this is a follow-up, reuse context
        if is_followup and state.last_recommended_products and self.last_searched:
            products = list(state.last_recommended_products)

            # Re-rank based on follow-up intent
            products = self._rerank_for_followup(products, user_input)

            # Apply preference-based filtering
            products = self._filter_owned_products(products)
            products = self._filter_disliked_products(products)
            products = self._penalize_recommended(products)

            # Apply budget from current query if present
            budget = extract_budget(user_input)
            if budget is not None:
                products = [p for p in products if float(p.get("price", 0) or 0) <= budget]

            # Limit to single if requested
            if is_single and products:
                products = [products[0]]

            if not products:
                state = get_conversation_state(self.user_id)
                last_rec = state.last_recommended_products
                return self._format_empty_recommendation(user_input, last_rec)

            product_list = self._format_product_list(products)
            rec_type = RecommendationEngine().get_recommendation_type(intent)

            self.last_user_query = user_input
            self.last_searched = True
            self.last_products = products
            self.conversation_service.store_product_context(products, user_input)
            state.store_recommendation(user_input, products)

            return (
                f"\nAI:\n"
                f"🌟 {rec_type}\n\n"
                f"{product_list}\n\n"
                f"Here are my top suggestions! "
                f"Would you like more details on any of these?"
            )

        engine = RecommendationEngine()
        all_products = self._get_all_products()
        if not all_products:
            return (
                "\nAI:\n"
                "I don't have any products available right now. "
                "Please check back later!"
            )

        max_results = 10
        if intent == Intent.COLLECTION_BUILDER:
            max_results = 20
        elif is_single:
            max_results = 1

        ranked = engine.recommend(
            all_products,
            user_input,
            intent,
            max_results=max_results,
            user_id=self.user_id,
        )

        if not ranked:
            return self._format_empty_recommendation(user_input, [])

        # Apply preference-based filtering
        ranked = self._filter_owned_products(ranked)
        ranked = self._filter_disliked_products(ranked)
        ranked = self._penalize_recommended(ranked)

        # For collection builder, build diverse collection
        if intent == Intent.COLLECTION_BUILDER:
            ranked = self._build_collection(ranked)

        # Track these as recommended for future diversity
        self._track_recommended(ranked)

        rec_type = engine.get_recommendation_type(intent)
        product_lines = []
        for product in ranked:
            name = product.get("name", "")
            brand = product.get("brand", "")
            price = product.get("price", "")
            reason = product.get("ranking_reason", "")
            product_lines.append(
                f"• {name} | {brand} | ৳{price}"
            )
            if reason:
                product_lines.append(f"  → {reason}")

        product_list = "\n".join(product_lines)

        self.last_user_query = user_input
        self.last_searched = True
        self.last_products = ranked
        self.conversation_service.store_product_context(ranked, user_input)
        state = get_conversation_state(self.user_id)
        state.store_recommendation(user_input, ranked)

        return (
            f"\nAI:\n"
            f"🌟 {rec_type}\n\n"
            f"{product_list}\n\n"
            f"Here are my top suggestions! "
            f"Would you like more details on any of these?"
        )

    def _format_empty_recommendation(
        self,
        user_input: str,
        products: list[dict],
    ) -> str:
        active_filters = []
        prefs = get_preferences(self.user_id)
        if prefs.budget is not None:
            active_filters.append(f"under ৳{prefs.budget}")
        if prefs.gender:
            active_filters.append(f"for {prefs.gender}")
        if prefs.occasion:
            active_filters.append(f"for {prefs.occasion}")
        if prefs.weather:
            active_filters.append(f"for {prefs.weather}")
        if prefs.style:
            active_filters.append(f"{prefs.style} scent")
        if prefs.clone_pref == "original_only":
            active_filters.append("originals only")
        elif prefs.clone_pref == "clone_only":
            active_filters.append("clones only")
        if prefs.disliked_notes:
            active_filters.append(f"no {', '.join(prefs.disliked_notes[:2])}")
        from app.filters import detect_brand
        b = detect_brand(user_input)
        if b:
            active_filters.append(f"brand: {b}")

        if active_filters:
            filter_str = " ".join(active_filters)
            msg = (
                f"No {filter_str} products were found. "
                f"Try removing one filter or expanding your budget."
            )
        elif not products:
            msg = (
                "I couldn't find matching products. "
                "Could you try different preferences?"
            )
        else:
            msg = "No products matched all your criteria. Try relaxing one filter."

        return f"\nAI:\n{msg}"

    def _detect_ambiguity(self, query: str) -> str | None:
        """Detect contradictory or ambiguous requests.

        Returns a clarification question if ambiguity is detected, else None.
        """
        q = query.lower().strip()
        ambiguities = []

        # Fresh but warm (contradictory)
        has_fresh = any(w in q for w in ("fresh", "aquatic", "marine", "citrus", "clean"))
        has_warm = any(w in q for w in ("warm", "spicy", "oriental", "amber", "rich", "cozy"))
        if has_fresh and has_warm:
            ambiguities.append("You mentioned both 'fresh' and 'warm' — those lean in opposite directions. "
                               "Would you like something fresh (light, aquatic) or warm (spicy, amber)?")

        # Sweet but not sweet
        has_sweet = any(w in q for w in ("sweet", "vanilla", "gourmand", "sugary", "candy"))
        has_not_sweet = any(w in q for w in ("not sweet", "not too sweet", "but not sweet", "no vanilla"))
        if has_sweet and has_not_sweet:
            ambiguities.append("You mentioned 'sweet' but also said 'not sweet'. "
                               "Should I look for a lightly sweet scent (balanced) or avoid sweetness entirely?")

        # Strong but not overpowering
        has_strong = any(w in q for w in ("strong", "powerful", "intense", "beast"))
        has_not_overpowering = any(w in q for w in ("not overpowering", "not too strong", "not heavy", "not intense"))
        if has_strong and has_not_overpowering:
            ambiguities.append("You asked for 'strong' but also 'not overpowering'. "
                               "Do you want moderate strength with good projection, or something softer?")

        # Summer perfume for winter
        season_words_q = set()
        for s, kw in {"summer": {"summer", "hot", "sunny", "spring", "warm"},
                       "winter": {"winter", "cold", "chilly", "fall", "autumn"}}.items():
            if any(w in q for w in kw):
                season_words_q.add(s)
        if len(season_words_q) >= 2:
            ambiguities.append("You mentioned both summer and winter preferences. "
                               "Do you want a versatile all-season scent, or a specific seasonal pick?")

        if ambiguities:
            return ambiguities[0]

        return None

    def _detect_refinement(self, query: str) -> str | None:
        """Detect if the query is a refinement of previous results.

        Returns the refinement type if detected, else None.
        """
        q = query.lower().strip()
        if re.search(r"(?:only|show|want|filter)\s+(?:original|authentic|real)", q) or q in ("original", "authentic", "only original", "only authentic", "show original", "show authentic"):
            return "original_only"
        if re.search(r"(?:no|without|avoid|don't show|hide|exclude)\s+(?:clone|clones|dupe|dupes|inspired|fake|copy)", q) or q in ("no clones", "no clone", "no inspired"):
            return "original_only"
        if re.search(r"(?:only|show|want)\s+(?:clone|clones|dupe|dupes|inspired)", q) or q in ("show inspired", "only inspired", "only clones"):
            return "clone_only"
        if re.search(r"(?:no|without|avoid|don't show)\s+(?:combo|combo|set|bundle)", q):
            return "no_combo"
        return None

    def process_message(self, user_input: str) -> str:
        """Process a single user message and return the assistant's reply."""

        if not user_input:
            return "Type something."

        # Extract and update user preferences from every message
        extract_preferences_from_message(user_input, self.user_id)

        # Detect ambiguous/contradictory requests
        _ambiguity_question = self._detect_ambiguity(user_input)
        if _ambiguity_question:
            return f"\nAI:\n{_ambiguity_question}"

        # Check if this is a refinement of previous results
        _refinement = self._detect_refinement(user_input)
        if _refinement and self.last_searched and self.last_products:
            from app.filters import detect_brand
            new_brand = detect_brand(user_input)
            if new_brand:
                old_brands_in_results = {p.get("brand", "").lower().strip() for p in self.last_products if p.get("brand")}
                if old_brands_in_results and new_brand not in old_brands_in_results:
                    _refinement = None
            products = self._apply_refinement(self.last_products, _refinement)
            searched = True
            self.last_products = products
            self.last_user_query = user_input
            self.conversation_service.store_product_context(products, user_input)

            # Re-apply preference filtering
            products = self._filter_owned_products(products)
            products = self._filter_disliked_products(products)
            products = self._penalize_recommended(products)

            product_lines = self._format_product_list(products)
            ai_output = self.ai_service.generate_reply(user_input, products, searched)
            reply = ai_output[0] if isinstance(ai_output, tuple) else ai_output

            return (
                f"\nProducts found:\n"
                f"{product_lines}\n\n"
                f"AI:\n{reply}"
            )

        # Check if this is a mixed greeting + request
        from app.intent import GREETINGS
        _has_greeting = any(
            user_input.strip().lower().startswith(g) or user_input.strip().lower().startswith(g + " ")
            for g in GREETINGS
        )

        intent = self.intent_service.detect(
            user_input,
            previous_intent=self.previous_intent,
        )
        logger.debug("Detected intent: %s", intent)
        self.previous_intent = intent

        # Handle new intents with dedicated responses
        if intent == Intent.BEGINNER:
            # Check if the beginner message also asks for a recommendation
            _rec_request_words = {"pick", "recommend", "suggest", "choose", "want", "need", "give", "decide"}
            _has_rec_request = any(w in user_input.lower().split() for w in _rec_request_words)
            if _has_rec_request:
                # Set beginner mode and route to recommendation engine
                prefs = get_preferences(self.user_id)
                prefs.beginner_mode = True
                recommendation_reply = self._handle_recommendation(user_input, Intent.BEST_RECOMMENDATION)
                if recommendation_reply:
                    return recommendation_reply
            reply = self.conversation_service.handle(intent)
            if reply:
                return reply

        if intent == Intent.COLLECTION_BUILDER:
            # Route collection builder to recommendation engine
            recommendation_reply = self._handle_recommendation(user_input, Intent.BEST_RECOMMENDATION)
            if recommendation_reply:
                return recommendation_reply
            reply = self.conversation_service.handle(intent)
            if reply:
                return reply

        # Standard conversation handling (greeting, thanks, etc.)
        conversation_reply = self.conversation_service.handle(intent)
        if conversation_reply and isinstance(conversation_reply, str) and intent != Intent.PRODUCT_SEARCH:
            return conversation_reply
            # For mixed greeting+request, ConversationService returns None for PRODUCT_SEARCH
            # so this branch isn't reached - handled below with _has_greeting check

        # -----------------------------
        # Sales objection handling (high priority — before FAQ & product search)
        # -----------------------------
        objection_intents = {
            Intent.OBJECTION_PRICE,
            Intent.OBJECTION_COMPETITOR,
            Intent.REQUEST_DISCOUNT,
            Intent.REQUEST_NEGOTIATION,
            Intent.REQUEST_DELIVERY,
            Intent.SALES_PERSUASION,
            Intent.TRUST_CONCERN,
        }

        if intent in objection_intents:
            last_product = self.conversation_service.get_last_product()
            reply = handle_objection(intent, user_input, last_product)
            if reply:
                if _has_greeting:
                    return "\nAI:\nHello! 😊\n" + reply
                return f"\nAI:\n{reply}"

        faq_answer = get_faq_answer(user_input)
        if faq_answer:
            # If greeting + FAQ, still prepend short greeting
            if _has_greeting:
                return "\nAI:\nHello! 😊\n" + faq_answer
            return f"\nAI:\n{faq_answer}"

        # -----------------------------
        # Recommendation intents (handled before product search)
        # -----------------------------
        recommendation_reply = self._handle_recommendation(user_input, intent)
        if recommendation_reply:
            if _has_greeting:
                return "\nAI:\nHello! 😊\n" + recommendation_reply
            return recommendation_reply

        # Comparison follow-up: answer ranking queries using stored comparison state
        # Must be checked BEFORE search/reuse logic so "Which lasts longer?" works
        # after a comparison.
        cs = get_comparison_state()
        if cs.has_comparison() and get_ranking_criteria(user_input) is not None:
            ranking_reply = answer_ranking_query(user_input, cs.left_product, cs.right_product)
            if ranking_reply:
                self.last_user_query = user_input
                self.last_searched = False
                reply = ranking_reply
                if _has_greeting:
                    reply = "Hello! 😊\n\n" + reply
                return f"\nAI:\n{reply}"

        # Get conversation state for accumulated preferences and recommendation context
        state = get_conversation_state(self.user_id)

        # Build comprehensive follow-up keyword set that covers refinement phrases
        followup_product_intents = {
            Intent.PRODUCT_SEARCH,
            Intent.PRODUCT_DETAIL,
            Intent.PRODUCT_INFO,
            Intent.PRICE_QUERY,
            Intent.ATTRIBUTE_QUERY,
            Intent.COMPARISON_QUERY,
            Intent.ORDER,
            Intent.FOLLOW_UP,
            Intent.GIFT,
        }
        followup_keywords = {
            "which one", "which is best", "best one", "lasts longer",
            "longer", "better", "which should i buy", "which one should i buy",
            "compare", "comparison", "choose", "recommend one", "just one",
            "kon ta", "kun ta bhalo", "eituku", "ei tao",
            "kon ta bhalo", "kon ta valo", "kon one",
            "what about", "what is the price", "how much is",
            "how much does it cost", "notes", "how long",
            "is it original", "original", "authentic",
            "description", "details", "stock",
            "kina", "eta", "আসল", "এটা", "কিনা",
            "last price", "dam", "tester", "available",
            "stock ase", "performance", "longevity",
            "projection", "sizes", "প্রজেকশন",
            "লংগেটিভিটি", "স্টক", "tester ache",
            "eta original", "original kina",
            "oita", "oi ta", "seta",
            # Comparison follow-up keywords
            "projects more", "projects most", "longest lasting",
            "strongest", "richest", "most luxurious",
            "most compliments", "best blind buy", "worth buying",
            "pick one", "which projects", "which lasts",
            "which is stronger", "which is richer",
            "most versatile", "best projection", "best value",
            # Refinement keywords for filtering previous results
            "only original", "only authentic", "show original", "show authentic",
            "only originals", "no clones", "no clone", "no inspired",
            "show inspired", "only inspired", "only clones",
            "worth paying extra", "worth it", "worth the price",
            "which is better", "which one is better",
        }

        normalized_input = user_input.strip().lower()
        clean_input = normalized_input.rstrip(string.punctuation)
        intent_is_followup = intent in followup_product_intents
        has_followup_keywords = contains_keyword(clean_input, followup_keywords) or contains_keyword(user_input, followup_keywords)

        resolved_prod = self.conversation_service.resolve_referenced_product(user_input)
        has_reference = resolved_prod is not None and (
            any(w in clean_input for w in _PRONOUN_REFERENCES)
            or self._is_attribute_followup(user_input)
        )

        # Recommendation follow-up keywords
        _rec_followup_keywords = {
            "cheaper", "more expensive", "another", "just one",
            "cheapest", "affordable", "budget friendly",
            "best value", "top pick", "favorite", "safest",
        }
        has_rec_followup = contains_keyword(clean_input, _rec_followup_keywords) or contains_keyword(user_input, _rec_followup_keywords)

        # Performance/ranking follow-up keywords that should reuse and rerank
        _ranking_followup_keywords = {
            "longest lasting", "best projection", "most versatile",
            "most compliments", "most luxurious", "strongest",
            "cheapest", "best value", "top rated",
        }
        has_ranking_followup = contains_keyword(clean_input, _ranking_followup_keywords) or contains_keyword(user_input, _ranking_followup_keywords)

        reuse_previous_products = (
            (intent_is_followup and has_followup_keywords)
            or has_reference
            or (
                intent in {Intent.PRICE_QUERY, Intent.ATTRIBUTE_QUERY, Intent.PRODUCT_INFO}
                and self.last_searched and bool(self.last_products)
            )
            or (
                has_rec_followup
                and state.last_recommended_products
                and self.last_searched
            )
            or (
                has_ranking_followup
                and state.last_recommended_products
                and self.last_searched
            )
        ) and self.last_searched and bool(self.last_products)

        searched = False
        products = []

        if reuse_previous_products:
            searched = self.last_searched
            if (has_rec_followup or has_ranking_followup) and state.last_recommended_products:
                products = list(state.last_recommended_products)
            else:
                products = list(self.last_products)
            if resolved_prod and not products:
                products = [resolved_prod]
                searched = True

            # Apply budget from current query on reused products
            budget = extract_budget(user_input)
            if budget is not None:
                products = [p for p in products if float(p.get("price", 0) or 0) <= budget]

            # Re-rank for performance/ranking follow-ups using comparison engine scoring
            if has_ranking_followup and products:
                criteria = get_ranking_criteria(user_input)
                if criteria:
                    from app.comparison_engine import score_product_for_criteria
                    scored = [(score_product_for_criteria(p, criteria), p) for p in products]
                    scored.sort(key=lambda x: -x[0])
                    products = [p for _, p in scored]

            # Re-rank for cheapest by price
            if has_rec_followup and "cheapest" in user_input.lower():
                products = sorted(products, key=lambda p: float(p.get("price", 0) or 0))
        else:
            product_intents = {
                Intent.PRODUCT_SEARCH,
                Intent.PRODUCT_DETAIL,
                Intent.PRODUCT_INFO,
                Intent.PRICE_QUERY,
                Intent.ATTRIBUTE_QUERY,
                Intent.COMPARISON_QUERY,
                Intent.ORDER,
                Intent.GIFT,
            }

            if intent in product_intents:
                searched = True
            elif intent == Intent.UNKNOWN:
                # Try exact name search for direct product queries like "Do you have Aventus"
                exact = exact_name_search(user_input)
                if exact:
                    searched = True
                    products = [exact]
                elif contains_keyword(user_input, PRODUCT_KEYWORDS):
                    searched = True
            elif intent not in {
                Intent.GREETING, Intent.THANKS, Intent.GOODBYE,
                Intent.CASUAL, Intent.STORE_INFO,
                Intent.DELIVERY, Intent.PAYMENT, Intent.LOCATION,
                Intent.UNKNOWN, Intent.BEGINNER, Intent.BLIND_BUY,
                Intent.COLLECTION_BUILDER,
                Intent.OBJECTION_PRICE, Intent.OBJECTION_COMPETITOR,
                Intent.REQUEST_DISCOUNT, Intent.REQUEST_NEGOTIATION,
                Intent.REQUEST_DELIVERY, Intent.SALES_PERSUASION,
                Intent.TRUST_CONCERN,
            }:
                searched = True

            if searched:
                search_query = user_input

                if self._is_sales_question(user_input):
                    search_query = user_input

                if intent in {
                    Intent.PRODUCT_SEARCH, Intent.PRODUCT_DETAIL,
                    Intent.PRODUCT_INFO, Intent.PRICE_QUERY,
                    Intent.ATTRIBUTE_QUERY, Intent.COMPARISON_QUERY,
                    Intent.ORDER, Intent.GIFT,
                }:
                    search_query = self._apply_semantic_mapping(user_input)

                min_price, max_price = self._extract_price_range(user_input)

                # Merge accumulated budget from conversation state as hard filter
                state = get_conversation_state(self.user_id)
                accumulated = state.get_all_accumulated_preferences()
                acc_budget = accumulated.get("budget")
                if acc_budget is not None:
                    if max_price is None:
                        max_price = acc_budget
                    else:
                        max_price = min(max_price, acc_budget)

                if self._has_vague_budget(user_input) and max_price is None:
                    max_price = 1500

                if intent == Intent.COMPARISON_QUERY:
                    products = self._handle_comparison(user_input, min_price, max_price)
                else:
                    products = self._search_with_range(
                        search_query,
                        min_price,
                        max_price,
                    )

                logger.debug("Found %d products", len(products))

        _pronoun_words = {"this", "it", "that"}
        has_pronoun_ref = any(w in user_input.lower().split() for w in _pronoun_words)
        prev_prod = self.conversation_service.get_last_product()
        prev_name = prev_prod.get("name", "") if prev_prod else ""
        if has_pronoun_ref and prev_name:
            if not products:
                products = [prev_prod]
                searched = True
            user_input = f"{user_input} (referring to {prev_name})"

        if self._is_sales_question(user_input) and not products:
            return (
                "\nAI:\n"
                "I don't have sales statistics. "
                "Here are our top-rated products instead.\n\n"
                "Could you tell me your preference? (Budget, Brand, or Scent type)"
            )

        if not searched and has_reference and resolved_prod:
            searched = True
            products = [resolved_prod]

        if not searched and products:
            searched = True

        # Apply preference-based filtering (negative recommendation, diversity)
        if searched and products:
            prefs = get_preferences(self.user_id)

            # 1. Filter out owned products
            products = self._filter_owned_products(products)

            # 2. Filter out disliked-note products
            products = self._filter_disliked_products(products)

            # 3. Filter based on accumulated preferences
            #    - Clone/original preference
            if prefs.clone_pref == "original_only":
                from app.product_attrs import get_product_attributes
                products = [
                    p for p in products
                    if (get_product_attributes(p).get("product_origin") or "").lower().strip() in ("original", "", None)
                ]
            elif prefs.clone_pref == "clone_only":
                from app.product_attrs import get_product_attributes
                products = [
                    p for p in products
                    if (get_product_attributes(p).get("product_origin") or "").lower().strip() == "inspired"
                ]

            #    - Combo preference
            if prefs.combo_pref == "no_combo":
                from app.ranking import _is_combo_product
                products = [p for p in products if not _is_combo_product(p)]
            elif prefs.combo_pref == "combo":
                from app.ranking import _is_combo_product
                combo_only = [p for p in products if _is_combo_product(p)]
                if combo_only:
                    products = combo_only

            # 4. Re-rank based on accumulated preferences (gender, occasion, season, style)
            #    This ensures filters persist across turns without hard-excluding relevant products.
            if prefs.gender or prefs.occasion or prefs.weather or prefs.style:
                def _acc_pref_score(p):
                    s = 0
                    if prefs.gender:
                        cat = (p.get("category") or "").lower()
                        if prefs.gender == "male" and "men" in cat or prefs.gender == "female" and "women" in cat:
                            s += 20
                    if prefs.occasion:
                        from app.ranking import _matches_occasion
                        if _matches_occasion(p, prefs.occasion):
                            s += 20
                    if prefs.weather:
                        from app.ranking import _matches_season
                        if _matches_season(p, prefs.weather):
                            s += 15
                    if prefs.style:
                        from app.ranking import _matches_scent
                        if _matches_scent(p, prefs.style):
                            s += 15
                    return s
                products.sort(key=_acc_pref_score, reverse=True)

            # 5. Penalize already-recommended products (move to end)
            products = self._penalize_recommended(products)

            # 6. Apply blind-buy mode re-ranking
            products = self._apply_blind_buy_boost(products)

            # 7. Track these as recommended for future diversity
            self._track_recommended(products)

        ai_output = self.ai_service.generate_reply(
            user_input,
            products,
            searched,
        )

        self.last_user_query = user_input
        self.last_searched = searched
        if searched and isinstance(products, list):
            self.last_products = products
            self.conversation_service.store_product_context(products, user_input)
            state = get_conversation_state(self.user_id)
            state.store_search(user_input, products, searched)
        if isinstance(ai_output, (tuple, list)):
            reply = ai_output[0]
        else:
            reply = ai_output

        # Prepend short greeting for mixed greeting+request
        if _has_greeting:
            reply = "Hello! 😊\n\n" + reply

        # Build response with product listing + AI reply
        if isinstance(products, list) and products and intent == Intent.COMPARISON_QUERY and len(products) >= 2:
            left, right = products[0], products[1]
            get_comparison_state().set_products(left, right)
            # Also store in conversation state (backup)
            state = get_conversation_state(self.user_id)
            state.store_comparison(user_input, products)
            comparison_output = build_full_comparison(left, right)
            return (
                f"\nAI:\n"
                f"{comparison_output}\n\n"
                f"{reply}"
            )

        if isinstance(products, list) and products:
            product_list = self._format_product_list(products)
            return (
                f"\nProducts found:\n"
                f"{product_list}\n\n"
                f"AI:\n{reply}"
            )

        if searched and not products:
            from app.filters import detect_brand
            active_filters = []
            prefs = get_preferences(self.user_id)
            if prefs.budget is not None:
                active_filters.append(f"under ৳{prefs.budget}")
            if prefs.gender:
                active_filters.append(prefs.gender)
            if prefs.occasion:
                active_filters.append(prefs.occasion)
            if prefs.weather:
                active_filters.append(prefs.weather)
            if prefs.style:
                active_filters.append(prefs.style)
            b = detect_brand(user_input)
            if b:
                active_filters.append(b)
            if prefs.clone_pref == "original_only":
                active_filters.append("original")
            elif prefs.clone_pref == "clone_only":
                active_filters.append("inspired")
            if prefs.disliked_notes:
                active_filters.append(f"no {prefs.disliked_notes[0]}")
            if active_filters:
                filter_str = " ".join(active_filters)
                note = f"No {filter_str} perfumes were found. Try adjusting your filters or expanding your budget."
                reply = f"{reply}\n\n{note}"
            elif _has_greeting:
                reply = "Hello! 😊\n\n" + reply

        return f"\nAI:\n{reply}"
