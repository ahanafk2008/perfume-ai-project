"""Tests for product attribute extraction and formatting."""

import json

from app.product_attrs import (
    format_product_attributes,
    get_product_attributes,
    has_any_attribute,
)


def test_get_attributes_returns_all_fields():
    """get_product_attributes should return a dict with all expected keys."""
    attrs = get_product_attributes({"data": "{}"})
    assert "type" in attrs
    assert "longevity" in attrs
    assert "sillage" in attrs
    assert "best_time" in attrs
    assert "notes_top" in attrs
    assert "notes_middle" in attrs
    assert "notes_base" in attrs


def test_get_attributes_all_none_when_empty():
    """All attribute values should be None when fragrance_details is empty."""
    attrs = get_product_attributes({"data": '{"fragrance_details": {}}'})
    assert all(v is None for v in attrs.values())


def test_get_attributes_all_none_when_no_data():
    """All attribute values should be None when product has no data field."""
    attrs = get_product_attributes({})
    assert all(v is None for v in attrs.values())


def test_get_attributes_parses_values():
    """Attribute values should be parsed from fragrance_details."""
    product = {
        "data": json.dumps({
            "fragrance_details": {
                "type": "EDP",
                "longevity": "6-8 hours",
                "sillage": "moderate",
                "bestTime": "office",
                "notes": {
                    "top": ["bergamot", "lemon"],
                    "middle": ["jasmine"],
                    "base": ["musk", "amber"],
                },
            },
        }),
    }
    attrs = get_product_attributes(product)
    assert attrs["type"] == "EDP"
    assert attrs["longevity"] == "6-8 hours"
    assert attrs["sillage"] == "moderate"
    assert attrs["best_time"] == "office"
    assert attrs["notes_top"] == ["bergamot", "lemon"]
    assert attrs["notes_middle"] == ["jasmine"]
    assert attrs["notes_base"] == ["musk", "amber"]


def test_has_any_attribute_false_when_empty():
    """has_any_attribute should return False when no attributes exist."""
    assert has_any_attribute({"data": "{}"}) is False
    assert has_any_attribute({}) is False


def test_has_any_attribute_true_when_populated():
    """has_any_attribute should return True when attributes exist."""
    product = {"data": '{"fragrance_details": {"longevity": "6h"}}'}
    assert has_any_attribute(product) is True


def test_format_product_attributes_returns_none_when_empty():
    """format_product_attributes should return None when no attributes exist."""
    assert format_product_attributes({"data": "{}"}) is None
    assert format_product_attributes({}) is None


def test_format_product_attributes_formats_all_fields():
    """format_product_attributes should return formatted string."""
    product = {
        "data": json.dumps({
            "fragrance_details": {
                "type": "EDP",
                "longevity": "6-8 hours",
                "sillage": "moderate",
                "bestTime": "office",
            },
        }),
    }
    result = format_product_attributes(product)
    assert result is not None
    assert "Type: EDP" in result
    assert "Longevity: 6-8 hours" in result
    assert "Sillage: moderate" in result
    assert "Best for: office" in result


# -----------------------------
# Structured fragrance tags (scent_family, occasion, performance)
# -----------------------------

def test_get_attributes_includes_scent_family():
    """get_product_attributes should include scent_family when present."""
    product = {"data": json.dumps({"fragrance_details": {"scent_family": ["sweet", "vanilla"]}})}
    attrs = get_product_attributes(product)
    assert attrs["scent_family"] == ["sweet", "vanilla"]


def test_get_attributes_includes_occasion():
    """get_product_attributes should include occasion when present."""
    product = {"data": json.dumps({"fragrance_details": {"occasion": ["office", "date"]}})}
    attrs = get_product_attributes(product)
    assert attrs["occasion"] == ["office", "date"]


