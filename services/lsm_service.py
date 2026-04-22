"""LSM (Log-Structured Merge) Tree Tracker."""

import time
import random
import uuid
from datetime import datetime

class LSMDebugService:
    """Tracks real inserts and simulates LSM tree flushes and compactions based on actual data volume."""

    def __init__(self, memtable_limit_mb: float = 2.0):
        self.memtable_limit_bytes = memtable_limit_mb * 1024 * 1024
        self.memtable_current_bytes = 0
        self.memtable_entries = 0
        
        self.levels = []
        self.max_levels = 7
        self.compaction_events = []
        
        # Initialize LSM Levels
        for i in range(self.max_levels):
            self.levels.append({
                "level": i,
                "name": f"L{i}",
                # Level limits: L1=10MB, L2=100MB, L3=1GB...
                "max_size_bytes": (10 * (10 ** i)) * 1024 * 1024 if i > 0 else 0,
                "current_size_bytes": 0,
                "sstables": []
            })

    def insert(self, key: str, size_bytes: int) -> None:
        """Track a real insertion. Triggers flushes if memtable fills up."""
        self.memtable_current_bytes += size_bytes
        self.memtable_entries += 1
        
        # If MemTable exceeds the limit, flush to Level 0
        if self.memtable_current_bytes >= self.memtable_limit_bytes:
            self._flush_memtable(trigger_key=key)

    def _log_event(self, event_type: str, level: int, size_bytes: float, entries: int, key: str = None) -> None:
        """Add an event to the timeline log."""
        self.compaction_events.append({
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "level": level,
            "details": {
                "size_mb": size_bytes / (1024 * 1024),
                "entries_written": entries,
                "key": key
            }
        })
        # Keep only recent events so the memory/UI doesn't blow up
        if len(self.compaction_events) > 50:
            self.compaction_events.pop(0)

    def _flush_memtable(self, trigger_key: str) -> None:
        """Flush MemTable to an SSTable in Level 0."""
        sstable_size = self.memtable_current_bytes
        entries = self.memtable_entries
        
        self._log_event("flush_memtable", 0, sstable_size, entries, trigger_key)
        self._add_sstable(0, sstable_size, entries)
        
        # Reset MemTable
        self.memtable_current_bytes = 0
        self.memtable_entries = 0
        
        # Cascading compaction check for Level 0
        self._check_compaction(0)

    def _add_sstable(self, level_idx: int, size_bytes: float, entries: int) -> None:
        """Add an SSTable to a specific level."""
        sstable = {
            "id": f"SST_{level_idx}_{int(time.time()*1000)}_{random.randint(0,999)}",
            "size_mb": size_bytes / (1024 * 1024),
            "size_bytes": size_bytes,
            "entries": entries,
            "created_at": datetime.now().isoformat()
        }
        self.levels[level_idx]["sstables"].append(sstable)
        self.levels[level_idx]["current_size_bytes"] += size_bytes

    def _check_compaction(self, level_idx: int) -> None:
        """Check if a level needs compaction and recursively compact downwards."""
        if level_idx >= self.max_levels - 1:
            return
            
        level = self.levels[level_idx]
        needs_compaction = False
        
        # L0 compacts based on file count, other levels base on total size limit
        if level_idx == 0 and len(level["sstables"]) >= 4:
            needs_compaction = True
        elif level_idx > 0 and level["current_size_bytes"] > level["max_size_bytes"]:
            needs_compaction = True
            
        if needs_compaction:
            total_size = level["current_size_bytes"]
            total_entries = sum(s["entries"] for s in level["sstables"])
            
            self._log_event("compaction", level_idx + 1, total_size, total_entries)
            
            # Clear current level
            level["sstables"] = []
            level["current_size_bytes"] = 0
            
            # Push the merged SSTable down to the next level
            self._add_sstable(level_idx + 1, total_size, total_entries)
            
            # Cascading check for the next level
            self._check_compaction(level_idx + 1)
            
    def get_state(self) -> dict:
        """Return the current tree state formatted for the API."""
        levels_formatted = []
        for l in self.levels:
            levels_formatted.append({
                "level": l["level"],
                "current_size_mb": l["current_size_bytes"] / (1024 * 1024),
                "sstables": l["sstables"]
            })
            
        return {
            "levels": levels_formatted,
            "timestamp": datetime.now().isoformat()
        }

    def get_timeline(self) -> list[dict]:
        """Return the recent timeline events."""
        return self.compaction_events