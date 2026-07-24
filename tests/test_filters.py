from app.filters import (
    correct_common_typos,
    detect_brand,
    detect_category,
    detect_combo,
    detect_gender,
    detect_luxury,
    detect_performance,
    detect_recommendation,
    extract_budget,
    normalize_words,
    tokenize_query,
)

# -----------------------------
# Typo correction
# -----------------------------

def test_common_typos():
    assert correct_common_typos("latafa") == "lattafa"
    assert correct_common_typos("guci") == "gucci"
    assert correct_common_typos("savage") == "sauvage"
    assert correct_common_typos("unknown") == "unknown"


# -----------------------------
# normalize_words
# -----------------------------

def test_normalize_words():
    assert normalize_words(["wife", "perfume"]) == ["female"]
    assert normalize_words(["under", "lattafa"]) == ["lattafa"]
    assert normalize_words(["guci"]) == ["gucci"]


# -----------------------------
# tokenize_query
# -----------------------------

def test_tokenize_query():
    tokens = tokenize_query("Lattafa under 2000")
    assert "lattafa" in tokens
    assert "under" not in tokens

    tokens = tokenize_query("wife perfume")
    assert "female" in tokens
    assert "perfume" not in tokens

    tokens = tokenize_query("guci perfume")
    assert "gucci" in tokens


# -----------------------------
# Budget
# -----------------------------

def test_extract_budget():
    assert extract_budget("under 2000") == 2000
    assert extract_budget("2000 taka") == 2000
    assert extract_budget("৳3000") == 3000
    assert extract_budget("no budget mentioned") is None


# -----------------------------
# Gender
# -----------------------------

def test_detect_gender():
    assert detect_gender("men perfume") == "male"
    assert detect_gender("wife perfume") == "female"
    assert detect_gender("unisex perfume") == "unisex"
    assert detect_gender("lattafa khamrah") is None


# -----------------------------
# Brand
# -----------------------------

def test_detect_brand():
    assert detect_brand("lattafa khamrah") == "lattafa"
    assert detect_brand("guci perfume") == "gucci"
    assert detect_brand("unknown brand") is None


# -----------------------------
# Category
# -----------------------------

def test_detect_category():
    assert detect_category("oud perfume") == "oud"
    assert detect_category("body spray") == "body spray"
    assert detect_category("lattafa") is None


# -----------------------------
# Combo
# -----------------------------

def test_detect_combo():
    assert detect_combo("gift set") is True
    assert detect_combo("combo pack") is True
    assert detect_combo("lattafa perfume") is False


# -----------------------------
# Stop words
# -----------------------------

def test_tokenize_strips_nonsearch_words():
    tokens = tokenize_query("best perfume under 2000")

    assert "best" not in tokens  # stop word, detect_recommendation uses raw query
    assert "perfume" not in tokens
    assert "under" not in tokens

    tokens = tokenize_query("good perfume for men")

    assert "male" in tokens
    assert "good" not in tokens
    assert "perfume" not in tokens

    assert tokenize_query("recommend perfume") == []
    assert tokenize_query("find me a perfume") == []
    assert tokenize_query("show best perfume") == []


# -----------------------------
# Descriptive words
# -----------------------------

def test_tokenize_preserves_descriptive_words():
    tokens = tokenize_query("blue perfume under 2000")
    assert "blue" in tokens

    tokens = tokenize_query("vanilla perfume")
    assert "vanilla" in tokens

    tokens = tokenize_query("oud perfume")
    assert "oud" in tokens


# -----------------------------
# Expanded budget extraction
# -----------------------------

def test_extract_budget_less_than():
    assert extract_budget("less than 2000") == 2000


def test_extract_budget_max():
    assert extract_budget("max 3000") == 3000


def test_extract_budget_maximum():
    assert extract_budget("maximum 2500") == 2500


def test_extract_budget_upto():
    assert extract_budget("upto 2000") == 2000


def test_extract_budget_up_to():
    assert extract_budget("up to 1500") == 1500


# -----------------------------
# Gender should not be category
# -----------------------------

