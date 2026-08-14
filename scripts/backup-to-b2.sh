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

# pipx installs the b2 CLI to ~/.local/bin, which is NOT on PATH in a fresh shell (before
# `pipx ensurepath` takes effect) or in cron (minimal PATH). Add it so `b2` is found whether
# this runs by hand, from deploy-prod.sh, or from the nightly cron. The #1 "b2 not found" trap.
export PATH="$HOME/.local/bin:$PATH"

# Read specific keys from .env safely (never `source` — values may contain specials)
_env() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
B2_KEY_ID="$(_env B2_KEY_ID)"
B2_APP_KEY="$(_env B2_APP_KEY)"
B2_BUCKET="$(_env B2_BUCKET)"
BACKUP_GPG_PASSPHRASE="$(_env BACKUP_GPG_PASSPHRASE)"
PGUSER="$(_env POSTGRES_USER)"; PGUSER="${PGUSER:-helix_user}"
PGDB="$(_env POSTGRES_DB)"; PGDB="${PGDB:-helix_db}"
: "${BACKUP_GPG_PASSPHRASE:?set BACKUP_GPG_PASSPHRASE in .env}"
command -v gpg >/dev/null || { echo "❌ gpg not found"; exit 1; }

# --local-only: make the encrypted dumps and keep them ON THIS BOX, no upload.
# Added 2026-08-14, for the day the offsite leg is down for a reason that has nothing to do
# with the data — a storage cap, an expired key, Backblaze having a bad afternoon. Without it,
# a BILLING problem stops the shop deploying a security fix, which is the wrong trade.
# A local copy dies with the machine. It is still the difference between rolling a bad deploy
# back in ten minutes and not being able to.
if [ "${1:-}" = "--local-only" ]; then SKIP_B2=1; LOCAL_ONLY=1; fi

# SKIP_B2=1 makes + verifies the encrypted dumps locally but does NOT upload —
# for testing the chain in a sandbox without real B2 credentials.
if [ "${SKIP_B2:-0}" != 1 ]; then
  : "${B2_KEY_ID:?set B2_KEY_ID in .env}"
  : "${B2_APP_KEY:?set B2_APP_KEY in .env}"
  : "${B2_BUCKET:?set B2_BUCKET in .env}"
  command -v b2 >/dev/null || { echo "❌ b2 CLI not found — install it: pipx install b2"; exit 1; }
fi

# Optional dead-man's switch. Set HEALTHCHECK_PING_URL in .env (a healthchecks.io
# check URL) and this pings /start now, the bare URL on SUCCESS, and /fail if anything
# below errors — so you get ALERTED when a nightly backup silently stops running (a
# backup you don't know has stopped is not a backup). Never fatal; no-op if unset.
HC="$(_env HEALTHCHECK_PING_URL)"
_ping(){ [ -n "$HC" ] && command -v curl >/dev/null 2>&1 && curl -fsS -m 10 "$1" >/dev/null 2>&1 || true; }

TS="$(date +%Y%m%d_%H%M%S)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"; [ "${DONE:-0}" = 1 ] || _ping "$HC/fail"' EXIT
_ping "$HC/start"

# Authorize to B2 once for the whole run (skipped in sandbox test mode).
if [ "${SKIP_B2:-0}" != 1 ]; then
  echo "🔑 Authorizing to B2..."
  b2 account authorize "$B2_KEY_ID" "$B2_APP_KEY" >/dev/null
fi

# Dump ONE database → gzip → encrypt → (upload | keep locally). Used for both
# the POS data AND Keycloak: a restore that brings back the products but not the
# logins is a shop nobody can sign into. Keycloak lives in its own `keycloak` DB
# (compose: KC_DB_URL .../keycloak) — the old single-DB backup silently skipped it.
dump_and_ship() {
  local db="$1" name file
  name="banco_${db}_${TS}.sql.gz.gpg"
  file="${WORK}/${name}"
  echo "🗄️  Dumping ${db} → gzip → encrypt (AES256)..."
  docker compose exec -T postgres pg_dump -U "$PGUSER" "$db" \
    | gzip \
    | gpg --batch --yes --symmetric --cipher-algo AES256 \
          --pinentry-mode loopback --passphrase "$BACKUP_GPG_PASSPHRASE" \
          -o "$file"
  [ -s "$file" ] || { echo "❌ dump of ${db} produced nothing"; return 1; }
  echo "   made ${name} ($(du -h "$file" | cut -f1), encrypted)"
  if [ "${SKIP_B2:-0}" = 1 ]; then
    # NOT /tmp for a real local backup — /tmp is cleared on reboot, and the reboot is
    # exactly when you want the file. ./backups is gitignored and survives.
    if [ "${LOCAL_ONLY:-0}" = 1 ]; then
      mkdir -p ./backups
      cp "$file" "./backups/${name}"
      echo "   💾 kept LOCALLY at ./backups/${name} — this box only, NOT offsite"
    else
      cp "$file" "/tmp/${name}"
      echo "   ⏭️  SKIP_B2=1 — kept at /tmp/${name}, not uploaded"
    fi
  else
    echo "⬆️  Uploading to b2://${B2_BUCKET}/banco/${name} ..."
    b2 file upload "$B2_BUCKET" "$file" "banco/${name}" >/dev/null
    echo "   ✅ in B2: banco/${name}"
  fi
}

dump_and_ship "$PGDB"       # the POS database
dump_and_ship keycloak      # staff logins — NEW: was silently missing

_ping "$HC"        # tell the dead-man's switch this run succeeded
DONE=1
if [ "${LOCAL_ONLY:-0}" = 1 ]; then
  echo "✅ LOCAL backups complete: ${PGDB} + keycloak, in ./backups/"
  echo "   ⚠️  On this machine only. Get the offsite leg working again:"
  echo "      https://secure.backblaze.com  →  Buckets / Caps & Alerts"
else
  echo "✅ Backups complete: ${PGDB} + keycloak."
fi
echo "   Restore any time with:  ./scripts/restore-from-b2.sh"
