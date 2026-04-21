"""Manual Trie implementation with sales-based ranking for autocomplete."""

from typing import Optional


class TrieNode:
    """Node in the Trie structure."""

    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.products: list[tuple[int, str]] = []  # (sales, product_id)


class Trie:
    """Trie for fast prefix-based autocomplete with sales ranking."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, product_id: str, name: str, sales: int) -> None:
        """Insert a product into the Trie with its sales count."""
        node = self.root
        for char in name.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            # Store (sales, product_id) for ranking
            if (sales, product_id) not in node.products:
                node.products.append((sales, product_id))
                # Keep top products sorted by sales (descending)
                node.products.sort(key=lambda x: -x[0])  # x[0] is sales (int)

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
