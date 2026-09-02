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
# NOT on this list: the on-screen keyboard. It is locked ON, because the lock
# screen needs it and a counter tablet with no keyboard attached cannot be
# unlocked without it. Turning it off locked Angel out of his own machine.
#
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
# It also sets Chromium's default search engine to Google (see the bottom of
# this file). Felix asked for Google; a fresh Debian Chromium ships DuckDuckGo,
# and the counter tablet is where somebody stands looking up a product they are
# holding. Set as a MANAGED POLICY, not a preference, for the same reason as
# everything above: a preference is one stray tap from being something else.
#
# To undo: rm /etc/dconf/db/local.d/00-banco-counter
#          rm /etc/dconf/db/local.d/locks/banco-counter
#          rm /etc/chromium*/policies/managed/00-banco-search.json
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
screen-reader-enabled=false
# ON, and locked ON. This one is NOT a hazard and it is not optional: the LOCK
# SCREEN uses it to let you type your password. Locked to false on 2026-09-02
# and Angel could not log in to his own tablet without plugging a keyboard in.
# It never appears inside a browser on this machine anyway — which is the entire
# reason Banco draws its own keypad — so it costs the till nothing.
screen-keyboard-enabled=true

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

# ---------------------------------------------------------------------------
# CHROMIUM: default search engine = Google.
#
# Debian's Chromium ships DuckDuckGo as the default. Felix wants Google, and the
# counter tablet is the machine somebody stands at holding a packet they cannot
# identify — so the omnibox matters more here than it does on a desk.
#
# Written as a MANAGED POLICY rather than a setting inside the profile, because:
#   - it survives a new profile, a wiped profile, and a second user account
#   - Chromium then shows the field as managed and it cannot be changed by a tap
#   - it needs no login to apply — it is there the first time the browser opens
#
# One line to change the country: www.google.ch (Swiss results, the shop is in
# Luzern). www.google.de or www.google.com work identically — .com redirects to
# the local domain anyway, so .ch just skips a hop.
# ---------------------------------------------------------------------------
SEARCH_HOST="${BANCO_SEARCH_HOST:-www.google.ch}"

wrote_policy=0
for d in /etc/chromium/policies/managed \
         /etc/chromium-browser/policies/managed \
         /etc/opt/chrome/policies/managed; do
  # Both CHROMIUM paths get the file regardless of what is on disk: Debian has
  # shipped /etc/chromium and /etc/chromium-browser at different times, the
  # package does not necessarily create either, and a policy file sitting in a
  # directory no browser reads costs nothing. Chrome's tree is only filled if
  # Chrome is actually installed. Guessing wrong here fails SILENTLY — the
  # browser simply ignores you — which is why chrome://policy is the check.
  base="$(dirname "$(dirname "$d")")"
  if [ "$d" != "/etc/opt/chrome/policies/managed" ] || [ -d "$base" ]; then
    mkdir -p "$d"
    cat > "$d/00-banco-search.json" <<JSON
{
  "DefaultSearchProviderEnabled": true,
  "DefaultSearchProviderName": "Google",
  "DefaultSearchProviderKeyword": "google",
  "DefaultSearchProviderSearchURL": "https://${SEARCH_HOST}/search?q={searchTerms}",
  "DefaultSearchProviderSuggestURL": "https://${SEARCH_HOST}/complete/search?output=chrome&q={searchTerms}"
}
JSON
    echo "  wrote $d/00-banco-search.json"
    wrote_policy=1
  fi
done
[ "$wrote_policy" -eq 1 ] || echo "  ⚠️  no Chromium policy directory found — search engine NOT set"

echo
echo "✅ Locked. Log out and back in (or reboot) for the shell to pick it up."
echo "   After that the accessibility toggles are greyed out and the little"
echo "   person icon is gone — nobody can magnify the till by accident again."
echo
echo "🔎 Search engine: Google (${SEARCH_HOST}). QUIT Chromium fully and reopen it,"
echo "   then check chrome://policy — DefaultSearchProviderSearchURL must be listed"
echo "   with status OK. A reload is not enough; the browser reads policy at start."
