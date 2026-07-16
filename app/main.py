import logging

from .faq import get_faq_answer
from .intent import Intent, detect_intent
from .ollama_ai import ask_ai
from .search import search_products

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

        # -----------------------------
        # Intent Detection
        # -----------------------------
        intent = detect_intent(user)

        if intent == Intent.GREETING:
            print(
                "\nAI:\n"
                "Hello! 👋\n\n"
                "Welcome to Scent Of Time.\n\n"
                "I can help you:\n"
                "• Recommend perfumes\n"
                "• Find perfumes within your budget\n"
                "• Suggest gifts\n"
                "• Compare fragrances\n"
                "• Answer product questions\n\n"
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

        # -----------------------------
        # FAQ
        # -----------------------------
        faq_answer = get_faq_answer(user)

        if faq_answer:
            print("\nAI:\n", faq_answer)
            continue

        # -----------------------------
        # Product Search
        # -----------------------------
        products = search_products(user)

        print("\nProducts found:")

        if products:
            for product in products:
                print(
                    f"{product['name']} | "
                    f"{product['brand']} | "
                    f"{product['category']} | "
                    f"৳{product['price']}"
                )
        else:
            print("No matching products.")

        # -----------------------------
        # AI Response
        # -----------------------------
        reply, _ = ask_ai(user, products)

        print("\nAI:\n", reply)

    except KeyboardInterrupt:
        break

    except Exception:
        logger.exception("Error processing query")
        print("\nSomething went wrong. Please try again.")