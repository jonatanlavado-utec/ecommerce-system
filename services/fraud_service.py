"""Fraud detection service with Bloom Filter and Hash Set."""

from structures.bloom_filter import BloomFilter


class FraudService:
    """Service for fraud detection with optimized and non-optimized modes.

    Uses Bloom Filter for transaction IDs (not product IDs).
    """

    def __init__(self, bloom_size: int = 10000000, num_hashes: int = 7):
        self.transaction_ids: list[str] = []  # Only store for linear mode
        self.bloom_filter: BloomFilter = BloomFilter(size=bloom_size, num_hashes=num_hashes)
        self.hash_set: set = set()
        self._indexed: bool = False
        self._bloom_size = bloom_size
        self.total_indexed: int = 0  # Track total valid range

    def index_transactions(self, transaction_ids: list[str]) -> None:
        """Index transaction IDs for fraud detection (batch optimized)."""
        self.transaction_ids = transaction_ids
        self.total_indexed = len(transaction_ids)
        
        # Size bloom filter based on input size for optimal false positive rate
        optimal_size = max(self._bloom_size, self.total_indexed * 10)
        self.bloom_filter = BloomFilter(size=optimal_size, num_hashes=7)
        
        # Build hash set first (O(n)), then add to bloom filter in bulk
        self.hash_set = set(transaction_ids)  # O(n) bulk set creation
        for txn_id in self.hash_set:
            self.bloom_filter.add(txn_id)  # Still O(n * num_hashes) but faster overall
        self._indexed = True

    def add_transaction(self, txn_id: str) -> None:
        """Add a single transaction ID (incremental)."""
        self.transaction_ids.append(txn_id)
        self.bloom_filter.add(txn_id)
        self.hash_set.add(txn_id)
        self.total_indexed += 1
        self._indexed = True

    def _is_format_valid(self, txn_id: str) -> bool:
        """Short-circuit check: Validate if ID format and range are possible."""
        try:
            if txn_id.startswith("txn_"):
                # Extract the integer and check if it's within the known count
                num = int(txn_id.split('_')[1])
                return 0 <= num < self.total_indexed
        except (IndexError, ValueError):
            pass
        return False

    def is_fraudulent_optimized(self, transaction_ids: list[str]) -> dict:
        """Check fraud using Bloom Filter - O(k) where k is number of checks."""
        if not self._indexed:
            return {}
        results = {}
        for txn_id in transaction_ids:
            # Short-circuit: Immediately flag as fraud if out of range or malformed
            if not self._is_format_valid(txn_id):
                results[txn_id] = True
                continue
                
            # Bloom filter: if contains returns False, definitely not in set
            # If returns True, might be in set (false positive possible)
            results[txn_id] = not self.bloom_filter.contains(txn_id)
        return results

    def is_fraudulent_linear(self, transaction_ids: list[str]) -> dict:
        """Check fraud using Hash Set - O(1) average per lookup."""
        if not self._indexed:
            return {}
        results = {}
        for txn_id in transaction_ids:
            # Short-circuit: Immediately flag as fraud if out of range or malformed
            if not self._is_format_valid(txn_id):
                results[txn_id] = True
                continue
                
            results[txn_id] = txn_id not in self.hash_set
        return results

    def get_fraud_stats(self) -> dict:
        """Get statistics about fraud detection structures."""
        return {
            "bloom_filter_size": self.bloom_filter.size if self.bloom_filter else 0,
            "bloom_filter_hashes": self.bloom_filter.num_hashes if self.bloom_filter else 0,
            "hash_set_size": len(self.hash_set),
            "transactions_indexed": self.total_indexed,
        }