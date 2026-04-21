"""Benchmark service for comparing optimized vs non-optimized implementations."""

import time
import random
import psutil
from typing import Callable, Any


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
