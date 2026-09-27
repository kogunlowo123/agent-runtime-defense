"""Application configuration via pydantic-settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_cors_origins: list[str] = ["http://localhost:3000"]

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"

    # Database (PostgreSQL + pgvector)
    database_url: str = "postgresql://ard_user:ard_password@localhost:5432/agent_runtime_defense"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Azure AI Search
    azure_ai_search_endpoint: str = ""
    azure_ai_search_api_key: str = ""
    azure_ai_search_index_name: str = "agent-runtime-defense"

    # Azure Service Bus
    azure_service_bus_connection_string: str = ""
    azure_service_bus_queue_name: str = "agent-events"

    # JWT Authentication
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_seconds: int = 3600

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Anomaly Detection
    anomaly_detection_contamination: float = 0.1
    anomaly_detection_threshold: float = 0.7
    isolation_approval_required: bool = True

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "agent-runtime-defense"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
