FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first (for Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY nexus_core/ ./nexus_core/
COPY servers/ ./servers/
COPY data/ ./data/
COPY main.py ./
COPY .python-version ./

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["uv", "run", "uvicorn", "nexus_core.api:app", "--host", "0.0.0.0", "--port", "8000"]
