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
# ── HOW TO RUN IT ──────────────────────────────────────────────────────────
#
# From your laptop, with this repo checked out — the one you want 99% of the
# time. Pushes THIS version to the machine, installs it, applies it, and arms it
# to re-apply at every boot:
#
#     ./scripts/tablet-lockdown.sh --push            (defaults to host `tablet`)
#     ./scripts/tablet-lockdown.sh --push counter2
#
# On the machine itself:
#
#     sudo ./scripts/tablet-lockdown.sh
#
# THE SCRIPT LIVES IN THIS REPO. Never park a copy in /tmp. Angel, 2026-09-03:
# "we want to keep that script in case we get another tablet." A /tmp copy is
# gone at the next reboot — which is exactly what happened between handing him
# the command and his running it, and the test sheet came back with
# "sudo: /tmp/tablet-lockdown.sh: command not found".
#
# ── WHY IT ALSO RUNS AT BOOT ───────────────────────────────────────────────
#
# Angel, 2026-09-03: "sometimes the tablet gets messed up... the only way to fix
# it is run that script, or you could try to reboot, but sometimes that doesn't
# help." That is the wrong way round, and it is worth fixing rather than
# documenting: a reboot is what a shop ALREADY tries when something is odd, and
# on a counter machine it should be the thing that puts the settings back.
#
# So running this installs itself to /usr/local/sbin/banco-counter-lockdown and
# enables banco-lockdown.service, a oneshot that re-applies everything on every
# boot. The dconf locks and the Chromium policy are ordinary files and do
# survive a reboot on their own — this is for the case where they do not: a
# package update, a half-finished reinstall, or somebody with sudo and a good
# reason. After this, "turn it off and on again" is a real repair on this
# machine instead of a superstition.
#
# It is idempotent. Running it twice, or a hundred boots in a row, writes the
# same files and changes nothing else.
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

INSTALLED=/usr/local/sbin/banco-counter-lockdown
UNIT=/etc/systemd/system/banco-lockdown.service
QUIET=0

# ── --push: run from the LAPTOP, no root here ──────────────────────────────
# One ssh, one password prompt. The script is piped into `cat`, landed at its
# permanent path, made executable and run — in that order, so the copy that
# executes is the copy that will still be there tomorrow. Nothing touches /tmp.
if [ "${1:-}" = "--push" ]; then
  HOST="${2:-tablet}"
  SELF="${BASH_SOURCE[0]:-$0}"
  STAGE=".banco-counter-lockdown.push"

  # NOT WITH SUDO. `tablet` is a Host alias in YOUR ~/.ssh/config; root has its own
  # config and its own keys, and has never heard of it. Angel, 2026-09-03, after the
  # first version made him reach for sudo:
  #     sudo ./scripts/tablet-lockdown.sh --push
  #     ssh: Could not resolve hostname tablet: Name or service not known
  # The only password anyone needs here is the TABLET's, and ssh asks for that itself.
  if [ "$(id -u)" -eq 0 ]; then
    echo "Run --push as yourself, WITHOUT sudo." >&2
    echo "  '$HOST' is a Host alias in your own ~/.ssh/config and root cannot see it," >&2
    echo "  which is why sudo turns this into 'Could not resolve hostname $HOST'." >&2
    echo "  The only password needed is the tablet's; ssh will ask for it." >&2
    exit 2
  fi
  [ -r "$SELF" ] || { echo "--push needs the script as a file, not a pipe" >&2; exit 2; }

  # TWO STEPS, AND THAT IS THE WHOLE FIX. The first version piped the script into
  # `ssh -t ... sudo`, which cannot work and which I shipped having only ever tested
  # it without the sudo:
  #     Pseudo-terminal will not be allocated because stdin is not a terminal.
  #     sudo: a terminal is required to read the password
  # ssh refuses a TTY when stdin is a file, and sudo needs a TTY to prompt. So: copy
  # first with scp (no TTY needed), THEN run with a real terminal and stdin free.
  echo "→ copying $(basename "$SELF") to $HOST"
  scp -q "$SELF" "$HOST:$STAGE" || { echo "copy to $HOST failed" >&2; exit 1; }

  # One sudo, so one password prompt. The staged copy is moved into place and then
  # removed — the permanent copy is $INSTALLED and nothing is left lying around.
  # shellcheck disable=SC2029  # $INSTALLED/$STAGE must expand HERE; $HOME/$1 must not
  ssh -t "$HOST" \
    "sudo sh -c 'install -m 755 \"\$1\" $INSTALLED && exec $INSTALLED' _ \"\$HOME/$STAGE\"; \
     rc=\$?; rm -f \"\$HOME/$STAGE\"; exit \$rc"
  exit $?