def test_detect_category_not_gender():
    assert detect_category("men perfume") is None
    assert detect_category("women fragrance") is None
    assert detect_category("male perfume") is None
    assert detect_category("female perfume") is None
    assert detect_category("unisex perfume") is None


# -----------------------------
# Regression: k shorthand budget (2k = 2000)
# -----------------------------

def test_extract_budget_k_shorthand():
    """'2k' should be parsed as 2000."""
    assert extract_budget("perfume within 2k") == 2000
    assert extract_budget("perfume under 2k") == 2000
    assert extract_budget("under 2k budget") == 2000


def test_extract_budget_decimal_k_shorthand():
    """'2.5k' should be parsed as 2500."""
    assert extract_budget("perfume under 2.5k") == 2500
    assert extract_budget("up to 1.5k") == 1500


# -----------------------------
# Regression: cheaper than pattern
# -----------------------------

def test_extract_budget_cheaper_than():
    """'cheaper than X' should extract budget X."""
    assert extract_budget("cheaper than 800") == 800
    assert extract_budget("cheap than 500") == 500


# -----------------------------
# Regression: my budget is pattern
# -----------------------------

def test_extract_budget_my_budget_is():
    """'my budget is X' should extract budget X."""
    assert extract_budget("my budget is 2500") == 2500
    assert extract_budget("budget is 3000") == 3000


# -----------------------------
# Regression: Bangla gender detection
# -----------------------------

def test_detect_gender_bangla():
    """Bangla gender words should map correctly."""
    assert detect_gender("ছেলেদের জন্য ভালো perfume") == "male"
    assert detect_gender("মেয়েদের perfume দেখান") == "female"
    assert detect_gender("cheleder jonno perfume") == "male"
    assert detect_gender("meyeder best perfume") == "female"


# -----------------------------
# Regression: Budget enforcement (end-to-end)
# -----------------------------

def test_budget_enforcement_end_to_end():
    """Products over budget should never be returned."""
    from app.search import search_products
    results = search_products("perfume under 2000")
    for product in results:
        assert float(product.get("price", 0)) <= 2000, (
            f"Product {product.get('name')} costs {product.get('price')} "
            f"which exceeds budget of 2000"
        )


# -----------------------------
# Regression: Budget enforcement for custom amounts
# -----------------------------

def test_budget_enforcement_custom():
    """Budget filtering must be strict at different thresholds."""
    from app.search import search_products
    for budget_str, max_price in [
        ("under 1000", 1000),
        ("under 5000", 5000),
    ]:
        results = search_products(f"perfume {budget_str}")
        for product in results:
            assert float(product.get("price", 0)) <= max_price, (
                f"Product {product.get('name')} costs {product.get('price')} "
                f"which exceeds {budget_str}"
            )


# -----------------------------
# Recommendation intent detection
# -----------------------------

def test_detect_recommendation():
    assert detect_recommendation("best perfume") is True
    assert detect_recommendation("recommend a perfume") is True
    assert detect_recommendation("top fragrance") is True
    assert detect_recommendation("popular perfume") is True
    assert detect_recommendation("cheap perfume") is False
    assert detect_recommendation("show me perfumes") is False
    assert detect_recommendation("what is available") is False


def test_detect_recommendation_bangla():
    assert detect_recommendation("best পারফিউম") is True
    assert detect_recommendation("ভালো পারফিউম") is False


# -----------------------------
# Performance attribute detection
# -----------------------------

def test_detect_performance():
    assert detect_performance("long lasting perfume") is not None
    assert detect_performance("suggest a long lasting perfume") is not None
    assert detect_performance("strong perfume") is not None
    assert detect_performance("beast mode perfume") is not None
    assert detect_performance("good projection") is not None
    assert detect_performance("show me perfumes") is None


# -----------------------------
# Luxury intent detection
# -----------------------------

def test_detect_luxury():
    assert detect_luxury("luxury perfume") is True
    assert detect_luxury("premium fragrance") is True
    assert detect_luxury("designer perfume") is True
    assert detect_luxury("high end perfume") is True
    assert detect_luxury("expensive perfume") is True
    assert detect_luxury("signature scent") is True
    assert detect_luxury("exclusive perfume") is True
    assert detect_luxury("best perfume") is False  # not luxury-specific
    assert detect_luxury("cheap perfume") is False


