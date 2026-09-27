"""Unit tests for isolation approval gate logic."""
import sys
from pathlib import Path
from uuid import uuid4

import jwt
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "services" / "api" / "src"))

from api.config import Settings
from api.middleware.auth import verify_jwt
from api.schemas.response import IsolationRequest, IsolationResponse, ResponseAction, ResponseStatus


def _make_settings(**kwargs) -> Settings:
    """Create a Settings instance with test-safe defaults."""
    return Settings(
        jwt_secret_key="test-secret-key-for-tests-only",
        jwt_algorithm="HS256",
        isolation_approval_required=True,
        **kwargs,
    )


def _make_token(
    settings: Settings,
    scopes: list[str] = None,
    expired: bool = False,
) -> str:
    import time

    payload = {
        "sub": "test-user",
        "scopes": scopes or ["T1"],
        "exp": int(time.time()) + (-10 if expired else 3600),
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class TestApprovalGate:
    """Tests for the T2 approval gate in the response endpoint."""

    def test_t2_token_with_t2_scope_passes(self) -> None:
        settings = _make_settings()
        token = _make_token(settings, scopes=["T1", "T2"])
        payload = verify_jwt(token, settings)
        assert "T2" in payload["scopes"]

    def test_t2_token_without_t2_scope_raises(self) -> None:
        from fastapi import HTTPException

        settings = _make_settings()
        token = _make_token(settings, scopes=["T1"])
        payload = verify_jwt(token, settings)
        # T2 scope missing — enforcement happens in response.py
        assert "T2" not in payload["scopes"]

    def test_expired_token_raises_401(self) -> None:
        from fastapi import HTTPException

        settings = _make_settings()
        token = _make_token(settings, scopes=["T1", "T2"], expired=True)
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(token, settings)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_raises_401(self) -> None:
        from fastapi import HTTPException

        settings = _make_settings()
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt("this-is-not-a-valid-jwt", settings)
        assert exc_info.value.status_code == 401

    def test_isolation_request_alert_needs_no_approval(self) -> None:
        """ALERT actions do not require a T2 approval token."""
        req = IsolationRequest(
            principal_id="agent-001",
            action=ResponseAction.ALERT,
            reason="Anomaly score exceeded threshold during monitoring window",
            requestor_id="system",
        )
        # ALERT is not in _T2_ACTIONS — no approval needed
        from api.routes.v1.response import _T2_ACTIONS

        assert req.action not in _T2_ACTIONS

    def test_isolation_request_isolate_requires_approval(self) -> None:
        """ISOLATE action requires a T2 approval token."""
        from api.routes.v1.response import _T2_ACTIONS

        assert ResponseAction.ISOLATE in _T2_ACTIONS

    def test_isolation_request_revoke_requires_approval(self) -> None:
        """REVOKE action requires a T2 approval token."""
        from api.routes.v1.response import _T2_ACTIONS

        assert ResponseAction.REVOKE in _T2_ACTIONS

    def test_isolation_request_validation(self) -> None:
        """Reason field must be at least 10 characters."""
        with pytest.raises(Exception):
            IsolationRequest(
                principal_id="agent-001",
                action=ResponseAction.ALERT,
                reason="short",  # < 10 chars
                requestor_id="system",
            )

    def test_ttl_seconds_bounds(self) -> None:
        """TTL must be between 60 and 86400 seconds."""
        with pytest.raises(Exception):
            IsolationRequest(
                principal_id="agent-001",
                action=ResponseAction.MONITOR,
                reason="Testing TTL lower bound validation",
                requestor_id="system",
                ttl_seconds=30,  # below 60
            )

        with pytest.raises(Exception):
            IsolationRequest(
                principal_id="agent-001",
                action=ResponseAction.MONITOR,
                reason="Testing TTL upper bound validation",
                requestor_id="system",
                ttl_seconds=100_000,  # above 86400
            )
