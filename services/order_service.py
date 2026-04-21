"""Order priority queue service using heapq."""

import heapq
from typing import Iterator, Optional
from models.models import Order, OrderPriority


class OrderService:
    """Service for managing orders with priority queue."""

    def __init__(self):
        self.orders: list[Order] = []
        self.priority_heap: list[tuple[int, int, Order]] = []  # (priority, counter, order)
        self.counter: int = 0

    def index_orders(self, orders: Iterator[Order]) -> None:
        """Index orders into priority queue from iterator (optimized for batching)."""
        self.orders = []
        self.priority_heap = []
        self.counter = 0
        
        # Build list of heap items first
        heap_items = []
        for order in orders:
            self.orders.append(order)
            heap_items.append((order.priority, self.counter, order))
            self.counter += 1
        
        # Use heapify (O(n)) instead of n heappush calls (O(n log n))
        self.priority_heap = heap_items
        heapq.heapify(self.priority_heap)

    def add_order(self, order: Order) -> None:
        """Add a single order (incremental)."""
        self.orders.append(order)
        heapq.heappush(self.priority_heap, (order.priority, self.counter, order))
        self.counter += 1

    def get_priority_orders(self, page: int = 1, limit: int = 20) -> dict:
        """Get paginated orders sorted by priority using heapq (optimized for pagination)."""
        if not self.priority_heap:
            return {"orders": [], "total": 0, "page": page, "limit": limit, "pages": 0}

        total = len(self.orders)
        pages = (total + limit - 1) // limit

        start = (page - 1) * limit
        end = start + limit

        # Use heapq.nsmallest for efficient pagination instead of full sort
        all_sorted = heapq.nsmallest(end, self.priority_heap, key=lambda x: (x[0], x[1]))
        all_sorted = all_sorted[start:end]

        page_orders = []
        for priority, counter, order in all_sorted:
            page_orders.append({
                "id": order.id,
                "customer_id": order.customer_id,
                "product_ids": order.product_ids,
                "priority": OrderPriority(priority).name,
                "total": order.total
            })

        return {
            "orders": page_orders,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages
        }

    def get_heap_size(self) -> int:
        """Get the number of orders in the priority queue."""
        return len(self.priority_heap)

    def get_all_orders(self) -> list:
        """Get all orders (for persistence)."""
        return self.priority_heap
