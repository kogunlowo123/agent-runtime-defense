"""Abstract base for text chunking strategies."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    start_char: int
    end_char: int
    metadata: dict


class BaseChunker(ABC):
    """Contract all chunking strategies must satisfy."""

    @abstractmethod
    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """Split text into chunks with positional metadata."""
