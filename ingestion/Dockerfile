FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY sources ./sources
COPY transform ./transform
COPY load ./load
COPY embed ./embed
COPY pipelines ./pipelines
RUN pip install -e .

COPY . .

# No long-running process — this image is invoked on demand, e.g.:
#   docker compose run --rm ingestion python -m pipelines.backfill
CMD ["python", "-c", "print('ingestion image ready — run a pipeline module, e.g. python -m pipelines.backfill')"]
