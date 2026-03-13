"""
Generic in-memory LRU cache with TTL eviction.

Both DatasetStore and AnalysisRunStore inherit from BaseStore so all
cleanup, locking, and eviction logic lives in exactly one place.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Generic, Protocol, TypeVar


class _HasCreatedAt(Protocol):
    created_at: float


V = TypeVar("V", bound=_HasCreatedAt)


class BaseStore(Generic[V]):
    """
    Thread-safe in-memory LRU store with TTL expiry and max-entry eviction.

    Subclasses only need to implement their ``save()`` method; all lookup,
    expiry, and eviction logic is centralised here.
    """

    def __init__(self, *, max_entries: int = 30, ttl_seconds: int = 3600) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._items: OrderedDict[str, V] = OrderedDict()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Protected helpers (used by subclasses)
    # ------------------------------------------------------------------

    def _put(self, key: str, value: V) -> None:
        """Insert *value* under *key*, then evict stale/excess entries."""
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            self._cleanup_locked()

    def _get(self, key: str) -> V | None:
        """Return the stored value if it exists and hasn't expired."""
        with self._lock:
            self._cleanup_locked()
            item = self._items.get(key)
            if item is None:
                return None
            if self._is_expired(item):
                del self._items[key]
                return None
            self._items.move_to_end(key)
            return item

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _cleanup_locked(self) -> None:
        """Must be called while holding *_lock*."""
        expired = [k for k, v in self._items.items() if self._is_expired(v)]
        for k in expired:
            self._items.pop(k, None)
        while len(self._items) > self._max_entries:
            self._items.popitem(last=False)

    def _is_expired(self, value: V) -> bool:
        return (time.time() - value.created_at) > self._ttl_seconds
