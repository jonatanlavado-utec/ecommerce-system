"""Search service with B+ Tree simulation and linear search."""

from typing import Optional
from collections import defaultdict
from sortedcontainers import SortedDict
from models.models import Product


class SearchService:
    """Service for product search with optimized and non-optimized modes."""

    def __init__(self):
        self.products: list[Product] = []
        self.b_plus_tree: Optional[SortedDict] = None  # SKU index
        self.name_index: Optional[SortedDict] = None  # Name prefix index
        self.category_index: Optional[SortedDict] = None  # Category index
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
            self.name_index = SortedDict()
            self.category_index = SortedDict()
        key = product.sku.lower()
        if key not in self.b_plus_tree:
            self.b_plus_tree[key] = []
        self.b_plus_tree[key].append(product)
        # Also index by first 3 chars of name for prefix search
        name_prefix = product.name[:3].lower()
        if name_prefix not in self.name_index:
            self.name_index[name_prefix] = []
        self.name_index[name_prefix].append(product)
        # Index by category
        cat_key = product.category.lower() if product.category else ""
        if cat_key and cat_key not in self.category_index:
            self.category_index[cat_key] = []
        if cat_key:
            self.category_index[cat_key].append(product)
        self._indexed = True

    def _build_b_plus_tree(self) -> None:
        """Build B+ Tree index from all products (optimized for batching)."""
        sku_dict = defaultdict(list)
        name_dict = defaultdict(list)
        cat_dict = defaultdict(list)
        for product in self.products:
            # SKU index
            key = product.sku.lower()
            sku_dict[key].append(product)
            # Name prefix index (first 3 chars for fast prefix lookup)
            name_prefix = product.name[:3].lower()
            name_dict[name_prefix].append(product)
            # Category index
            cat_key = product.category.lower() if product.category else ""
            if cat_key:
                cat_dict[cat_key].append(product)
        # Bulk convert to SortedDict for efficient tree structure
        self.b_plus_tree = SortedDict(sku_dict)
        self.name_index = SortedDict(name_dict)
        self.category_index = SortedDict(cat_dict)
        self._indexed = True

    def _search_tree(self, tree: Optional[SortedDict], query: str) -> list[Product]:
        """Generic prefix search on a SortedDict."""
        if not tree:
            return []
        query_lower = query.lower()
        results = []
        try:
            start_idx = tree.bisect_left(query_lower)
            keys = list(tree.keys())
            for i in range(start_idx, min(start_idx + 100, len(keys))):
                key = keys[i]
                if key.startswith(query_lower):
                    results.extend(tree[key])
                else:
                    break
        except (ValueError, IndexError):
            pass
        return results[:100]

    def search_optimized(self, query: str) -> list[Product]:
        """Search by SKU, name, or category using B+ Tree - O(log n)."""
        if not self._indexed:
            return []

        query_lower = query.lower()
        results_dict = {}

        # 1. Search by SKU (exact prefix match)
        sku_results = self._search_tree(self.b_plus_tree, query_lower)
        for p in sku_results:
            results_dict[p.id] = p

        # 2. Search by name (prefix match)
        name_results = self._search_tree(self.name_index, query_lower)
        for p in name_results:
            if p.id not in results_dict:
                results_dict[p.id] = p

        # 3. Search by category
        cat_results = self._search_tree(self.category_index, query_lower)
        for p in cat_results:
            if p.id not in results_dict:
                results_dict[p.id] = p

        # 4. If not enough results, also search in full name (contains)
        if len(results_dict) < 50:
            for p in self.products:
                if p.id in results_dict:
                    continue
                if query_lower in p.name.lower() or query_lower in p.category.lower():
                    results_dict[p.id] = p
                    if len(results_dict) >= 100:
                        break

        return list(results_dict.values())[:100]

    def search_linear(self, query: str) -> list[Product]:
        """Linear search - O(n)."""
        query_lower = query.lower()
        results = [
            p for p in self.products
            if query_lower in p.sku.lower() or query_lower in p.name.lower()
        ][:100]
        return results
