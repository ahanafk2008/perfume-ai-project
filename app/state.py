"""Conversation state for persistent memory across turns.

Centralises:
- accumulated user preferences
- last search results and query
- last recommended products
- last compared products
- follow-up memory

Every message updates the state instead of replacing it.
"""

from __future__ import annotations

import logging
from typing import Any

from app.preferences import (
    UserPreferences,
    extract_preferences_from_message,
)
from app.preferences import (
    get_preferences as _get_raw_preferences,
)

logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "cli"


class ConversationState:
    """Persistent conversation memory for a single user session.

    Wraps UserPreferences and adds ephemeral turn-level memory
    (last search, last comparison, etc.) so follow-up questions
    can reuse previous context.
    """

    def __init__(self, user_id: str = DEFAULT_USER_ID) -> None:
        self.user_id = user_id

        # ---------- preference store ----------
        # Delegates to the existing module-level UserPreferences dict,
        # so all code that calls get_preferences() still works.
        self._preferences: UserPreferences | None = None

        # ---------- ephemeral turn memory ----------
        self.last_query: str = ""
        self.last_products: list[dict[str, Any]] = []
        self.last_searched: bool = False
        self.last_intent: Any = None

        # Last recommendation context
        self.last_recommended_products: list[dict[str, Any]] = []
        self.last_recommended_query: str = ""

        # Last comparison context
        self.last_compared_products: list[dict[str, Any]] = []
        self.last_comparison_query: str = ""
        self._comparing: bool = False

    # ------------------------------------------------------------------
    # Preferences (delegates to module-level store)
    # ------------------------------------------------------------------

    @property
    def preferences(self) -> UserPreferences:
        if self._preferences is None:
            self._preferences = _get_raw_preferences(self.user_id)
        return self._preferences

    def update_from_message(self, message: str) -> dict[str, Any]:
        """Parse *message* and merge extracted data into accumulated state.

        Returns the dict of fields that were updated (same contract as
        ``extract_preferences_from_message``).
        """
        return extract_preferences_from_message(message, self.user_id)

    # ------------------------------------------------------------------
    # Turn memory helpers
    # ------------------------------------------------------------------

    def store_search(
        self,
        query: str,
        products: list[dict[str, Any]],
        searched: bool,
    ) -> None:
        self.last_query = query
        self.last_products = products if isinstance(products, list) else []
        self.last_searched = searched

    def store_recommendation(
        self,
        query: str,
        products: list[dict[str, Any]],
    ) -> None:
        self.last_recommended_query = query
        self.last_recommended_products = products if isinstance(products, list) else []

    def store_comparison(
        self,
        query: str,
        products: list[dict[str, Any]],
    ) -> None:
        self.last_comparison_query = query
        self.last_compared_products = products if isinstance(products, list) else []
        self._comparing = len(products) >= 2

    def is_in_comparison(self) -> bool:
        return self._comparing and len(self.last_compared_products) >= 2

    def get_comparison_pair(self) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if self._comparing and len(self.last_compared_products) >= 2:
            return self.last_compared_products[0], self.last_compared_products[1]
        return None, None

    def get_all_accumulated_preferences(self) -> dict[str, Any]:
        """Return ALL accumulated preferences as a flat dict for passing to search/ranking."""
        p = self.preferences
        return {
            "budget": p.budget,
            "gender": p.gender,
            "occasion": p.occasion,
            "season": p.weather,
            "style": p.style,
            "strength": p.strength_pref,
            "longevity": p.longevity_pref,
            "projection": p.projection_pref,
            "preferred_notes": list(p.liked_notes),
            "disliked_notes": list(p.disliked_notes),
            "preferred_brands": list(p.preferred_brands),
            "disliked_brands": list(p.disliked_brands),
            "authenticity_pref": p.authenticity_pref,
            "clone_pref": p.clone_pref,
            "combo_pref": p.combo_pref,
            "beginner_mode": p.beginner_mode,
            "blind_buy_mode": p.blind_buy_mode,
            "owned_perfumes": list(p.owned_perfumes),
            "recommended_product_ids": list(p.recommended_product_ids),
        }

    def has_meaningful_preferences(self) -> bool:
        """Return True when accumulated state adds value beyond a bare query."""
        return self.preferences.has_any_preference()


# ------------------------------------------------------------------
# Module-level singleton helpers (backward-compatible API)
# ------------------------------------------------------------------

_conversation_states: dict[str, ConversationState] = {}


def get_conversation_state(user_id: str = DEFAULT_USER_ID) -> ConversationState:
    if user_id not in _conversation_states:
        _conversation_states[user_id] = ConversationState(user_id)
    return _conversation_states[user_id]


def reset_conversation_state(user_id: str | None = None) -> None:
    if user_id is not None:
        _conversation_states.pop(user_id, None)
    else:
        _conversation_states.clear()
