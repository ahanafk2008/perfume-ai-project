"""Intent detection service."""

from app.intent import Intent, detect_intent


class IntentService:
    """Service wrapper for intent detection."""

    def detect(
        self,
        message: str,
        previous_intent: Intent | None = None,
    ) -> Intent:
        """Detect the user's intent, optionally using previous-turn context."""
        return detect_intent(
            message,
            previous_intent=previous_intent,
        )