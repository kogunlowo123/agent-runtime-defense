"""JWT authentication middleware and dependency."""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.config import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=True)


def verify_jwt(token: str, settings: Settings) -> dict:
    """Decode and validate a JWT token. Returns the decoded payload."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload  # type: ignore[return-value]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(_bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """FastAPI dependency that validates the Bearer token and returns the payload."""
    return verify_jwt(credentials.credentials, settings)


def require_scope(required_scope: str):
    """Dependency factory: raises 403 if the token doesn't carry the required scope."""

    async def _check(
        payload: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        scopes: list[str] = payload.get("scopes", [])
        if required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope; '{required_scope}' required",
            )
        return payload

    return _check
