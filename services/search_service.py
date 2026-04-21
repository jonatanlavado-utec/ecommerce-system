"""Search service with B+ Tree simulation and linear search."""

from typing import Optional
from collections import defaultdict
from sortedcontainers import SortedDict
from models.models import Product


class SearchService:
    """Service for product search with optimized and non-optimized modes."""

    def __init__(self):
        self.products: list[Product] = []
        self.b_plus_tree: Optional[SortedDict] = None
        self._indexed: bool = False

    def index_products(self, products: list[Product]) -> None:
        """Index products for search using B+ Tree simulation."""
        self.products = products
        self._build_b_plus_tree()

    def add_product(self, product: Product) -> None:
        """Add a single product to the index (incremental)."""
        self.products.append(product)
        if self.b_plus_tree is None:
            self.b_plus_tree = SortedDict()
        key = product.sku.lower()
        if key not in self.b_plus_tree:
            self.b_plus_tree[key] = []
        self.b_plus_tree[key].append(product)
        self._indexed = True

    def _build_b_plus_tree(self) -> None:
        """Build B+ Tree index from all products (optimized for batching)."""
        # Use defaultdict for faster bulk collection
        temp_dict = defaultdict(list)
        for product in self.products:
            key = product.sku.lower()
            temp_dict[key].append(product)
        # Bulk convert to SortedDict for efficient tree structure
        self.b_plus_tree = SortedDict(temp_dict)
        self._indexed = True

    def search_by_sku_optimized(self, sku_query: str) -> list[Product]:
        """Search by SKU using B+ Tree - O(log n)."""
        if not self._indexed or not self.b_plus_tree:
            return []
        query_lower = sku_query.lower()
        results = []
        try:
            start_idx = self.b_plus_tree.bisect_left(query_lower)
            keys = list(self.b_plus_tree.keys())
            for i in range(start_idx, min(start_idx + 100, len(keys))):
                key = keys[i]
                if key.startswith(query_lower):
                    results.extend(self.b_plus_tree[key])
                else:
                    break
        except (ValueError, IndexError):
            pass
        return results[:100]

    def search_optimized(self, query: str) -> list[Product]:
        """Search using B+ Tree simulation - O(log n)."""
        return self.search_by_sku_optimized(query)

    def search_linear(self, query: str) -> list[Product]:
        """Linear search - O(n)."""
        query_lower = query.lower()
        return [p for p in self.products if query_lower in p.sku.lower() or query_lower in p.name.lower()][:100]
