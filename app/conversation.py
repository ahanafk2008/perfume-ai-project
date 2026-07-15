"""In-memory conversation history management."""

import logging
from collections import defaultdict
from copy import deepcopy
from typing import Literal, TypedDict

try:
    from .config import MAX_HISTORY_MESSAGES
except ImportError:  # pragma: no cover - supports running modules directly
    from config import MAX_HISTORY_MESSAGES


logger = logging.getLogger(__name__)

Role = Literal["user", "assistant"]


class Message(TypedDict):
    """A single conversation message."""

    role: Role
    content: str


_conversations: dict[str, list[Message]] = defaultdict(list)


def create_conversation(user_id: str) -> None:
    """Create an empty conversation if one does not already exist."""

    _conversations.setdefault(user_id, [])


def get_history(user_id: str) -> list[Message]:
    """Return a copy of the recent history for a user."""

    create_conversation(user_id)
    return deepcopy(_conversations[user_id])


def add_user_message(user_id: str, message: str) -> None:
    """Add a user message to the conversation."""

    _add_message(user_id, "user", message)


def add_assistant_message(user_id: str, reply: str) -> None:
    """Add an assistant reply to the conversation."""

    _add_message(user_id, "assistant", reply)


def clear(user_id: str) -> None:
    """Clear a user's conversation history."""

    _conversations.pop(user_id, None)
    logger.debug("Cleared conversation for user_id=%s", user_id)


def _add_message(user_id: str, role: Role, content: str) -> None:
    """Add and trim one message."""

    create_conversation(user_id)
    _conversations[user_id].append({"role": role, "content": content})
    _trim(user_id)


def _trim(user_id: str) -> None:
    """Keep only the most recent configured number of messages."""

    overflow = len(_conversations[user_id]) - MAX_HISTORY_MESSAGES
    if overflow > 0:
        del _conversations[user_id][:overflow]
        logger.debug(
            "Trimmed %d old messages for user_id=%s",
            overflow,
            user_id,
        )
