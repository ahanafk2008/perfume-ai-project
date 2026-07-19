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

