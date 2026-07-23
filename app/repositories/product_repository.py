"""Product repository layer for database access abstraction."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.database import (
    DEFAULT_DB_PATH,
    fetch_product_by_id,
    fetch_product_candidates,
    fetch_products,
)


class ProductRepository:
    """Repository providing access to product data."""

    @staticmethod
    def search_candidates(
        query: str,
        tokens: Sequence[str],
        budget: int | None = None,
        gender: str | None = None,
        brand: str | None = None,
        category: str | None = None,
        combo_requested: bool | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        db_path: Path = DEFAULT_DB_PATH,
    ) -> list[dict[str, Any]]:
        """
        Search for product candidates using the supplied filters.
        """
        return fetch_product_candidates(
            query=query,
            tokens=tokens,
            budget=budget,
            gender=gender,
            brand=brand,
            category=category,
            combo_requested=combo_requested,
            min_price=min_price,
            max_price=max_price,
            db_path=db_path,
        )

    @staticmethod
    def get_all(
        db_path: Path = DEFAULT_DB_PATH,
    ) -> list[dict[str, Any]]:
        """Return all products."""
        return fetch_products(db_path=db_path)

    @staticmethod
    def get_by_id(
        product_id: str,
        db_path: Path = DEFAULT_DB_PATH,
    ) -> dict[str, Any] | None:
        """Return a single product by its ID."""
        return fetch_product_by_id(
            product_id=product_id,
            db_path=db_path,
        )

