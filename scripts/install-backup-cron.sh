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

# Idempotent: drop any previous banco backup lines (the marker + the command), then re-add.
current="$(crontab -l 2>/dev/null || true)"
cleaned="$(printf '%s\n' "$current" | grep -vF "$MARK" | grep -vF "scripts/backup-to-b2.sh" || true)"
{ printf '%s\n' "$cleaned" | sed '/^$/d'; printf '%s\n%s\n' "$MARK" "$LINE"; } | crontab -

printf "\n✅ Nightly backup scheduled: %02d:00 every day → backup-to-b2.sh\n" "$HOUR"
echo "   see it:   crontab -l"
echo "   its log:  ${REPO}/backup.log"
echo "   test now: ./scripts/backup-to-b2.sh   (should upload one + green your healthcheck)"
