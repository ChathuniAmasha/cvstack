# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for layer cache
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source and migrations
COPY src ./src
COPY migrations ./migrations
COPY .env.example ./.env.example

# Non-root user
RUN useradd -m appuser
USER appuser

ENV PYTHONPATH=/app/src

EXPOSE 8080
CMD ["uvicorn", "cvstack.api.app:app", "--host", "0.0.0.0", "--port", "8080"]