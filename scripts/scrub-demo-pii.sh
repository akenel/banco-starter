#!/usr/bin/env bash
# ---------------------------------------------------------------
# scrub-demo-pii — make a restored PRODUCTION database safe to demo.
#
# Restoring a real prod backup gives you the impressive full catalog,
# but it also carries real MEMBER identities and real SUPPLIER COSTS.
# This strips those (anonymizes members, blanks costs/margins) while
# keeping products, prices, photos, and loyalty data intact — so the
# showroom looks alive without leaking anyone's name or your margins.
#
# Run it right AFTER restore-from-b2.sh and BEFORE you hand out a login:
#   ./scripts/restore-from-b2.sh          # pull + restore real prod data
#   ./scripts/scrub-demo-pii.sh           # <-- make it demo-safe
#   docker compose up -d app && ./scripts/standup.sh
#
# It runs scripts/db/scrub-demo-pii.sql inside the postgres container.
# Idempotent — safe to run again. Only touches a DEMO box; never run it
# on the real shop's database.
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

# Read specific keys from .env safely (never `source` it — values may hold
# shell metacharacters). Same helper the backup/restore scripts use.
_env() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
PGUSER="$(_env POSTGRES_USER)"; PGUSER="${PGUSER:-helix_user}"
PGDB="$(_env POSTGRES_DB)";     PGDB="${PGDB:-helix_db}"

SQL="scripts/db/scrub-demo-pii.sql"
[ -f "$SQL" ] || { echo "❌ $SQL not found"; exit 1; }

echo "🧽 Scrubbing DEMO PII from '${PGDB}' (members anonymized, costs/margins blanked)…"
echo "   Products, prices, photos, loyalty tiers are KEPT."

# Guard: make sure the DB is actually reachable before we claim success.
docker compose exec -T postgres psql -U "$PGUSER" -d "$PGDB" -tc "SELECT 1;" >/dev/null \
  || { echo "❌ Can't reach postgres/${PGDB}. Is the stack up? (docker compose up -d postgres)"; exit 1; }

docker compose exec -T postgres psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 -f - < "$SQL"

echo
echo "✅ Scrub complete. The table above should read 0 in the real_names_left /"
echo "   trade_discount / cost / supplier_price columns."
echo "   Safe to demo: refresh /pos → real catalog, no real names, no margins."
