FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv (frozen = reproducible)
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 16050

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:16050/health')" || exit 1

# Use venv from uv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Run API
CMD ["python", "-m", "src.api"]
