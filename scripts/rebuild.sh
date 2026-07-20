#!/usr/bin/env bash
# ---------------------------------------------------------------
# Banco POS — rebuild + boot, STAMPED with the real git commit.
#
# The login screen shows a build stamp so you can prove your `git pull` actually
# took. But the container can't read .git (the build context excludes it), so this
# reads the commit on the HOST and passes it into the image as build args. After a
# pull, run this instead of a bare `docker compose up --build` and the stamp on the
# login page will match HEAD.
#
#   git pull
#   ./scripts/rebuild.sh          # stamps + builds + starts everything
#   ./scripts/standup.sh          # audit log + the "✅ safe to test" verdict
#
# A bare `docker compose up -d --build` still works — it just stamps "dev" honestly.
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

if git rev-parse --git-dir >/dev/null 2>&1; then
  GIT_SHA="$(git rev-parse --short HEAD)"
  GIT_DATE="$(git show -s --format=%cI HEAD)"
  GIT_COUNT="$(git rev-list --count HEAD)"
  export GIT_SHA GIT_DATE GIT_COUNT
  echo "🔖 Stamping build ${GIT_SHA}  (b${GIT_COUNT}, ${GIT_DATE})"
else
  echo "⚠️  not a git checkout — the build will stamp as 'dev'"
fi

docker compose up -d --build "$@"

echo
echo "✅ Built + started. The login screen should now show ${GIT_SHA:-dev}."
echo "   Next: ./scripts/standup.sh"
