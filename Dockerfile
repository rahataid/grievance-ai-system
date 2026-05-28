FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system cmake setuptools wheel && \
    uv sync --frozen --no-install-project --no-dev


FROM python:3.12-slim-bookworm AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/services/api-gateway:/app" \
    PORT=8000

WORKDIR /app

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /sbin/nologin appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

COPY --chown=appuser:appgroup services/${SERVICE_NAME}/ /app/services/${SERVICE_NAME}/
COPY --chown=appuser:appgroup shared/ /app/shared/
COPY --chown=appuser:appgroup config.py /app/config.py

EXPOSE 8000

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

# Start the specific microservice using uvicorn dynamically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir services/${SERVICE_NAME}"]