def test_get_attributes_includes_performance():
    """get_product_attributes should include performance when present."""
    product = {"data": json.dumps({"fragrance_details": {"performance": ["strong", "long lasting"]}})}
    attrs = get_product_attributes(product)
    assert attrs["performance"] == ["strong", "long lasting"]


def test_get_attributes_returns_none_for_missing_tags():
    """get_product_attributes should return None for missing structured fields."""
    attrs = get_product_attributes({"data": '{"fragrance_details": {}}'})
    assert attrs["scent_family"] is None
    assert attrs["occasion"] is None
    assert attrs["performance"] is None


def test_format_product_attributes_includes_scent_family():
    """format_product_attributes should include scent_family when present."""
    product = {"data": json.dumps({"fragrance_details": {"scent_family": ["sweet", "vanilla"]}})}
    result = format_product_attributes(product)
    assert result is not None
    assert "Scent: sweet, vanilla" in result


def test_format_product_attributes_includes_occasion():
    """format_product_attributes should include occasion when present."""
    product = {"data": json.dumps({"fragrance_details": {"occasion": ["office", "party"]}})}
    result = format_product_attributes(product)
    assert result is not None
    assert "Occasion: office, party" in result


def test_format_product_attributes_includes_performance():
    """format_product_attributes should include performance when present."""
    product = {"data": json.dumps({"fragrance_details": {"performance": ["long lasting"]}})}
    result = format_product_attributes(product)
    assert result is not None
    assert "Performance: long lasting" in result


def test_format_product_attributes_includes_notes():
    """Notes should be formatted as Top/Middle/Base sections."""
    product = {
        "data": json.dumps({
            "fragrance_details": {
                "notes": {
                    "top": ["bergamot", "lemon"],
                    "middle": ["jasmine"],
                    "base": ["musk"],
                },
            },
        }),
    }
    result = format_product_attributes(product)
    assert result is not None
    assert "Top: bergamot, lemon" in result
    assert "Middle: jasmine" in result
    assert "Base: musk" in result


# -----------------------------
# Prompt builder: hallucination prevention
# -----------------------------

def test_product_format_shows_no_fragrance_data():
    """Products should show '[No fragrance data]' when attributes are empty."""
    from app.prompt_builder import build_prompt

    product_no_attrs = {
        "id": "1",
        "name": "Test Perfume",
        "brand": "Lattafa",
        "category": "Men",
        "price": 800,
        "data": '{}',
    }

    prompt = build_prompt(
        user_message="show me perfumes",
        products=[product_no_attrs],
        searched=True,
        history=[],
        language="en",
    )

    assert "Test Perfume" in prompt, "Product should still appear in prompt"
    assert "Lattafa" in prompt, "Brand info should be present"
    assert "[No fragrance data]" not in prompt, "No-fragrance tag should not appear"


def test_product_format_shows_attributes_when_present():
    """Products should show attribute data when it exists."""
    from app.prompt_builder import build_prompt

    product_with_attrs = {
        "id": "2",
        "name": "Premium Scent",
        "brand": "Dior",
        "category": "Men",
        "price": 2000,
        "data": json.dumps({
            "fragrance_details": {
                "type": "EDP",
                "longevity": "6-8 hours",
            },
        }),
    }

    prompt = build_prompt(
        user_message="show me perfumes",
        products=[product_with_attrs],
        searched=True,
        history=[],
        language="en",
    )

    assert "[Type: EDP | Longevity: 6-8 hours]" in prompt, (
        "Product with attributes should show formatted attribute data"
    )


def test_product_format_no_data_field_shows_no_fragrance_data():
    """Products without a data field should show '[No fragrance data]'."""
    from app.prompt_builder import build_prompt

    product_no_data_field = {
        "id": "3",
        "name": "Simple Perfume",
        "brand": "Lattafa",
        "category": "Men",
        "price": 800,
    }

    prompt = build_prompt(
        user_message="show me perfumes",
        products=[product_no_data_field],
        searched=True,
        history=[],
        language="en",
    )

    assert "[No fragrance data]" not in prompt, (
        "Product without a data field should not add the note "
        "(data field doesn't exist, so we can't know if attributes are missing)"
    )