# -----------------------------
# Gift intent detection
# -----------------------------

def test_detect_gift():
    from app.filters import detect_gift
    assert detect_gift("gift for wife") is True
    assert detect_gift("gift for husband") is True
    assert detect_gift("birthday gift") is True
    assert detect_gift("anniversary present") is True
    assert detect_gift("valentine gift") is True
    assert detect_gift("for her") is True
    assert detect_gift("for him") is True
    assert detect_gift("show me perfumes") is False
    assert detect_gift("best perfume") is False


# -----------------------------
# Cheap/budget intent detection
# -----------------------------

def test_detect_cheap_intent():
    from app.filters import detect_cheap_intent
    assert detect_cheap_intent("cheap perfume") is True
    assert detect_cheap_intent("cheapest perfume") is True
    assert detect_cheap_intent("affordable perfume") is True
    assert detect_cheap_intent("budget perfume") is True
    assert detect_cheap_intent("value perfume") is True
    assert detect_cheap_intent("economy perfume") is True
    assert detect_cheap_intent("discount perfume") is True
    assert detect_cheap_intent("reasonable price") is True
    assert detect_cheap_intent("best perfume") is False
    assert detect_cheap_intent("luxury perfume") is False


# -----------------------------
# Stop words include connectors
# -----------------------------

def test_tokenize_removes_connectors():
    from app.filters import tokenize_query
    tokens = tokenize_query("cheap but good perfume")
    assert "cheap" not in tokens
    assert "but" not in tokens
    assert "good" not in tokens
    tokens = tokenize_query("very nice perfume")
    assert "very" not in tokens


# -----------------------------
# Season detection
# -----------------------------

def test_detect_season():
    from app.filters import detect_season
    assert detect_season("summer perfume") == "summer"
    assert detect_season("winter fragrance") == "winter"
    assert detect_season("hot weather perfume") == "summer"
    assert detect_season("cold weather") == "winter"
    assert detect_season("rainy season perfume") == "summer"
    assert detect_season("office perfume") is None
    assert detect_season("best perfume") is None


# -----------------------------
# Bangla/Banglish occasion keywords
# -----------------------------

def test_detect_occasion_bangla():
    from app.filters import detect_occasion
    assert detect_occasion("অফিস পারফিউম") == "office"
    assert detect_occasion("কাজের জন্য পারফিউম") == "office"
    assert detect_occasion("biyer jonno perfume") == "wedding"
    assert detect_occasion("বিয়ের পারফিউম") == "wedding"
    assert detect_occasion("eid perfume") == "eid"
    assert detect_occasion("ঈদের জন্য পারফিউম") == "eid"


# -----------------------------
# Product context follow-up (Bangla/Banglish)
# -----------------------------

def test_detect_original_kina():
    from app.intent import Intent, detect_intent
    assert detect_intent("Original kina?") == Intent.PRODUCT_INFO


def test_detect_eta_original():
    from app.intent import Intent, detect_intent
    assert detect_intent("Eta original?") == Intent.PRODUCT_INFO


def test_detect_eta_asal():
    from app.intent import Intent, detect_intent
    assert detect_intent("এটা আসল?") == Intent.PRODUCT_INFO


# -----------------------------
# FAQ delivery time / COD
# -----------------------------

def test_faq_delivery_time():
    from app.faq import get_faq_answer
    answer = get_faq_answer("delivery koto din?")
    assert answer is not None
    assert "delivery" in answer.lower() or "shipping" in answer.lower()


def test_faq_cod():
    from app.faq import get_faq_answer
    answer = get_faq_answer("COD ache?")
    assert answer is not None
    assert "cod" in answer.lower() or "cash on delivery" in answer.lower()


# -----------------------------
# Gift keyword Bangla variants
# -----------------------------

def test_detect_gift_bangla():
    from app.filters import detect_gift
    assert detect_gift("ঈদের জন্য উপহার") is True
    assert detect_gift("eid gift") is True

