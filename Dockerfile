# Adaptive Document Intelligence System - Docker Container
# Phase 11: Containerization
#
# This Dockerfile creates a reproducible environment for the ADI system
# with Tesseract OCR as the default engine (PaddleOCR optional).

# Use Python 3.11 slim for compatibility (NOT 3.14)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TESSERACT_CMD=/usr/bin/tesseract \
    OCR_ENGINE=tesseract \
    PYTHONPATH=/app

# Install system dependencies
# - tesseract-ocr: OCR engine
# - tesseract-ocr-eng: English language data
# - libgl1, libglib2.0-0, libsm6, libxext6, libxrender-dev: OpenCV dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
# Note: PaddleOCR is NOT installed by default (Tesseract only)
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Verify Tesseract installation
RUN tesseract --version && \
    echo "Tesseract OCR installed successfully"

# Create output directories
RUN mkdir -p /app/output/logs /app/output/cache/ocr

# Default command: run tests
CMD ["python", "-m", "pytest", "-v"]