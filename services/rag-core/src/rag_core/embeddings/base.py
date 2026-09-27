"""Abstract base for embedding providers."""
from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Contract all embedding backends must satisfy."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text string, returning a dense vector."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in one call."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the output vector dimensionality."""
