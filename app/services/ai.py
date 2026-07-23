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


class AIResponseGenerator:
    """AI response generator that wraps the AIService."""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
    def generate_response(self, user_input: str, products: list, searched: bool):
        """Generate an AI response using the wrapped service."""
        return self.ai_service.generate_reply(user_input, products, searched)