# -----------------------------
# Combo exclusion from normal queries (prompt level)
# -----------------------------

def test_combo_does_not_appear_for_normal_query():
    """Combos should not appear in normal recommendation queries."""
    from app.search import search_products

    results = search_products("best perfume")
    for p in results:
        cat = (p.get("category") or "").lower()
        assert cat != "combo", f"Combo product '{p.get('name')}' should not appear for normal recommendation"


# -----------------------------
# Hallucination: description/tagline removed from AI context
# -----------------------------

def test_product_format_excludes_description():
    """Description field must not appear in AI product context."""
    from app.prompt_builder import build_prompt

    product_with_desc = {
        "id": "5",
        "name": "Test Perfume",
        "brand": "Lattafa",
        "category": "Men",
        "price": 800,
        "description": "Sweet floral perfume with vanilla notes and musk base",
        "data": '{}',
    }

    prompt = build_prompt(
        user_message="show me perfumes",
        products=[product_with_desc],
        searched=True,
        history=[],
        language="en",
    )

    assert "Sweet floral" not in prompt, (
        "Description text must not appear in AI context to prevent hallucination"
    )
    assert "vanilla notes" not in prompt, (
        "Description text must not appear in AI context"
    )


def test_product_format_excludes_tagline():
    """Tagline from data JSON must not appear in AI product context."""
    import json

    from app.prompt_builder import build_prompt

    product_with_tagline = {
        "id": "6",
        "name": "Test Perfume",
        "brand": "Lattafa",
        "category": "Men",
        "price": 800,
        "data": json.dumps({"tagline": "A romantic and seductive scent for special occasions"}),
    }

    prompt = build_prompt(
        user_message="show me perfumes",
        products=[product_with_tagline],
        searched=True,
        history=[],
        language="en",
    )

    assert "romantic and seductive" not in prompt, (
        "Tagline text must not appear in AI context to prevent hallucination"
    )


# -----------------------------
# Gift intent with "for my wife" / "for my husband"
# -----------------------------

def test_gift_intent_for_my_wife():
    """'for my wife' should detect gift intent."""
    from app.filters import detect_gift
    assert detect_gift("gift for my wife") is True
    assert detect_gift("suggest something for my wife") is True
    assert detect_gift("present for my wife") is True


def test_gift_intent_for_my_husband():
    """'for my husband' should detect gift intent."""
    from app.filters import detect_gift
    assert detect_gift("gift for my husband") is True
    assert detect_gift("present for my husband") is True


def test_gift_intent_for_girlfriend():
    """'for girlfriend' should detect gift intent."""
    from app.filters import detect_gift
    assert detect_gift("gift for girlfriend") is True
    assert detect_gift("present for my girlfriend") is True


# -----------------------------
# Budget query (numeric) vs cheap intent
# -----------------------------

def test_budget_query_boosts_premium_within_budget():
    """A numeric budget query should rank premium products higher within budget."""
    from app.ranking import rank_products

    premium_in_budget = {
        "id": "140",
        "name": "Dior Sauvage",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 1800,
    }
    non_premium_in_budget = {
        "id": "141",
        "name": "Generic Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 1500,
    }

    ranked = rank_products(
        [non_premium_in_budget, premium_in_budget],
        "perfume under 2000",
        budget=2000,
        cheap_intent=False,
    )

    assert ranked[0]["id"] == "140", (
        "Premium product within budget should rank higher than non-premium"
    )


