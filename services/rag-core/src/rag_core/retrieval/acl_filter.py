"""ACL-aware filter for retrieval results."""
from __future__ import annotations

from ..stores.vector_base import SearchResult


class AclFilter:
    """Removes documents the requesting principal is not authorised to read."""

    def filter(
        self,
        results: list[SearchResult],
        principal_id: str,
        principal_groups: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        Keep only documents where the principal or one of their groups
        appears in doc metadata['allowed_principals'] or metadata['allowed_groups'].
        Documents with no ACL metadata are treated as public.
        """
        groups = set(principal_groups or [])
        allowed: list[SearchResult] = []
        for result in results:
            meta = result.metadata
            allowed_principals: list[str] = meta.get("allowed_principals", [])
            allowed_groups: list[str] = meta.get("allowed_groups", [])
            if not allowed_principals and not allowed_groups:
                allowed.append(result)
                continue
            if principal_id in allowed_principals:
                allowed.append(result)
                continue
            if groups & set(allowed_groups):
                allowed.append(result)
        return allowed
