"""Registry of document loaders keyed by content type."""
from __future__ import annotations

from typing import Callable


_registry: dict[str, Callable[[str], str]] = {}


def register(content_type: str):
    """Decorator that registers a loader function for a content type."""
    def decorator(fn: Callable[[str], str]):
        _registry[content_type] = fn
        return fn
    return decorator


def get_loader(content_type: str) -> Callable[[str], str]:
    """Look up a loader by MIME type or raise KeyError."""
    if content_type not in _registry:
        raise KeyError(f"No loader registered for content_type={content_type!r}")
    return _registry[content_type]


def load(source_path: str, content_type: str) -> str:
    """Load a document from source_path using the registered loader."""
    loader = get_loader(content_type)
    return loader(source_path)
