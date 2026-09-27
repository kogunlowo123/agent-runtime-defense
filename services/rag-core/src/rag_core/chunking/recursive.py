"""Recursive character text splitter."""
from .base import BaseChunker, Chunk


class RecursiveChunker(BaseChunker):
    """Splits text recursively on paragraph, sentence, then character boundaries."""

    _SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        meta = metadata or {}
        raw_chunks = self._split(text, self._SEPARATORS)
        result = []
        offset = 0
        for raw in raw_chunks:
            start = text.find(raw, offset)
            if start == -1:
                start = offset
            end = start + len(raw)
            result.append(Chunk(text=raw, start_char=start, end_char=end, metadata=dict(meta)))
            offset = max(0, end - self._chunk_overlap)
        return result

    def _split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self._chunk_size:
            return [text] if text.strip() else []

        separator = ""
        remaining = list(separators)
        while remaining:
            sep = remaining.pop(0)
            if sep == "" or sep in text:
                separator = sep
                break

        if separator == "":
            return self._hard_split(text)

        parts = text.split(separator)
        chunks: list[str] = []
        current = ""
        for part in parts:
            candidate = (current + separator + part).lstrip(separator) if current else part
            if len(candidate) <= self._chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > self._chunk_size:
                    chunks.extend(self._split(part, remaining or [""]))
                    current = ""
                else:
                    current = part
        if current:
            chunks.append(current)
        return chunks

    def _hard_split(self, text: str) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self._chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self._chunk_overlap
        return chunks
