from app.filters import (
    correct_common_typos,
    normalize_words,
    tokenize_query,
    extract_budget,
    detect_gender,
    detect_brand,
    detect_category,
    detect_combo,
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

    assert "best" not in tokens
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

