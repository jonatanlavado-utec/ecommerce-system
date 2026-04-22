"""Benchmark service for comparing optimized vs non-optimized implementations."""

import time
import random
import psutil
from typing import Callable, Any

# Add these imports at the top of benchmark_service.py if missing:
from services.search_service import SearchService
from services.autocomplete_service import AutocompleteService
from services.topk_service import TopKService
from services.fraud_service import FraudService

def get_memory_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def benchmark_function(func: Callable, iterations: int = 100) -> dict:
    """Benchmark a function with memory tracking."""
    start_mem = get_memory_mb()
    start_time = time.perf_counter()

    for _ in range(iterations):
        func()

    end_time = time.perf_counter()
    end_mem = get_memory_mb()

    return {
        "time_ms": (end_time - start_time) * 1000,
        "memory_mb": end_mem - start_mem,
        "iterations": iterations,
        "avg_time_ms": (end_time - start_time) * 1000 / iterations
    }


class BenchmarkService:
    """Service for running benchmarks across all services."""

    def __init__(self, app_state: dict):
        self.app_state = app_state

    def run_search_benchmark(self) -> dict:
        """Benchmark search with optimized vs non-optimized."""
        if not self.app_state.get("products"):
            return {"error": "No products indexed"}

        products = self.app_state["products"]
        queries = ["premium", "wireless", "smart", "portable", "pro", "tech"]

        # Pick random products for queries
        test_queries = random.sample(queries, min(5, len(queries)))

        def optimized_search():
            from services.search_service import SearchService
            svc = SearchService()
            svc.index_products(products)
            for q in test_queries:
                svc.search_optimized(q)

        def linear_search():
            from services.search_service import SearchService
            svc = SearchService()
            svc.index_products(products)
            for q in test_queries:
                svc.search_linear(q)

        return {
            "optimized": benchmark_function(optimized_search, iterations=50),
            "linear": benchmark_function(linear_search, iterations=50),
            "query_count": len(test_queries)
        }

    def run_autocomplete_benchmark(self) -> dict:
        """Benchmark autocomplete with optimized vs non-optimized."""
        if not self.app_state.get("products"):
            return {"error": "No products indexed"}

        products = self.app_state["products"]
        queries = ["pre", "wire", "sma", "por", "pro", "tec"]

        def optimized_autocomplete():
            from services.autocomplete_service import AutocompleteService
            svc = AutocompleteService()
            svc.index_products(products)
            for q in queries:
                svc.autocomplete_optimized(q)

        def linear_autocomplete():
            from services.autocomplete_service import AutocompleteService
            svc = AutocompleteService()
            svc.index_products(products)
            for q in queries:
                svc.autocomplete_linear(q)

        return {
            "optimized": benchmark_function(optimized_autocomplete, iterations=50),
            "linear": benchmark_function(linear_autocomplete, iterations=50),
            "query_count": len(queries)
        }

    def run_topk_benchmark(self) -> dict:
        """Benchmark top K with optimized vs non-optimized."""
        if not self.app_state.get("products"):
            return {"error": "No products indexed"}

        products = self.app_state["products"]

        def optimized_topk():
            from services.topk_service import TopKService
            svc = TopKService()
            svc.index_products(products)
            svc.get_top_k_optimized(100)

        def linear_topk():
            from services.topk_service import TopKService
            svc = TopKService()
            svc.index_products(products)
            svc.get_top_k_linear(100)

        return {
            "optimized": benchmark_function(optimized_topk, iterations=50),
            "linear": benchmark_function(linear_topk, iterations=50)
        }

    def run_fraud_benchmark(self) -> dict:
        """Benchmark fraud detection with optimized vs non-optimized."""
        if not self.app_state.get("products"):
            return {"error": "No products indexed"}

        products = self.app_state["products"]
        product_ids = [p.id for p in random.sample(products, min(1000, len(products)))]

        def optimized_fraud():
            from services.fraud_service import FraudService
            svc = FraudService()
            svc.index_products(products)
            svc.is_fraudulent_optimized(product_ids)

        def linear_fraud():
            from services.fraud_service import FraudService
            svc = FraudService()
            svc.index_products(products)
            svc.is_fraudulent_linear(product_ids)

        return {
            "optimized": benchmark_function(optimized_fraud, iterations=50),
            "linear": benchmark_function(linear_fraud, iterations=50),
            "check_count": len(product_ids)
        }

    def run_full_benchmark(self) -> dict:
        """Run full benchmark suite."""
        start_mem = get_memory_mb()

        results = {
            "search": self.run_search_benchmark(),
            "autocomplete": self.run_autocomplete_benchmark(),
            "top_k": self.run_topk_benchmark(),
            "fraud": self.run_fraud_benchmark(),
            "memory_snapshot_mb": start_mem
        }

        # Calculate summary
        summary = {}
        for operation, data in results.items():
            if isinstance(data, dict) and "optimized" in data and "linear" in data:
                opt_time = data["optimized"].get("avg_time_ms", 0)
                lin_time = data["linear"].get("avg_time_ms", 0)
                if lin_time > 0:
                    speedup = lin_time / opt_time
                else:
                    speedup = 0
                summary[operation] = {
                    "speedup": round(speedup, 2),
                    "opt_avg_ms": round(opt_time, 4),
                    "lin_avg_ms": round(lin_time, 4)
                }

        results["summary"] = summary
        return results
    def run_scaling_comparisons(self) -> list[dict]:
        """Generate scaling benchmarks (time vs dataset size N) for all structures."""
        if not self.app_state.get("products"):
            raise ValueError("No products indexed")

        all_products = self.app_state["products"]
        
        # Test sizes up to 100,000 items to prevent the HTTP request from timing out
        max_p = min(len(all_products), 500000) 
        sizes = [int(max_p * f) for f in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
        sizes = sorted(list(set([s for s in sizes if s > 0])))
        
        search_opt, search_lin = [], []
        auto_opt, auto_lin = [], []
        topk_opt, topk_lin = [], []

        queries = ["premium", "wireless", "smart", "pro"]

        for size in sizes:
            subset = all_products[:size]
            
            # --- 1. Search (B+ Tree vs Linear) ---
            s_svc = SearchService()
            s_svc.index_products(subset)
            
            opt_s = benchmark_function(lambda: [s_svc.search_optimized(q) for q in queries], iterations=5)
            lin_s = benchmark_function(lambda: [s_svc.search_linear(q) for q in queries], iterations=5)
            search_opt.append({"x": size, "time": opt_s["avg_time_ms"]})
            search_lin.append({"x": size, "time": lin_s["avg_time_ms"]})

            # --- 2. Autocomplete (Trie vs Linear) ---
            a_svc = AutocompleteService()
            a_svc.index_products(subset)
            
            opt_a = benchmark_function(lambda: [a_svc.autocomplete_optimized(q) for q in queries], iterations=5)
            lin_a = benchmark_function(lambda: [a_svc.autocomplete_linear(q) for q in queries], iterations=5)
            auto_opt.append({"x": size, "time": opt_a["avg_time_ms"]})
            auto_lin.append({"x": size, "time": lin_a["avg_time_ms"]})

            # --- 3. TopK (Heap vs Sort) ---
            t_svc = TopKService()
            t_svc.index_products(subset)
            
            opt_t = benchmark_function(lambda: t_svc.get_top_k_optimized(10), iterations=5)
            lin_t = benchmark_function(lambda: t_svc.get_top_k_linear(10), iterations=5)
            topk_opt.append({"x": size, "time": opt_t["avg_time_ms"]})
            topk_lin.append({"x": size, "time": lin_t["avg_time_ms"]})

        # --- 4. Fraud (Bloom vs Hash Set) True Negatives + Memory ---
        fraud_opt_time, fraud_lin_time = [], []
        fraud_opt_mem, fraud_lin_mem = [], []
        fraud_state = self.app_state.get("fraud_service")
        
        if fraud_state and getattr(fraud_state, "_indexed", False):
            txn_max = min(len(fraud_state.transaction_ids), 250000)
            txn_sizes = [int(txn_max * f) for f in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
            txn_sizes = sorted(list(set([s for s in txn_sizes if s > 0])))
            
            # Generate 1000 True Negatives (IDs guaranteed NOT to be in the set)
            check_ids = [f"unknown_txn_{i:010d}" for i in range(1000)]
            
            for size in txn_sizes:
                subset_tx = fraud_state.transaction_ids[:size]
                f_svc = FraudService()
                f_svc.index_transactions(subset_tx)
                
                # A. Calculate Memory footprint (in MB)
                # Bitarray size (bits / 8 = bytes) vs Hash Set size (approx 80 bytes per string in Python)
                bloom_mb = len(f_svc.bloom_filter.bit_array) / (8 * 1024 * 1024) 
                hash_mb = (size * 80) / (1024 * 1024)
                
                fraud_opt_mem.append({"x": size, "memory": max(0.01, bloom_mb)})
                fraud_lin_mem.append({"x": size, "memory": max(0.01, hash_mb)})
                
                # B. Benchmark Time using raw underlying structures
                # This bypasses the short-circuit range check to test the actual data structures!
                opt_f = benchmark_function(lambda: [f_svc.bloom_filter.contains(x) for x in check_ids], iterations=5)
                lin_f = benchmark_function(lambda: [x in f_svc.hash_set for x in check_ids], iterations=5)
                
                fraud_opt_time.append({"x": size, "time": opt_f["avg_time_ms"]})
                fraud_lin_time.append({"x": size, "time": lin_f["avg_time_ms"]})

    # --- 5. Priority Queue vs Full Sort (Orders) ---
        order_opt, order_lin = [], []
        order_state = self.app_state.get("order_service")
        
        if order_state and getattr(order_state, "orders", None):
            import heapq
            # Test up to 100k orders to prevent timeouts
            max_orders = min(len(order_state.orders), 100000) 
            order_sizes = [int(max_orders * f) for f in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
            order_sizes = sorted(list(set([s for s in order_sizes if s > 0])))
            
            for size in order_sizes:
                subset_orders = order_state.orders[:size]
                
                # A. Setup Min-Heap (Pre-heapified tuple of priority, index, order)
                heap_data = [(o.priority, i, o) for i, o in enumerate(subset_orders)]
                heapq.heapify(heap_data)
                
                # B. Setup Baseline Flat Array
                flat_data = [(o.priority, i, o) for i, o in enumerate(subset_orders)]
                
                # Benchmark finding the top 20 highest priority orders
                # Heap is O(k log n) vs Full Array Sort is O(n log n)
                opt_o = benchmark_function(lambda: heapq.nsmallest(20, heap_data, key=lambda x: (x[0], x[1])), iterations=10)
                lin_o = benchmark_function(lambda: sorted(flat_data, key=lambda x: (x[0], x[1]))[:20], iterations=10)
                
                order_opt.append({"x": size, "time": opt_o["avg_time_ms"]})
                order_lin.append({"x": size, "time": lin_o["avg_time_ms"]})

        # --- 6. Range Queries (B+ Tree vs Linear Scan) ---
        range_opt, range_lin = [], []
        for size in sizes:
            subset = all_products[:size]
            
            s_svc = SearchService()
            s_svc.index_products(subset)
            
            # Select a prefix that acts as a sequential Range Query (e.g., all SKUs from 100-199)
            prefix_query = "sku-10"
            
            # Optimized: B+ Tree bisects down to the start node, then walks the leaves - O(log n + k)
            opt_r = benchmark_function(lambda: s_svc.search_by_sku_optimized(prefix_query), iterations=10)
            
            # Baseline: Linear Scan must evaluate every single product - O(n)
            lin_r = benchmark_function(lambda: [p for p in subset if p.sku.lower().startswith(prefix_query)][:100], iterations=10)
            
            range_opt.append({"x": size, "time": opt_r["avg_time_ms"]})
            range_lin.append({"x": size, "time": lin_r["avg_time_ms"]})

        # Format output exactly as expected by BenchmarkPage.tsx
        return [
            {
                "id": "search",
                "title": "B+ Tree vs Linear Search",
                "description": "Product lookup performance by exact match. B+ Tree offers O(log n) while Linear is O(n).",
                "metric": "time",
                "series": [{"label": "B+ Tree", "points": search_opt}, {"label": "Linear Search", "points": search_lin}]
            },
            {
                "id": "autocomplete",
                "title": "Trie vs Prefix Filter",
                "description": "Autocomplete performance. Trie provides O(m) lookups independent of dataset size.",
                "metric": "time",
                "series": [{"label": "Trie", "points": auto_opt}, {"label": "Linear Filter", "points": auto_lin}]
            },
            {
                "id": "topk",
                "title": "Min-Heap vs Full Sort",
                "description": "Finding top K products. Min-Heap is O(n + k log n), sorting is O(n log n).",
                "metric": "time",
                "series": [{"label": "CMS + Min-Heap", "points": topk_opt}, {"label": "Full Sort", "points": topk_lin}]
            },
            {
                "id": "fraud_time",
                "title": "Bloom Filter vs Hash Set (True Negatives)",
                "description": "Speed of rejecting unknown IDs. Hash Set is highly optimized in C, so it often ties or beats the 7x hashing of the Bloom Filter.",
                "metric": "time",
                "series": [{"label": "Bloom Filter", "points": fraud_opt_time}, {"label": "Hash Set", "points": fraud_lin_time}]
            },
            {
                "id": "fraud_memory",
                "title": "Bloom Filter vs Hash Set (Memory Usage)",
                "description": "Space Complexity. The Bloom Filter sacrifices a tiny bit of CPU speed to use >90% less RAM.",
                "metric": "memory",
                "series": [{"label": "Bloom Filter", "points": fraud_opt_mem}, {"label": "Hash Set", "points": fraud_lin_mem}]
            },
            {
                "id": "orders_pq",
                "title": "Min-Heap vs Full Sort (Pagination)",
                "description": "Fetching the top 20 priority orders. Heaps extract exactly what you need in O(k log n), while arrays waste CPU sorting everything in O(n log n).",
                "metric": "time",
                "series": [{"label": "Min-Heap", "points": order_opt}, {"label": "Full Sort", "points": order_lin}]
            },
            {
                "id": "search_range",
                "title": "B+ Tree vs Linear Scan (Range Queries)",
                "description": "Finding a sequence of items. B+ Trees drop down to the start node and walk horizontally across leaves O(log n + k).",
                "metric": "time",
                "series": [{"label": "B+ Tree Walk", "points": range_opt}, {"label": "Linear Scan", "points": range_lin}]
            }
        ]