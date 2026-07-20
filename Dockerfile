# ---------------------------------------------------------------
# Banco POS — application image (FastAPI + SQLAlchemy async)
# Single-stage, slim. Frontend deps are vendored in src/static/vendor,
# so there is NO node build step and NO node_modules at runtime.
# ---------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:${PATH}" \
    PYTHONPATH="/app"

# Install deps first (layer-cached) — libpq for psycopg/asyncpg, netcat for the wait loop
COPY requirements.txt /app/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      netcat-openbsd \
      build-essential \
      libpq-dev \
    && python -m venv /app/venv \
    && /app/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# App source
COPY src /app/src
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
