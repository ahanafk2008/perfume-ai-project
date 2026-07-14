# Scraper module — fetches products from Supabase and stores them in local SQLite

import json
import logging
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "products.db"


def fetch_and_store() -> None:
    """Fetch all products from Supabase and insert/update them in the local database."""

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")
        raise SystemExit(1)

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }

    url = f"{supabase_url}/rest/v1/products?select=*"

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    products: list[dict] = response.json()

    if not isinstance(products, list):
        logger.error("Unexpected API response format — expected a list of products.")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        for p in products:
            cursor.execute("""
            INSERT OR REPLACE INTO products
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["id"],
                p["name"],
                p["brand"],
                p["price"],
                p["original_price"],
                p["category"],
                p["description"],
                p["image_url"],
                json.dumps(p),
            ))

        conn.commit()
        logger.info("Imported %d products.", len(products))
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_and_store()