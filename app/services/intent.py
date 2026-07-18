"""Intent detection service."""

from app.intent import Intent, detect_intent


class IntentService:
    """Service wrapper for intent detection."""

    def detect(self, message: str) -> Intent:
        """Detect the user's intent."""
        return detect_intent(message)