"""LRU cache wrapper for embedding providers."""
from __future__ import annotations

import hashlib
from collections import OrderedDict

from .base import BaseEmbedder


class CachedEmbedder(BaseEmbedder):
    """Wraps any BaseEmbedder with an in-memory LRU cache keyed on text hash."""

    def __init__(self, inner: BaseEmbedder, max_size: int = 1000) -> None:
        self._inner = inner
        self._max_size = max_size
        self._cache: OrderedDict[str, list[float]] = OrderedDict()

    def _key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def _get(self, key: str) -> list[float] | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _put(self, key: str, vector: list[float]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = vector

    def embed(self, text: str) -> list[float]:
        key = self._key(text)
        cached = self._get(key)
        if cached is not None:
            return cached
        vector = self._inner.embed(text)
        self._put(key, vector)
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        keys = [self._key(t) for t in texts]
        results: list[list[float] | None] = [self._get(k) for k in keys]
        missing_indices = [i for i, r in enumerate(results) if r is None]
        if missing_indices:
            missing_texts = [texts[i] for i in missing_indices]
            new_vectors = self._inner.embed_batch(missing_texts)
            for idx, vec in zip(missing_indices, new_vectors):
                self._put(keys[idx], vec)
                results[idx] = vec
        return [r for r in results if r is not None]

    @property
    def dimensions(self) -> int:
        return self._inner.dimensions
