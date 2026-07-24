"""
Intent detection for Perfume AI Assistant.
"""

from __future__ import annotations

import logging
import re
from enum import Enum

from .normalize import normalize

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    GREETING = "greeting"
    THANKS = "thanks"
    GOODBYE = "goodbye"
    CASUAL = "casual"

    STORE_INFO = "store_info"

    PRODUCT_SEARCH = "product_search"
    PRODUCT_DETAIL = "product_detail"
    PRODUCT_INFO = "product_info"
    PRICE_QUERY = "price_query"
    ATTRIBUTE_QUERY = "attribute_query"
    COMPARISON_QUERY = "comparison_query"

    DELIVERY = "delivery"
    PAYMENT = "payment"
    LOCATION = "location"
    ORDER = "order"

    FOLLOW_UP = "follow_up"

    GIFT = "gift"
    LUXURY = "luxury"
    COMPLIMENT = "compliment"

    # Recommendation intents (between comparison and product search in priority)
    BEST_RECOMMENDATION = "best_recommendation"
    LUXURY_RECOMMENDATION = "luxury_recommendation"
    GENDER_FILTER = "gender_filter"
    BUDGET_RECOMMENDATION = "budget_recommendation"
    OCCASION_RECOMMENDATION = "occasion_recommendation"
    SEASON_RECOMMENDATION = "season_recommendation"
    STYLE_RECOMMENDATION = "style_recommendation"
    GIFT_RECOMMENDATION = "gift_recommendation"

    BEGINNER = "beginner"
    BLIND_BUY = "blind_buy"
    COLLECTION_BUILDER = "collection_builder"

    # Sales objections (higher priority than product search)
    OBJECTION_PRICE = "objection_price"
    OBJECTION_COMPETITOR = "objection_competitor"
    REQUEST_DISCOUNT = "request_discount"
    REQUEST_NEGOTIATION = "request_negotiation"
    REQUEST_DELIVERY = "request_delivery"
    SALES_PERSUASION = "sales_persuasion"
    TRUST_CONCERN = "trust_concern"

    UNKNOWN = "unknown"


# -----------------------------
# Conversation
# -----------------------------

STORE_INFO_KEYWORDS = {
    "what do you sell",
    "what do you have",
    "what products",
    "what are you selling",
    "what do you guys sell",
    "what does your shop sell",

    "কি বিক্রি করেন",
    "কি কি বিক্রি করেন",
    "কি আছে",

    "ki bikri koren",
    "ki ki bikri koren",
    "ki ase",
    "apnara ki bikri koren",
    "apnara ki ki bikri koren",
}

GREETINGS = {
    "hi",
    "hello",
    "hey",
    "salam",
    "assalamu alaikum",
    "হাই",
    "হ্যালো",
    "সালাম",
    "কেমন আছেন",
    "kemon achen",
}


THANKS = {
    "thanks",
    "thank you",
    "thankyou",
    "thank u",
    "thx",
    "ধন্যবাদ",
    "dhonnobad",
}


GOODBYES = {
    "bye",
    "goodbye",
    "see you",
    "take care",
    "allah hafez",
    "আল্লাহ হাফেজ",
}


CASUAL = {
    "nice",
    "perfect",
    "great",
    "awesome",
    "cool",
    "ok",
    "okay",
}


# -----------------------------
# FAQ
# -----------------------------

DELIVERY_KEYWORDS = {
    "delivery",
    "deliver",
    "shipping",
    "courier",
    "delivery charge",
    "delivery time",
    "ডেলিভারি",
    "ডেলিভারী",
    "কত দিনে",
    "কত দিন",
    "koto din",
    "delivery koto din",
    "কবে পাবো",
    "kobe pabo",
    "ডেলিভারি চার্জ",
    "চার্জ",
    "delivery charge koto",
    "lokkhon",
}


PAYMENT_KEYWORDS = {
    "payment",
    "pay",
    "cod",
    "cash on delivery",
    "bkash",
    "nagad",
    "card",
    "পেমেন্ট",
    "বিকাশ",
    "নগদ",
    "rocket",
    "রকেট",
    " বিকাশে ",
    " নগদে ",
    "mobile banking",
    "মোবাইল ব্যাংকিং",
    "কি ভাবে পেমেন্ট করবো",
    "payment method",
}


