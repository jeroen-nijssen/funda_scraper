FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install headless Chromium + its OS-level dependencies for the Funda scraper
RUN playwright install --with-deps chromium

# Copy application code
COPY app/ .

# Kanboard bootstrap script, run once by the kanboard-init service
COPY setup_kanboard.py .

# Create log directory
RUN mkdir -p /app/log

# Set environment variables with defaults
ENV LOCATION=gemeente-amsterdam
ENV DISTANCE=5
ENV MAX_PRICE=450000
ENV MIN_ROOMS=5
ENV MIN_AREA=100
ENV FUNDA_SLEEP=3600
ENV PARARIUS_SLEEP=1800
ENV HUISPEDIA_SLEEP=3600
ENV LOG_DIR=/app/log

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["python", "main.py"]