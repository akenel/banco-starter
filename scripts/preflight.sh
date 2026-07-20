#!/usr/bin/env bash
# ---------------------------------------------------------------
# preflight — is this machine ready to run Banco?
# Checks hardware + the tools Banco needs, and gives a clear verdict
# BEFORE you waste an afternoon. Reads only — installs nothing.
#
#   ./scripts/preflight.sh
#
# (Chicken-and-egg note: you need `git` to clone this repo in the first place,
#  so the very first checks live in onboarding/00-prerequisites.md as a paste-in
#  snippet. This script is for re-checking once you have the repo.)
# ---------------------------------------------------------------
set -u
ok(){ printf "  \033[32m✅ %s\033[0m\n" "$1"; }
warn(){ printf "  \033[33m⚠️  %s\033[0m\n" "$1"; WARN=$((WARN+1)); }
bad(){ printf "  \033[31m❌ %s\033[0m\n" "$1"; FAIL=$((FAIL+1)); }
WARN=0; FAIL=0

echo ""
echo "🩺 Banco preflight — can this machine run the shop?"
echo ""

# ---- hardware ----
echo "Hardware"
CORES=$(nproc 2>/dev/null || echo 0)
[ "$CORES" -ge 2 ] 2>/dev/null && ok "CPU: $CORES cores" || warn "CPU: only $CORES core — it'll be slow"

MEM_AV=$(free -m 2>/dev/null | awk '/^Mem:/{print $7}')
MEM_TOT=$(free -m 2>/dev/null | awk '/^Mem:/{print $2}')
if [ -n "${MEM_AV:-}" ]; then
  if [ "$MEM_AV" -ge 3000 ]; then ok "RAM: ${MEM_AV}MB available (of ${MEM_TOT}MB)"
  elif [ "$MEM_AV" -ge 1500 ]; then warn "RAM: only ${MEM_AV}MB free — close other apps; swap helps"
  else bad "RAM: ${MEM_AV}MB free — too little; Keycloak + Postgres may be killed"; fi
else warn "RAM: couldn't read"; fi

DISK_AV=$(df -Pm / 2>/dev/null | awk 'NR==2{print $4}')
if [ -n "${DISK_AV:-}" ]; then
  if [ "$DISK_AV" -ge 8000 ]; then ok "Disk: $((DISK_AV/1000))GB free on /"
  elif [ "$DISK_AV" -ge 4000 ]; then warn "Disk: only $((DISK_AV/1000))GB free — images need room"
  else bad "Disk: only $((DISK_AV/1000))GB free — not enough for the images"; fi
else warn "Disk: couldn't read"; fi

# ---- tools you MUST have to run Banco ----
echo ""
echo "Required to run"
command -v docker >/dev/null 2>&1 && ok "docker: $(docker --version 2>/dev/null)" || bad "docker: MISSING — install it (see onboarding/00-prerequisites.md)"
docker compose version >/dev/null 2>&1 && ok "docker compose: $(docker compose version 2>/dev/null | head -1)" || bad "docker compose (v2): MISSING"
command -v git >/dev/null 2>&1 && ok "git: $(git --version 2>/dev/null)" || bad "git: MISSING — you can't clone without it"

# ---- tools for the full experience ----
echo ""
echo "Needed for backups / tools"
command -v gpg >/dev/null 2>&1 && ok "gpg: $(gpg --version 2>/dev/null | head -1)" || warn "gpg: MISSING — needed to encrypt backups"
command -v python3 >/dev/null 2>&1 && ok "python3: $(python3 --version 2>/dev/null)" || warn "python3: MISSING — needed for banco-doctor + scripts"
if command -v b2 >/dev/null 2>&1; then
  ok "b2: $(b2 version 2>/dev/null | head -1)"
elif [ -f .env ] && grep -qE '^B2_KEY_ID=.+' .env 2>/dev/null; then
  # creds ARE configured — so the tool is now genuinely needed (backups + the deploy's
  # backup-first step), not a "later" nicety. Point at the install, not at guide 6.
  warn "b2 CLI: MISSING — but your B2 keys ARE set in .env. Install it now: sudo apt install -y pipx && pipx install b2 && pipx ensurepath"
else
  warn "b2: MISSING — needed only for B2 backups (install when you set them up: guide 6)"
fi
command -v curl >/dev/null 2>&1 && ok "curl: present" || warn "curl: MISSING — handy for downloads/health checks"

# ---- verdict ----
echo ""
if [ "$FAIL" -gt 0 ]; then
  printf "\033[31m❌ Not ready: %s blocker(s). Install what's missing, then re-run.\033[0m\n" "$FAIL"
  echo "   See onboarding/00-prerequisites.md for the install commands."
  exit 1
elif [ "$WARN" -gt 0 ]; then
  printf "\033[33m⚠️  Good enough to start (%s note(s)). You can run Banco; sort the ⚠️ items before go-live.\033[0m\n" "$WARN"
  exit 0
else
  printf "\033[32m✅ Ready. Head to QUICKSTART.md.\033[0m\n"
  exit 0
fi