LOCATION_KEYWORDS = {
    "location",
    "address",
    "shop",
    "store",
    "branch",
    "ঠিকানা",
    "কোথায়",
    "লোকেশন",
    "দোকান",
    " shop er ",
    "apnader dokan",
    "kothay apnader",
    "apnader address",
}


# -----------------------------
# Order
# ONLY strong, unambiguous buying-action phrases.
# Do NOT add bare words like "want" / "need" / "looking for" here —
# those are what caused order/product-search confusion before, since
# they show up constantly in ordinary product questions too.
# -----------------------------

ORDER_KEYWORDS = {
    # English - explicit checkout intent
    "place order",
    "confirm order",
    "order now",
    "checkout",
    "add to cart",
    "buy now",
    "purchase now",
    "i want to order",
    "i want this delivered",
    "send this to me",

    # Bangla
    "অর্ডার করবো",
    "অর্ডার দিবো",
    "অর্ডার করতে চাই",
    "এটা অর্ডার করবো",
    "এটা বুক করুন",

    # Banglish
    "order korbo",
    "order dibo",
    "order korte chai",
    "eta order korbo",
    "pathiye din",
    "send kore den",
}

# -----------------------------
# Gift
# -----------------------------

GIFT_KEYWORDS = {
    "gift",
    "gifts",
    "present",
    "presents",
    "birthday",
    "anniversary",
    "valentine",
    "for her",
    "for him",
    "for wife",
    "for husband",
    "for girlfriend",
    "for boyfriend",
    "for mom",
    "for dad",
    "for mother",
    "for father",
    "for sister",
    "for brother",
    "wife",
    "husband",
    "girlfriend",
    "boyfriend",
    "mom",
    "dad",
    "উপহার",
    "গিফট",
    "eid",
    "ঈদ",
    "সারপ্রাইজ",
    "surprise",
    "বিয়ে",
    "biye",
    "জন্মদিন",
    "জন্মদিনের উপহার",
    "jonmodin",
    "বিয়ে উপহার",
    "জামাই",
    "স্ত্রী",
    "স্বামী",
    "বউ",
    "বউয়ের জন্য",
    "স্বামীর জন্য",
    "বান্ধবী",
    "বন্ধুর জন্য",
}

# -----------------------------
# Product Search
# -----------------------------

PRODUCT_KEYWORDS = {

    # Product types
    "perfume",
    "fragrance",
    "attar",
    "ittr",
    "scent",
    "body spray",
    "mist",
    "oud",
    "musk",

    # Brands
    "lattafa",
    "armaf",
    "rasasi",
    "dior",
    "chanel",
    "versace",
    "gucci",
    "tom ford",
    "hawas",
    "yara",
    "asad",

    # Price/budget
    "under",
    "below",
    "budget",
    "price",
    "cost",
    "cheap",
    "taka",
    "tk",
    "৳",

    # Recommendation keywords
    "recommend",
    "recommends",
    "recommended",
    "suggest",
    "suggestion",
    "suggestions",
    "suggested",
    "gift",

    # Occasion
    "office",
    "party",
    "wedding",
    "date",
    "work",
    "casual",
    "formal",
    "club",
    "event",

    # Season
    "summer",
    "winter",
    "spring",
    "autumn",
    "monsoon",
    "rainy",

    # Notes & accords
    "vanilla",
    "rose",
    "woody",
    "fresh",
    "sweet",
    "citrus",
    "amber",
    "aquatic",
    "floral",
    "spicy",
    "gourmand",
    "powdery",
    "fruity",

    # Performance
    "long lasting",
    "longevity",
    "projection",
    "performance",
    "strong",
    "beast",

    # Search patterns (multi-word, handled by substring check)
    "looking for",
    "looking",
    "i want",
    "need a",

    # Bangla
    "পারফিউম",
    "আতর",
    "সুগন্ধি",
    "দাম",
    "কত",
    "অফিস",
    "পার্টি",
    "গ্রীষ্ম",
    "শীত",
    "মিষ্টি",
    "তাজা",
    "সুপারিশ",
    "মহিলাদের",
    "নারীদের",
    "পুরুষদের",
    "ছেলেদের",
    "মেয়েদের",
    "উপহার",
    "গিফট",
    "গরম",
    "ফ্রেশ",
    "ভ্যানিলা",
    "অফিসে ব্যবহার",
    "বেশিক্ষণ",
    "সারাদিন",
    "ঘন্টার পর ঘন্টা",
    "লং লাস্টিং",
    "longlasting",
    "প্রজেকশন",
    "sasto",
    "sasta",
    "kom dam",
}


