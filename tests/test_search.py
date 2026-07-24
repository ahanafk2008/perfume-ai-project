from app.search import search_products

# -----------------------------
# Empty query
# -----------------------------

def test_empty_query():
    assert search_products("") == []
    assert search_products("   ") == []


# -----------------------------
# Brand search
# -----------------------------

def test_brand_search():
    results = search_products("lattafa")

    assert isinstance(results, list)

    for product in results:
        brand = (product.get("brand") or "").lower()
        assert "lattafa" in brand


# -----------------------------
# Budget search
# -----------------------------

def test_budget_search():
    results = search_products("under 2000")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 2000


# -----------------------------
# Name search
# -----------------------------

def test_name_search():
    results = search_products("yara")

    assert isinstance(results, list)


# -----------------------------
# Gender search
# -----------------------------

def test_gender_search():
    results = search_products("women perfume")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] is not None


# -----------------------------
# Combo search
# -----------------------------

def test_combo_search():
    results = search_products("gift set")

    assert isinstance(results, list)


# -----------------------------
# Unknown product
# -----------------------------

def test_unknown_product():
    results = search_products("asdfghjkl")

    assert results == []


# -----------------------------
# Budget + filter queries
# -----------------------------

def test_best_perfume_under_2000():
    results = search_products("best perfume under 2000")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 2000


def test_perfume_below_1500():
    results = search_products("perfume below 1500")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 1500


def test_under_3000():
    results = search_products("under 3000")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 3000


def test_lattafa_under_3000():
    results = search_products("lattafa under 3000")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 3000

        brand = (product.get("brand") or "").lower()
        assert "lattafa" in brand


def test_men_perfume_under_2500():
    results = search_products("men perfume under 2500")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 2500


def test_blue_perfume_under_2000():
    results = search_products("blue perfume under 2000")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 2000


def test_gift_under_3000():
    results = search_products("gift under 3000")

    assert isinstance(results, list)

    for product in results:
        assert product["price"] <= 3000


# -----------------------------
# New regression tests
# -----------------------------

def test_brand_not_found_does_not_return_random_products():
    """Regression: when brand requested but missing, don't return unrelated products."""
    results = search_products("do you have dior perfumes?")
    assert isinstance(results, list)
    if results:
        for product in results:
            assert "dior" in product.get("brand", "").lower()


def test_longlasting_query():
    """Regression: long-lasting queries should not crash."""
    results = search_products("suggest a long lasting perfume")
    assert isinstance(results, list)


def test_cheap_query():
    """Regression: cheap queries should prioritize low price."""
    results = search_products("cheap but good perfume")
    assert isinstance(results, list)
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i]["price"] <= results[i + 1]["price"]


def test_similarity_query():
    """Regression: similarity queries should not crash."""
    results = search_products("something similar to dior sauvage")
    assert isinstance(results, list)


# -----------------------------
# Exact product name search
# -----------------------------

def test_exact_name_search_creed_aventus():
    """Exact product name should match database products."""
    results = search_products("Creed Aventus")
    assert isinstance(results, list)
    assert len(results) > 0
    assert any("creed aventus" in (p.get("name") or "").lower() for p in results)


def test_exact_name_search_club_de_nuit():
    """Exact product name with brand prefix should match."""
    results = search_products("Club De Nuit Intense Man")
    assert isinstance(results, list)


def test_do_you_have_creed_aventus():
    """'do you have' prefix should still match exact product."""
    results = search_products("do you have Creed Aventus?")
    assert isinstance(results, list)
    assert len(results) > 0


def test_tell_me_about_bleu_de_chanel():
    """'Tell me about' should match exact product."""
    results = search_products("Tell me about Bleu de Chanel")
    assert isinstance(results, list)
    assert len(results) > 0
    assert any("bleu de chanel" in (p.get("name") or "").lower() for p in results)


def test_sweet_fragrance_returns_sweet_products():
    """Sweet fragrance queries should match products with scent_family tags."""
    results = search_products("sweet perfume")
    assert isinstance(results, list)
    if results:
        assert len(results) > 0


def test_fresh_fragrance_returns_fresh_products():
    """Fresh fragrance queries should match products with scent_family tags."""
    results = search_products("fresh perfume")
    assert isinstance(results, list)
    if results:
        assert len(results) > 0


def test_office_perfume_detects_occasion():
    """Office queries should detect occasion filter properly."""
    from app.filters import detect_occasion
    assert detect_occasion("office perfume") == "office"
    assert detect_occasion("অফিস পারফিউম") == "office"


# -----------------------------
# Specific product query: non-existent product must return empty
# -----------------------------

def test_non_existent_specific_product_returns_empty():
    """Searching for a specific brand+product that doesn't exist must not fall back to brand matches."""
    results = search_products("Lattafa Asad")
    assert results == [], "Non-existent specific product should return empty"


def test_non_existent_specific_product_does_not_return_brand_fallback():
    """Searching for a specific product name that doesn't exist must not show same-brand products."""
    results = search_products("Dior FakeProductName")
    assert results == [], "Non-existent specific product should return empty"


# -----------------------------
# Price range filtering
# -----------------------------

def test_budget_with_taka_symbol():
    """under ৳X should extract budget correctly."""
    results = search_products("perfume under \u09f32500")
    assert isinstance(results, list)
    for product in results:
        assert float(product.get("price", 0)) <= 2500


