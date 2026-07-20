#!/usr/bin/env bash
# ---------------------------------------------------------------
# Banco POS — post-boot stand-up: wait for the app, then apply the
# audit-log machine (triggers + audit_log table). The app schema
# itself auto-creates on first boot (Base.metadata.create_all), so
# all this adds is the who/when/what change-log.
# Idempotent — safe to re-run.
#
# Usage:  ./scripts/standup.sh
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

# Read specific keys from .env safely (values may contain spaces/specials — never `source` it)
_env() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
PGUSER="$(_env POSTGRES_USER)"; PGUSER="${PGUSER:-helix_user}"
PGDB="$(_env POSTGRES_DB)"; PGDB="${PGDB:-helix_db}"
APP_HOST_PORT="$(_env APP_HOST_PORT)"; APP_HOST_PORT="${APP_HOST_PORT:-8000}"
APP_URL="http://localhost:${APP_HOST_PORT}/health/healthz"

echo "⏳ Waiting for the app to answer ${APP_URL} ..."
for i in $(seq 1 60); do
  if curl -fsS "${APP_URL}" >/dev/null 2>&1; then
    echo "✅ App is up."
    break
  fi
  sleep 3
  if [ "$i" = 60 ]; then echo "❌ App did not become healthy in time." >&2; exit 1; fi
done

echo "🧱 Applying the audit-log machine (scripts/db/audit_log_setup.sql) → ${PGDB} ..."
docker compose exec -T postgres \
  psql -U "${PGUSER}" -d "${PGDB}" -v ON_ERROR_STOP=1 \
  < scripts/db/audit_log_setup.sql

echo "✅ Audit log installed. Change-log cockpit: http://localhost:${APP_HOST_PORT}/pos/audit"

# Final gate: the post-boot smoke test pokes the LIVE stack (containers, app health,
# Keycloak realm, seeded catalog) and prints one plain verdict — "✅ SAFE TO TEST →
# open <url>, log in pam/pam" or "❌ NOT READY → fix this". Non-fatal (|| true) so the
# verdict always shows even when a check is red; re-run any time: python3 scripts/postboot-check.py
python3 scripts/postboot-check.py || true
