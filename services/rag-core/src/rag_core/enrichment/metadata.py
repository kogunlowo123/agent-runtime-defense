"""Document metadata enrichment pipeline."""
from __future__ import annotations

import datetime


def enrich_metadata(
    raw_metadata: dict,
    source_uri: str = "",
    content_type: str = "text/plain",
) -> dict:
    """Attach standard metadata fields to a document's metadata dict."""
    return {
        **raw_metadata,
        "source_uri": source_uri,
        "content_type": content_type,
        "ingested_at": datetime.datetime.utcnow().isoformat() + "Z",
        "schema_version": "1.0",
    }
