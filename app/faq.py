"""
Frequently Asked Questions.
"""

from __future__ import annotations


FAQS = {
    "delivery": {
        "keywords": [
            "delivery",
            "deliver",
            "shipping",
            "courier",
            "home delivery",
            "ডেলিভারি",
        ],
        "answer": (
            "Yes, we provide delivery service across Bangladesh. "
            "Delivery time and charges may vary depending on your location."
        ),
    },

    "payment": {
        "keywords": [
            "payment",
            "pay",
            "bkash",
            "bikash",
            "nagad",
            "rocket",
            "cash on delivery",
            "cod",
            "পেমেন্ট",
            "বিকাশ",
            "নগদ",
        ],
        "answer": (
            "We accept available payment methods. "
            "Cash on delivery and mobile payment options may be available."
        ),
    },

    "exchange": {
        "keywords": [
            "exchange",
            "replace",
            "replacement",
            "change product",
            "এক্সচেঞ্জ",
        ],
        "answer": (
            "For exchange requests, please contact Scent Of Time customer support "
            "with your order details."
        ),
    },

    "return": {
        "keywords": [
            "return",
            "refund",
            "money back",
            "রিটার্ন",
            "রিফান্ড",
        ],
        "answer": (
            "For return or refund requests, please contact Scent Of Time customer "
            "support with your order information."
        ),
    },

    "contact": {
        "keywords": [
            "contact",
            "phone",
            "number",
            "whatsapp",
            "facebook",
            "যোগাযোগ",
        ],
        "answer": (
            "You can contact Scent Of Time through their official Facebook page "
            "or WhatsApp for assistance."
        ),
    },

    "business_hours": {
        "keywords": [
            "open",
            "close",
            "time",
            "hours",
            "working hour",
            "when open",
            "when close",
            "কখন খোলা",
            "কখন বন্ধ",
        ],
        "answer": (
            "Please contact Scent Of Time for the latest store opening hours."
        ),
    },

    "location": {
        "keywords": [
            "location",
            "address",
            "shop",
            "store",
            "where are you",
            "where located",
            "কোথায়",
            "ঠিকানা",
        ],
        "answer": (
            "Please contact Scent Of Time for the exact store location."
        ),
    },

    "product_quality": {
        "keywords": [
            "original",
            "authentic",
            "quality",
            "fake",
            "genuine",
            "অরিজিনাল",
        ],
        "answer": (
            "We provide quality perfumes and authentic products. "
            "For specific product details, please ask about the perfume name."
        ),
    },

    "customize": {
        "keywords": [
            "custom",
            "customize",
            "own fragrance",
            "make perfume",
        ],
        "answer": (
            "Yes, we have customized fragrance options available. "
            "Tell us your preferred scent style and we can help."
        ),
    },
}


def get_faq_answer(message: str) -> str | None:
    """
    Return an FAQ answer if the message matches.
    """

    message = message.lower().strip()

    for faq in FAQS.values():
        for keyword in faq["keywords"]:
            if keyword in message:
                return faq["answer"]

    return None