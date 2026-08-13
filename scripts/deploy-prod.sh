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

# PREFLIGHT — a sandbox default must never reach production.
# 2026-08-13: compose.yml gained KC_HOSTNAME_URL for the sandbox, compose.prod.yml is an
# OVERLAY on it, and KC_HOSTNAME_URL takes precedence over KC_HOSTNAME in Keycloak. For one
# commit, deploying would have made production issue every token for http://localhost:8090
# and broken every login — silently, because the containers start fine.
#
# Checks the REAL merged config, and rejects EMPTY as well as local. The first version of
# this guard only grepped for "localhost" and passed happily on `https://` with the host
# unset — found by running it with KC_PUBLIC_HOST deliberately missing, which is the only
# reason it is written this way.
echo "🔎 1b/4 — Preflight: Keycloak's public URL is real"
docker compose -f compose.yml -f compose.prod.yml config 2>/dev/null | python3 -c '
import sys, yaml
try:
    env = yaml.safe_load(sys.stdin)["services"]["keycloak"].get("environment", {}) or {}
except Exception as e:
    print(f"   could not resolve the compose config: {e}"); sys.exit(1)
bad = []
for key in ("KC_HOSTNAME", "KC_HOSTNAME_URL"):
    val = (env.get(key) or "").strip()
    host = val.split("://", 1)[-1].strip("/")
    if not host:
        bad.append(f"{key} is EMPTY ({val!r}) — set KC_PUBLIC_HOST in .env")
    elif any(x in host.lower() for x in ("localhost", "127.0.0.1", ".local")):
        bad.append(f"{key} points at a sandbox address: {val}")
for b in bad:
    print("   " + b)
sys.exit(1 if bad else 0)
' || {
  echo "❌ Production would issue tokens for that address and EVERY login would fail." >&2
  echo "   → python3 scripts/go-live.py   (writes KC_PUBLIC_HOST + POS_KC_PUBLIC_URL)" >&2
  exit 1
}
echo "   ✅ Keycloak's public URL is a real host."

echo "🔖 2/4 — Build (stamped) + start the production stack"
if git rev-parse --git-dir >/dev/null 2>&1; then
  export GIT_SHA="$(git rev-parse --short HEAD)"
  export GIT_DATE="$(git show -s --format=%cI HEAD)"
  export GIT_COUNT="$(git rev-list --count HEAD)"
  echo "   commit ${GIT_SHA} (b${GIT_COUNT})"
fi
docker compose -f compose.yml -f compose.prod.yml up -d --build

echo "🧱 2a/4 — Apply the audit log + the compliance append-only guarantee"
./scripts/standup.sh || {
  echo "❌ standup.sh failed — the append-only trigger on age_check_event may be missing." >&2
  echo "   Do not call the 18+ evidence permanent until this is green." >&2
  exit 1
}

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
