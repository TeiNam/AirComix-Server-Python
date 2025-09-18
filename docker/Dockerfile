# Comix Server Python Port - Docker Configuration
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install .

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    unrar-free \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r comix && useradd -r -g comix comix

# Create application directory
WORKDIR /app

# Copy application code
COPY app/ ./app/
COPY README.md ./

# Create manga directory and set permissions
RUN mkdir -p /manga && \
    chown -R comix:comix /app /manga

# Switch to non-root user
USER comix

# Expose port
EXPOSE 31257

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:31257/', timeout=5)" || exit 1

# Default command
CMD ["python", "-m", "app.main"]