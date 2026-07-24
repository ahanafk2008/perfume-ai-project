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
            "এক্সচেঞ্জ করা",
            "badle din",
            "change kora",
            "product change",
            "product replace",
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
            "টাকা ফেরত",
            "taka ferot",
            "back taka",
            "return kora",
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
            "ফোন নম্বর",
            "মোবাইল",
            "mobile number",
            "phone number",
            "how to contact",
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
            "opening hours",
            "business hours",
            "shop khula",
            "shop bondho",
        ],
        "answer": (
            "Please contact Scent Of Time for the latest store opening hours."
        ),
    },

    "product_quality": {
        "keywords": [
            "quality",
            "fake",
            "genuine",
        ],
        "answer": (
            "For specific product information, please ask about the perfume "
            "name and I'll check the product details."
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
            "ডেলিভারি কত দিন",
            "কত দিনের মধ্যে",
            "delivery koto din lagbe",
            "koto din lagbe",
            "কত দিন লেগেছে",
        ],
        "answer": (
            "Delivery typically takes 2-4 business days within Bangladesh. "
            "For specific delivery timeframes, please contact Scent Of Time directly."
        ),
    },

    "delivery_charge": {
        "keywords": [
            "delivery charge",
            "shipping charge",
            "ডেলিভারি চার্জ",
            "charge koto",
            "ডেলিভারি ফি",
            "shipping cost",
            "delivery fee",
        ],
        "answer": (
            "Delivery charges depend on your location. "
            "Please contact Scent Of Time for specific delivery charges."
        ),
    },

    "discount": {
        "keywords": [
            "discount",
            "offer",
            "ছাড়",
            "অফার",
            "আফার",
            "ডিসকাউন্ট",
            "কম দাম",
            "special offer",
            "মূল্য ছাড়",
            "কোন অফার আছে",
            "offer ase",
            "discount ase",
        ],
        "answer": (
            "Please contact Scent Of Time for current offers and discounts."
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
            "bkash",
            "nagad",
            "rocket",
            "বিকাশ",
            "নগদ",
            "রকেট",
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
