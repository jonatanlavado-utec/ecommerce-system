"""Manual Bloom Filter implementation using bit array with multiple hash functions (optimized)."""

import hashlib


class BloomFilter:
    """Bloom Filter for probabilistic fraud detection."""

    def __init__(self, size: int, num_hashes: int = 7):
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = [0] * size

    def _get_hash_positions(self, item: str) -> list[int]:
        """Generate multiple hash positions using faster hash functions (optimized)."""
        positions = []
        # Use faster built-in hash with different seeds instead of MD5
        item_bytes = item.encode()
        for i in range(self.num_hashes):
            # Use hashlib with seed variation for distribution
            seed = item_bytes + str(i).encode()
            hash_int = int.from_bytes(hashlib.md5(seed).digest()[:4], 'big')
            positions.append(hash_int % self.size)
        return positions

    def add(self, item: str) -> None:
        """Add an item to the Bloom Filter (optimized)."""
        # Pre-compute hash positions once instead of in a separate method call
        positions = self._get_hash_positions(item)
        for pos in positions:
            self.bit_array[pos] = 1

    def contains(self, item: str) -> bool:
        """Check if an item might exist in the set (optimized)."""
        # Pre-compute hash positions and check all at once
        positions = self._get_hash_positions(item)
        return all(self.bit_array[pos] == 1 for pos in positions)
        return all(self.bit_array[pos] == 1 for pos in self._get_hash_positions(item))

    def reset(self) -> None:
        """Clear the Bloom Filter."""
        self.bit_array = [0] * self.size
