"""Tenant extraction middleware."""
import re

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

_TENANT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$")


class TenantMiddleware(BaseHTTPMiddleware):
    """Extract and validate the X-Tenant-ID header, injecting it into request.state."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        tenant_id = request.headers.get("X-Tenant-ID", "default")

        if not _TENANT_ID_PATTERN.match(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid X-Tenant-ID format. "
                    "Must be 3-64 alphanumeric characters with optional hyphens."
                ),
            )

        request.state.tenant_id = tenant_id
        response = await call_next(request)
        response.headers["X-Tenant-ID"] = tenant_id
        return response
