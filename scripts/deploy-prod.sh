#!/usr/bin/env bash
# ---------------------------------------------------------------
# Banco POS — production deploy, the safe way (backup first, check after).
# The same discipline as the reference shop: never touch prod without a fresh
# backup, and never trust "it started" — prove it's actually serving.
#
#   ./scripts/deploy-prod.sh
#
# Steps:
#   1. BACKUP first (encrypted → your B2). If that fails, we stop — nothing changed.
#   2. Build (stamped with the real commit) + start the prod stack (app + Caddy +
#      Keycloak in production mode).
#   3. GATE — app is up AND the login screen's build stamp matches this commit
#      (postboot-check.py). A restart that kept old code passes health but fails this.
#   4. GATE — HTTPS is actually serving on your public domain.
#
# Run go-live.py once first (it writes .env + ./Caddyfile). Re-run this any time you
# `git pull` new code.
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

_env() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }

if [ ! -f Caddyfile ]; then
  echo "❌ No ./Caddyfile — run  python3 scripts/go-live.py  first." >&2
  exit 1
fi

echo "🛟 1/4 — Backup first (before touching anything)"
if [ -n "$(_env B2_KEY_ID)" ] && [ -n "$(_env B2_APP_KEY)" ] && [ -n "$(_env BACKUP_GPG_PASSPHRASE)" ]; then
  if ! ./scripts/backup-to-b2.sh; then
    echo "❌ Backup failed — ABORTING the deploy. Nothing was changed." >&2
    exit 1
  fi
else
  echo "⚠️  B2 not configured — skipping backup. STRONGLY recommended before prod (guide 06)."
  read -r -p "   Deploy without a backup? [y/N] " ans
  case "${ans:-n}" in y|Y|yes) ;; *) echo "Stopped. Wire B2 first: python3 scripts/init-banco.py"; exit 1;; esac
fi

echo "🔖 2/4 — Build (stamped) + start the production stack"
if git rev-parse --git-dir >/dev/null 2>&1; then
  export GIT_SHA="$(git rev-parse --short HEAD)"
  export GIT_DATE="$(git show -s --format=%cI HEAD)"
  export GIT_COUNT="$(git rev-list --count HEAD)"
  echo "   commit ${GIT_SHA} (b${GIT_COUNT})"
fi
docker compose -f compose.yml -f compose.prod.yml up -d --build

echo "🔑 2b/4 — Teach Keycloak your production URL (or login gets 'Invalid redirect_uri')"
./scripts/kc-set-redirect.py || {
  echo "❌ Could not set the production redirect URI in Keycloak — login would fail." >&2
  echo "   Fix + retry:  ./scripts/kc-set-redirect.py" >&2
  exit 1
}

if [ -n "$(_env SMTP_PASSWORD)" ]; then
  echo "📧 2c/4 — Wire Keycloak email through Resend"
  ./scripts/kc-set-smtp.py || echo "⚠️  Email wiring failed — password resets won't send until fixed (./scripts/kc-set-smtp.py). Continuing."
fi

echo "🔍 3/4 — Gate: is the app really up (health + build stamp)?"
if ! ./scripts/postboot-check.py; then
  echo "❌ app-gate failed — the new code is NOT serving. Check: docker compose logs app" >&2
  exit 1
fi

echo "🌐 4/4 — Gate: is HTTPS live on the public domain?"
APP_HOST="$(_env APP_PUBLIC_HOST)"
if [ -z "$APP_HOST" ]; then
  echo "⚠️  APP_PUBLIC_HOST not set — run go-live.py. Skipping the HTTPS check."
elif curl -fsS --max-time 15 "https://${APP_HOST}/health/healthz" >/dev/null 2>&1; then
  echo "✅ https://${APP_HOST} is live and healthy."
else
  echo "⚠️  https://${APP_HOST} isn't answering yet. Usually one of:"
  echo "      • Caddy is still fetching the Let's Encrypt cert (~1 min on first boot)"
  echo "      • DNS hasn't propagated (the A record is new)"
  echo "      • the firewall isn't allowing 443"
  echo "    Re-check in a minute:  curl -I https://${APP_HOST}/pos"
fi

echo
echo "✅ Deploy done. Shop: https://${APP_HOST:-<set APP_PUBLIC_HOST>}"
