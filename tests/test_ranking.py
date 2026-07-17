from app.ranking import calculate_score, rank_products


male_product = {
    "id": "1",
    "name": "Lattafa Asad",
    "brand": "Lattafa",
    "category": "Male",
    "description": "Woody spicy perfume",
    "price": 1800,
}

female_product = {
    "id": "2",
    "name": "Yara",
    "brand": "Lattafa",
    "category": "Female",
    "description": "Sweet vanilla perfume",
    "price": 1500,
}

combo_product = {
    "id": "3",
    "name": "Lattafa Combo Set",
    "brand": "Lattafa",
    "category": "Male",
    "description": "Gift set combo",
    "price": 3000,
}


def test_exact_name_scores_higher():
    score = calculate_score(
        male_product,
        "lattafa asad",
    )

    assert score >= 20


def test_brand_match():
    score = calculate_score(
        male_product,
        "lattafa perfume",
    )

    assert score >= 15


def test_budget_bonus():
    score = calculate_score(
        male_product,
        "lattafa",
        budget=2000,
    )

    assert score >= 3


def test_gender_penalty():
    male_score = calculate_score(
        male_product,
        "male perfume",
    )

    female_score = calculate_score(
        female_product,
        "male perfume",
    )

    assert male_score > female_score


def test_combo_bonus():
    combo = calculate_score(
        combo_product,
        "combo set",
    )

    normal = calculate_score(
        male_product,
        "combo set",
    )

    assert combo > normal


def test_rank_products():
    ranked = rank_products(
        [
            female_product,
            male_product,
        ],
        "lattafa asad",
    )

    assert ranked[0]["name"] == "Lattafa Asad"


def test_remove_duplicates():
    ranked = rank_products(
        [
            male_product,
            male_product,
            female_product,
        ],
        "lattafa",
    )

    ids = [p["id"] for p in ranked]

    assert len(ids) == len(set(ids))