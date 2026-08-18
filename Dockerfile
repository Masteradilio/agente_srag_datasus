# Multi-stage Python 3.12 Slim Dockerfile for DataSUS Epidemiological Intelligence & RAG Agent
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies including font rendering for PDF and charts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libjpeg62-turbo \
    libopenjp2-7 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source and assets
COPY src/ src/
COPY app/ app/
COPY configs/ configs/
COPY data/ data/
COPY docs/ docs/
COPY pyproject.toml .

EXPOSE 8501

# Health check for Streamlit service
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Default command: run Streamlit application
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
