"""SQLite database helpers."""

from collections.abc import Mapping, Sequence
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from .config import DATABASE_PATH
except ImportError:  # pragma: no cover - supports running this file directly
    from config import DATABASE_PATH


DEFAULT_DB_PATH = DATABASE_PATH
QueryParams = Sequence[Any] | Mapping[str, Any]


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection configured for dictionary-like rows."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(
    sql: str,
    params: QueryParams = (),
    db_path: Path = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Execute a read query and return rows as dictionaries."""

    conn = get_connection(db_path)
    try:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def execute_write(
    sql: str,
    params: QueryParams = (),
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Execute a write query and return the number of affected rows."""

    conn = get_connection(db_path)
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def fetch_products(db_path: Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    """Return all products from the local product database."""

    return execute_query("SELECT * FROM products", db_path=db_path)


def fetch_product_by_id(
    product_id: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, Any] | None:
    """Return one product by ID, or None if it does not exist."""

    rows = execute_query(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
        db_path=db_path,
    )
    return rows[0] if rows else None


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create the products table if it does not already exist."""

    conn = get_connection(db_path)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT,
            brand TEXT,
            price REAL,
            original_price REAL,
            category TEXT,
            description TEXT,
            image_url TEXT,
            data TEXT
        )
        """)
        conn.commit()
    finally:
        conn.close()

    logger.info("Database ready at %s", db_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