# -----------------------------
# Product detail keywords
# Only phrases that clearly reference a specific product context.
# -----------------------------

PRODUCT_INFO_KEYWORDS = {
    "how much is",
    "how much does it cost",
    "what is the price",
    "what's the price",
    "price of",
    "cost of",
    "কত টাকা",
    "দাম কত",
    "দাম",
    "কত দাম",
    "what are the notes",
    "what notes does it have",
    "notes of",
    "notes in",
    "how long does it last",
    "longevity",
    "long lasting",
    "lasts long",
    "how long",
    "is it original",
    "is this original",
    "is it authentic",
    "is this authentic",
    "authentic",
    "original",
    "description of",
    "about this",
    "about that",
    "tell me about",
    "information about",
    "details of",
    "size of",
    "weight of",
    "stock",
    "available",
    "original kina",
    "eta original",
    "kina",
    "আসল",
    "এটা আসল",
    "এটা অরিজিনাল",
    "stock ase",
    "stock ache",
    "tester",
    "tester ache",
    "প্রজেকশন",
    "লংগেটিভিটি",
    "লাস্টিং",
    "সাইজ",
    "এটা প্রোজেকশন",
    "এটা লংগেটিভিটি",
    "notes ki",
    "notes gula ki",
    "এটা কি অরিজিনাল",
    "authentic kina",
    "available ase",
}

PRICE_QUERY_KEYWORDS = {
    "how much",
    "what is the price",
    "price",
    "cost",
    "pricing",
}

ATTRIBUTE_QUERY_KEYWORDS = {
    "notes",
    "note",
    "ingredients",
    "composition",
    "top notes",
    "middle notes",
    "base notes",
    "longevity",
    "lasting",
    "sillage",
    "projection",
    "authentic",
    "original",
    "fake",
    "real",
    "replica",
    "copy",
    "dupe",
    "similar",
    "alternative",
    "size",
    "ml",
    "volume",
    "weight",
    "kina",
    "আসল",
    "অরিজিনাল",
    "eta",
    "প্রজেকশন",
    "লংগেটিভিটি",
    "সাইজ",
    "স্টক",
    "tester",
    "tester ache",
    "stock ase",
    "গুলি কেমন",
}

COMPARISON_QUERY_KEYWORDS = {
    "vs",
    "versus",
    "compare",
    "comparison",
    "difference between",
    "which is better",
    "which one is better",
    "better than",
    "or",
    "or this one",
    "or that one",
    "should i buy",
    "which should i choose",
    "which one should i",
}

# -----------------------------
# Recommendation Intent Keywords
# -----------------------------

BEST_RECOMMENDATION_KEYWORDS: set[str] = {
    "best",
    "best one",
    "best perfume",
    "top",
    "top rated",
    "top perfume",
    "recommend one",
    "recommend a perfume",
    "recommend me",
    "suggest",
    "suggest one",
    "suggest a perfume",
    "popular",
    "most popular",
    "favorite",
    "number one",
    "সেরা",
    "সেরা পারফিউম",
    "best ta",
    "best kon ta",
    "suggest koren",
    "recommend koren",
    "bhalo",
    "valo",
    "ভালো",
    "সবচেয়ে ভালো",
}

LUXURY_RECOMMENDATION_KEYWORDS: set[str] = {
    "luxury",
    "luxurious",
    "premium",
    "designer",
    "high end",
    "high-end",
    "expensive",
    "signature",
    "exclusive",
    "elite",
    "classy",
    "sophisticated",
    "high quality",
    "বিলাসবহুল",
    "প্রিমিয়াম",
    "luxury perfume",
    "premium perfume",
    "designer perfume",
}