fi

if [ "${1:-}" = "--quiet" ]; then QUIET=1; fi          # how the boot unit calls us
say() { [ "$QUIET" -eq 1 ] || echo "$@"; }

if [ "$(id -u)" -ne 0 ]; then
  # $0 is "bash" when this arrives over a pipe, so name the ways out explicitly.
  echo "This needs root. Either:" >&2
  echo "    ./scripts/tablet-lockdown.sh --push [host]   (from your laptop — does everything)" >&2
  echo "    sudo ./scripts/tablet-lockdown.sh            (on the machine itself)" >&2
  exit 1
fi

PROFILE=/etc/dconf/profile/user
KEYFILE=/etc/dconf/db/local.d/00-banco-counter
LOCKS=/etc/dconf/db/local.d/locks/banco-counter

mkdir -p /etc/dconf/profile /etc/dconf/db/local.d/locks

# The profile makes the system database real. Keep any existing one intact.
if [ ! -f "$PROFILE" ] || ! grep -q '^system-db:local' "$PROFILE" 2>/dev/null; then
  printf 'user-db:user\nsystem-db:local\n' > "$PROFILE"
  say "  wrote $PROFILE"
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
say "  wrote $KEYFILE"
say "  wrote $LOCKS"

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
    say "  wrote $d/00-banco-search.json"
    wrote_policy=1
  fi
done
[ "$wrote_policy" -eq 1 ] || say "  ⚠️  no Chromium policy directory found — search engine NOT set"

# ---------------------------------------------------------------------------
# MAKE A REBOOT A REPAIR.
#
# Everything above writes ordinary files that already survive a restart. This
# part is for when they do not — a package update, a half-finished reinstall, or
# somebody with sudo and a good reason. A counter machine should come back from
# a power cycle in a known state, because "turn it off and on again" is what a
# shop tries first and it should be the fix rather than a superstition.
#
# Self-install first: the unit has to point at a path that will still be there
# tomorrow, not at a checkout on somebody's laptop. When this arrives over a
# pipe there is no file to copy — but --push has already landed it at $INSTALLED
# and is executing THAT, so the common route installs itself correctly.
# ---------------------------------------------------------------------------
SELF="${BASH_SOURCE[0]:-$0}"
if [ -r "$SELF" ] && [ "$SELF" != "$INSTALLED" ]; then
  mkdir -p "$(dirname "$INSTALLED")"
  cp -f "$SELF" "$INSTALLED"
  chmod 755 "$INSTALLED"
  say "  installed $INSTALLED"
fi

if [ -x "$INSTALLED" ]; then
  cat > "$UNIT" <<UNITFILE
[Unit]
Description=Banco counter lockdown — re-apply the till's settings at boot
Documentation=https://github.com/akenel/banco-starter
After=local-fs.target
Before=display-manager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=$INSTALLED --quiet

[Install]
WantedBy=multi-user.target
UNITFILE
  systemctl daemon-reload
  systemctl enable banco-lockdown.service >/dev/null 2>&1 || true
  say "  installed $UNIT (runs at every boot)"
else
  # Say it out loud. A boot job that silently did not get installed is worse
  # than one that was never promised.
  echo "  ⚠️  could not install the boot job: $INSTALLED is not there." >&2
  echo "      Settings ARE applied, but a reboot will not re-apply them." >&2
  echo "      Run it as a file:  sudo ./scripts/tablet-lockdown.sh" >&2
fi

if [ "$QUIET" -eq 1 ]; then exit 0; fi   # booting: no essays on the console

echo
echo "✅ Locked. Log out and back in (or reboot) for the shell to pick it up."
echo "   After that the accessibility toggles are greyed out and the little"
echo "   person icon is gone — nobody can magnify the till by accident again."
echo
echo "🔎 Search engine: Google (${SEARCH_HOST}). QUIT Chromium fully and reopen it,"
echo "   then check chrome://policy — DefaultSearchProviderSearchURL must be listed"
echo "   with status OK. A reload is not enough; the browser reads policy at start."
echo
echo "🔁 This machine now re-applies all of it at every boot"
echo "   (banco-lockdown.service). If the tablet ever goes strange, restarting it"
echo "   IS the fix — and if you want to force it without rebooting:"
echo "       ssh -t tablet 'sudo systemctl start banco-lockdown.service'"
