"""
FastAPI ecommerce backend with data structures benchmarking.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Endpoints:
    GET /init?products=1000000&transactions=10000000  - Initialize with dataset
    GET /api/search?q=SKU-123&optimized=true|false    - B+ Tree vs linear
    GET /api/autocomplete?q=pre&optimized=true|false - Trie vs startswith
    GET /api/top-products?k=10&optimized=true|false  - Count-Min + MinHeap vs sort
    GET /api/fraud-check?n=50&optimized=true|false  - Bloom Filter vs Hash Set
    GET /api/priority-orders?page=1&limit=20         - Priority queue with heapq
    GET /api/benchmark                               - Full benchmark suite
    GET /api/lsm-debug                              - LSM simulation
    GET /api/stats                                  - System stats
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import psutil
import os
import time
import pickle
import json

# Persistence file path (in data/ directory)
import pathlib
BASE_DIR = pathlib.Path(__file__).parent.resolve()
STATE_FILE = BASE_DIR / "data" / "app_state.pkl"

print(f"[STATE] Base dir: {BASE_DIR}")
print(f"[STATE] State file: {STATE_FILE}")

from models.models import Product, Order, OrderPriority
from utils.data_generator import (
    generate_products, generate_transactions, generate_orders_from_transactions,
    estimate_memory_size
)
from services.search_service import SearchService
from services.autocomplete_service import AutocompleteService
from services.topk_service import TopKService
from services.fraud_service import FraudService
from services.order_service import OrderService
from services.benchmark_service import BenchmarkService
from services.lsm_service import LSMDebugService

app = FastAPI(
    title="Ecommerce Backend API",
    description="FastAPI backend with data structures benchmarking",
    version="1.0.0"
)

# Global application state
app_state = {
    "initialized": False,
    "products_count": 0,
    "transactions_count": 0,
    # Indexed structures
    "search_service": SearchService(),
    "autocomplete_service": AutocompleteService(),
    "topk_service": TopKService(),
    "fraud_service": FraudService(),
    "order_service": OrderService(),
    "lsm_service": LSMDebugService(memtable_limit_mb=2.0),
    # Only store products list for linear search fallback
    "products": [],
    # Async initialization state
    "init_progress": {
        "running": False,
        "started_at": None,
        "products_done": 0,
        "products_total": 0,
        "transactions_done": 0,
        "transactions_total": 0,
        "phase": "idle",  # idle, products, transactions, orders, done
        "error": None,
    },
}


def save_state():
    """Save app state to disk (only essential data, rebuild indexes on load)."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = STATE_FILE.with_suffix('.tmp')

        txn_ids = list(app_state["fraud_service"].hash_set) if hasattr(app_state["fraud_service"], "hash_set") else []

        # FIX: Extract the Order object (index 2) from the heap tuple (priority, counter, order)
        raw_orders = app_state["order_service"].get_all_orders() if hasattr(app_state["order_service"], "get_all_orders") else []
        orders = []
        for item in raw_orders:
            # If the service returns the raw heap tuple, take the 3rd element (the Order object)
            if isinstance(item, tuple) and len(item) == 3:
                orders.append(item[2])
            else:
                orders.append(item)

        data = {
            "initialized": app_state["initialized"],
            "products_count": app_state["products_count"],
            "transactions_count": app_state["transactions_count"],
            "products": app_state["products"],
            "transaction_ids": txn_ids,
            "orders": orders, # Now saving clean Order objects
        }

        with open(temp_file, "wb") as f:
            pickle.dump(data, f)

        temp_file.rename(STATE_FILE)
        print(f"[STATE] Saved - products: {len(app_state['products'])}, txns: {len(txn_ids)}, orders: {len(orders)}")
    except Exception as e:
        print(f"[STATE] Save FAILED: {e}")


