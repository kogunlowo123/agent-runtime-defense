"""pgvector-backed vector store."""
from __future__ import annotations

import json
import uuid

from .vector_base import BaseVectorStore, Document, SearchResult


class PgVectorStore(BaseVectorStore):
    """Stores and retrieves document vectors using PostgreSQL + pgvector."""

    def __init__(self, connection_url: str, table_name: str = "rag_documents") -> None:
        import psycopg2
        import psycopg2.extras

        self._conn_url = connection_url
        self._table = table_name
        self._conn = psycopg2.connect(connection_url)
        self._conn.autocommit = True
        self._ensure_table()

    def _ensure_table(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    vector vector,
                    metadata JSONB
                )
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self._table}_vector_idx
                ON {self._table} USING ivfflat (vector vector_cosine_ops)
                WITH (lists = 100)
            """)

    def upsert(self, documents: list[Document]) -> None:
        import psycopg2.extras

        with self._conn.cursor() as cur:
            for doc in documents:
                cur.execute(
                    f"""
                    INSERT INTO {self._table} (id, text, vector, metadata)
                    VALUES (%s, %s, %s::vector, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET text = EXCLUDED.text,
                        vector = EXCLUDED.vector,
                        metadata = EXCLUDED.metadata
                    """,
                    (doc.id, doc.text, str(doc.vector), json.dumps(doc.metadata)),
                )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, text, metadata,
                       1 - (vector <=> %s::vector) AS score
                FROM {self._table}
                ORDER BY vector <=> %s::vector
                LIMIT %s
                """,
                (str(query_vector), str(query_vector), top_k),
            )
            rows = cur.fetchall()
        return [
            SearchResult(id=row[0], text=row[1], score=float(row[3]), metadata=row[2] or {})
            for row in rows
        ]

    def delete(self, ids: list[str]) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table} WHERE id = ANY(%s)",
                (ids,),
            )
