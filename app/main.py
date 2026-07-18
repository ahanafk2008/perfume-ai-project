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
        print(f"Detected intent: {intent}")

        # -----------------------------
        # Basic Conversations
        # -----------------------------
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
        # FAQ / Store Information
        # -----------------------------
        faq_answer = get_faq_answer(user)

        if faq_answer:
            print("\nAI:\n", faq_answer)
            continue

        # -----------------------------
        # Business Intents
        # -----------------------------
        if intent == Intent.DELIVERY:
            print(
                "\nAI:\n"
                "Yes, we provide delivery service."
            )
            continue

        if intent == Intent.PAYMENT:
            print(
                "\nAI:\n"
                "We accept available payment methods. "
                "Please contact Scent Of Time for payment details."
            )
            continue

        if intent == Intent.LOCATION:
            print(
                "\nAI:\n"
                "Please contact Scent Of Time for our store location."
            )
            continue

        if intent == Intent.ORDER:
            print(
                "\nAI:\n"
                "Great! I can help you place your order. 😊\n\n"
                "Please provide:\n"
                "• Perfume name\n"
                "• Your name\n"
                "• Phone number\n"
                "• Delivery address\n\n"
                "Once I have these details, we can proceed with your order."
            )
            continue

        # -----------------------------
        # Unknown Intent
        # -----------------------------
        
        if intent == Intent.UNKNOWN:
            products = search_products(user)
            print(f"Found {len(products)} products")

            reply, _ = ask_ai(user, products)
            print("\nAI:\n", reply)
            continue

        # -----------------------------
        # Product Search
        # -----------------------------
        products = search_products(user)
        print(f'Found {len(products)} products')

        if products:
            print('\nProducts found:')

            for product in products:
                print(
                    f"{product['name']} | "
                    f"{product['brand']} | "
                    f"{product['category']} | "
                    f"৳{product['price']}"
                )

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