"""Structural chunker: splits on Markdown/document headings."""
import re
from .base import BaseChunker, Chunk


class StructuralChunker(BaseChunker):
    """Splits a document at heading boundaries (Markdown H1-H3 or blank lines)."""

    _HEADING_RE = re.compile(r"^#{1,3}\s+.+", re.MULTILINE)

    def __init__(self, max_chunk_size: int = 2048) -> None:
        self._max_chunk_size = max_chunk_size

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        meta = metadata or {}
        boundaries = [m.start() for m in self._HEADING_RE.finditer(text)]
        if not boundaries:
            return [Chunk(text=text, start_char=0, end_char=len(text), metadata=dict(meta))]

        result: list[Chunk] = []
        starts = boundaries + [len(text)]
        for i, start in enumerate(starts[:-1]):
            end = starts[i + 1]
            segment = text[start:end].strip()
            if segment:
                result.append(Chunk(text=segment, start_char=start, end_char=end, metadata=dict(meta)))

        # Split oversized segments further at paragraph boundaries
        final: list[Chunk] = []
        for chunk in result:
            if len(chunk.text) <= self._max_chunk_size:
                final.append(chunk)
            else:
                paragraphs = chunk.text.split("\n\n")
                sub_start = chunk.start_char
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    end = sub_start + len(para)
                    final.append(Chunk(text=para, start_char=sub_start, end_char=end, metadata=dict(meta)))
                    sub_start = end + 2
        return final
