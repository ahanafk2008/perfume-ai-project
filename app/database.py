"""SQLite database helpers."""

from collections.abc import Mapping, Sequence
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from .config import DATABASE_PATH
except ImportError:  # pragma: no cover
    from config import DATABASE_PATH


DEFAULT_DB_PATH = DATABASE_PATH

QueryParams = Sequence[Any] | Mapping[str, Any]


def get_connection(
    db_path: Path = DEFAULT_DB_PATH,
) -> sqlite3.Connection:
    """
    Return a production-ready SQLite connection.

    Features:
    - dictionary-like rows
    - timeout handling
    - WAL mode for concurrency
    - foreign key support
    """

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(
        db_path,
        timeout=10,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON"
    )

    return conn


def execute_query(
    sql: str,
    params: QueryParams = (),
    db_path: Path = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Execute a read query and return rows as dictionaries."""

    conn = get_connection(db_path)

    try:
        cursor = conn.execute(
            sql,
            params,
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    except sqlite3.Error:
        logger.exception(
            "Database read failed"
        )
        raise

    finally:
        conn.close()


def execute_write(
    sql: str,
    params: QueryParams = (),
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Execute a write query and return affected rows."""

    conn = get_connection(db_path)

    try:
        cursor = conn.execute(
            sql,
            params,
        )

        conn.commit()

        return cursor.rowcount

    except sqlite3.Error:
        conn.rollback()

        logger.exception(
            "Database write failed"
        )

        raise

    finally:
        conn.close()


def fetch_products(
    db_path: Path = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Return all products."""

    return execute_query(
        "SELECT * FROM products",
        db_path=db_path,
    )


def fetch_product_candidates(
    query: str,
    tokens: Sequence[str],
    budget: int | None = None,
    gender: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    combo_requested: bool | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """
    Search products by token and optional budget.

    Matches:
    - name
    - brand
    - category
    - description
    """

    conditions: list[str] = []
    params: list[Any] = []

    unique_tokens = list(
        dict.fromkeys(
            token.lower().strip()
            for token in tokens
            if token and token.strip()
        )
    )

    # Remove gender tokens if there are other search terms.
    search_tokens = [
        token
        for token in unique_tokens
        if token not in {
            "male",
            "female",
            "unisex",
        }
    ]

    # Common conversational words that shouldn't affect search.
    STOP_WORDS = {
        "ki",
        "ase",
        "ache",
        "apnader",
        "tomader",
        "amader",
        "amar",
        "chai",
        "ekta",
        "ekti",
        "please",
        "show",
        "list",
        "all",
    }

    # Remove stop words.
    search_tokens = [
        token
        for token in search_tokens
        if token not in STOP_WORDS
    ]

    # Use cleaned tokens.
    unique_tokens = search_tokens

    # General browsing query → return some products.
    if (
        not unique_tokens
        and brand is None
        and category is None
        and budget is None
    ):
        return execute_query(
            """
            SELECT *
            FROM products
            ORDER BY price ASC
            LIMIT 20
            """,
            db_path=db_path,
        )

    # Security: prevent huge queries
    unique_tokens = unique_tokens[:20]

    for token in unique_tokens:
        conditions.append(
            """
            (
                LOWER(name) LIKE ?
                OR LOWER(brand) LIKE ?
                OR LOWER(category) LIKE ?
                OR LOWER(description) LIKE ?
            )
            """
        )

        like_value = f"%{token}%"

        params.extend(
            [
                like_value,
                like_value,
                like_value,
                like_value,
            ]
        )

    sql = """
    SELECT *
    FROM products
    """

    where_clauses: list[str] = []

    if conditions:
        where_clauses.append(
            "(" + " OR ".join(conditions) + ")"
        )

    if brand:
        where_clauses.append("LOWER(brand) LIKE ?")
        params.append(f"%{brand.lower()}%")

    if category:
        where_clauses.append("LOWER(category) LIKE ?")
        params.append(f"%{category.lower()}%")

    if combo_requested:
        where_clauses.append(
            "(LOWER(category) = 'combo' "
            "OR LOWER(name) LIKE '%combo%' "
            "OR LOWER(name) LIKE '%set%' "
            "OR LOWER(name) LIKE '%gift%')"
        )

    if budget is not None:
        where_clauses.append("price <= ?")
        params.append(budget)

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += """
    ORDER BY price ASC
    LIMIT 100
    """
    logger.debug(
        "Product search SQL executed with %d parameters",
        len(params),
    )

    return execute_query(
        sql,
        params,
        db_path=db_path,
    )


def fetch_product_by_id(
    product_id: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, Any] | None:
    """Return one product by ID."""

    rows = execute_query(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,),
        db_path=db_path,
    )

    return rows[0] if rows else None


def init_db(
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    """
    Initialize database and indexes.
    """

    conn = get_connection(db_path)

    try:

        conn.execute(
            """
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
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_products_name
            ON products(name)
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_products_brand
            ON products(brand)
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_products_category
            ON products(category)
            """
        )


        conn.commit()


    except sqlite3.Error:
        logger.exception(
            "Database initialization failed"
        )
        raise


    finally:
        conn.close()


    logger.info(
        "Database ready at %s",
        db_path,
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO
    )

    init_db()