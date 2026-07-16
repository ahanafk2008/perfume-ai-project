import logging

from intent import Intent, detect_intent
from ollama_ai import ask_ai
from search import search_products

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

while True:
    try:
        user = input("You: ").strip()

        if user.lower() == "exit":
            break

        if not user:
            print("Type something.")
            continue

        # Detect user intent first
        intent = detect_intent(user)

        if intent == Intent.GREETING:
            print(
                "\nAI:\n"
                "Hello! 👋\n\n"
                "Welcome to Scent Of Time.\n\n"
                "I can help you:\n"
                "- Recommend perfumes\n"
                "- Find perfumes by budget\n"
                "- Compare fragrances\n"
                "- Answer product questions\n\n"
                "How can I help you today?"
            )
            continue

        if intent == Intent.THANKS:
            print(
                "\nAI:\n"
                "You're welcome! 😊\n"
                "If you need any perfume recommendations, just let me know."
            )
            continue

        if intent == Intent.GOODBYE:
            print(
                "\nAI:\n"
                "Thank you for visiting Scent Of Time.\n"
                "Have a wonderful day! 👋"
            )
            continue

        products = search_products(user)

        print("\nProducts found:")
        for p in products:
            print(
                f"{p['name']} | {p['brand']} | {p['category']} | ৳{p['price']}"
            )

        reply, _ = ask_ai(user, products)

        print("\nAI:\n", reply)

    except KeyboardInterrupt:
        break
    except Exception:
        logger.exception("Error processing query")
        print("\nSomething went wrong. Please try again.")