GENDER_FILTER_KEYWORDS: set[str] = {
    "men perfume",
    "men's perfume",
    "male perfume",
    "man perfume",
    "boys perfume",
    "gentlemen perfume",
    "women perfume",
    "women's perfume",
    "female perfume",
    "woman perfume",
    "girls perfume",
    "ladies perfume",
    "unisex perfume",
    "men",
    "men's",
    "male",
    "woman",
    "women",
    "women's",
    "female",
    "unisex",
    "gentlemen",
}

BUDGET_RECOMMENDATION_KEYWORDS: set[str] = {
    "cheap",
    "cheapest",
    "affordable",
    "budget",
    "value",
    "economy",
    "reasonable",
    "discount",
    "under",
    "below",
    "sasto",
    "sasta",
    "kom dam",
    "komdami",
    "low budget",
    "সস্তা",
    "কম দাম",
}

OCCASION_RECOMMENDATION_KEYWORDS: set[str] = {
    "office",
    "work",
    "professional",
    "formal",
    "corporate",
    "university",
    "college",
    "gym",
    "workout",
    "sport",
    "date",
    "dating",
    "romantic",
    "dinner",
    "night out",
    "party",
    "club",
    "nightclub",
    "event",
    "wedding",
    "marriage",
    "casual",
    "everyday",
    "daily",
    "regular",
    "অফিস",
    "পার্টি",
    "বিয়ে",
}

SEASON_RECOMMENDATION_KEYWORDS: set[str] = {
    "summer",
    "hot",
    "heat",
    "sunny",
    "warm",
    "spring",
    "winter",
    "cold",
    "cool",
    "chilly",
    "fall",
    "autumn",
    "rainy",
    "monsoon",
    "গ্রীষ্ম",
    "গরম",
    "শীত",
    "ঠান্ডা",
    "বর্ষা",
}

STYLE_RECOMMENDATION_KEYWORDS: set[str] = {
    "clean",
    "marine",
    "ocean",
    "sugary",
    "candy",
    "earthy",
    "pepper",
    "flower",
}

GIFT_RECOMMENDATION_KEYWORDS: set[str] = {
    "gift idea",
    "gift ideas",
    "gift suggestion",
    "gift suggestions",
    "gift for",
    "gift item",
    "gift items",
    "gift option",
    "gift options",
    "gift recommendation",
    "উপহার আইডিয়া",
    "উপহার সাজেস্ট",
    "gift diye",
    "gift hishebe",
    "উপহার হিসেবে",
    "গিফট আইডিয়া",
    "গিফট সাজেস্ট",
}

# -----------------------------
# Follow-up phrases
# Used only when the CALLER tells us the previous turn was a
# product search (see `previous_intent` param below). This is
# intentionally tiny — it just keeps a bare "which one is best?"
# from falling into UNKNOWN right after a product list was shown.
# Real multi-turn memory (storing the actual product list, filters,
# etc.) belongs in the calling app/session layer, not here.
# -----------------------------

FOLLOWUP_KEYWORDS = {
    "which one",
    "which is best",
    "best one",
    "recommend one",
    "kon ta",
    "kun ta bhalo",
    "eituku",
    "ei tao",
    "how about it",
    "should i buy",
    "this perfume",
    "this one",
    "that one",
    "eta",
    "oita",
    "oi ta",
    "eitar",
    "seta",
    "shei ta",
    "last price",
    "dam koto",
    "last perfume",
    "previous perfume",
    "agor ta",
    "agor perfume",
}


# -----------------------------
# Helpers
# -----------------------------

def matches_phrase(message: str, phrases: set[str]) -> bool:
    return message in phrases


def starts_with_phrase(message: str, phrases: set[str]) -> bool:
    return any(
        message == p or message.startswith(p + " ")
        for p in phrases
    )


def _token_matches(word: str, keyword: str) -> bool:
    """Match a single-word keyword against a message token, tolerating
    simple English plurals (oud/ouds, attar/attars)."""
    if word == keyword:
        return True
    if word == keyword + "s":
        return True
    return bool(word.endswith("s") and word[:-1] == keyword)


def contains_keyword(message: str, keywords: set[str]) -> bool:

    words = message.split()

    for keyword in keywords:

        if " " in keyword:
            if keyword in message:
                return True

        else:
            if any(_token_matches(w, keyword) for w in words):
                return True

    return False


# -----------------------------
# Main Detector
# -----------------------------

