"""Search orchestration service."""

from app.search import search_products


class SearchService:
    """Service wrapper for product search."""

    def search(self, query: str):
        """Search for products."""
        return search_products(query)