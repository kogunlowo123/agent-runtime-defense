"""Azure AI Search (Cognitive Search) vector store."""
from __future__ import annotations

import json

from .vector_base import BaseVectorStore, Document, SearchResult


class AzureAISearchStore(BaseVectorStore):
    """Stores and retrieves document vectors using Azure AI Search."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str,
        vector_field: str = "vector",
        dimensions: int = 3072,
    ) -> None:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient

        self._endpoint = endpoint
        self._index_name = index_name
        self._vector_field = vector_field
        self._dimensions = dimensions
        self._search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
        )
        self._index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )
        self._ensure_index()

    def _ensure_index(self) -> None:
        from azure.search.documents.indexes.models import (
            SearchField,
            SearchFieldDataType,
            SearchIndex,
            SimpleField,
            SearchableField,
            VectorSearch,
            HnswAlgorithmConfiguration,
            VectorSearchProfile,
        )

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="text", type=SearchFieldDataType.String),
            SearchField(
                name=self._vector_field,
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self._dimensions,
                vector_search_profile_name="default",
            ),
            SimpleField(name="metadata", type=SearchFieldDataType.String),
        ]

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
            profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw")],
        )

        index = SearchIndex(name=self._index_name, fields=fields, vector_search=vector_search)
        try:
            self._index_client.create_or_update_index(index)
        except Exception:
            pass  # Index may already exist

    def upsert(self, documents: list[Document]) -> None:
        docs = [
            {
                "id": doc.id,
                "text": doc.text,
                self._vector_field: doc.vector,
                "metadata": json.dumps(doc.metadata),
            }
            for doc in documents
        ]
        self._search_client.upload_documents(documents=docs)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        from azure.search.documents.models import VectorizedQuery

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields=self._vector_field,
        )
        results = self._search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            top=top_k,
        )
        return [
            SearchResult(
                id=r["id"],
                text=r["text"],
                score=r.get("@search.score", 0.0),
                metadata=json.loads(r.get("metadata", "{}")),
            )
            for r in results
        ]

    def delete(self, ids: list[str]) -> None:
        self._search_client.delete_documents(documents=[{"id": doc_id} for doc_id in ids])