# Keywords that turn a greeting into a product request
_GREETING_REQUEST_KEYWORDS: set[str] = {
    *PRODUCT_KEYWORDS,
    *GIFT_KEYWORDS,
    "recommend", "suggest", "show", "want", "need", "looking",
    "দেখান", "চাই", "লাগবে", "সুপারিশ",
    "recommend koren", "suggest koren", "dekhan", "chai", "lagbe",
}

COLLECTION_BUILDER_KEYWORDS: set[str] = {
    "collection", "multiple", "variety", "different occasions",
    "rotation", "wardrobe", "set of", "a few", "several",
    "collection build", "build my collection", "starting collection",
    "different perfumes", "multiple perfumes", "a few perfumes",
    "several perfumes", "some perfumes", "multiple fragrance",
    "perfume collection",
    "কয়েকটা", "বিভিন্ন", "কালেকশন",
}

BEGINNER_KEYWORDS: set[str] = {
    "know nothing", "don't know", "dont know", "new to", "beginner",
    "just started", "no idea", "first perfume",
    "knew na", "kisu jani na", "kichui jani na",
    "not a pro", "novice", "newbie",
    "don't know anything", "dont know anything",
}

BLIND_BUY_KEYWORDS: set[str] = {
    "blind buy", "blind-buy", "blindbuy",
    "can't smell", "without smelling", "not testing",
    "blind order", "without trying",
}

# -----------------------------
# Sales Objection Keywords
# -----------------------------

OBJECTION_PRICE_KEYWORDS: set[str] = {
    "why is your price so high",
    "why are your prices so high",
    "your price is too high",
    "your prices are too high",
    "price is too high",
    "too expensive",
    "why so expensive",
    "why is it so expensive",
    "very expensive",
    "it's too expensive",
    "expensive",
    "price ta beshi",
    "dam beshi hoye geche",
    "etan dam keno eto beshi",
    "etan ki eto dam",
    "dam komaben",
    "pricess komaben",
    "dam beshi",
    "praisen komaben",
    "dam ki beshi",
    "এতো দাম",
    "দাম বেশি",
    "etan dam",
    "i won't buy unless you reduce price",
    "etan dam beshi",
    "dam expensive",
    "price expensive",
    "keno expensive",
    "expensive keno",
    "eti ki eto dam",
}

OBJECTION_COMPETITOR_KEYWORDS: set[str] = {
    "daraz",
    "daraz এ",
    "daraz a",
    "another page",
    "other page",
    "other shop",
    "another shop",
    "competitor",
    "cheaper than",
    "sells cheaper",
    "other site",
    "another site",
    "other website",
    "another website",
    "অন্য দোকান",
    "onno dokan",
    "any dokan",
    "দারাজ",
    "priyoshop",
    "priyo shop",
}

REQUEST_DISCOUNT_KEYWORDS: set[str] = {
    "give me discount",
    "give discount",
    "discount dao",
    "discount den",
    "discount day",
    "কোন discount",
    "কোন অফার",
    "ডিসকাউন্ট দিন",
    "ছাড় দিন",
    "ছাড় দেন",
    "offer dao",
    "কম দামে দিন",
    "discount koro",
    "কিছু কম করুন",
    "একটু কম দাম",
    "ektu kom dam",
    "discount ase",
    "অফার আছে",
    "offer ase",
    "কি অফার",
    "ki offer",
    "কোন offer",
}

REQUEST_NEGOTIATION_KEYWORDS: set[str] = {
    "last price",
    "lastprice",
    "final price",
    "finalprice",
    "সর্বশেষ দাম",
    "sobcheye kom dam",
    "সবচেয়ে কম দাম",
    "nego",
    "negotiation",
    "sorbo shesh dam",
    "last price koto",
    "আসল দাম কত",
    "সেরা দাম",
    "koto kom dam",
    "reduce price",
    "price reduce",
    "price komaben",
    "dam komaben",
    "price koman",
    "dam koman",
}

REQUEST_DELIVERY_KEYWORDS: set[str] = {
    "free delivery",
    "free shipping",
    "delivery free",
    "শিপিং ফ্রি",
    "ডেলিভারি ফ্রি",
    "ডেলিভারি কি ফ্রি",
    "delivery ki free",
    "ফ্রি ডেলিভারি",
    "কুরিয়ার ফ্রি",
    "courier free",
    "shipping free",
    "delivery charge free",
    "free courier",
}

