"""LSM (Log-Structured Merge) debug/simulation service."""

import random
from datetime import datetime, timedelta


class LSMDebugService:
    """Simulate LSM tree behavior for educational purposes."""

    def __init__(self):
        self.levels = []
        self.sstables = []
        self.compaction_events = []
        self.max_levels = 7
        self.max_sstables_per_level = 10

        # Initialize levels
        for i in range(self.max_levels):
            self.levels.append({
                "level": i,
                "name": f"L{i}",
                "max_size_mb": 10 * (2 ** i),  # Each level 10x larger
                "current_size_mb": 0,
                "sstables": []
            })

    def add_sstable(self, level: int, sstable_id: str, size_mb: float) -> None:
        """Simulate adding an SSTable to a level."""
        if level >= len(self.levels):
            return

        sstable = {
            "id": sstable_id,
            "size_mb": size_mb,
            "key_count": random.randint(1000, 100000),
            "created_at": datetime.now().isoformat()
        }
        self.levels[level]["sstables"].append(sstable)
        self.levels[level]["current_size_mb"] += size_mb
        self.sstables.append(sstable)

        # Simulate compaction if level is full
        if len(self.levels[level]["sstables"]) > self.max_sstables_per_level:
            self._trigger_compaction(level)

    def _trigger_compaction(self, level: int) -> None:
        """Simulate compaction event."""
        if level >= self.max_levels - 1:
            return

        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "compaction",
            "source_level": level,
            "target_level": level + 1,
            "sstables_merged": len(self.levels[level]["sstables"]),
            "size_mb": self.levels[level]["current_size_mb"]
        }
        self.compaction_events.append(event)

        # Move SSTables to next level
        self.levels[level]["sstables"].clear()
        self.levels[level]["current_size_mb"] = 0

    def generate_simulated_state(self, num_sstables: int = 50) -> dict:
        """Generate a simulated LSM state for visualization."""
        self.compaction_events = []
        for level in self.levels:
            level["sstables"] = []
            level["current_size_mb"] = 0

        # Populate with random SSTables
        for i in range(num_sstables):
            level = min(i // self.max_sstables_per_level, self.max_levels - 1)
            size = random.uniform(0.5, 5.0)
            self.add_sstable(level, f"SST_{i:04d}", size)

        return self.get_state()

    def get_state(self) -> dict:
        """Get current LSM state."""
        return {
            "levels": self.levels,
            "total_sstables": len(self.sstables),
            "total_size_mb": sum(s["size_mb"] for s in self.sstables),
            "compaction_events": self.compaction_events[-10:],  # Last 10 events
            "timestamp": datetime.now().isoformat()
        }

    def get_timeline(self) -> list[dict]:
        """Get timeline of simulated events."""
        timeline = []

        # Generate initial compaction events
        for i in range(20):
            event_time = datetime.now() - timedelta(hours=random.randint(1, 48))
            timeline.append({
                "timestamp": event_time.isoformat(),
                "event": random.choice([
                    "flush_memtable",
                    "level_compaction",
                    "minor_compaction",
                    "major_compaction"
                ]),
                "level": random.randint(0, self.max_levels - 1),
                "details": {
                    "entries_written": random.randint(10000, 500000),
                    "entries_removed": random.randint(0, 10000),
                    "size_mb": round(random.uniform(1.0, 100.0), 2)
                }
            })

        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        return timeline[:20]
