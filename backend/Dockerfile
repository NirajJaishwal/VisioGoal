FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps occasionally needed by scientific wheels; kept minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching. The `[dev]` extra brings
# in ruff + pytest so `docker compose exec backend ruff check .` / `pytest` work
# in this development image — with a plain `pip install -e .` they are absent
# from $PATH and those commands fail with "executable file not found".
COPY pyproject.toml ./
COPY app ./app
RUN pip install -e ".[dev]"

COPY . .

EXPOSE 8000

# app.main:app is added in the next phase.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
