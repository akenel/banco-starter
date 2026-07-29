#!/usr/bin/env bash
# ---------------------------------------------------------------
# Install the label-printer keepalive on THIS TILL. Run once per machine.
#
#   sudo ./scripts/install-label-keepalive.sh
#
# RUN THIS ON THE MACHINE WITH THE PRINTER PLUGGED INTO IT — the till, not the
# server. Banco's pages come from the server, but printing happens entirely on
# the till: browser -> CUPS -> ipp-usb -> USB cable -> printer. The server has
# no printer attached and nothing here would find one.
#
# This is MACHINE SETUP, not application code. It installs into /etc and /opt,
# so it survives `git pull`, redeploys, reboots and power cuts. You do not
# re-run it after a deploy. Once per till, then forget it.
#
# What it does: a systemd timer pokes the printer every minute with an IPP
# status query. ipp-usb's USB session dies after ~6-13 minutes IDLE, so regular
# traffic should stop it ever going stale — and if it does anyway, the timer
# restarts ipp-usb within a minute. Without this the browser's Print button
# silently does nothing whenever the printer has been sitting unused, because
# window.print() cannot restart a daemon.
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$(id -u)" -ne 0 ]; then
    echo "❌ Needs root:  sudo $0" >&2
    exit 1
fi

echo "🏷️  Installing the label-printer keepalive on $(hostname)"

if ! command -v ipptool >/dev/null 2>&1; then
    echo "❌ ipptool not found — install CUPS first:  apt install cups-ipp-utils" >&2
    exit 1
fi

if ! lsusb -d 04f9: >/dev/null 2>&1; then
    echo "⚠️  No Brother printer on USB right now."
    echo "   Installing anyway — the timer sits quiet until one appears."
    echo "   But if this is your SERVER rather than the till, stop: it belongs on the till."
fi

install -d -m 0755 /opt/banco
install -m 0755 scripts/label-printer-keepalive.sh /opt/banco/label-printer-keepalive.sh
install -m 0644 scripts/systemd/banco-label-keepalive.service /etc/systemd/system/
install -m 0644 scripts/systemd/banco-label-keepalive.timer   /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now banco-label-keepalive.timer

echo
echo "✅ Installed and running."
systemctl list-timers banco-label-keepalive.timer --no-pager 2>/dev/null | head -3
echo
echo "   Check it any time:   systemctl status banco-label-keepalive.timer"
echo "   Watch it work:       journalctl -u banco-label-keepalive.service -f"
echo "   Prove it by hand:    /opt/banco/label-printer-keepalive.sh --loud"
echo
echo "   Survives deploys and reboots. Run once per till — not again."
