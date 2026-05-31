FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PIP_NO_CACHE_DIR=1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    git make gcc g++ python3-dev

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system cmake setuptools wheel && \
    uv sync --frozen --no-install-project --no-dev

RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -name "*.pyc" -delete && \
    find /app/.venv -name "*.pyo" -delete && \
    rm -rf /app/.venv/lib/python3.12/site-packages/torch/include && \
    rm -rf /app/.venv/lib/python3.12/site-packages/torch/test && \
    rm -rf /app/.venv/lib/python3.12/site-packages/caffe2 && \
    rm -rf /app/.venv/lib/python3.12/site-packages/triton && \
    find /app/.venv -name "*.so" -exec strip --strip-debug {} + 2>/dev/null || true

FROM python:3.12-slim-bookworm AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /sbin/nologin appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --chown=appuser:appgroup services/ /app/services/
COPY --chown=appuser:appgroup shared/ /app/shared/
COPY --chown=appuser:appgroup config.py /app/config.py

USER appuser
