"""Top K products service with Count-Min Sketch and Min Heap."""

import heapq
from structures.count_min_sketch import CountMinSketch
from models.models import Product

class TopKService:
    def __init__(self, sketch_depth: int = 7, sketch_width: int = 1000000):
        self.products: list[Product] = []
        self.product_map: dict = {}  
        self.current_sales: dict = {} # ---> ADD THIS: Track latest sales
        self.count_min_sketch = CountMinSketch(depth=sketch_depth, width=sketch_width)
        self.min_heap: list[tuple[int, str]] = []
        self._indexed: bool = False
        self._sketch_width = sketch_width

    def index_products(self, products: list[Product]) -> None:
        self.products = products
        self.product_map = {p.id: p for p in products}
        self.current_sales = {p.id: p.sales for p in products} # ---> ADD THIS
        self._rebuild_sketch_and_heap()

    def add_product(self, product: Product) -> None:
        self.products.append(product)
        self.product_map[product.id] = product
        self.current_sales[product.id] = product.sales # ---> ADD THIS
        self.count_min_sketch.update(product.id, product.sales)
        heapq.heappush(self.min_heap, (-product.sales, product.id))
        self._indexed = True

    def _rebuild_sketch_and_heap(self) -> None:
        self.count_min_sketch = CountMinSketch(depth=7, width=self._sketch_width)
        heap_items = []
        for product in self.products:
            self.count_min_sketch.update(product.id, product.sales)
            heap_items.append((-product.sales, product.id))
        self.min_heap = heap_items
        heapq.heapify(self.min_heap)
        self._indexed = True

    def get_top_k_optimized(self, k: int) -> list[dict]:
        if not self._indexed: return []
        return self._extract_top_k(k)

    def get_top_k_linear(self, k: int) -> list[dict]:
        if not self._indexed: return []
        sorted_products = sorted(self.products, key=lambda p: -p.sales)
        return [{"id": p.id, "name": p.name, "sales": p.sales} for p in sorted_products[:k]]

    def _extract_top_k(self, k: int) -> list[dict]:
        if not self.min_heap: return []
        
        top_k = heapq.nsmallest(k, self.min_heap, key=lambda x: x[0])
        results = []
        seen = set()
        for neg_sales, pid in top_k:
            if pid in seen:
                continue
            
            # ---> ADD THIS: Stale node check
            if -neg_sales != self.current_sales.get(pid, 0):
                continue
                
            seen.add(pid)
            product = self.product_map.get(pid)
            if product:
                results.append({"id": pid, "name": product.name, "sales": product.sales})
                
        return results