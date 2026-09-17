#!/usr/bin/env bash
# ---------------------------------------------------------------
# install-backup-cron — schedule the nightly encrypted backup (idempotent).
# Adds a cron job that runs backup-to-b2.sh every night, so the shop backs itself
# up without anyone remembering. Safe to run repeatedly — it replaces its own line,
# never duplicates, and leaves your other cron jobs untouched.
#
#   ./scripts/install-backup-cron.sh        # 03:00 daily (default)
#   ./scripts/install-backup-cron.sh 4      # 04:00 daily
#
# Pair it with HEALTHCHECK_PING_URL in .env (a healthchecks.io check) so a run that
# silently STOPS alerts you — a backup you don't know has stopped is not a backup.
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$(pwd)"

HOUR="${1:-3}"
case "$HOUR" in ''|*[!0-9]*) echo "❌ hour must be a number 0–23 (got '$HOUR')"; exit 1;; esac
[ "$HOUR" -ge 0 ] && [ "$HOUR" -le 23 ] || { echo "❌ hour must be 0–23"; exit 1; }

[ -x "$REPO/scripts/backup-to-b2.sh" ] || { echo "❌ scripts/backup-to-b2.sh missing or not executable"; exit 1; }

_env() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
if [ -z "$(_env B2_KEY_ID)" ] || [ -z "$(_env BACKUP_GPG_PASSPHRASE)" ]; then
  echo "⚠️  B2 isn't fully configured in .env yet — the cron will fail until it is."
  echo "    Wire it: python3 scripts/init-banco.py  (or  rotate-secret.py b2)"
fi
if [ -z "$(_env HEALTHCHECK_PING_URL)" ]; then
  echo "💡 No HEALTHCHECK_PING_URL set — the backup will run, but nothing watches whether it"
  echo "   STOPS. Create a check at healthchecks.io (one per box), put its ping URL in .env,"
  echo "   and you'll get alerted if a night is ever missed."
fi

MARK="# banco-nightly-backup (managed by install-backup-cron.sh)"
LINE="0 ${HOUR} * * * cd ${REPO} && ./scripts/backup-to-b2.sh >> ${REPO}/backup.log 2>&1"

# ── THE OTHER TWO SCHEDULES (added 2026-09-17) ───────────────────────────────
# This installer used to manage ONE line, so the media and archive jobs were
# whatever somebody had typed by hand — which is how a schedule drifts. All three
# live here now, and a shop that clones this gets the whole policy, not a third
# of it.
#
# MEDIA IS WEEKLY, NOT NIGHTLY, and that is the single biggest saving. Measured on
# the live shop: 105 MB EVERY NIGHT for a photo volume that barely changes — 2.80 GB
# of a 4.23 GB bucket. Weekly cuts the growth about sevenfold and loses nothing that
# matters: photos that appear on Tuesday are in Sunday's archive, and MinIO still
# holds the originals.
MEDIA_LINE="15 ${HOUR} * * 0 cd ${REPO} && ./scripts/backup-media-to-b2.sh >> ${REPO}/backup.log 2>&1"
# MONTHLY keeps one night for ever, outside the lifecycle rule. The rule answers
# "the disk died last night"; this answers "something was quietly wrong in March".
ARCH_LINE="0 $(( (HOUR + 1) % 24 )) 1 * * cd ${REPO} && ./scripts/archive-monthly-to-b2.sh >> ${REPO}/backup.log 2>&1"

# Idempotent: drop any previous banco backup lines (the marker + the commands), then re-add.
current="$(crontab -l 2>/dev/null || true)"
cleaned="$(printf '%s\n' "$current" | grep -vF "$MARK" \
           | grep -vF "scripts/backup-to-b2.sh" \
           | grep -vF "scripts/backup-media-to-b2.sh" \
           | grep -vF "scripts/archive-monthly-to-b2.sh" || true)"
{ printf '%s\n' "$cleaned" | sed '/^$/d'
  printf '%s\n%s\n' "$MARK" "$LINE"
  [ -x "$REPO/scripts/backup-media-to-b2.sh" ]    && printf '%s\n' "$MEDIA_LINE"
  [ -x "$REPO/scripts/archive-monthly-to-b2.sh" ] && printf '%s\n' "$ARCH_LINE"
  true
} | crontab -

printf "\n✅ Backup schedule installed:\n"
printf "   %02d:00 daily      → backup-to-b2.sh         (database + logins)\n" "$HOUR"
[ -x "$REPO/scripts/backup-media-to-b2.sh" ]    && printf "   %02d:15 SUNDAYS    → backup-media-to-b2.sh   (photos — weekly on purpose)\n" "$HOUR"
[ -x "$REPO/scripts/archive-monthly-to-b2.sh" ] && printf "   %02d:00 on the 1st → archive-monthly-to-b2.sh (kept for ever)\n" "$(( (HOUR + 1) % 24 ))"
echo "   see it:   crontab -l"
echo "   its log:  ${REPO}/backup.log"
echo
echo "💡 Dailies expire on the bucket's LIFECYCLE RULE (90 days is sensible); the monthly"
echo "   archive sits under archive/ where no rule matches it. See onboarding/06."

echo "   test now: ./scripts/backup-to-b2.sh   (should upload one + green your healthcheck)"
