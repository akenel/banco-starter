#!/usr/bin/env bash
# ---------------------------------------------------------------
# Banco POS — encrypted offsite backup of the PRODUCT PHOTOS (MinIO).
#
# backup-to-b2.sh saves the DATABASES. This saves the IMAGES the product rows
# point at — the half a pg_dump can't see. Same chain, same discipline:
#   tar (read-only) -> gzip -> gpg --symmetric AES256 -> b2 upload
# Result: banco/media/banco_media_<timestamp>.tar.gz.gpg in your bucket.
#
# INDEPENDENT of the DB backup on purpose: a media failure never breaks the DB
# backup, and the MinIO volume is mounted READ-ONLY so this can never corrupt
# live storage. Add a nightly cron line next to backup-to-b2.sh.
#
# SKIP_B2=1 makes + verifies the encrypted archive locally but does NOT upload —
# for testing the chain in a sandbox without real B2 credentials.
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

_env() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
B2_KEY_ID="$(_env B2_KEY_ID)"
B2_APP_KEY="$(_env B2_APP_KEY)"
B2_BUCKET="$(_env B2_BUCKET)"
BACKUP_GPG_PASSPHRASE="$(_env BACKUP_GPG_PASSPHRASE)"
: "${BACKUP_GPG_PASSPHRASE:?set BACKUP_GPG_PASSPHRASE in .env}"
command -v gpg >/dev/null || { echo "❌ gpg not found"; exit 1; }
if [ "${SKIP_B2:-0}" != 1 ]; then
  : "${B2_KEY_ID:?set B2_KEY_ID in .env}"
  : "${B2_APP_KEY:?set B2_APP_KEY in .env}"
  : "${B2_BUCKET:?set B2_BUCKET in .env}"
  command -v b2 >/dev/null || { echo "❌ b2 CLI not found — install it: pipx install b2"; exit 1; }
fi

# Optional dead-man's switch (see backup-to-b2.sh). Never fatal; no-op if unset.
HC="$(_env HEALTHCHECK_PING_URL)"
_ping(){ [ -n "$HC" ] && command -v curl >/dev/null 2>&1 && curl -fsS -m 10 "$1" >/dev/null 2>&1 || true; }

TS="$(date +%Y%m%d_%H%M%S)"
NAME="banco_media_${TS}.tar.gz.gpg"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"; [ "${DONE:-0}" = 1 ] || _ping "$HC/fail"' EXIT
_ping "$HC/start"
FILE="${WORK}/${NAME}"

# Find the MinIO data volume behind the running `minio` service — project-agnostic
# (works whether the compose project is banco-starter, a sandbox, whatever).
MC="$(docker compose ps -q minio)"
[ -n "$MC" ] || { echo "❌ minio service not running — 'docker compose up -d minio' first"; exit 1; }
VOL="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$MC")"
[ -n "$VOL" ] || { echo "❌ could not find the MinIO /data volume"; exit 1; }

echo "📷 Archiving MinIO photos (volume ${VOL}, READ-ONLY) → gzip → encrypt (AES256)..."
docker run --rm -v "${VOL}:/data:ro" alpine sh -c 'cd /data && tar -czf - .' 2>/dev/null \
  | gpg --batch --yes --symmetric --cipher-algo AES256 \
        --pinentry-mode loopback --passphrase "$BACKUP_GPG_PASSPHRASE" -o "$FILE"
[ -s "$FILE" ] || { echo "❌ media archive came out empty (tar/gpg failed)"; exit 1; }
echo "   made ${NAME} ($(du -h "$FILE" | cut -f1), encrypted)"

# Integrity check: decrypt + count entries, so a silently-broken archive is caught.
N="$(gpg --batch --quiet --decrypt --pinentry-mode loopback \
       --passphrase "$BACKUP_GPG_PASSPHRASE" "$FILE" 2>/dev/null | tar -tzf - 2>/dev/null | wc -l)"
echo "   verified: ${N} entries recover from the encrypted archive"

if [ "${SKIP_B2:-0}" = 1 ]; then
  cp "$FILE" "/tmp/${NAME}"
  echo "   ⏭️  SKIP_B2=1 — kept at /tmp/${NAME}, not uploaded"
else
  echo "🔑 Authorizing to B2..."
  b2 account authorize "$B2_KEY_ID" "$B2_APP_KEY" >/dev/null
  echo "⬆️  Uploading to b2://${B2_BUCKET}/banco/media/${NAME} ..."
  b2 file upload "$B2_BUCKET" "$FILE" "banco/media/${NAME}" >/dev/null
  echo "✅ Media backup in B2: banco/media/${NAME}"
fi
_ping "$HC"
DONE=1
