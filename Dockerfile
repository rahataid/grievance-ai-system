
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Prevent uv from copying files into a cache inside the image
ENV UV_LINK_MODE=copy

# Copy dependency files first to leverage Docker caching layers
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment (.venv)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


FROM python:3.12-slim-bookworm AS runner

# Set environment variables for production performance and security
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/services/api-gateway:/app" \
    PORT=8000

WORKDIR /app

# Create a non-root system user and group for security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /sbin/nologin appuser

# Copy the virtual environment from the builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy necessary source code directories
# (Ensuring both the service and shared utilities are present)
COPY --chown=appuser:appgroup services/api-gateway/ /app/services/api-gateway/
COPY --chown=appuser:appgroup shared/ /app/shared/
COPY --chown=appuser:appgroup config.py /app/config.py

# Expose the API Gateway port
EXPOSE 8000

# Switch to the non-root user
USER appuser

# Health check to ensure the API Gateway container is running properly
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

# Start the FastAPI application using uvicorn via the virtual environment
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "services/api-gateway"]