def load_state():
    """Load app state from disk and rebuild indexes."""
    if not os.path.exists(STATE_FILE):
        print(f"[STATE] No state file found")
        return False

    # Check file size
    file_size = STATE_FILE.stat().st_size
    if file_size < 100:
        print(f"[STATE] File too small ({file_size} bytes), ignoring")
        return False

    try:
        with open(STATE_FILE, "rb") as f:
            data = pickle.load(f)

        products = data.get("products", [])
        transaction_ids = data.get("transaction_ids", [])
        orders = data.get("orders", [])

        print(f"[STATE] Loaded data - products: {len(products)}, txns: {len(transaction_ids)}, orders: {len(orders)}")

        # Rebuild search index (B+ Tree)
        for product in products:
            app_state["search_service"].add_product(product)
            app_state["autocomplete_service"].add_product(product)
            app_state["topk_service"].add_product(product)

        # Rebuild fraud index (Bloom Filter)
        for txn_id in transaction_ids:
            app_state["fraud_service"].add_transaction(txn_id)

        # Rebuild order index (Priority Heap)
        for order in orders:
            # Safety check: if 'order' is the heap tuple (priority, count, obj), unpack it
            actual_order = order[2] if isinstance(order, tuple) and len(order) == 3 else order
            app_state["order_service"].add_order(actual_order)

        # Set state
        app_state["initialized"] = data["initialized"]
        app_state["products_count"] = data.get("products_count", len(products))
        app_state["transactions_count"] = data.get("transactions_count", len(transaction_ids))
        app_state["products"] = products

        print(f"[STATE] Indexes rebuilt - search: {app_state['search_service']._indexed}, fraud: {app_state['fraud_service']._indexed}")
        return True
    except Exception as e:
        print(f"[STATE] Load failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Try to load saved state on startup
_loaded = load_state()


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Ecommerce Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "Benchmark optimized vs non-optimized data structures",
        "endpoints": {
            "init": "/init?products=1000000&transactions=10000000",
            "search": "/api/search?q=query&optimized=true|false",
            "autocomplete": "/api/autocomplete?q=pre&optimized=true|false",
            "top_products": "/api/top-products?k=10&optimized=true|false",
            "fraud_check": "/api/fraud-check?n=50&optimized=true|false",
            "priority_orders": "/api/priority-orders?page=1&limit=20",
            "benchmark": "/api/benchmark",
            "lsm_debug": "/api/lsm-debug",
            "stats": "/api/stats"
        }
    }


