from app.intent import Intent, detect_intent

# -----------------------------
# Greeting
# -----------------------------

def test_greeting():
    assert detect_intent("hello") == Intent.GREETING
    assert detect_intent("Hi") == Intent.GREETING
    assert detect_intent("assalamu alaikum") == Intent.GREETING
    assert detect_intent("হ্যালো") == Intent.GREETING


# -----------------------------
# Thanks
# -----------------------------

def test_thanks():
    assert detect_intent("thanks") == Intent.THANKS
    assert detect_intent("thank you") == Intent.THANKS
    assert detect_intent("thx") == Intent.THANKS
    assert detect_intent("ধন্যবাদ") == Intent.THANKS


# -----------------------------
# Goodbye
# -----------------------------

def test_goodbye():
    assert detect_intent("bye") == Intent.GOODBYE
    assert detect_intent("goodbye") == Intent.GOODBYE
    assert detect_intent("allah hafez") == Intent.GOODBYE


# -----------------------------
# Casual
# -----------------------------

def test_casual():
    assert detect_intent("nice") == Intent.CASUAL
    assert detect_intent("awesome") == Intent.CASUAL
    assert detect_intent("okay") == Intent.CASUAL


# -----------------------------
# Delivery
# -----------------------------

def test_delivery():
    assert detect_intent("delivery charge") == Intent.DELIVERY
    assert detect_intent("how much is delivery") == Intent.DELIVERY
    assert detect_intent("কত দিনে ডেলিভারি") == Intent.DELIVERY


# -----------------------------
# Payment
# -----------------------------

def test_payment():
    assert detect_intent("bkash") == Intent.PAYMENT
    assert detect_intent("cash on delivery") == Intent.PAYMENT
    assert detect_intent("payment methods") == Intent.PAYMENT


# -----------------------------
# Location
# -----------------------------

def test_location():
    assert detect_intent("shop address") == Intent.LOCATION
    assert detect_intent("location") == Intent.LOCATION
    assert detect_intent("ঠিকানা") == Intent.LOCATION


# -----------------------------
# Product Search
# -----------------------------

def test_product_search():
    assert detect_intent("lattafa") == Intent.PRODUCT_SEARCH
    assert detect_intent("best perfume") == Intent.BEST_RECOMMENDATION
    assert detect_intent("perfume under 2000") in (Intent.PRODUCT_SEARCH, Intent.BUDGET_RECOMMENDATION)
    assert detect_intent("sweet fragrance") == Intent.PRODUCT_SEARCH


# -----------------------------
# Explicit Order
# -----------------------------

def test_order():
    assert detect_intent("checkout") == Intent.ORDER
    assert detect_intent("order now") == Intent.ORDER
    assert detect_intent("order korbo") == Intent.ORDER


# -----------------------------
# Context Order
# -----------------------------

def test_context_order():
    assert (
        detect_intent(
            "this one",
            previous_intent=Intent.PRODUCT_SEARCH,
        )
        == Intent.ORDER
    )


# -----------------------------
# Product Follow-up
# -----------------------------

def test_followup():
    assert (
        detect_intent(
            "which one",
            previous_intent=Intent.PRODUCT_SEARCH,
        )
        == Intent.FOLLOW_UP
    )


def test_product_followup():
    """Regression: product info questions after search should use PRODUCT_INFO."""
    # Turn 1: product search
    assert (
        detect_intent("show me all perfumes")
        == Intent.PRODUCT_SEARCH
    )

    # Turn 2: follow-up product info
    assert (
        detect_intent(
            "how long does it last?",
            previous_intent=Intent.PRODUCT_SEARCH,
        )
        == Intent.PRODUCT_INFO
    )


# -----------------------------
# Gift Intent (must be detected before UNKNOWN)
# -----------------------------

def test_gift_intent_husband():
    assert detect_intent("suggest a gift for my husband") == Intent.GIFT
    assert detect_intent("gift for husband") == Intent.GIFT
    assert detect_intent("something for my husband") == Intent.GIFT


def test_gift_intent_wife():
    assert detect_intent("gift for wife") == Intent.GIFT
    assert detect_intent("present for my wife") == Intent.GIFT


