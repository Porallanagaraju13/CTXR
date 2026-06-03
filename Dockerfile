# ContextForge Core — Production Dockerfile for Render
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed by pymupdf
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY main.py .
COPY contextforge/ contextforge/

# Set production defaults
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO
ENV PORT=10000

# Expose the port Render assigns
EXPOSE ${PORT}

# Run the FastAPI server with uvicorn
CMD uvicorn contextforge.api.app:app --host 0.0.0.0 --port ${PORT}
