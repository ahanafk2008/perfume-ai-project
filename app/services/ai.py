"""AI interaction service."""

from app.ollama_ai import ask_ai


class AIService:
    """Service wrapper around the AI model."""

    def generate_reply(
        self,
        message: str,
        products: list,
        searched: bool,
    ):
        """Generate an AI response."""
        return ask_ai(
            message,
            products,
            searched=searched,
        )