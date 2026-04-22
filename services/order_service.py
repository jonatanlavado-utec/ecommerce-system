"""Order priority queue service using heapq."""

import heapq
from typing import Iterator, Optional
from models.models import Order, OrderPriority

class OrderService:
    def __init__(self):
        self.orders: list[Order] = []
        self.active_orders: dict = {}  # ---> ADD THIS: Tracks recent order state
        self.priority_heap: list[tuple[int, int, Order]] = []  
        self.counter: int = 0

    def index_orders(self, orders: Iterator[Order]) -> None:
        self.orders = []
        self.active_orders = {} # ---> ADD THIS
        self.priority_heap = []
        self.counter = 0
        
        heap_items = []
        for order in orders:
            self.orders.append(order)
            self.active_orders[order.id] = order # ---> ADD THIS
            heap_items.append((order.priority, self.counter, order))
            self.counter += 1
            
        self.priority_heap = heap_items
        heapq.heapify(self.priority_heap)

    def add_order(self, order: Order) -> None:
        self.orders.append(order)
        self.active_orders[order.id] = order # ---> ADD THIS
        heapq.heappush(self.priority_heap, (order.priority, self.counter, order))
        self.counter += 1

    def get_priority_orders(self, page: int = 1, limit: int = 20) -> dict:
        if not self.priority_heap:
            return {"orders": [], "total": 0, "page": page, "limit": limit, "pages": 0}

        # ---> ADD THIS: Lazy deletion cleanup of stale nodes at the root
        while self.priority_heap:
            _, _, head_order = self.priority_heap[0]
            if head_order.id not in self.active_orders or self.active_orders[head_order.id] is not head_order:
                heapq.heappop(self.priority_heap)
            else:
                break

        total = len(self.active_orders) # Use active_orders instead of orders
        pages = (total + limit - 1) // limit
        start = (page - 1) * limit
        end = start + limit

        all_sorted = heapq.nsmallest(end, self.priority_heap, key=lambda x: (x[0], x[1]))
        
        page_orders = []
        seen = set()
        
        for priority, counter, order in all_sorted:
            # ---> UPDATE THIS: Skip stale orders
            if order.id in seen or self.active_orders.get(order.id) is not order:
                continue
            seen.add(order.id)
            page_orders.append({
                "id": order.id,
                "customer_id": order.customer_id,
                "product_ids": order.product_ids,
                "priority": OrderPriority(priority).name,
                "total": order.total
            })

        # Correct pagination slice after filtering
        final_orders = page_orders[start:end]

        return {
            "orders": final_orders,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages
        }

    def get_heap_size(self) -> int:
        return len(self.active_orders)