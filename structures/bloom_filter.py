"""Manual Bloom Filter implementation using bit array with multiple hash functions."""

import hashlib


class BloomFilter:
    """Bloom Filter for probabilistic fraud detection."""

    def __init__(self, size: int, num_hashes: int = 7):
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = [0] * size

    def _get_hash_positions(self, item: str) -> list[int]:
        """Generate multiple hash positions using hashlib with different seeds."""
        positions = []
        for i in range(self.num_hashes):
            seed = f"{item}_{i}".encode()
            hash_obj = hashlib.md5(seed)
            hash_int = int(hash_obj.hexdigest(), 16)
            positions.append(hash_int % self.size)
        return positions

    def add(self, item: str) -> None:
        """Add an item to the Bloom Filter."""
        for pos in self._get_hash_positions(item):
            self.bit_array[pos] = 1

    def contains(self, item: str) -> bool:
        """Check if an item might exist in the set."""
        return all(self.bit_array[pos] == 1 for pos in self._get_hash_positions(item))

    def reset(self) -> None:
        """Clear the Bloom Filter."""
        self.bit_array = [0] * self.size