@app.get("/init")
async def init_dataset(
    products: int = Query(default=1000000, ge=1000, le=10000000, description="Number of products"),
    transactions: int = Query(default=10000000, ge=1000, le=100000000, description="Number of transactions"),
    chunk_size: int = Query(default=50000, ge=1000, le=100000, description="Chunk size for incremental indexing")
):
    """
    Initialize dataset and build all indexes in one pass.

    Products go to: B+ Tree (search), Trie (autocomplete), Count-Min + MinHeap (top-k)
    Transactions go to: Bloom Filter (fraud), Hash Set (fraud linear), Orders (priority queue)
    """
    if app_state["initialized"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Already initialized. Restart the server to regenerate."}
        )

    start_time = time.time()
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)

    products_list = []
    transaction_ids = []
    orders_list = []
    product_ids = []

    # Collect product_ids for order generation
    chunk_count = 0

    # STEP 1: Collect all products into a list (consume generator fully)
    products_list = list(generate_products(products))
    product_ids = [p.id for p in products_list]  # For order generation

    # Batch index products into services (replaces incremental loop)
    app_state["search_service"].index_products(products_list)        # Builds B+ Tree in one pass
    app_state["autocomplete_service"].index_products(products_list)  # Builds Trie in one pass
    app_state["topk_service"].index_products(products_list)          # Builds Count-Min Sketch + Heap in one pass

    app_state["products"] = products_list

    # STEP 2: Collect all transactions and orders into lists (batch mode)
    transaction_ids = []
    orders_list = []
    
    for txn in generate_transactions(transactions):  # Loop only to collect data
        transaction_ids.append(txn.id)
        
        # Generate order from purchase transactions
        if txn.transaction_type == 'purchase':
            rank = len(orders_list)
            order = Order(
                id=txn.id,
                customer_id=txn.user_id,
                product_ids=[product_ids[rank % len(product_ids)]],
                priority=OrderPriority(rank % 3 + 1) if rank < 1000000 else OrderPriority.STANDARD,
                total=txn.amount
            )
            orders_list.append(order)
    
    # Batch index transactions and orders (replaces incremental loop)
    app_state["fraud_service"].index_transactions(transaction_ids)  # Builds Bloom Filter + Hash Set in one pass
    app_state["order_service"].index_orders(orders_list)            # Builds priority heap in one pass

    # Store app state
    app_state["initialized"] = True
    app_state["products_count"] = products
    app_state["transactions_count"] = transactions

    elapsed = time.time() - start_time
    mem_after = process.memory_info().rss / (1024 * 1024)

    mem_estimate = estimate_memory_size(products, transactions)

    return {
        "status": "initialized",
        "products_indexed": products,
        "transactions_indexed": transactions,
        "orders_created": len(orders_list),
        "timing": {
            "init_time_seconds": round(elapsed, 2),
            "products_per_second": round(products / elapsed, 0),
            "transactions_per_second": round(transactions / elapsed, 0)
        },
        "memory": {
            "used_mb": round(mem_after - mem_before, 2),
            "estimated_products_mb": round(mem_estimate["estimated_products_memory_mb"], 2)
        },
        "indexes": {
            "b_plus_tree": "ready (indexed by SKU)",
            "trie": "ready (indexed by product name)",
            "count_min_sketch": "ready (indexed by product_id and sales)",
            "bloom_filter": "ready (indexed by transaction_id)",
            "priority_heap": f"ready ({len(orders_list)} orders)"
        }
    }

    # Save state to disk
    save_state()


