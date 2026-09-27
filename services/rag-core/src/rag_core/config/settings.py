"""RAG core service settings."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RagCoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore")

    # Embedding settings
    embedding_provider: str = Field(default="local_bge", description="'local_bge' or 'azure_openai'")
    bge_model_name: str = Field(default="BAAI/bge-large-en-v1.5")
    embedding_cache_size: int = Field(default=1000)

    # Azure OpenAI embeddings
    azure_openai_endpoint: str = Field(default="")
    azure_openai_api_key: str = Field(default="")
    azure_openai_embedding_deployment: str = Field(default="text-embedding-3-large")
    azure_openai_api_version: str = Field(default="2024-02-01")

    # Vector store
    vector_store: str = Field(default="pgvector", description="'pgvector' or 'ai_search'")
    pgvector_url: str = Field(default="postgresql://localhost:5432/ragdb")
    ai_search_endpoint: str = Field(default="")
    ai_search_api_key: str = Field(default="")
    ai_search_index_name: str = Field(default="rag-index")

    # Chunking
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)

    # Retrieval
    top_k: int = Field(default=10)
    rerank_top_n: int = Field(default=3)
    hybrid_alpha: float = Field(default=0.7, description="Weight for vector vs keyword (0=keyword, 1=vector)")

    # PII and ACL
    pii_detection_enabled: bool = Field(default=True)
    acl_enforcement_enabled: bool = Field(default=True)


_settings: RagCoreSettings | None = None


def get_settings() -> RagCoreSettings:
    global _settings
    if _settings is None:
        _settings = RagCoreSettings()
    return _settings
