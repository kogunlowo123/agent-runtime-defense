"""TTL-aware in-memory cache with automatic expiry."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TtlCache:
    """Simple in-memory cache where each entry expires after a TTL."""

    def __init__(self, default_ttl_seconds: float = 300.0) -> None:
        self._default_ttl = default_ttl_seconds
        self._store: dict[str, _Entry] = {}

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._store[key] = _Entry(value=value, expires_at=time.monotonic() + ttl)

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def evict_expired(self) -> int:
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if now > v.expires_at]
        for key in expired:
            del self._store[key]
        return len(expired)

    def __len__(self) -> int:
        self.evict_expired()
        return len(self._store)