@app.get("/init-async")
async def init_dataset_async(
    products: int = Query(default=1000000, ge=1000, le=10000000, description="Number of products"),
    transactions: int = Query(default=10000000, ge=1000, le=100000000, description="Number of transactions"),
    chunk_size: int = Query(default=50000, ge=1000, le=100000, description="Chunk size for incremental indexing")
):
    """
    Start async dataset initialization in background.
    Use /init-status to poll for progress.
    """
    # 1. State: Already finished
    if app_state["initialized"]:
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "message": "Dataset is already initialized."}
        )
    print(f"[INIT] Starting async init - products: {products}, transactions: {transactions}")
    if app_state["init_progress"]["running"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Initialization already in progress. Check /init-status"}
        )

    if app_state["initialized"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Already initialized. Restart the server to regenerate."}
        )

    # Initialize progress state
    app_state["init_progress"] = {
        "running": True,
        "started_at": time.time(),
        "products_done": 0,
        "products_total": products,
        "transactions_done": 0,
        "transactions_total": transactions,
        "phase": "products",
        "error": None,
    }

    import asyncio
    import threading

    def run_init():
        """Run initialization in background thread."""
        try:
            products_list = []
            transaction_ids = []
            orders_list = []
            product_ids = []

            # Grab the real LSM Service from app state
            lsm = app_state["lsm_service"]

            # STEP 1: Collect and batch index products
            print('### START PRODUCTS')
            app_state["init_progress"]["phase"] = "products"
            products_list = list(generate_products(products))  # Collect all at once
            product_ids = [p.id for p in products_list]
            print('### START INDEX')

            # Batch index (replaces incremental loop)
            app_state["search_service"].index_products(products_list)
            print('### FINISH INDEX SEARCH')

            app_state["autocomplete_service"].index_products(products_list)
            print('### FINISH INDEX AUTOCOMPLETE')
            app_state["topk_service"].index_products(products_list)
            print('### FINISH INDEX TOPK')

            # ---> ADDED: Push products to LSM Tree Tracker
            print('### START LSM PRODUCTS')
            for product in products_list:
                lsm.insert(key=product.sku, size_bytes=150)
            print('### FINISH LSM PRODUCTS')
            
            app_state["products"] = products_list
            app_state["init_progress"]["products_done"] = products  # Mark as complete
            app_state["init_progress"]["phase"] = "products:done"

            # STEP 2: Collect and batch index transactions/orders
            print('### START TANSACTIONS')
            app_state["init_progress"]["phase"] = "transactions"
            transaction_ids = []
            purchase_transactions = []  # Store only purchase transactions separately
            product_ids_len = len(product_ids)  # Cache length - O(1) but repeated calls add up
            product_ids_len_1m = 1000000  # Cache constant

            # Single pass: collect all transaction IDs
            for txn in generate_transactions(transactions):
                transaction_ids.append(txn.id)

                # Only collect purchase transactions (avoid creating Order objects yet)
                if txn.transaction_type == 'purchase':
                    purchase_transactions.append(txn)
            print('### START order TANSACTIONS')
            # Batch create Order objects outside the generator loop (after all data collected)
            orders_list = []
            for rank, txn in enumerate(purchase_transactions):
                order = Order(
                    id=txn.id,
                    customer_id=txn.user_id,
                    product_ids=[product_ids[rank % product_ids_len]],
                    priority=OrderPriority(rank % 3 + 1) if rank < product_ids_len_1m else OrderPriority.STANDARD,
                    total=txn.amount
                )
                orders_list.append(order)

            # Batch index (replaces incremental loop)
            print('### START INDEX TRANSACTIONS')
            app_state["fraud_service"].index_transactions(transaction_ids)
            print('### FINISH INDEX FRAUD')
            app_state["order_service"].index_orders(orders_list)
            print('### FINISH INDEX ORDER')

            # ---> ADDED: Push transactions to LSM Tree Tracker
            print('### START LSM TRANSACTIONS')
            for txn_id in transaction_ids:
                lsm.insert(key=txn_id, size_bytes=60)
            print('### FINISH LSM TRANSACTIONS')

            app_state["init_progress"]["transactions_done"] = transactions  # Mark as complete
            app_state["init_progress"]["phase"] = "done"

            # Mark as complete
            app_state["initialized"] = True
            app_state["products_count"] = products
            app_state["transactions_count"] = transactions
            app_state["init_progress"]["running"] = False
            app_state["init_progress"]["phase"] = "done"

            # Save state to disk
            save_state()

        except Exception as e:
            app_state["init_progress"]["error"] = str(e)
            app_state["init_progress"]["running"] = False

    # Start background thread
    thread = threading.Thread(target=run_init, daemon=True)
    thread.start()

    return {
        "status": "started",
        "message": "Initialization started in background",
        "products_target": products,
        "transactions_target": transactions,
        "status_endpoint": "/init-status"
    }


@app.get("/init-status")
async def init_status():
    """
    Get initialization progress status.
    """
    # print(f"[STATUS] Request received - running: {app_state['init_progress']['running']}, initialized: {app_state['initialized']}")
    progress = app_state["init_progress"]

    return {
        "running": progress["running"],
        "phase": progress["phase"],
        "products": {
            "done": progress["products_done"],
            "total": progress["products_total"],
            "percent": round(progress["products_done"] / progress["products_total"] * 100, 1) if progress["products_total"] > 0 else 0
        },
        "transactions": {
            "done": int(progress["transactions_done"]) if progress["transactions_done"] else 0,
            "total": progress["transactions_total"],
            "percent": round(int(progress["transactions_done"] or 0) / progress["transactions_total"] * 100, 1) if progress["transactions_total"] > 0 else 0
        },
        "error": progress["error"],
        "initialized": app_state["initialized"]
    }


