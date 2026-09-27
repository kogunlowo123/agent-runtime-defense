"""Azure OpenAI embedding provider."""
from __future__ import annotations

from .base import BaseEmbedder


class AzureOpenAIEmbedder(BaseEmbedder):
    """Embeds text using Azure OpenAI's embedding endpoint via LiteLLM."""

    _DIMENSIONS = {
        "text-embedding-3-large": 3072,
        "text-embedding-3-small": 1536,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        deployment: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2024-02-01",
    ) -> None:
        self._deployment = deployment
        self._endpoint = endpoint
        self._api_key = api_key
        self._api_version = api_version

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        import litellm

        response = litellm.embedding(
            model=f"azure/{self._deployment}",
            input=texts,
            api_base=self._endpoint,
            api_key=self._api_key,
            api_version=self._api_version,
        )
        return [item["embedding"] for item in response.data]

    def embed(self, text: str) -> list[float]:
        return self._call_api([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            results.extend(self._call_api(texts[i : i + batch_size]))
        return results

    @property
    def dimensions(self) -> int:
        return self._DIMENSIONS.get(self._deployment, 1536)
