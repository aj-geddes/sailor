# Multi-stage build for Flask backend
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy only requirements for better caching
COPY requirements.txt .

# Create wheels for all dependencies
RUN pip install --no-cache-dir wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Final stage - minimal runtime
FROM python:3.11-slim

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user
RUN useradd -m -u 1000 flask && \
    mkdir -p /app/static /app/templates && \
    chown -R flask:flask /app

WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels /root/.cache/pip

# Copy application code
COPY --chown=flask:flask . .

USER flask

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_APP=app.py

EXPOSE 5000

# Health check using socket connection test
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 5000)); s.close()" || exit 1

# Run with gunicorn for production (fallback to development server)
CMD ["sh", "-c", "if command -v gunicorn >/dev/null 2>&1; then gunicorn -w 4 -b 0.0.0.0:5000 app:app; else python app.py; fi"]