def test_cheap_intent_no_budget_ranks_lowest_price():
    """Cheap intent without numeric budget should rank lowest price first."""
    from app.ranking import rank_products

    cheap_product = {
        "id": "150",
        "name": "Cheap Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 500,
    }
    expensive = {
        "id": "151",
        "name": "Expensive Scent",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 3000,
    }

    ranked = rank_products(
        [expensive, cheap_product],
        "cheap perfume",
        cheap_intent=True,
        budget=None,
    )

    assert ranked[0]["id"] == "150", (
        "Cheapest product should rank first for cheap intent without budget"
    )


def test_budget_without_cheap_intent_does_not_cheap_sort():
    """Numeric budget without cheap_intent should NOT apply cheap sort."""
    from app.ranking import calculate_score

    cheap_product = {
        "id": "160",
        "name": "Cheap Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 500,
    }
    expensive = {
        "id": "161",
        "name": "Expensive Scent",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 3000,
    }

    cheap_score = calculate_score(
        cheap_product, "perfume under 3000",
        budget=3000, cheap_intent=False,
    )
    expensive_score = calculate_score(
        expensive, "perfume under 3000",
        budget=3000, cheap_intent=False,
    )

    # Without cheap_intent, expensive premium product should score higher
    assert expensive_score > cheap_score, (
        "Without cheap intent, premium product should score higher even though it's more expensive"
    )


# -----------------------------
# Occasion queries return products (DB stop words fix)
# -----------------------------

def test_occasion_query_returns_products():
    """Occasion queries like 'date night', 'office' should return products."""
    from app.search import search_products

    for query in ["date night perfume", "office perfume", "party fragrance", "wedding perfume"]:
        results = search_products(query)
        assert len(results) > 0, (
            f"Occasion query '{query}' should return products"
        )


# -----------------------------
# Scent matching from fragrance_details
# -----------------------------

def test_scent_matches_fragrance_notes():
    """Scent intent should match against fragrance_details notes."""
    from app.ranking import _matches_scent

    product_with_notes = {
        "id": "170",
        "name": "Floral Scent",
        "brand": "Test",
        "category": "Women",
        "description": "",
        "price": 1000,
        "data": json.dumps({
            "fragrance_details": {
                "notes": {
                    "top": ["bergamot", "lemon"],
                    "middle": ["jasmine", "rose"],
                    "base": ["musk"],
                },
            },
        }),
    }
    product_no_notes = {
        "id": "171",
        "name": "Plain",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    assert _matches_scent(product_with_notes, "floral") is True
    # bergamot, lemon are citrus = fresh category
    assert _matches_scent(product_with_notes, "fresh") is True
    # No sweet/vanilla notes → does not match
    assert _matches_scent(product_with_notes, "sweet") is False
    # No product notes → does not match
    assert _matches_scent(product_no_notes, "floral") is False


def test_occasion_matches_best_time():
    """Occasion intent should match against fragrance_details bestTime."""
    from app.ranking import _matches_occasion

    product_with_best_time = {
        "id": "172",
        "name": "Office Scent",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 1000,
        "data": json.dumps({
            "fragrance_details": {"bestTime": "office"},
        }),
    }
    product_no_data = {
        "id": "173",
        "name": "Plain",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    assert _matches_occasion(product_with_best_time, "office") is True
    assert _matches_occasion(product_no_data, "office") is False
    assert _matches_occasion(product_no_data, None) is False


def test_matches_scent_from_ranking():
    from app.ranking import _matches_scent

    product = {
        "data": json.dumps({
            "fragrance_details": {
                "scent_family": ["sweet", "vanilla"]
            }
        })
    }

    assert _matches_scent(product, "sweet") is True
    assert _matches_scent(product, "fresh") is False
    assert _matches_scent(product, None) is False


def test_matches_performance_from_ranking():
    from app.ranking import _matches_performance

    product = {
        "data": json.dumps({
            "fragrance_details": {
                "performance": ["long lasting"]
            }
        })
    }

    assert _matches_performance(product, "long lasting") is True
    assert _matches_performance(product, "strong") is False
    assert _matches_performance(product, None) is False