def test_gift_intent_girlfriend():
    assert detect_intent("perfume for my girlfriend birthday") == Intent.GIFT
    assert detect_intent("gift for girlfriend") == Intent.GIFT


def test_gift_intent_boyfriend():
    assert detect_intent("something for my boyfriend") == Intent.GIFT
    assert detect_intent("birthday gift for boyfriend") == Intent.GIFT


def test_gift_intent_generic():
    assert detect_intent("gift") == Intent.GIFT
    assert detect_intent("valentine gift") == Intent.GIFT
    assert detect_intent("anniversary present") == Intent.GIFT


def test_gift_intent_not_confused_with_product_search():
    """Gift must take priority over generic product_search for ambiguous queries."""
    assert detect_intent("gift for husband") == Intent.GIFT


# -----------------------------
# Price/Objection
# -----------------------------

def test_objection_price():
    assert detect_intent("Why is your price so high?") == Intent.OBJECTION_PRICE
    assert detect_intent("too expensive") == Intent.OBJECTION_PRICE
    assert detect_intent("your price is too high") == Intent.OBJECTION_PRICE
    assert detect_intent("I won't buy unless you reduce price") == Intent.OBJECTION_PRICE


def test_objection_competitor():
    assert detect_intent("Daraz is cheaper") == Intent.OBJECTION_COMPETITOR
    assert detect_intent("Another page sells cheaper") == Intent.OBJECTION_COMPETITOR
    assert detect_intent("competitor") == Intent.OBJECTION_COMPETITOR


def test_request_discount():
    assert detect_intent("Give me discount") == Intent.REQUEST_DISCOUNT
    assert detect_intent("discount den") == Intent.REQUEST_DISCOUNT
    assert detect_intent("কোন অফার আছে") == Intent.REQUEST_DISCOUNT


def test_request_negotiation():
    assert detect_intent("Last price?") == Intent.REQUEST_NEGOTIATION
    assert detect_intent("final price") == Intent.REQUEST_NEGOTIATION
    assert detect_intent("sorbo shesh dam") == Intent.REQUEST_NEGOTIATION


def test_request_delivery():
    assert detect_intent("কুরিয়ার ফ্রি") == Intent.REQUEST_DELIVERY


def test_sales_persuasion():
    assert detect_intent("Convince me") == Intent.SALES_PERSUASION
    assert detect_intent("why should i buy") == Intent.SALES_PERSUASION
    assert detect_intent("sell me") == Intent.SALES_PERSUASION


def test_trust_concern():
    assert detect_intent("Why should I buy from you?") == Intent.TRUST_CONCERN
    assert detect_intent("how can i trust") == Intent.TRUST_CONCERN
    assert detect_intent("i don't trust online") == Intent.TRUST_CONCERN


# -----------------------------
# Objection intents take priority over product search
# -----------------------------

def test_objection_price_takes_priority_over_product_search():
    """Regression: price objection must not trigger product search."""
    result = detect_intent("Why is your price so high?")
    assert result == Intent.OBJECTION_PRICE
    assert result != Intent.PRODUCT_SEARCH


def test_objection_competitor_takes_priority_over_product_search():
    """Regression: competitor objection must not trigger product search."""
    result = detect_intent("Daraz is cheaper")
    assert result == Intent.OBJECTION_COMPETITOR
    assert result != Intent.PRODUCT_SEARCH


def test_request_discount_takes_priority_over_product_search():
    """Regression: discount request must not trigger product search."""
    result = detect_intent("Give me discount")
    assert result == Intent.REQUEST_DISCOUNT
    assert result != Intent.PRODUCT_SEARCH


def test_trust_concern_over_product_search():
    """Regression: trust concern must not trigger product search."""
    assert detect_intent("why should i buy from you") == Intent.TRUST_CONCERN
    assert detect_intent("i don't trust online") == Intent.TRUST_CONCERN
    assert detect_intent("scam") == Intent.TRUST_CONCERN


# -----------------------------
# Unknown
# -----------------------------

def test_unknown():
    assert detect_intent("asdfgh") == Intent.UNKNOWN
    assert detect_intent("123456") == Intent.UNKNOWN