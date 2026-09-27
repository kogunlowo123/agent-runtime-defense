"""Idempotency key store: prevent duplicate action execution."""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class IdempotencyRecord:
    key: str
    result: dict
    created_at: float
    ttl_seconds: float


class IdempotencyStore:
    """Records completed actions keyed by idempotency key."""

    def __init__(self, default_ttl_seconds: float = 86400.0) -> None:
        self._store: dict[str, IdempotencyRecord] = {}
        self._default_ttl = default_ttl_seconds

    def check(self, key: str) -> dict | None:
        """Return stored result if key exists and is not expired, else None."""
        record = self._store.get(key)
        if record is None:
            return None
        if time.monotonic() - record.created_at > record.ttl_seconds:
            del self._store[key]
            return None
        return record.result

    def record(self, key: str, result: dict, ttl_seconds: float | None = None) -> None:
        self._store[key] = IdempotencyRecord(
            key=key,
            result=result,
            created_at=time.monotonic(),
            ttl_seconds=ttl_seconds if ttl_seconds is not None else self._default_ttl,
        )

    def clear_expired(self) -> int:
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if now - v.created_at > v.ttl_seconds]
        for k in expired:
            del self._store[k]
        return len(expired)
