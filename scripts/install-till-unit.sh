#!/usr/bin/env bash
# install-till-unit.sh — the thing that puts the till on the screen.
#
# `scripts/systemd/banco-till.service` is a USER unit: it belongs to the account
# that runs the till (`art` on the shop tablet), it lives in that account's
# ~/.config/systemd/user/, and it needs NO ROOT — so this pushes over the `tablet`
# door, not `tablet-admin`.
#
#     ./scripts/install-till-unit.sh --check [host]    # is the tablet's copy ours?
#     ./scripts/install-till-unit.sh --push  [host]    # make it ours
#
# host defaults to `tablet`.
#
# ── WHY THIS EXISTS ────────────────────────────────────────────────────────
#
# Until 2026-09-05 this unit lived on EXACTLY ONE MACHINE and nowhere else. It was
# hand-edited on the tablet, by hand, over months. `tablet-lockdown.sh` says of
# itself, correctly: "THIS SCRIPT DOES NOT START THE TILL and must not learn to" —
# a lockdown that also launches the browser put the tablet into a 48-restart loop
# inside a minute on 2026-09-05. That boundary is right and this script does not
# cross it: lockdown locks the machine down, this one installs the launcher.
#
# But "not lockdown's job" had quietly become "nobody's job". In one evening the
# unit gained three fixes, every one of them found by Angel watching the screen
# during a cold boot, and NONE of them existed anywhere but that tablet:
#
#   --password-store=basic  the till NEVER CAME UP on a cold boot. GDM autologin
#                           means GDM has no password for `art`, so the login
#                           keyring stays locked; Chromium blocks asking it for
#                           safe storage and never navigates. Thirteen minutes of
#                           a white window that a tap could not fix.
#   ExecStartPre wait       once the boot got 50s faster, Chromium started 3s
#                           after the network instead of 68s, and lost that race.
#   timeout 20 (was 90)     with the network genuinely down, that wait held a
#                           BLANK screen in front of a working offline mode.
#
# A second tablet would have got none of it. Now it is in the repo, and --check
# says when the machine and the repo have drifted apart.
#
# Angel, 2026-09-05.

set -euo pipefail
cd "$(dirname "$0")/.."

UNIT=scripts/systemd/banco-till.service
DEST='~/.config/systemd/user/banco-till.service'
MODE=${1:-}
HOST=${2:-tablet}

[ -r "$UNIT" ] || { echo "❌ no $UNIT in this repo" >&2; exit 1; }

case "$MODE" in
  --check)
    echo "🔎 comparing $HOST:$DEST against $UNIT"
    if ssh -o ConnectTimeout=15 "$HOST" "cat $DEST" 2>/dev/null > /tmp/.banco-till-live.$$; then
      if diff -u "$UNIT" /tmp/.banco-till-live.$$ > /tmp/.banco-till-diff.$$; then
        echo "✅ identical — the tablet is running what this repo says."
      else
        echo "⚠️  DRIFT. The tablet differs from the repo:"
        echo "   (- = repo, + = tablet — decide which one is right before you push)"
        sed -n '3,200p' /tmp/.banco-till-diff.$$
      fi
      rm -f /tmp/.banco-till-live.$$ /tmp/.banco-till-diff.$$
    else
      echo "❌ could not read $DEST on $HOST" >&2; exit 1
    fi
    ;;

  --push)
    echo "→ $UNIT  →  $HOST:$DEST"
    # Keep a dated copy on the machine before overwriting: this unit is the only
    # thing that puts the till on the screen, and a bad one is a shop that cannot
    # sell. Restoring is `cp` and `systemctl --user daemon-reload`.
    ssh -o ConnectTimeout=15 "$HOST" \
      "mkdir -p ~/.config/systemd/user && \
       [ -f $DEST ] && cp -f $DEST $DEST.bak-\$(date +%Y%m%d-%H%M%S) || true"
    scp -q -o ConnectTimeout=15 "$UNIT" "$HOST:.config/systemd/user/banco-till.service"
    ssh -o ConnectTimeout=15 "$HOST" \
      "systemctl --user daemon-reload && systemctl --user enable banco-till.service >/dev/null 2>&1 || true"
    echo "✅ installed and daemon-reloaded."
    echo
    echo "   It does NOT restart the browser — that would blank the till under whoever is"
    echo "   standing at it. The new unit takes effect at the next restart or reboot:"
    echo "       ssh $HOST 'systemctl --user restart banco-till.service'"
    echo
    echo "   Then prove it the only way that counts — a real power-off and power-on, with"
    echo "   somebody watching the screen. Every fault in this file was found that way and"
    echo "   none of them were visible from a terminal."
    ;;

  *)
    echo "usage: $0 --check [host] | --push [host]   (host defaults to 'tablet')" >&2
    exit 2 ;;
esac
