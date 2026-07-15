import logging

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
