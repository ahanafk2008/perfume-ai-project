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


# -----------------------------
# Budget search
# -----------------------------

def test_budget_search():
    results = search_products("under 2000")

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