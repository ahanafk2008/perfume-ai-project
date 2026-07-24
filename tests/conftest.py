"""pytest configuration — reset module-level state between tests."""

import pytest

from app.preferences import reset_preferences
from app.state import reset_conversation_state


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Reset module-level conversation/preference state before each test.
    
    Ensures tests are isolated from each other.
    """
    reset_preferences()
    reset_conversation_state()
