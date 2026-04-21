"""Top K products service with Count-Min Sketch and Min Heap."""

import heapq
from structures.count_min_sketch import CountMinSketch
from models.models import Product


class TopKService:
    """Service for finding top K products with optimized and non-optimized modes."""

    def __init__(self, sketch_depth: int = 7, sketch_width: int = 1000000):
        self.products: list[Product] = []
        self.count_min_sketch = CountMinSketch(depth=sketch_depth, width=sketch_width)
        self.min_heap: list[tuple[int, str]] = []  # (negative_sales, product_id)
        self._indexed: bool = False
        self._sketch_width = sketch_width

    def index_products(self, products: list[Product]) -> None:
        """Index products for top K queries."""
        self.products = products
        self._rebuild_sketch_and_heap()

    def add_product(self, product: Product) -> None:
        """Add a single product (incremental)."""
        self.products.append(product)
        self.count_min_sketch.update(product.id, product.sales)
        # Add to min heap
        heapq.heappush(self.min_heap, (-product.sales, product.id))
        self._indexed = True

    def _rebuild_sketch_and_heap(self) -> None:
        """Rebuild Count-Min Sketch and Min Heap from all products (optimized for batching)."""
        self.count_min_sketch = CountMinSketch(depth=7, width=max(self._sketch_width, len(self.products) * 10))
        heap_items = []
        seen_ids = set()  # Dedupe by ID to prevent wasted work
        for product in self.products:
            if product.id not in seen_ids:
                self.count_min_sketch.update(product.id, product.sales)
                heap_items.append((-product.sales, product.id))
                seen_ids.add(product.id)
        # Use heapify (O(n)) instead of n heappush calls (O(n log n))
        self.min_heap = heap_items
        heapq.heapify(self.min_heap)
        self._indexed = True

    def get_top_k_optimized(self, k: int) -> list[dict]:
        """Get top K using Min Heap - O(n + k log n)."""
        if not self._indexed:
            return []
        return self._extract_top_k(k)

    def get_top_k_linear(self, k: int) -> list[dict]:
        """Get top K using sort - O(n log n)."""
        if not self._indexed:
            return []
        sorted_products = sorted(self.products, key=lambda p: -p.sales)
        return [
            {"id": p.id, "name": p.name, "sales": p.sales}
            for p in sorted_products[:k]
        ]

    def _extract_top_k(self, k: int) -> list[dict]:
        """Extract top K from min heap."""
        if not self.min_heap:
            return []
        top_k = heapq.nsmallest(k, self.min_heap, key=lambda x: x[0])
        results = []
        seen = set()
        for neg_sales, pid in top_k:
            if pid in seen:
                continue
            seen.add(pid)
            product = next((p for p in self.products if p.id == pid), None)
            if product:
                results.append({
                    "id": product.id,
                    "name": product.name,
                    "sales": -neg_sales
                })
        return sorted(results, key=lambda x: -x["sales"])
