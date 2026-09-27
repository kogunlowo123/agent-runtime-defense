"""JWT token broker for agent identity issuance."""
import time
from dataclasses import dataclass, field
from typing import Any

import jwt


@dataclass
class TokenRequest:
    agent_id: str
    family: str
    tier: str
    scopes: list[str]
    ttl_seconds: int = 3600
    subject: str = ""
    audience: str = "agent-runtime-defense"


@dataclass
class IssuedToken:
    token: str
    expires_at: int
    jti: str
    scopes: list[str]


class TokenBroker:
    """Issues and validates JWT tokens for agent identities."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._revoked: set[str] = set()

    def issue(self, request: TokenRequest) -> IssuedToken:
        """Issue a new JWT for an agent."""
        import uuid

        now = int(time.time())
        jti = str(uuid.uuid4())

        payload: dict[str, Any] = {
            "sub": request.subject or request.agent_id,
            "iss": "agent-runtime-defense/token-broker",
            "aud": request.audience,
            "iat": now,
            "exp": now + request.ttl_seconds,
            "jti": jti,
            "agent_id": request.agent_id,
            "family": request.family,
            "tier": request.tier,
            "scopes": request.scopes,
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return IssuedToken(
            token=token,
            expires_at=now + request.ttl_seconds,
            jti=jti,
            scopes=request.scopes,
        )

    def verify(self, token: str, required_scope: str | None = None) -> dict:
        """Verify a token and optionally check for a required scope."""
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                audience="agent-runtime-defense",
                options={"verify_exp": True},
            )
        except jwt.PyJWTError as exc:
            raise ValueError(f"Token verification failed: {exc}") from exc

        if payload.get("jti") in self._revoked:
            raise ValueError("Token has been revoked")

        if required_scope and required_scope not in payload.get("scopes", []):
            raise PermissionError(
                f"Token lacks required scope '{required_scope}'. "
                f"Has: {payload.get('scopes', [])}"
            )

        return payload  # type: ignore[return-value]

    def revoke(self, jti: str) -> None:
        """Revoke a token by its JTI."""
        self._revoked.add(jti)
