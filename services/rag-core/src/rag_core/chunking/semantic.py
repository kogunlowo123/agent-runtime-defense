"""Semantic chunker: splits on embedding cosine-distance peaks."""
from __future__ import annotations

from .base import BaseChunker, Chunk


class SemanticChunker(BaseChunker):
    """Groups sentences into chunks based on semantic similarity boundaries."""

    def __init__(
        self,
        embedder,
        threshold: float = 0.85,
        max_chunk_size: int = 1024,
    ) -> None:
        self._embedder = embedder
        self._threshold = threshold
        self._max_chunk_size = max_chunk_size

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        import re

        meta = metadata or {}
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return []

        vectors = self._embedder.embed_batch(sentences)

        groups: list[list[str]] = []
        current_group: list[str] = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = self._cosine_similarity(vectors[i - 1], vectors[i])
            combined = " ".join(current_group + [sentences[i]])
            if sim >= self._threshold and len(combined) <= self._max_chunk_size:
                current_group.append(sentences[i])
            else:
                groups.append(current_group)
                current_group = [sentences[i]]
        groups.append(current_group)

        result: list[Chunk] = []
        offset = 0
        for group in groups:
            chunk_text = " ".join(group)
            start = text.find(group[0], offset)
            if start == -1:
                start = offset
            end = start + len(chunk_text)
            result.append(Chunk(text=chunk_text, start_char=start, end_char=end, metadata=dict(meta)))
            offset = end
        return result
