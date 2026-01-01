# =============================================================================
# DOCKERFILE - DevOps Multi-Agent Chatbot
# =============================================================================
# Multi-stage build for optimized production image
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim as production

# Labels for container metadata
LABEL maintainer="DevOps Team"
LABEL description="DevOps Multi-Agent Chatbot with 42+ specialized agents"
LABEL version="1.0.0"

# Create non-root user for security
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=chatbot:chatbot . .

# Create directory for config if mounting external config
RUN mkdir -p /app/config && chown chatbot:chatbot /app/config

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Switch to non-root user
USER chatbot

# Run the chatbot
CMD ["python", "run_chatbot.py", "--web", "--host", "0.0.0.0", "--port", "8000"]