@app.get("/api/search")
async def search_products(
    q: str = Query(..., min_length=1, description="Search query (SKU or name)"),
    optimized: bool = Query(default=True, description="Use optimized B+ Tree search")
):
    """Search products by SKU or name."""
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="Call /init first")

    if optimized:
        results = app_state["search_service"].search_optimized(q)
    else:
        results = app_state["search_service"].search_linear(q)

    return {
        "query": q,
        "optimized": optimized,
        "count": len(results),
        "results": [
            {"id": p.id, "sku": p.sku, "name": p.name, "price": p.price, "sales": p.sales}
            for p in results[:50]
        ]
    }


@app.get("/api/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1, description="Prefix to search for"),
    optimized: bool = Query(True, description="Use Trie vs Linear search")
):
    """Get autocomplete suggestions for products."""
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="System not initialized. Call /init first.")
        
    svc = app_state["autocomplete_service"]
    
    if optimized:
        results = svc.autocomplete_optimized(q)
    else:
        results = svc.autocomplete_linear(q)
        
    return results


@app.get("/api/top-products")
async def top_products(
    k: int = Query(default=10, ge=1, le=1000, description="Number of top products"),
    optimized: bool = Query(default=True, description="Use optimized Count-Min + MinHeap")
):
    """Get top K products by sales."""
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="Call /init first")

    if optimized:
        results = app_state["topk_service"].get_top_k_optimized(k)
    else:
        results = app_state["topk_service"].get_top_k_linear(k)

    return {
        "k": k,
        "optimized": optimized,
        "count": len(results),
        "results": results
    }


@app.get("/api/products")
async def get_products(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=12, ge=1, le=100, description="Productos por página")
):
    """
    Endpoint paginado para obtener la lista completa de productos.
    Mantiene la estructura requerida por el frontend.
    """
    # 1. Verificar si el sistema está inicializado
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="Call /init first")

    products_list = app_state["products"]
    total_count = len(products_list)

    # 2. Calcular índices de rebanado (slicing)
    start = (page - 1) * page_size
    end = start + page_size
    
    # 3. Obtener el segmento de la lista
    items = products_list[start:end]

    # 4. Construir la respuesta con el formato exacto de TypeScript
    return {
        "items": [
            {"id": p.id, "sku": p.sku, "name": p.name, "price": p.price, "sales": p.sales}
            for p in items
        ],
        "page": page,
        "pageSize": page_size,
        "total": total_count,
        "hasMore": end < total_count
    }

# main.py - Update the /api/fraud-check endpoint
@app.get("/api/fraud-check")
async def fraud_check(
    n: int = Query(default=50, ge=1, le=10000, description="Number of transaction IDs to check"),
    optimized: bool = Query(default=True, description="Use optimized Bloom Filter")
):
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="Call /init first")

    stats = app_state["fraud_service"].get_fraud_stats()
    total_txns = stats["transactions_indexed"]

    import random
    check_ids = []
    for _ in range(n):
        # 80% chance of a valid ID, 20% chance of an "Unknown" (Fraud) ID
        if random.random() > 0.20:
            txn_num = random.randint(0, total_txns - 1)
        else:
            # Pick a number far outside the valid range
            txn_num = total_txns + random.randint(999999, 999990009)
        
        check_ids.append(f"txn_{txn_num:010d}")

    if optimized:
        results = app_state["fraud_service"].is_fraudulent_optimized(check_ids)
    else:
        results = app_state["fraud_service"].is_fraudulent_linear(check_ids)

    fraudulent = sum(1 for v in results.values() if v)

    return {
        "optimized": optimized,
        "total_checked": len(check_ids),
        "fraudulent_count": fraudulent,
        "stats": stats,
        "results": dict(list(results.items())[:100])
    }


@app.get("/api/priority-orders")
async def priority_orders(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    """Get orders sorted by priority using heapq."""
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="Call /init first")

    result = app_state["order_service"].get_priority_orders(page, limit)

    return {
        "page": page,
        "limit": limit,
        "orders": result["orders"],
        "total": result["total"],
        "pages": result["pages"]
    }


