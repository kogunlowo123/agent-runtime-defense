"""Ingestion sync pipeline: load → chunk → enrich → embed → store."""
from __future__ import annotations

import uuid

from ..chunking.base import BaseChunker
from ..embeddings.base import BaseEmbedder
from ..enrichment import acl_stamper, metadata as meta_enrichment, pii_tagger
from ..stores.vector_base import BaseVectorStore, Document
from .loader_registry import load


def sync_document(
    source_path: str,
    content_type: str,
    chunker: BaseChunker,
    embedder: BaseEmbedder,
    store: BaseVectorStore,
    allowed_principals: list[str] | None = None,
    allowed_groups: list[str] | None = None,
    extra_metadata: dict | None = None,
) -> list[str]:
    """
    Full ingestion pipeline for one document.
    Returns list of document IDs upserted into the vector store.
    """
    text = load(source_path, content_type)
    chunks = chunker.chunk(text, metadata=extra_metadata or {})

    documents: list[Document] = []
    for chunk in chunks:
        chunk_meta = dict(chunk.metadata)
        chunk_meta = meta_enrichment.enrich_metadata(
            chunk_meta,
            source_uri=source_path,
            content_type=content_type,
        )
        chunk_meta = pii_tagger.tag_pii(chunk_meta, chunk.text)
        chunk_meta = acl_stamper.stamp_acl(chunk_meta, allowed_principals, allowed_groups)
        vector = embedder.embed(chunk.text)
        doc_id = str(uuid.uuid4())
        documents.append(Document(id=doc_id, text=chunk.text, vector=vector, metadata=chunk_meta))

    store.upsert(documents)
    return [doc.id for doc in documents]
