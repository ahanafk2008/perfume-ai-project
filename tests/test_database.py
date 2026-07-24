from pathlib import Path

from app.database import (
    execute_write,
    fetch_product_by_id,
    fetch_product_candidates,
    fetch_products,
    init_db,
)


def make_db(tmp_path: Path):
    db_path = tmp_path / "test.db"

    init_db(db_path)

    execute_write(
        """
        INSERT INTO products
        (id, name, brand, price, original_price, category, description, image_url, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "1",
            "Lattafa Asad",
            "Lattafa",
            1800,
            2200,
            "Male",
            "Woody spicy perfume",
            "",
            "",
        ),
        db_path=db_path,
    )

    execute_write(
        """
        INSERT INTO products
        (id, name, brand, price, original_price, category, description, image_url, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "2",
            "Yara",
            "Lattafa",
            1500,
            1800,
            "Female",
            "Sweet vanilla perfume",
            "",
            "",
        ),
        db_path=db_path,
    )

    return db_path


def test_fetch_products(tmp_path):
    db = make_db(tmp_path)

    products = fetch_products(db)

    assert len(products) == 2


def test_fetch_product_by_id(tmp_path):
    db = make_db(tmp_path)

    product = fetch_product_by_id("1", db)

    assert product is not None
    assert product["name"] == "Lattafa Asad"


def test_fetch_product_candidates_brand(tmp_path):
    db = make_db(tmp_path)

    results = fetch_product_candidates(
        query="lattafa",
        tokens=["lattafa"],
        db_path=db,
    )

    assert len(results) == 2


def test_fetch_product_candidates_budget(tmp_path):
    db = make_db(tmp_path)

    results = fetch_product_candidates(
        query="lattafa under 1600",
        tokens=["lattafa"],
        budget=1600,
        db_path=db,
    )

    assert len(results) == 1
    assert results[0]["name"] == "Yara"


def test_fetch_product_candidates_name(tmp_path):
    db = make_db(tmp_path)

    results = fetch_product_candidates(
        query="asad",
        tokens=["asad"],
        db_path=db,
    )

    assert len(results) == 1
    assert results[0]["name"] == "Lattafa Asad"


def test_fetch_product_candidates_no_match(tmp_path):
    db = make_db(tmp_path)

    results = fetch_product_candidates(
        query="dior",
        tokens=["dior"],
        db_path=db,
    )

    assert results == []