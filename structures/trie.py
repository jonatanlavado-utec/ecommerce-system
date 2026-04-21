"""Manual Trie implementation with sales-based ranking for autocomplete."""

import heapq
from typing import Optional


class TrieNode:
    """Node in the Trie structure."""

    def __init__(self, max_products: int = 100):
        self.children: dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.products: list[tuple[int, str]] = []  # (sales, product_id)
        self.seen_products: set[tuple[int, str]] = set()  # O(1) duplicate tracking
        self.max_products: int = max_products


class Trie:
    """Trie for fast prefix-based autocomplete with sales ranking (optimized for 1M+ products)."""

    def __init__(self, max_products_per_node: int = 100):
        self.root = TrieNode(max_products_per_node)
        self.max_products = max_products_per_node

    def insert(self, product_id: str, name: str, sales: int) -> None:
        """Insert a product into the Trie (optimized for batching)."""
        node = self.root
        name_lower = name.lower()  # Pre-compute once instead of per-char
        
        for char in name_lower:
            if char not in node.children:
                node.children[char] = TrieNode(self.max_products)
            node = node.children[char]
            
            # O(1) duplicate check using set instead of O(k) list search
            product_tuple = (sales, product_id)
            if product_tuple not in node.seen_products:
                node.products.append(product_tuple)
                node.seen_products.add(product_tuple)

    def _sort_all_nodes(self, node: Optional[TrieNode] = None) -> None:
        """Recursively sort and keep top-k products per node (optimized)."""
        if node is None:
            node = self.root
        
        # Use heapq.nlargest for O(n log k) instead of O(n log n) sort
        if len(node.products) > node.max_products:
            node.products = heapq.nlargest(node.max_products, node.products, key=lambda x: x[0])
        else:
            # Still sort if under limit
            node.products.sort(key=lambda x: -x[0])
        
        # Update seen set to match trimmed products
        node.seen_products = set(node.products)
        
        # Recursively sort all children
        for child in node.children.values():
            self._sort_all_nodes(child)

    def search_prefix(self, prefix: str, limit: int = 10) -> list[tuple[int, str]]:
        """Find all products matching a prefix, ranked by sales."""
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        return node.products[:limit]

    def _collect_all(self, node: TrieNode) -> list[tuple[int, str]]:
        """Recursively collect all products from a node."""
        results = list(node.products)
        for child in node.children.values():
            results.extend(self._collect_all(child))
        return results

    def get_all(self) -> list[tuple[int, str]]:
        """Get all products in the Trie."""
        return self._collect_all(self.root)