SALES_PERSUASION_KEYWORDS: set[str] = {
    "convince me",
    "persuade me",
    "sell me",
    "why should i buy",
    "why should i purchase",
    "বোঝান",
    "বুঝান",
    " convince ",
    "বিক্রি করান",
    "bujhan",
    "bojhan",
    "tell me why",
    "give me reasons",
    "kno kinbo",
    "keno kinbo",
    "keno kinbo apnar kache",
}

TRUST_CONCERN_KEYWORDS: set[str] = {
    "don't trust",
    "dont trust",
    "do not trust",
    "no trust",
    "how can i trust",
    "why should i trust",
    "bishshash",
    "bisshash",
    "বিশ্বাস",
    "বিশ্বাস হয় না",
    "bishshash hoy na",
    "bissash nei",
    "scam",
    "fraud",
    "guarantee",
    "গ্যারান্টি",
    "guarantee ase",
    "guarantee ki",
    "warranty",
    "online shop",
    "online theke",
    "online a kinbo",
        "secure",
    "i don't trust online",
    "why should i buy from you",
    "why would i buy from you",
    "keno apnar kacha theke kinbo",
    "kinbo keno",
}


def detect_intent(
    message: str,
    previous_intent: Intent | None = None,
    debug: bool = False,
) -> Intent:
    """Detect the user's intent."""

    raw_message = message.strip().lower()
    message = normalize(message)

    result = Intent.UNKNOWN

    # Precompute flags for the combined budget+recommendation check
    # (must be before the if-elif chain since Python requires elif to follow directly)
    _has_number = bool(re.search(r"\d+", raw_message))
    _has_budget_word = contains_keyword(raw_message, BUDGET_RECOMMENDATION_KEYWORDS) or contains_keyword(message, BUDGET_RECOMMENDATION_KEYWORDS)
    _has_luxury_word = contains_keyword(raw_message, LUXURY_RECOMMENDATION_KEYWORDS) or contains_keyword(message, LUXURY_RECOMMENDATION_KEYWORDS)
    _has_best_word = contains_keyword(raw_message, BEST_RECOMMENDATION_KEYWORDS) or contains_keyword(message, BEST_RECOMMENDATION_KEYWORDS)
    _RECOMMEND_REQUEST_WORDS = {"recommend", "suggest", "want", "looking", "need", "pick", "give me"}
    _has_request_word = any(w in raw_message.split() for w in _RECOMMEND_REQUEST_WORDS)
    # Specific best words vs generic recommendation words (suggest/recommend)
    _BEST_SPECIFIC_WORDS = {"best", "best one", "best perfume", "top", "top rated",
                            "top perfume", "popular", "most popular", "favorite", "number one",
                            "সেরা", "সেরা পারফিউম", "best ta", "best kon ta"}
    _has_specific_best = contains_keyword(raw_message, _BEST_SPECIFIC_WORDS) or contains_keyword(message, _BEST_SPECIFIC_WORDS)

    # -----------------------------
    # New intent checks (before greeting)
    # -----------------------------

    if contains_keyword(raw_message, BEGINNER_KEYWORDS) or contains_keyword(message, BEGINNER_KEYWORDS):
        result = Intent.BEGINNER

    elif contains_keyword(raw_message, BLIND_BUY_KEYWORDS) or contains_keyword(message, BLIND_BUY_KEYWORDS):
        result = Intent.BLIND_BUY

    elif contains_keyword(raw_message, COLLECTION_BUILDER_KEYWORDS) or contains_keyword(message, COLLECTION_BUILDER_KEYWORDS):
        result = Intent.COLLECTION_BUILDER

    elif _has_number and not contains_keyword(raw_message, GIFT_KEYWORDS) and any(p in raw_message for p in ["perfumes", "fragrances", "scents", "পারফিউম", "সুগন্ধি"]):
        # "buy 5 perfumes" → collection builder (multiple items)
        result = Intent.COLLECTION_BUILDER

    # -----------------------------
    # Combined budget/recommendation + luxury/best check (must come before objection!)
    # Prevents "expensive smelling under 3000" or "I want expensive perfume"
    # from routing to price objection. Only fires when not already matched above.
    # -----------------------------

    elif (_has_budget_word or _has_number or _has_request_word) and (_has_luxury_word or _has_best_word) and not contains_keyword(raw_message, GIFT_KEYWORDS):
        # Priority: specific best > luxury > budget > generic best
        if _has_specific_best:
            # "best perfume under 3000" → BEST_RECOMMENDATION
            result = Intent.BEST_RECOMMENDATION
        elif _has_luxury_word:
            # "expensive under 3000" or "luxury with budget" → LUXURY_RECOMMENDATION
            result = Intent.LUXURY_RECOMMENDATION
        elif _has_budget_word and _has_best_word and not _has_request_word:
            # budget + generic best + no request word → BUDGET_RECOMMENDATION
            result = Intent.BUDGET_RECOMMENDATION
        elif _has_request_word and (_has_budget_word or _has_number):
            # "suggest cheap" or "want something under 3000" → BUDGET_RECOMMENDATION (budget > generic suggest)
            result = Intent.BUDGET_RECOMMENDATION
        elif _has_best_word:
            # "suggest" alone → BEST_RECOMMENDATION
            result = Intent.BEST_RECOMMENDATION
        elif _has_budget_word:
            # fallback to budget
            result = Intent.BUDGET_RECOMMENDATION

    # -----------------------------
    # Conversation
    # -----------------------------

    elif starts_with_phrase(message, THANKS):
        result = Intent.THANKS

    elif starts_with_phrase(message, GOODBYES):
        result = Intent.GOODBYE

    elif starts_with_phrase(message, GREETINGS):
        # Check if greeting also contains a product request
        if contains_keyword(raw_message, _GREETING_REQUEST_KEYWORDS):
            result = Intent.PRODUCT_SEARCH
        else:
            result = Intent.GREETING

    # -----------------------------
    # FAQ
    # -----------------------------

    elif "cash on delivery" in message:
        result = Intent.PAYMENT

    elif contains_keyword(message, DELIVERY_KEYWORDS):
        result = Intent.DELIVERY

    elif contains_keyword(message, PAYMENT_KEYWORDS):
        result = Intent.PAYMENT

    elif contains_keyword(message, LOCATION_KEYWORDS):
        result = Intent.LOCATION

    # -----------------------------
    # Store information
    # -----------------------------

    elif contains_keyword(message, STORE_INFO_KEYWORDS):
        result = Intent.STORE_INFO

    # -----------------------------
    # Sales objections (higher priority than product search, comparison, gift)
    # -----------------------------

    elif contains_keyword(raw_message, OBJECTION_PRICE_KEYWORDS) or contains_keyword(message, OBJECTION_PRICE_KEYWORDS):
        result = Intent.OBJECTION_PRICE

    elif contains_keyword(raw_message, OBJECTION_COMPETITOR_KEYWORDS) or contains_keyword(message, OBJECTION_COMPETITOR_KEYWORDS):
        result = Intent.OBJECTION_COMPETITOR

    elif contains_keyword(raw_message, REQUEST_DISCOUNT_KEYWORDS) or contains_keyword(message, REQUEST_DISCOUNT_KEYWORDS):
        result = Intent.REQUEST_DISCOUNT

    elif contains_keyword(raw_message, REQUEST_NEGOTIATION_KEYWORDS) or contains_keyword(message, REQUEST_NEGOTIATION_KEYWORDS):
        result = Intent.REQUEST_NEGOTIATION

    elif contains_keyword(raw_message, REQUEST_DELIVERY_KEYWORDS) or contains_keyword(message, REQUEST_DELIVERY_KEYWORDS):
        result = Intent.REQUEST_DELIVERY

    elif contains_keyword(raw_message, TRUST_CONCERN_KEYWORDS) or contains_keyword(message, TRUST_CONCERN_KEYWORDS):
        result = Intent.TRUST_CONCERN

    elif contains_keyword(raw_message, SALES_PERSUASION_KEYWORDS) or contains_keyword(message, SALES_PERSUASION_KEYWORDS):
        result = Intent.SALES_PERSUASION

    # -----------------------------
    # Explicit product-info intents (must come before generic PRODUCT_SEARCH)
    # -----------------------------

    elif contains_keyword(message, PRODUCT_INFO_KEYWORDS):
        result = Intent.PRODUCT_INFO

    elif contains_keyword(message, PRICE_QUERY_KEYWORDS):
        result = Intent.PRICE_QUERY

    elif contains_keyword(message, ATTRIBUTE_QUERY_KEYWORDS):
        result = Intent.ATTRIBUTE_QUERY

    elif contains_keyword(message, COMPARISON_QUERY_KEYWORDS):
        result = Intent.COMPARISON_QUERY

    # -----------------------------
    # Gift intent (must be before recommendation intents and product search)
    # -----------------------------

    elif contains_keyword(message, GIFT_KEYWORDS) or contains_keyword(raw_message, GIFT_KEYWORDS):
        result = Intent.GIFT

    # -----------------------------
    # Recommendation intents (before product search)
    # Priority: BEST > LUXURY > GENDER > BUDGET > OCCASION > SEASON > STYLE > GIFT
    # -----------------------------

    elif contains_keyword(raw_message, BEST_RECOMMENDATION_KEYWORDS) or contains_keyword(message, BEST_RECOMMENDATION_KEYWORDS):
        result = Intent.BEST_RECOMMENDATION

    elif contains_keyword(raw_message, LUXURY_RECOMMENDATION_KEYWORDS) or contains_keyword(message, LUXURY_RECOMMENDATION_KEYWORDS):
        result = Intent.LUXURY_RECOMMENDATION

    elif contains_keyword(raw_message, GENDER_FILTER_KEYWORDS) or contains_keyword(message, GENDER_FILTER_KEYWORDS):
        result = Intent.GENDER_FILTER

    elif contains_keyword(raw_message, BUDGET_RECOMMENDATION_KEYWORDS) or contains_keyword(message, BUDGET_RECOMMENDATION_KEYWORDS):
        result = Intent.BUDGET_RECOMMENDATION

    elif contains_keyword(raw_message, OCCASION_RECOMMENDATION_KEYWORDS) or contains_keyword(message, OCCASION_RECOMMENDATION_KEYWORDS):
        result = Intent.OCCASION_RECOMMENDATION

    elif contains_keyword(raw_message, SEASON_RECOMMENDATION_KEYWORDS) or contains_keyword(message, SEASON_RECOMMENDATION_KEYWORDS):
        result = Intent.SEASON_RECOMMENDATION

    elif contains_keyword(raw_message, STYLE_RECOMMENDATION_KEYWORDS) or contains_keyword(message, STYLE_RECOMMENDATION_KEYWORDS):
        result = Intent.STYLE_RECOMMENDATION

    elif contains_keyword(raw_message, GIFT_RECOMMENDATION_KEYWORDS) or contains_keyword(message, GIFT_RECOMMENDATION_KEYWORDS):
        result = Intent.GIFT_RECOMMENDATION

    # -----------------------------
    # Product Search
    # -----------------------------

    elif contains_keyword(message, PRODUCT_KEYWORDS):
        result = Intent.PRODUCT_SEARCH

    # -----------------------------
    # Context order
    # -----------------------------

    elif (
        previous_intent == Intent.PRODUCT_SEARCH
        and message in {
            "i want this",
            "i need this",
            "want this one",
            "take this",
            "this one",
            "eta chai",
            "eta nibo",
            "এটা চাই",
            "এটা নিবো",
        }
    ) or contains_keyword(message, ORDER_KEYWORDS):
        result = Intent.ORDER

    # -----------------------------
    # Follow-up product question
    # -----------------------------

    elif (
        previous_intent in {
            Intent.PRODUCT_SEARCH,
            Intent.PRODUCT_DETAIL,
            Intent.PRODUCT_INFO,
            Intent.PRICE_QUERY,
            Intent.ATTRIBUTE_QUERY,
            Intent.COMPARISON_QUERY,
        }
        and contains_keyword(message, FOLLOWUP_KEYWORDS)
    ):
        result = Intent.FOLLOW_UP

    # -----------------------------
    # Casual
    # -----------------------------

    elif matches_phrase(message, CASUAL):
        result = Intent.CASUAL

    if debug:
        logger.debug("Input: %s | Previous intent: %s | Detected: %s", message, previous_intent, result)

    return result
