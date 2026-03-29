"""
In-memory semantic cache.
Key = SHA256(normalized_prompt + model). TTL and max size from settings.
"""
import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional
from app.config import settings


@dataclass
class CacheEntry:
    response: dict
    timestamp: float
    hits: int = 0
    model: str = ""
    cost_saved: float = 0.0


class InMemoryCache:
    """
    Thread-safe enough for single-process FastAPI with SQLite.
    For multi-process deployments, replace with Redis.
    """

    def __init__(self, ttl_seconds: int, max_size: int):
        self._store: dict[str, CacheEntry] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._total_requests = 0
        self._total_hits = 0

    def _make_key(self, prompt: str, model: str) -> str:
        """Normalize prompt and create a deterministic cache key."""
        normalized = prompt.lower().strip()
        raw = f"{normalized}::{model}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[dict]:
        """Return cached response if it exists and hasn't expired."""
        self._total_requests += 1
        key = self._make_key(prompt, model)
        entry = self._store.get(key)

        if entry is None:
            return None

        # Check TTL
        if time.time() - entry.timestamp > self.ttl:
            del self._store[key]
            return None

        # Cache hit
        entry.hits += 1
        self._total_hits += 1
        return entry.response

    def set(self, prompt: str, model: str, response: dict, cost: float = 0.0):
        """Store a response in the cache. Evicts oldest entry if at capacity."""
        # Evict if at max size — remove the oldest entry
        if len(self._store) >= self.max_size:
            oldest_key = min(self._store, key=lambda k: self._store[k].timestamp)
            del self._store[oldest_key]

        key = self._make_key(prompt, model)
        self._store[key] = CacheEntry(
            response=response,
            timestamp=time.time(),
            model=model,
            cost_saved=cost,
        )

    def stats(self) -> dict:
        """Return cache statistics for the dashboard."""
        now = time.time()
        active_entries = sum(
            1 for e in self._store.values()
            if now - e.timestamp <= self.ttl
        )
        total_cost_saved = sum(
            e.cost_saved * e.hits for e in self._store.values()
        )
        hit_rate = (self._total_hits / self._total_requests * 100) if self._total_requests > 0 else 0.0

        return {
            "total_entries": active_entries,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl,
            "total_requests": self._total_requests,
            "total_hits": self._total_hits,
            "hit_rate_pct": round(hit_rate, 2),
            "estimated_cost_saved_usd": round(total_cost_saved, 6),
        }

    def clear(self):
        """Clear the entire cache."""
        self._store.clear()
        self._total_requests = 0
        self._total_hits = 0


# Module-level singleton — import this everywhere
cache = InMemoryCache(
    ttl_seconds=settings.cache_ttl_seconds,
    max_size=settings.cache_max_size,
)