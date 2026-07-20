#!/usr/bin/env bash
# ---------------------------------------------------------------
# Banco POS — "Own Your Data" restore. Pull an encrypted backup from
# YOUR Backblaze B2 bucket and restore it into a fresh local Postgres.
# This is the continuity proof: with the repo + your B2 read key + the
# backup passphrase, you can stand the shop back up from zero.
#
# Backup format (what the box produces nightly):
#   banco_<env>_<timestamp>.sql.gz.gpg
#   = pg_dump  ->  gzip  ->  gpg --symmetric AES256
# Restore chain (this script):
#   b2 download  ->  gpg --decrypt  ->  gunzip  ->  psql
#
# PREREQS in .env (see .env.example, B2 section):
#   B2_KEY_ID, B2_APP_KEY   — a READ-ONLY B2 application key (not write/master)
#   B2_BUCKET               — your bucket name
#   BACKUP_GPG_PASSPHRASE   — passphrase for the .sql.gz.gpg (handed to you)
#
# Recommended order for a clean DR stand-up:
#   docker compose up -d postgres keycloak minio    # bring up infra, NOT the app
#   ./scripts/restore-from-b2.sh                     # restore real data
#   docker compose up -d app                         # app boots onto restored data
#   ./scripts/standup.sh                             # (re)apply the audit machine
#
# Usage:
#   ./scripts/restore-from-b2.sh                 # newest backup in the bucket
#   ./scripts/restore-from-b2.sh <exact-name>    # a specific .sql.gz.gpg
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

# Read specific keys from .env safely — the GPG passphrase & keys may contain shell
# metacharacters, so we NEVER `source` .env (a space or `$` would break or execute).
_env() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
B2_KEY_ID="$(_env B2_KEY_ID)"
B2_APP_KEY="$(_env B2_APP_KEY)"
B2_BUCKET="$(_env B2_BUCKET)"
BACKUP_GPG_PASSPHRASE="$(_env BACKUP_GPG_PASSPHRASE)"
PGUSER="$(_env POSTGRES_USER)"; PGUSER="${PGUSER:-helix_user}"
PGDB="$(_env POSTGRES_DB)"; PGDB="${PGDB:-helix_db}"
: "${B2_KEY_ID:?set B2_KEY_ID in .env}"
: "${B2_APP_KEY:?set B2_APP_KEY in .env}"
: "${B2_BUCKET:?set B2_BUCKET in .env}"
: "${BACKUP_GPG_PASSPHRASE:?set BACKUP_GPG_PASSPHRASE in .env}"

command -v b2  >/dev/null || { echo "❌ b2 CLI not found (pip install b2)"; exit 1; }
command -v gpg >/dev/null || { echo "❌ gpg not found"; exit 1; }

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

echo "🔑 Authorizing to B2 (read key)..."
b2 account authorize "$B2_KEY_ID" "$B2_APP_KEY" >/dev/null

NAME="${1:-}"
if [ -z "$NAME" ]; then
  echo "🔎 Finding newest *.sql.gz.gpg in b2://${B2_BUCKET} ..."
  # Newest by the YYYYMMDD_HHMM stamp IN THE FILENAME — a plain path sort would be
  # skewed by folder prefixes (e.g. banco/ vs sandbox/ vs staging/) and pick the
  # wrong stream. If your bucket mixes streams, pass an explicit filename instead.
  NAME="$(b2 ls --recursive "b2://${B2_BUCKET}" \
    | grep -E '\.sql\.gz\.gpg$' \
    | sed -E 's/.*_([0-9]{8}_[0-9]{4})\.sql\.gz\.gpg$/\1\t&/' \
    | sort | tail -1 | cut -f2-)"
  [ -n "$NAME" ] || { echo "❌ No .sql.gz.gpg found in bucket."; exit 1; }
fi
echo "📦 Restoring from: ${NAME}"

echo "⬇️  Downloading..."
b2 file download "b2://${B2_BUCKET}/${NAME}" "${WORK}/backup.sql.gz.gpg" >/dev/null

echo "♻️  Recreating a clean '${PGDB}' database..."
# terminate connections, drop, recreate — so the plain pg_dump restores without conflict
docker compose exec -T postgres psql -U "$PGUSER" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${PGDB}' AND pid<>pg_backend_pid();
DROP DATABASE IF EXISTS ${PGDB};
CREATE DATABASE ${PGDB} OWNER ${PGUSER};
SQL

echo "🔓 Decrypt → gunzip → restore..."
gpg --batch --quiet --pinentry-mode loopback \
    --passphrase "$BACKUP_GPG_PASSPHRASE" \
    --decrypt "${WORK}/backup.sql.gz.gpg" \
  | gunzip \
  | docker compose exec -T postgres psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 >/dev/null

echo "✅ Restore complete → ${PGDB}"
echo "   Row check:"
docker compose exec -T postgres psql -U "$PGUSER" -d "$PGDB" -tc \
  "SELECT 'products='||count(*) FROM products;" 2>/dev/null || true
echo "Next:  docker compose up -d app   &&   ./scripts/standup.sh"
