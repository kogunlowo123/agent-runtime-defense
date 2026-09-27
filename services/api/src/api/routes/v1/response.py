"""Isolation and response action endpoint."""
from datetime import datetime, timedelta
from typing import Annotated

import jwt
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from opentelemetry import trace

from api.config import Settings, get_settings
from api.schemas.response import (
    IsolationRequest,
    IsolationResponse,
    ResponseAction,
    ResponseStatus,
)

router = APIRouter(prefix="/response", tags=["response"])
tracer = trace.get_tracer(__name__)
logger = structlog.get_logger(__name__)

# T2 actions that require an approval token
_T2_ACTIONS: set[ResponseAction] = {ResponseAction.ISOLATE, ResponseAction.REVOKE}

# In-memory store for executed responses
_responses: dict[str, IsolationResponse] = {}


def _validate_approval_token(token: str, settings: Settings) -> dict:
    """Validate a T2 approval token; raise 403 on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approval token has expired",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid approval token: {exc}",
        )

    if "T2" not in payload.get("scopes", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approval token does not carry T2 scope",
        )
    return payload  # type: ignore[return-value]


@router.post("/isolate", response_model=IsolationResponse, status_code=200)
async def isolate_agent(
    request: Request,
    body: IsolationRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> IsolationResponse:
    """
    Execute a T2 response action (alert, isolate, revoke, throttle, monitor).
    ISOLATE and REVOKE actions require a valid approval token when
    ISOLATION_APPROVAL_REQUIRED is enabled.
    """
    with tracer.start_as_current_span("response.isolate") as span:
        span.set_attribute("principal_id", body.principal_id)
        span.set_attribute("action", body.action.value)
        span.set_attribute("requestor_id", body.requestor_id)

        needs_approval = settings.isolation_approval_required and body.action in _T2_ACTIONS

        if needs_approval:
            if not body.approval_token:
                logger.info(
                    "isolation_pending_approval",
                    principal_id=body.principal_id,
                    action=body.action.value,
                )
                response = IsolationResponse(
                    principal_id=body.principal_id,
                    action=body.action,
                    status=ResponseStatus.PENDING_APPROVAL,
                    requires_approval=True,
                    approval_url=(
                        f"https://example.com/approvals/new"
                        f"?principal={body.principal_id}"
                        f"&action={body.action.value}"
                    ),
                )
                _responses[str(response.response_id)] = response
                return response

            # Validate the approval token
            _validate_approval_token(body.approval_token, settings)

        # Execute the action
        executed_at = datetime.utcnow()
        expires_at = executed_at + timedelta(seconds=body.ttl_seconds)

        logger.info(
            "isolation_executed",
            principal_id=body.principal_id,
            action=body.action.value,
            requestor_id=body.requestor_id,
            ttl_seconds=body.ttl_seconds,
        )

        span.set_attribute("status", ResponseStatus.COMPLETED.value)

        response = IsolationResponse(
            principal_id=body.principal_id,
            action=body.action,
            status=ResponseStatus.COMPLETED,
            requires_approval=needs_approval,
            executed_at=executed_at,
            expires_at=expires_at,
        )
        _responses[str(response.response_id)] = response
        return response
