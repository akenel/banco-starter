#!/usr/bin/env bash
# ============================================================================
# prod-query — READ-ONLY SQL against Felix's live shop (ssh banco).
#
#   ./scripts/prod-query.sh -c "SELECT count(*) FROM products"
#   ./scripts/prod-query.sh < some.sql
#   ./scripts/prod-query.sh --csv -c "SELECT sku, name FROM products LIMIT 20"
#
# WHY THIS FILE EXISTS. Angel, 2026-08-28: "IMHO you should have access to prod
# can we change that now so you can do the look ups." He is right that the
# copilot cannot answer questions about the catalogue without seeing it. But
# `banco` is a real business's till taking real money, and it is the one box in
# the estate where a mistake lands on somebody who is not Angel.
#
# So the access is the NARROW shape, not the wide one: this script is the only
# allowlisted route to that database, and the database itself refuses to write.
#
# THE GUARD IS THE DATABASE, NOT THIS SCRIPT.
#   PGOPTIONS='-c default_transaction_read_only=on' makes Postgres reject every
#   INSERT / UPDATE / DELETE / TRUNCATE / CREATE / ALTER / DROP with
#   "cannot execute ... in a read-only transaction" — server-side, before the
#   statement runs. A regex over SQL text would be a guard I could fool with a
#   comment or a newline; this one cannot be talked out of it. The text checks
#   below are a courtesy that fails loudly and early, NOT the protection.
#
# NOT COVERED, honestly: a superuser connection could still reach COPY TO
# PROGRAM or pg_read_file. If that matters, move to the banco_ro role option
# (SELECT granted on the catalogue tables only) — see PROD-ACCESS.md.
# ============================================================================
set -euo pipefail

HOST="banco"
REMOTE_DIR="/root/banco-starter"
PSQL_FMT=(-P pager=off)
SQL=""

while [ $# -gt 0 ]; do
  case "$1" in
    -c|--command) SQL="${2:-}"; shift 2 ;;
    --csv)  PSQL_FMT=(-P pager=off --csv); shift ;;
    --tsv)  PSQL_FMT=(-P pager=off -tA -F $'\t'); shift ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "prod-query: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

[ -n "$SQL" ] || SQL="$(cat)"
[ -n "${SQL//[[:space:]]/}" ] || { echo "prod-query: no SQL given" >&2; exit 2; }

# Courtesy check — fail here with a clear message rather than get a Postgres
# error 400ms later. Deliberately crude: the real refusal happens server-side.
if printf '%s' "$SQL" | grep -Eiq '(^|[^[:alnum:]_])(insert|update|delete|truncate|drop|alter|create|grant|revoke|reindex|vacuum|refresh[[:space:]]+materialized)([^[:alnum:]_]|$)'; then
  echo "prod-query: this is the READ-ONLY route to a live till — writes are not sent." >&2
  echo "            (the server would refuse them too; this just says so sooner)" >&2
  exit 3
fi

exec ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST" \
  "cd $REMOTE_DIR && set -a && . ./.env 2>/dev/null; set +a; \
   CID=\$(docker compose ps -q postgres 2>/dev/null); \
   [ -n \"\$CID\" ] || CID=\$(docker ps --filter name=postgres --format '{{.ID}}' | head -1); \
   [ -n \"\$CID\" ] || { echo 'prod-query: no postgres container found on banco' >&2; exit 4; }; \
   docker exec -i -e PGOPTIONS='-c default_transaction_read_only=on' \
     \"\$CID\" psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -v ON_ERROR_STOP=1 $(printf '%q ' "${PSQL_FMT[@]}")" \
  <<< "$SQL"
