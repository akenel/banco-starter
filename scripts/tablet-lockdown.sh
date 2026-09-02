#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Banco — lock down a GNOME counter machine.
#
# WHY. A barcode gun IS a keyboard: thirteen digits in ~50ms, with a SHIFT in
# among them. GNOME keeps three settings one tap away, behind the little person
# icon in the top bar, whose entire purpose is to IGNORE KEYS TYPED QUICKLY:
#
#   slow keys    a key must be HELD to register  -> most of the barcode is lost
#   bounce keys  fast repeats discarded          -> 4455 arrives as 45, silently
#   sticky keys  modifiers latch                 -> the gun's SHIFT lands wrong
#   mouse keys   numpad moves the POINTER        -> no digits at all
#   zoom         one tap, magnifies everything, and on a touchscreen there is
#                no obvious way back. A reboot does not help: it is a SAVED
#                setting. Angel, 2026-09-02: "now it's impossible to set it back."
#
# Two of these were found ON, on the shop's own tablet, minutes before a scanner
# test. A gun with slow keys enabled does not look like a settings problem — it
# looks like a BROKEN GUN, and the shop buys another one.
#
# Turning them off is not enough; anyone can turn them back on by accident, which
# is exactly how they got on. So this writes a system dconf profile and LOCKS the
# keys — GNOME then greys the toggles out and they cannot be changed at all.
#
# Run it once per counter machine:
#     sudo ./scripts/tablet-lockdown.sh
#
# To undo: rm /etc/dconf/db/local.d/00-banco-counter
#          rm /etc/dconf/db/local.d/locks/banco-counter
#          dconf update
# ---------------------------------------------------------------------------
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "This needs root — run:  sudo $0" >&2
  exit 1
fi

PROFILE=/etc/dconf/profile/user
KEYFILE=/etc/dconf/db/local.d/00-banco-counter
LOCKS=/etc/dconf/db/local.d/locks/banco-counter

mkdir -p /etc/dconf/profile /etc/dconf/db/local.d/locks

# The profile makes the system database real. Keep any existing one intact.
if [ ! -f "$PROFILE" ] || ! grep -q '^system-db:local' "$PROFILE" 2>/dev/null; then
  printf 'user-db:user\nsystem-db:local\n' > "$PROFILE"
  echo "  wrote $PROFILE"
fi

cat > "$KEYFILE" <<'KEYS'
# Banco counter machine — see scripts/tablet-lockdown.sh for why each one.
[org/gnome/desktop/a11y]
always-show-universal-access-status=false

[org/gnome/desktop/a11y/applications]
screen-magnifier-enabled=false
screen-keyboard-enabled=false
screen-reader-enabled=false

[org/gnome/desktop/a11y/keyboard]
slowkeys-enable=false
bouncekeys-enable=false
stickykeys-enable=false
mousekeys-enable=false
togglekeys-enable=false

[org/gnome/desktop/interface]
enable-hot-corners=false
KEYS

cat > "$LOCKS" <<'LOCKS_LIST'
/org/gnome/desktop/a11y/always-show-universal-access-status
/org/gnome/desktop/a11y/applications/screen-magnifier-enabled
/org/gnome/desktop/a11y/applications/screen-keyboard-enabled
/org/gnome/desktop/a11y/applications/screen-reader-enabled
/org/gnome/desktop/a11y/keyboard/slowkeys-enable
/org/gnome/desktop/a11y/keyboard/bouncekeys-enable
/org/gnome/desktop/a11y/keyboard/stickykeys-enable
/org/gnome/desktop/a11y/keyboard/mousekeys-enable
/org/gnome/desktop/a11y/keyboard/togglekeys-enable
/org/gnome/desktop/interface/enable-hot-corners
LOCKS_LIST

dconf update
echo "  wrote $KEYFILE"
echo "  wrote $LOCKS"
echo
echo "✅ Locked. Log out and back in (or reboot) for the shell to pick it up."
echo "   After that the accessibility toggles are greyed out and the little"
echo "   person icon is gone — nobody can magnify the till by accident again."
