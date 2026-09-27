"""ACL stamper: attaches access-control lists to document metadata."""
from __future__ import annotations


def stamp_acl(
    metadata: dict,
    allowed_principals: list[str] | None = None,
    allowed_groups: list[str] | None = None,
) -> dict:
    """
    Attach ACL fields to metadata. Empty lists mean public (no restriction).
    """
    metadata["allowed_principals"] = allowed_principals or []
    metadata["allowed_groups"] = allowed_groups or []
    return metadata
