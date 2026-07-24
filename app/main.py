import logging

from .services.chat import ChatService

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the interactive chat loop."""
    chat_service = ChatService()

    while True:
        try:
            user = input("You: ").strip()

            if not user:
                continue

            if user.lower() == "exit":
                break

            response = chat_service.process_message(user)
            print(response)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception:
            logger.exception("Error processing query")
            print("\nSomething went wrong. Please try again.")


if __name__ == "__main__":
    main()