FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./
COPY requirements*.txt ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy source code
COPY src/ ./src/
COPY README.md ./

# Install the package
RUN uv pip install -e .

# Create non-root user
RUN groupadd -r keepass && useradd -r -g keepass keepass
RUN mkdir -p /data /data/backups && chown -R keepass:keepass /data

# Switch to non-root user
USER keepass

# Set up volumes
VOLUME ["/data"]

# Expose port (if needed for future web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from keepass_mcp_server.health import health_check; health_check()" || exit 1

# Default command
CMD ["python", "-m", "keepass_mcp_server.fastmcp_server"]