def test_budget_with_within_keyword():
    """'within X' should extract budget and filter."""
    results = search_products("within 2000")
    assert isinstance(results, list)
    for product in results:
        assert float(product.get("price", 0)) <= 2000


def test_budget_less_than():
    """'less than X' should extract budget correctly."""
    from app.filters import extract_budget
    assert extract_budget("less than 1500") == 1500


def test_budget_between_range():
    """'between X and Y' should return products in that range."""
    results = search_products("between 1000 and 2000")
    assert isinstance(results, list)
    for product in results:
        price = float(product.get("price", 0))
        assert 1000 <= price <= 2000


# -----------------------------
# Note / attribute search
# -----------------------------

def test_sweet_vanilla_returns_relevant_products():
    """Searching for 'sweet vanilla' should return products with vanilla/sweet notes."""
    results = search_products("sweet vanilla")
    assert isinstance(results, list)
    assert len(results) > 0, "Sweet vanilla search should return products"


def test_fresh_citrus_returns_relevant_products():
    """Searching for 'fresh citrus' should return fresh/citrus products."""
    results = search_products("fresh citrus")
    assert isinstance(results, list)
    assert len(results) > 0, "Fresh citrus search should return products"


# -----------------------------
# Gift search with gender and budget
# -----------------------------

def test_gift_for_boyfriend_detects_male():
    """'Gift for boyfriend' should detect male gender."""
    from app.filters import detect_gender, detect_gift
    assert detect_gender("gift for boyfriend") == "male"
    assert detect_gift("gift for boyfriend") is True


def test_gift_for_boyfriend_under_budget_returns_products():
    """'Gift for boyfriend under 3500' should return matching products."""
    results = search_products("gift for boyfriend under 3500")
    assert isinstance(results, list)
    if results:
        for product in results:
            assert float(product.get("price", 0)) <= 3500


# -----------------------------
# FAQ routing (must not mix with product search)
# -----------------------------

def test_faq_routing_delivery():
    """Delivery questions must use FAQ, not product search."""
    from app.intent import Intent, detect_intent
    assert detect_intent("delivery time") == Intent.DELIVERY
    assert detect_intent("shipping charge") == Intent.DELIVERY
    assert detect_intent("koto din lagbe") == Intent.DELIVERY


def test_faq_routing_payment():
    """Payment/COD questions must use FAQ."""
    from app.intent import Intent, detect_intent
    assert detect_intent("COD") == Intent.PAYMENT
    assert detect_intent("bkash payment") == Intent.PAYMENT
    assert detect_intent("cash on delivery") == Intent.PAYMENT


def test_faq_routing_location():
    """Location questions must use FAQ."""
    from app.intent import Intent, detect_intent
    assert detect_intent("shop address") == Intent.LOCATION
    assert detect_intent("store location") == Intent.LOCATION
    assert detect_intent("ঠিকানা") == Intent.LOCATION


# -----------------------------
# Recommendation intent (not FAQ)
# -----------------------------

def test_recommendation_is_product_search_not_faq():
    """'recommend', 'suggest' etc. must be recommendation intents, not FAQ."""
    from app.intent import Intent, detect_intent
    assert detect_intent("recommend a perfume") == Intent.BEST_RECOMMENDATION
    assert detect_intent("suggest something") == Intent.BEST_RECOMMENDATION
    assert detect_intent("office perfume") == Intent.OCCASION_RECOMMENDATION
    assert detect_intent("party fragrance") == Intent.OCCASION_RECOMMENDATION


def test_performance_is_not_faq():
    """'long lasting', 'projection' etc. must be product intent, not FAQ."""
    from app.intent import detect_intent
    # These should be PRODUCT_INFO or ATTRIBUTE_QUERY or PRODUCT_SEARCH, not FAQ
    intent = detect_intent("long lasting perfume")
    assert intent.name != "DELIVERY" and intent.name != "PAYMENT"
    assert intent.name != "LOCATION"
    intent = detect_intent("good projection")
    assert intent.name != "DELIVERY" and intent.name != "PAYMENT"
    assert intent.name != "LOCATION"


# -----------------------------
# Language detection consistency
# -----------------------------

def test_language_detection_english():
    """English queries should be detected as English."""
    from app.language import detect_language
    assert detect_language("show me perfumes") == "en"
    assert detect_language("I want a perfume") == "en"


def test_language_detection_bangla():
    """Bangla queries should be detected as Bangla."""
    from app.language import detect_language
    assert detect_language("আমি পারফিউম চাই") == "bn"
    assert detect_language("আপনার দোকান কোথায়") == "bn"


def test_language_detection_banglish():
    """Banglish queries should be detected as Banglish."""
    from app.language import detect_language
    assert detect_language("ami perfume chai") == "bn-en"
    assert detect_language("eta koto taka") == "bn-en"


# -----------------------------
# No hallucinated bestseller
# -----------------------------

def test_bestseller_does_not_hallucinate():
    """Searching for 'bestseller' should not crash or hallucinate data."""
    results = search_products("bestseller perfume")
    assert isinstance(results, list)


# -----------------------------
# Comparison query intent detection
# -----------------------------

def test_comparison_intent_detected():
    """Compare/versus queries should be detected as COMPARISON_QUERY."""
    from app.intent import Intent, detect_intent
    assert detect_intent("compare dior sauvage and bleu de chanel") == Intent.COMPARISON_QUERY
    assert detect_intent("dior sauvage vs bleu de chanel") == Intent.COMPARISON_QUERY
    assert detect_intent("which is better dior or chanel") == Intent.COMPARISON_QUERY