@app.get("/api/benchmark")
async def benchmark():
    """Run full benchmark comparing optimized vs non-optimized implementations."""
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="Call /init first")

    benchmark_service = BenchmarkService(app_state)
    results = benchmark_service.run_full_benchmark()

    return results


@app.get("/api/lsm-debug")
async def get_lsm_debug():
    """Return the real-time state and log timeline of the LSM Tree."""
    lsm = app_state.get("lsm_service")
    
    if not lsm:
        return JSONResponse(status_code=500, content={"error": "LSM Service not initialized"})
        
    return {
        "description": "Real-time LSM Tree Architecture",
        "lsm_state": lsm.get_state(),
        "timeline": lsm.get_timeline()
    }


@app.get("/api/stats")
async def stats():
    """Get current system and dataset statistics."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        "dataset": {
            "initialized": app_state["initialized"],
            "products_count": app_state["products_count"],
            "transactions_count": app_state["transactions_count"],
            "orders_in_heap": app_state["order_service"].get_heap_size()
        },
        "memory": {
            "rss_mb": round(memory_info.rss / (1024 * 1024), 2),
            "vms_mb": round(memory_info.vms / (1024 * 1024), 2),
            "percent": round(process.memory_percent(), 2)
        },
        "indexes": {
            "search": "B+ Tree (SortedDict)",
            "autocomplete": "Trie",
            "topk": "Count-Min + MinHeap",
            "fraud": "Bloom Filter",
            "orders": "Priority Heap (heapq)"
        }
    }


@app.get("/debug-state")
async def debug_state():
    """Debug endpoint to check state and file."""
    file_exists = os.path.exists(STATE_FILE)
    file_size = os.path.getsize(STATE_FILE) if file_exists else 0

    return {
        "file_exists": file_exists,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "initialized": app_state["initialized"],
        "products_count": app_state["products_count"],
        "transactions_count": app_state["transactions_count"],
        "products_in_memory": len(app_state["products"]),
        "services_indexed": {
            "search": app_state["search_service"]._indexed if hasattr(app_state["search_service"], "_indexed") else "unknown",
            "autocomplete": app_state["autocomplete_service"]._indexed if hasattr(app_state["autocomplete_service"], "_indexed") else "unknown",
            "topk": app_state["topk_service"]._indexed if hasattr(app_state["topk_service"], "_indexed") else "unknown",
            "fraud": app_state["fraud_service"]._indexed if hasattr(app_state["fraud_service"], "_indexed") else "unknown",
            "orders": app_state["order_service"]._indexed if hasattr(app_state["order_service"], "_indexed") else "unknown",
        }
    }

# ... Add this endpoint definition ...
@app.get("/api/benchmark-comparisons")
async def get_benchmark_comparisons():
    """Run dynamic scaling benchmarks across all services and return chart data."""
    if not app_state["initialized"]:
        raise HTTPException(status_code=400, detail="Call /init first to populate data")
        
    try:
        benchmark_svc = BenchmarkService(app_state)
        # This takes about 1-3 seconds to run dynamically depending on your CPU
        comparisons = benchmark_svc.run_scaling_comparisons()
        return JSONResponse(content=comparisons)
    except Exception as e:
        print(f"Benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_state():
    """Reset all state and delete saved data."""
    global app_state

    # Delete saved state file
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    # Reset in-memory state
    app_state = {
        "initialized": False,
        "products_count": 0,
        "transactions_count": 0,
        "search_service": SearchService(),
        "autocomplete_service": AutocompleteService(),
        "topk_service": TopKService(),
        "fraud_service": FraudService(),
        "order_service": OrderService(),
        "lsm_service": LSMDebugService(memtable_limit_mb=2.0),
        "products": [],
        "init_progress": {
            "running": False,
            "started_at": None,
            "products_done": 0,
            "products_total": 0,
            "transactions_done": 0,
            "transactions_total": 0,
            "phase": "idle",
            "error": None,
        },
    }

    return {"status": "reset", "message": "All state cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
