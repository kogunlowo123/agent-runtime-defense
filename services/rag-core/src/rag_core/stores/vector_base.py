"""Abstract base for vector store backends."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Document:
    id: str
    text: str
    vector: list[float]
    metadata: dict


@dataclass
class SearchResult:
    id: str
    text: str
    score: float
    metadata: dict


class BaseVectorStore(ABC):
    """Contract all vector store backends must satisfy."""

    @abstractmethod
    def upsert(self, documents: list[Document]) -> None:
        """Insert or update documents in the store."""

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Return the top_k nearest documents to query_vector."""

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """Remove documents by ID."""
