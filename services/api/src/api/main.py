"""Agent Runtime Defense — FastAPI application entry point."""
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.config import get_settings
from api.middleware.ratelimit import limiter
from api.middleware.tenant import TenantMiddleware
from api.middleware.tracing import configure_tracing
from api.routes.v1 import behavior, health, response, threat

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    settings = get_settings()

    # Configure OpenTelemetry tracing
    configure_tracing(
        service_name=settings.otel_service_name,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        environment=settings.app_env,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )

    logger.info("agent_runtime_defense_started", version="0.1.0", env=settings.app_env)

    yield

    logger.info("agent_runtime_defense_stopped")


def create_app() -> FastAPI:
    """Factory: create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Agent Runtime Defense API",
        description=(
            "Enterprise AI security platform for agent runtime defense — "
            "real-time anomaly detection, behavioral analysis, and automated threat response."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Rate limiter state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Tenant extraction
    app.add_middleware(TenantMiddleware)

    # Request ID injection middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[misc]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},  # type: ignore[attr-defined]
        )

    # Generic exception handler
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", exc_info=exc, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Check server logs."},
        )

    # Health routes (no /api/v1 prefix — accessible at root)
    app.include_router(health.router)

    # API v1 routes
    app.include_router(behavior.router, prefix="/api/v1")
    app.include_router(threat.router, prefix="/api/v1")
    app.include_router(response.router, prefix="/api/v1")

    # OpenTelemetry auto-instrumentation
    FastAPIInstrumentor.instrument_app(app)

    return app


app = create_app()
