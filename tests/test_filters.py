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
    assert tokenize_query("Lattafa under 2000") == ["lattafa"]
    assert tokenize_query("wife perfume") == ["female"]
    assert tokenize_query("guci perfume") == ["gucci"]


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