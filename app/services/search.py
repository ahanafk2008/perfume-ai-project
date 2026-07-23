"""Search orchestration service."""

from app.search import search_products


class SearchService:
    """Service wrapper for product search."""

    def search(self, query: str):
        """Search for products."""
        return search_products(query)

    def search_products(self, query: str = ""):
        """Alias for search method for backward compatibility."""
        return self.search(query)