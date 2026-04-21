"""Autocomplete service with Trie and linear prefix filtering."""

from structures.trie import Trie
from models.models import Product


class AutocompleteService:
    """Service for autocomplete with optimized (Trie) and non-optimized modes."""

    def __init__(self):
        self.products: list[Product] = []
        self.trie: Trie = Trie()
        self._indexed: bool = False

    def index_products(self, products: list[Product]) -> None:
        """Index products for autocomplete."""
        self.products = products
        self._build_trie()

    def add_product(self, product: Product) -> None:
        """Add a single product to the Trie (incremental)."""
        self.products.append(product)
        self.trie.insert(product.id, product.name, product.sales)
        self._indexed = True

    def _build_trie(self) -> None:
        """Build Trie from all products."""
        self.trie = Trie()
        for product in self.products:
            self.trie.insert(product.id, product.name, product.sales)
        self._indexed = True

    def autocomplete_optimized(self, query: str, limit: int = 10) -> list[dict]:
        """Autocomplete using Trie - O(m) where m is query length."""
        if not self._indexed:
            return []
        results = self.trie.search_prefix(query, limit)
        return [{"id": pid, "sales": sales} for sales, pid in results]

    def autocomplete_linear(self, query: str, limit: int = 10) -> list[dict]:
        """Linear autocomplete using startswith - O(n)."""
        query_lower = query.lower()
        matches = [
            {"id": p.id, "sales": p.sales}
            for p in self.products
            if p.name.lower().startswith(query_lower)
        ]
        matches.sort(key=lambda x: -x["sales"])
        return matches[:limit]
