#!/usr/bin/env bash
# ---------------------------------------------------------------
# Keep the label printer reachable, so "Print" always just works.
#
# THE PROBLEM: ipp-usb's USB session to the Brother QL dies after ~6-13 minutes
# idle and never re-opens itself. Jobs then queue silently and nothing comes
# out — no error, clean CUPS drain, printer sitting there lit and READY. The
# CLI tool (print-label.py) heals itself before printing, but a BROWSER can't:
# window.print() has no way to restart a daemon, and an HTTPS page can't even
# reach http://localhost. So the till's Print button needs the printer to
# already be awake.
#
# THE FIX, in two parts:
#   1. POKE it every minute. The failure is an idle timeout, so regular traffic
#      should stop it going stale in the first place. This is the cheap part —
#      one IPP status query, no interruption, no restart.
#   2. If the poke fails anyway, RESTART ipp-usb. ~5s, and any queued jobs
#      flush immediately afterwards.
#
# Runs as root from a systemd timer, so no sudo and no password prompt.
#
#   ./scripts/label-printer-keepalive.sh          # one check
#   ./scripts/label-printer-keepalive.sh --loud   # ... and say so even when fine
#
# Exit 0 = printer reachable (already, or after a heal). 1 = still unreachable.
# ---------------------------------------------------------------
set -uo pipefail

IPP_URI="ipp://localhost:60000/ipp/print"
TEST_FILE="/usr/share/cups/ipptool/get-printer-attributes.test"
LOUD="${1:-}"

log() { echo "$(date '+%H:%M:%S') label-keepalive: $*"; }

# Is ipp-usb actually RELAYING to the printer?
#
# Not just "is the port open" — a dead session still accepts TCP and answers a
# bare redirect, which is what fooled us for hours. Ask for real printer
# attributes: that is the part that goes silent, returning 0 bytes.
#
# ipptool ignores SIGTERM, hence `timeout -s KILL` on top of its own -T.
relaying() {
    local out
    out="$(timeout -s KILL 20 ipptool -T 12 -tv "$IPP_URI" "$TEST_FILE" 2>&1)" || return 1
    [[ "$out" == *"RECEIVED: 0 bytes"* ]] && return 1
    [[ "$out" == *"printer-state"* ]] || return 1
    return 0
}

if [ ! -e /dev/bus/usb ] || ! lsusb -d 04f9: >/dev/null 2>&1; then
    [ "$LOUD" = "--loud" ] && log "no Brother printer on USB — nothing to keep alive"
    exit 0                       # printer unplugged or off: not our problem to fix
fi

if relaying; then
    # The poke itself is the keepalive — traffic is what stops the idle timeout.
    [ "$LOUD" = "--loud" ] && log "ok — relaying"
    exit 0
fi

log "ipp-usb is not relaying — restarting it"
systemctl restart ipp-usb || { log "restart FAILED"; exit 1; }

for _ in $(seq 1 12); do         # it can take a few seconds to come back
    sleep 5
    if relaying; then
        log "back up"
        exit 0
    fi
done

log "still not relaying 60s after a restart — is the printer powered on?"
exit 1
