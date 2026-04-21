"""Manual Count-Min Sketch implementation using matrix with multiple hash functions."""

import hashlib


class CountMinSketch:
    """Count-Min Sketch for probabilistic frequency estimation."""

    def __init__(self, depth: int = 7, width: int = 1000000):
        self.depth = depth
        self.width = width
        self.matrix = [[0] * width for _ in range(depth)]
        self.hash_functions = self._generate_hash_functions()

    def _generate_hash_functions(self) -> list[callable]:
        """Generate hash functions using hashlib with different seeds."""
        def make_hash(seed: int):
            def hash_fn(item: str) -> int:
                seed_bytes = f"{item}_{seed}".encode()
                hash_obj = hashlib.md5(seed_bytes)
                return int(hash_obj.hexdigest(), 16) % self.width
            return hash_fn
        return [make_hash(i) for i in range(self.depth)]

    def update(self, item: str, count: int = 1) -> None:
        """Update the count for an item."""
        for i, hash_fn in enumerate(self.hash_functions):
            pos = hash_fn(item)
            self.matrix[i][pos] += count

    def estimate(self, item: str) -> int:
        """Estimate the frequency count for an item (minimum across all rows)."""
        return min(hash_fn(item) for hash_fn in self.hash_functions)

    def reset(self) -> None:
        """Clear the Count-Min Sketch."""
        self.matrix = [[0] * self.width for _ in range(self.depth)]
