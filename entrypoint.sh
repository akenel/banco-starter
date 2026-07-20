#!/usr/bin/env bash
# ---------------------------------------------------------------
# Banco POS starter entrypoint — minimal profile.
# Waits ONLY for Postgres (the one hard dependency at web-serve time).
# Redis/RabbitMQ are not part of the minimal profile; Celery is off, so
# nothing on the /pos request path needs a broker. Keycloak is soft at
# boot (the app defers its realm health check) and is required only when
# a user actually logs in.
# ---------------------------------------------------------------
set -euo pipefail

PGHOST="${POSTGRES_HOST:-postgres}"
PGPORT="${POSTGRES_PORT:-5432}"

echo "⏳ Waiting for Postgres (${PGHOST}:${PGPORT})..."
until nc -z "${PGHOST}" "${PGPORT}"; do
  echo "  waiting for postgres..."
  sleep 1
done
echo "✅ Postgres is up."

echo "🦄 Starting Banco POS (FastAPI)..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
