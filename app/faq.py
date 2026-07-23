"""
Frequently Asked Questions.
"""

from __future__ import annotations


FAQS = {
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

    "delivery_time": {
        "keywords": [
            "delivery time",
            "delivery koto din",
            "koto din",
            "কত দিন লাগে",
            "কত দিনে ডেলিভারি",
            "কতদিনে",
            "কবে পাবো",
            "kobe pabo",
            "shipping time",
            "how many days",
        ],
        "answer": (
            "Delivery typically takes 2-4 business days within Bangladesh. "
            "For specific delivery timeframes, please contact Scent Of Time directly."
        ),
    },

    "cod": {
        "keywords": [
            "cod",
            "cash on delivery",
            "cod ache",
            "cod আছে",
            "পেমেন্ট কি cod",
            "cod ki",
            "cash on delivery ki",
            "cash on delivery ache",
            "ক্যাশ অন ডেলিভারি",
        ],
        "answer": (
            "Yes, Cash on Delivery (COD) is available. "
            "Please confirm your order details with Scent Of Time for COD availability in your area."
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