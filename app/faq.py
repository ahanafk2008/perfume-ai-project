"""
Frequently Asked Questions.
"""

from __future__ import annotations

FAQS = {
    "delivery": {
        "keywords": [
            "delivery",
            "shipping",
            "courier",
            "ডেলিভারি",
            "shipping charge",
        ],
        "answer": "",
    },
    "payment": {
        "keywords": [
            "payment",
            "bkash",
            "bkash",
            "nagad",
            "rocket",
            "cash on delivery",
            "cod",
            "পেমেন্ট",
            "বিকাশ",
            "নগদ",
        ],
        "answer": "",
    },
    "exchange": {
        "keywords": [
            "exchange",
            "replace",
            "replacement",
            "change product",
            "এক্সচেঞ্জ",
        ],
        "answer": "",
    },
    "return": {
        "keywords": [
            "return",
            "refund",
            "money back",
            "রিটার্ন",
            "রিফান্ড",
        ],
        "answer": "",
    },
    "contact": {
        "keywords": [
            "contact",
            "phone",
            "number",
            "whatsapp",
            "যোগাযোগ",
        ],
        "answer": "",
    },
    "business_hours": {
        "keywords": [
            "open",
            "close",
            "time",
            "hours",
            "working hour",
            "কখন খোলা",
            "কখন বন্ধ",
        ],
        "answer": "",
    },
    "location": {
        "keywords": [
            "location",
            "address",
            "shop",
            "store",
            "কোথায়",
            "ঠিকানা",
        ],
        "answer": "",
    },
}


def get_faq_answer(message: str) -> str | None:
    """
    Return an FAQ answer if the message matches.
    """

    message = message.lower()

    for faq in FAQS.values():
        if any(keyword in message for keyword in faq["keywords"]):
            if faq["answer"]:
                return faq["answer"]

    return None