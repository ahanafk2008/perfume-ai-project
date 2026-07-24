"""Tests for the objection handler."""

from app.intent import Intent
from app.objection_handler import (
    _extract_product_name,
    handle_competitor_objection,
    handle_delivery_objection,
    handle_discount_request,
    handle_intent,
    handle_negotiation,
    handle_price_objection,
    handle_sales_persuasion,
    handle_trust_concern,
)

# -----------------------------
# Product name extraction
# -----------------------------

def test_extract_product_name_capitalized():
    assert _extract_product_name("Why is CDNIM expensive?") == "CDNIM"


def test_extract_product_name_quoted():
    assert _extract_product_name('What about "Lattafa Asad"?') == "Lattafa Asad"


def test_extract_product_name_none():
    assert _extract_product_name("Why is your price so high?") is None


# -----------------------------
# Price objection
# -----------------------------

def test_handle_price_objection_with_product():
    result = handle_price_objection("CDNIM")
    assert "CDNIM" in result
    assert "price" in result.lower()


def test_handle_price_objection_without_product():
    result = handle_price_objection()
    assert "authenticity" in result.lower() or "quality" in result.lower()
    assert "which perfume" in result.lower()


# -----------------------------
# Competitor objection
# -----------------------------

def test_handle_competitor_objection_daraz():
    result = handle_competitor_objection("Daraz")
    assert "Daraz" in result


def test_handle_competitor_objection_generic():
    result = handle_competitor_objection()
    assert "authenticity" in result.lower()


# -----------------------------
# Discount request
# -----------------------------

def test_handle_discount_request_with_product():
    result = handle_discount_request("Yara")
    assert "Yara" in result


def test_handle_discount_request_without_product():
    result = handle_discount_request()
    assert "Which perfume" in result or "which perfume" in result.lower()


# -----------------------------
# Negotiation
# -----------------------------

def test_handle_negotiation_with_product():
    result = handle_negotiation("Hawas")
    assert "Hawas" in result


def test_handle_negotiation_without_product():
    result = handle_negotiation()
    assert "Which perfume" in result


# -----------------------------
# Delivery objection
# -----------------------------

def test_handle_delivery_objection():
    result = handle_delivery_objection()
    assert "location" in result.lower() or "delivery" in result.lower()


# -----------------------------
# Sales persuasion
# -----------------------------

def test_handle_sales_persuasion_with_product():
    result = handle_sales_persuasion("Rasasi Hawas")
    assert "Rasasi" in result


def test_handle_sales_persuasion_without_product():
    result = handle_sales_persuasion()
    assert "authentic" in result.lower()


# -----------------------------
# Trust concern
# -----------------------------

def test_handle_trust_concern():
    result = handle_trust_concern()
    assert "authenticity" in result.lower() or "trust" in result.lower()
    assert "Scent Of Time" in result


# -----------------------------
# Intent routing
# -----------------------------

def test_handle_intent_price_objection():
    result = handle_intent(Intent.OBJECTION_PRICE, "Why is your price so high?")
    assert result is not None
    assert "authenticity" in result.lower()


def test_handle_intent_objection_competitor():
    result = handle_intent(Intent.OBJECTION_COMPETITOR, "Daraz is cheaper")
    assert result is not None
    assert "Daraz" in result


def test_handle_intent_request_discount():
    result = handle_intent(Intent.REQUEST_DISCOUNT, "Give me discount")
    assert result is not None
    assert "offer" in result.lower()


def test_handle_intent_request_negotiation():
    result = handle_intent(Intent.REQUEST_NEGOTIATION, "Last price?")
    assert result is not None
    assert "offer" in result.lower() or "price" in result.lower()


def test_handle_intent_request_delivery():
    result = handle_intent(Intent.REQUEST_DELIVERY, "Free delivery?")
    assert result is not None
    assert "delivery" in result.lower()


def test_handle_intent_sales_persuasion():
    result = handle_intent(Intent.SALES_PERSUASION, "Convince me")
    assert result is not None
    assert "authentic" in result.lower()


def test_handle_intent_trust_concern():
    result = handle_intent(Intent.TRUST_CONCERN, "I don't trust online shops")
    assert result is not None
    assert "authenticity" in result.lower() or "trust" in result.lower() or "Scent Of Time" in result


def test_handle_intent_explicit_product_name():
    """When a product name is mentioned in the message, it should be used."""
    result = handle_intent(Intent.OBJECTION_PRICE, "Why is CDNIM expensive?")
    assert result is not None
    assert "CDNIM" in result


def test_handle_intent_unknown_returns_none():
    result = handle_intent(Intent.UNKNOWN, "hello")
    assert result is None
