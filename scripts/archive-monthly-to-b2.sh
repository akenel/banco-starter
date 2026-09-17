#!/usr/bin/env bash
# archive-monthly-to-b2.sh — keep ONE backup a month, for ever.
#
# WHY THIS EXISTS
# ---------------
# 2026-09-17. The bucket had 613 files and 4.23 GB in it, going back to 20 July,
# because nothing ever deleted anything. The fix for that is a B2 lifecycle rule
# — but a rule that keeps only the last 90 days answers "the disk died last
# night" and does NOT answer "something was quietly wrong in March".
#
# So: dailies expire on the lifecycle rule under `banco/`, and this script copies
# ONE night a month into `archive/monthly/`, which NO rule touches. That is the
# ordinary grandfather-father-son shape, and for this shop it costs about 9 MB a
# month — twelve dumps a year, roughly 100 MB. Pennies, and it is the difference
# between a backup policy and a real one.
#
# It is a SERVER-SIDE COPY: B2 duplicates the object itself. Nothing is
# downloaded, nothing is re-encrypted, and the archived file is byte-identical to
# the backup that was verified that night.
#
# RUN   ./scripts/archive-monthly-to-b2.sh          (cron: 0 4 1 * *)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "❌ no .env beside the repo root"; exit 1; }
set -a; . ./.env; set +a
: "${B2_BUCKET:?B2_BUCKET not set in .env}"
B2="${B2_BIN:-$HOME/.local/bin/b2}"
[ -x "$B2" ] || B2="$(command -v b2 || true)"
[ -n "$B2" ] || { echo "❌ b2 CLI not found — see onboarding/06-own-your-data-backups.md"; exit 1; }

"$B2" account authorize "$B2_KEY_ID" "$B2_APP_KEY" >/dev/null

echo "📦 Monthly archive — $(date -u '+%Y-%m-%d %H:%M UTC')"
copied=0
# The DB and the logins BOTH matter: a restored catalogue nobody can log into is
# not a restored shop.
for kind in helix_db keycloak; do
  newest="$("$B2" ls --recursive "b2://${B2_BUCKET}/banco/" 2>/dev/null \
            | grep -E "banco_${kind}_[0-9]{8}_[0-9]{6}\.sql\.gz\.gpg$" | sort | tail -1)"
  if [ -z "$newest" ]; then
    echo "   ⚠️  no ${kind} backup found under banco/ — nothing to archive"
    continue
  fi
  base="$(basename "$newest")"
  dest="archive/monthly/${base}"
  if "$B2" ls "b2://${B2_BUCKET}/${dest}" 2>/dev/null | grep -q .; then
    echo "   ↩︎  ${base} already archived"
    continue
  fi
  "$B2" file server-side-copy "b2://${B2_BUCKET}/${newest}" "b2://${B2_BUCKET}/${dest}" >/dev/null
  echo "   ✅ ${base} → ${dest}"
  copied=$((copied + 1))
done
echo "📦 Done — ${copied} archived. These are kept FOR EVER: no lifecycle rule matches archive/."
