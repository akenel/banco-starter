#!/usr/bin/env bash
# ---------------------------------------------------------------
# Banco POS — make an encrypted backup and push it to YOUR Backblaze B2.
# The other half of "own your data": this CREATES backups; restore-from-b2.sh
# brings them back. Run it nightly (cron) or by hand before risky changes.
#
# Chain:  pg_dump  ->  gzip  ->  gpg --symmetric AES256  ->  b2 upload
# Result: banco/banco_<db>_<timestamp>.sql.gz.gpg in your bucket.
#
# PREREQS in .env (see .env.example, B2 section):
#   B2_KEY_ID, B2_APP_KEY   — a B2 application key WITH WRITE access (writeFiles)
#   B2_BUCKET               — your bucket name
#   BACKUP_GPG_PASSPHRASE   — the passphrase your backups are encrypted with
#                             (KEEP IT SAFE — without it, backups can't be restored)
#
# Usage:  ./scripts/backup-to-b2.sh
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

# Read specific keys from .env safely (never `source` — values may contain specials)
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

TS="$(date +%Y%m%d_%H%M%S)"
NAME="banco_${PGDB}_${TS}.sql.gz.gpg"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
FILE="${WORK}/${NAME}"

echo "🗄️  Dumping ${PGDB} → gzip → encrypt (AES256)..."
docker compose exec -T postgres pg_dump -U "$PGUSER" "$PGDB" \
  | gzip \
  | gpg --batch --yes --symmetric --cipher-algo AES256 \
        --pinentry-mode loopback --passphrase "$BACKUP_GPG_PASSPHRASE" \
        -o "$FILE"
SIZE="$(du -h "$FILE" | cut -f1)"
echo "   made ${NAME} (${SIZE}, encrypted)"

echo "🔑 Authorizing to B2..."
b2 account authorize "$B2_KEY_ID" "$B2_APP_KEY" >/dev/null

echo "⬆️  Uploading to b2://${B2_BUCKET}/banco/${NAME} ..."
b2 file upload "$B2_BUCKET" "$FILE" "banco/${NAME}" >/dev/null

echo "✅ Backup in B2: banco/${NAME}"
echo "   Restore any time with:  ./scripts/restore-from-b2.sh"
