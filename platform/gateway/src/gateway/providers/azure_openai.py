"""Azure OpenAI provider adapter for the platform gateway."""
import os
from dataclasses import dataclass


@dataclass
class AzureOpenAIConfig:
    endpoint: str
    api_key: str
    deployment: str
    api_version: str = "2024-02-01"


def load_azure_openai_config() -> AzureOpenAIConfig:
    """Load Azure OpenAI configuration from environment variables."""
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")

    if not endpoint or not api_key:
        raise EnvironmentError(
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set"
        )

    return AzureOpenAIConfig(
        endpoint=endpoint,
        api_key=api_key,
        deployment=deployment,
        api_version=api_version,
    )


def build_litellm_model_string(config: AzureOpenAIConfig) -> str:
    """Convert config to a LiteLLM-compatible model string."""
    return f"azure/{config.deployment}"
