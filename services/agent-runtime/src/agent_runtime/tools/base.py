"""Abstract base for agent tools."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str = ""
    tokens_consumed: int = 0
    latency_ms: float = 0.0


class BaseTool(ABC):
    """Contract all agent tools must satisfy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given keyword arguments."""
