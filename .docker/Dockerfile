FROM python:3.12-slim-bullseye

# Python environment setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system & debug dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev pkg-config default-libmysqlclient-dev \
    libpq-dev gcc git python3-venv curl iputils-ping && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -ms /bin/bash appuser
USER appuser
WORKDIR /home/appuser/app

# Create venv and install Python packages inside it
RUN python3 -m venv venv

# Copy requirements first for caching
COPY --chown=appuser:appuser requirements.txt ./
RUN ./venv/bin/pip install --no-cache-dir --upgrade pip && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Copy and set entrypoint
USER root
COPY .docker/entrypoint.sh /home/appuser/app/entrypoint.sh
RUN chmod +x /home/appuser/app/entrypoint.sh && chown appuser:appuser /home/appuser/app/entrypoint.sh

EXPOSE 8000

USER appuser