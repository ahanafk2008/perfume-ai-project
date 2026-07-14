# Database configuration and connection setup

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "products.db"


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create the products table if it does not already exist."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
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
    conn.close()

    logger.info("Database ready at %s", db_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()