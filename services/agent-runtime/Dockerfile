FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir uv==0.5.0
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

FROM python:3.12-slim AS runtime
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
USER appuser
CMD ["python", "-m", "agent_runtime.orchestrator.graph"]
