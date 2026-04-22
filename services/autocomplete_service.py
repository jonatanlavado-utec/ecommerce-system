"""Autocomplete service with Trie and linear prefix filtering."""

from structures.trie import Trie
from models.models import Product

class AutocompleteService:
    """Service for autocomplete with optimized (Trie) and non-optimized modes."""

    def __init__(self):
        self.products: list[Product] = []
        self.product_map: dict = {}  # Add a fast O(1) lookup dictionary
        self.trie: Trie = Trie()
        self._indexed: bool = False

    def index_products(self, products: list[Product]) -> None:
        """Index products for autocomplete."""
        self.products = products
        # Build the fast lookup map instantly
        self.product_map = {p.id: p for p in products}
        self._build_trie()

    def add_product(self, product: Product) -> None:
        """Add a single product to the Trie (incremental)."""
        self.products.append(product)
        self.product_map[product.id] = product
        self.trie.insert(product.id, product.name, product.sales)
        self._indexed = True

    def _build_trie(self) -> None:
        """Build Trie from all products (optimized for batching)."""
        self.trie = Trie()
        for product in self.products:
            self.trie.insert(product.id, product.name, product.sales)
        # Sort all nodes once after all inserts
        self.trie._sort_all_nodes()
        self._indexed = True

    def autocomplete_optimized(self, query: str, limit: int = 10) -> list[dict]:
        """Autocomplete using Trie - O(m) where m is query length."""
        if not self._indexed:
            return []
            
        # O(m) - extremely fast Trie lookup
        results = self.trie.search_prefix(query, limit)
        
        enriched_results = []
        for sales, pid in results:
            # O(1) - Instant dictionary lookup instead of O(n) array scan!
            product = self.product_map.get(pid)
            if product:
                enriched_results.append({
                    "id": pid, 
                    "name": product.name, 
                    "sales": sales
                })
        return enriched_results

    def autocomplete_linear(self, query: str, limit: int = 10) -> list[dict]:
        """Linear autocomplete using startswith - O(n)."""
        query_lower = query.lower()
        matches = [
            {"id": p.id, "name": p.name, "sales": p.sales}
            for p in self.products
            if p.name.lower().startswith(query_lower)
        ]
        # Must sort linear results by sales to match the Trie's behavior
        sorted_matches = sorted(matches, key=lambda x: x["sales"], reverse=True)
        return sorted_matches[:limit]