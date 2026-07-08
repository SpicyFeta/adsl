# ADSL Phase 1 — reproducible development and CI image
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install uv for fast, reproducible dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (layer cache optimization)
COPY pyproject.toml README.md ./
RUN uv sync --extra dev --no-install-project

# Copy application source and install project
COPY src/ ./src/
COPY data/ ./data/
RUN uv sync --extra dev

# Default command: run test suite
CMD ["uv", "run", "pytest"]