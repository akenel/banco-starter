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
#     ./scripts/tablet-lockdown.sh --push tablet-admin --autologin
#     ./scripts/tablet-lockdown.sh --push counter2
#
#   SINCE 2026-09-05 THE PUSH GOES TO `tablet-admin`, NOT `tablet`. The tablet has
#   two doors on purpose: `art` runs the till and is no longer in the sudo group,
#   so its password is safe to hand to a cashier; `admin` is the maintenance door.
#   Read-only checks (tablet-postboot-check.sh) must still go to `tablet`, because
#   they read gsettings and those are per-SESSION values — read as anyone else you
#   get an empty session's defaults on a screen nobody is looking at.
#
# THIS SCRIPT DOES NOT START THE TILL and must not learn to. That job belongs to
# ~/.config/systemd/user/banco-till.service, which already existed and already
# restarts the browser if it is closed. A --kiosk launcher was added here on
# 2026-09-05 and put the tablet into a 48-restart loop inside a minute — see the
# block near the bottom of this file, which now removes it again.
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
#          (and `systemctl disable --now banco-lockdown.service` to stop it
#           coming back at the next boot)
# ---------------------------------------------------------------------------
set -euo pipefail

INSTALLED=/usr/local/sbin/banco-counter-lockdown
# Where the copy lands in the far end's $HOME before sudo moves it to $INSTALLED.
# A bare filename on purpose: scp resolves a relative target against the remote home,
# and the ssh line below says "$HOME/$STAGE" for the same file.
#
# 2026-09-05: this was USED TWICE AND DEFINED NOWHERE, so with `set -u` every --push
# died at the first line that mentions it:
#     ./scripts/tablet-lockdown.sh: line 132: STAGE: unbound variable
# The two-step scp/ssh rewrite the night before fixed the no-terminal FAILURE path and
# broke the SUCCESS path, and nothing ran the success path — it needs a real terminal, a
# reachable tablet and a sudo password, so it sat unexercised until Angel typed it.
# Hence --dry-run below: the wiring can now be checked without any of those three.
STAGE=.banco-lockdown-push.sh
UNIT=/etc/systemd/system/banco-lockdown.service
QUIET=0
# ── --push: run from the LAPTOP, no root here ──────────────────────────────
# One ssh, one password prompt. The script is piped into `cat`, landed at its
# permanent path, made executable and run — in that order, so the copy that
# executes is the copy that will still be there tomorrow. Nothing touches /tmp.
if [ "${1:-}" = "--push" ]; then
  HOST="${2:-tablet}"
  SELF="${BASH_SOURCE[0]:-$0}"
  # --dry-run prints the two commands and touches nothing. It exists because the real
  # thing cannot be rehearsed: it wants a terminal, a reachable machine and a password.
  DRY=0
  for a in "$@"; do [ "$a" = "--dry-run" ] && DRY=1; done

  # EVERY OTHER FLAG HAS TO SURVIVE THE TRIP. `exec $INSTALLED` ran the script on the far
  # end with NO ARGUMENTS, so `--push tablet --autologin` parsed the flag here, exited
  # here, and the tablet did the lockdown and silently skipped the thing that was asked
  # for. Second time this shape has bitten in one day (see $STAGE): the push path cannot
  # be rehearsed, so anything added to it ships unexercised — and --dry-run, added THIS
  # MORNING for exactly that reason, would have printed the missing flag if I had run it
  # once with the new option.
  FWD=""
  i=0
  for a in "$@"; do
    i=$((i + 1))
    [ "$i" -le 1 ] && continue                                  # --push itself
    [ "$i" -eq 2 ] && case "$a" in -*) ;; *) continue ;; esac    # the host, when given
    case "$a" in
      --dry-run) continue ;;
      *[!A-Za-z0-9=_-]*) echo "refusing to forward $a — flags only" >&2; exit 2 ;;
    esac
    FWD="$FWD $a"
  done

  [ -r "$SELF" ] || { echo "--push needs the script as a file, not a pipe" >&2; exit 2; }

  # AND IT NEEDS A REAL TERMINAL, checked BEFORE anything is copied.
  #
  # This is the third version of the same failure and the first one that says so
  # up front. `ssh -t` cannot allocate a pseudo-terminal when stdin is not one,
  # and sudo on the far end cannot prompt without one — so run from inside an
  # editor, an agent shell or a script and you get this, half way through, after
  # the file has already been copied:
  #
  #     Pseudo-terminal will not be allocated because stdin is not a terminal.
  #     sudo: a terminal is required to read the password
  #
  # Hit on 2026-09-05 running it through Claude Code's `!` prefix. Nothing is
  # broken by it and the staged copy is cleaned up either way — but a command
  # that fails after doing half its work teaches you not to trust it, so it now
  # refuses at the door and names the fix.
  if [ "$DRY" -eq 1 ]; then
    echo "→ scp -q \"$SELF\" \"$HOST:$STAGE\""
    echo "→ ssh -t \"$HOST\" \"sudo sh -c 'install -m 755 \\\"\$1\\\" $INSTALLED && exec $INSTALLED$FWD' _ \\\"\$HOME/$STAGE\\\"; rc=\$?; rm -f \\\"\$HOME/$STAGE\\\"; exit \$rc\""
    [ -n "$FWD" ] && echo "   (forwarding:$FWD)" || echo "   (no flags to forward)"
    echo "(dry run — nothing copied, nothing run)"
    exit 0
  fi

  if [ ! -t 0 ]; then
    echo "--push needs a real terminal — sudo on '$HOST' has to ask you for its password." >&2
    echo "  Run it in an ordinary terminal window (not through an editor or agent shell):" >&2
    echo "      ./scripts/tablet-lockdown.sh --push $HOST" >&2
    echo "  Or, already on the machine:  sudo ./scripts/tablet-lockdown.sh" >&2
    exit 2
  fi

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
    "sudo sh -c 'install -m 755 \"\$1\" $INSTALLED && exec $INSTALLED$FWD' _ \"\$HOME/$STAGE\"; \
     rc=\$?; rm -f \"\$HOME/$STAGE\"; exit \$rc"
  exit $?
fi

if [ "${1:-}" = "--quiet" ]; then QUIET=1; fi          # how the boot unit calls us
say() { [ "$QUIET" -eq 1 ] || echo "$@"; }

# A FUNCTION, AND REHEARSABLE WITHOUT ROOT OR A TABLET. Twice today something on the
# --push path shipped broken because that path cannot be run from here: $STAGE was
# undefined, and then --autologin was parsed on the laptop and never forwarded. Both were
# one command away from being caught if the command had existed. So:
#
#     ./scripts/tablet-lockdown.sh --autologin-selftest
#
# runs this against a throwaway copy of a real daemon.conf and prints the result.
set_autologin() {
  conf="$1"; user="$2"
  [ -e "$conf" ] || return 2          # no GDM here; the caller says so
  [ -e "$conf.pre-autologin" ] || cp -a "$conf" "$conf.pre-autologin"
  # Strip any existing AutomaticLogin lines (commented or not), then insert ours directly
  # after the [daemon] header. Idempotent: running it twice leaves one copy.
  awk -v u="$user" '
    /^[[:space:]]*#?[[:space:]]*AutomaticLogin(Enable)?[[:space:]]*=/ { next }
    { print }
    /^\[daemon\][[:space:]]*$/ && !done { print "AutomaticLoginEnable=true"; print "AutomaticLogin=" u; done=1 }
  ' "$conf" > "$conf.new" && mv "$conf.new" "$conf"
  grep -q "^AutomaticLogin=$user\$" "$conf" && grep -q "^AutomaticLoginEnable=true\$" "$conf"
}

if [ "${1:-}" = "--autologin-selftest" ]; then
  t=$(mktemp -d); printf '%s\n' \
    "# GDM configuration storage" "[daemon]" "# Uncomment the line below to force Xorg" \
    "#WaylandEnable=false" "#  AutomaticLoginEnable = true" "#  AutomaticLogin = user1" \
    "[security]" > "$t/daemon.conf"
  echo "── before ──"; grep -vE '^[[:space:]]*$' "$t/daemon.conf" | sed 's/^/   /'
  set_autologin "$t/daemon.conf" testuser && echo "  ✅ set, and verified by reading it back" \
                                          || { echo "  ❌ did not take"; exit 1; }
  echo "── after ──";  grep -vE '^[[:space:]]*$' "$t/daemon.conf" | sed 's/^/   /'
  set_autologin "$t/daemon.conf" testuser >/dev/null
  n=$(grep -c '^AutomaticLogin=' "$t/daemon.conf")
  [ "$n" -eq 1 ] && echo "  ✅ running it twice leaves ONE line, not two" \
                 || { echo "  ❌ ran twice, $n lines"; exit 1; }
  [ -e "$t/daemon.conf.pre-autologin" ] && echo "  ✅ the original was backed up once" \
                 || { echo "  ❌ no backup"; exit 1; }
  grep -q "AutomaticLogin = user1" "$t/daemon.conf.pre-autologin" \
    && echo "  ✅ and the backup is the ORIGINAL, not the edited one" || { echo "  ❌ backup is wrong"; exit 1; }
  rm -rf "$t"; exit 0
fi

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

# A TILL DOES NOT LOCK ITSELF, AND IT DOES NOT GO TO SLEEP.
#
# Measured on the tablet, 2026-09-05, and nothing here had ever been looked at:
#
#     screensaver lock-enabled          true        <- locks itself
#     session idle-delay                900         <- after fifteen minutes
#     power sleep-inactive-ac-type      suspend     <- then suspends, on mains
#     ...and every one of them writable=true
#
# A quiet Tuesday afternoon is fifteen minutes. Then the counter shows a lock
# screen asking a cashier for an OS password she does not have, and shortly
# after that the tablet is asleep. Nobody found it because nobody has left the
# till alone for a quarter of an hour with a stopwatch — the same blind spot as
# the token refresh that had never worked, which no probe of mine could see
# because every probe finishes inside ninety seconds.
#
# A BLANK SCREEN AND A SUSPEND ARE NOT THE SAME THING, and the difference is the
# whole fix. Angel, 2026-09-05, after the tablet did it to us mid-conversation:
# "if it does go to sleep we get a screensaver instead ... it always goes to sleep
# and it's a real pain to start with the start button."
#
#   BLANK    display off, machine awake, network up, till still running.
#            A TOUCH wakes it. No power button, no password, nothing to know.
#   SUSPEND  machine off. Power button. Comes back to a LOCK SCREEN.
#
# So the screensaver stays — it saves the panel and it costs nothing, because
# waking it is a tap. What goes is the lock and the suspend. The first draft of
# this block set idle-delay=0 ("never blank"), which was heavier than the problem:
# blanking was never the fault.
# AND A BLACK SCREEN MUST MEAN "OFF", NOT "GUESS".
#
# Angel, 2026-09-05, looking at the tablet from across the room while the very
# fix below was being tested: "the screen is black ... it's impossible for me or
# an end user to know if the power is off or if it's just sleeping. In the past I
# would go for the power button."
#
# That is the whole fault, and it is worse than it sounds, because:
#
#     power-button-action = 'suspend'
#
# — so the reflex he describes SUSPENDS a tablet that was working perfectly. We
# made the machine behave correctly and left a human no way to tell, and the
# habit that fills the gap is the one thing that breaks it.
#
# So the screen never goes fully black on idle. It DIMS to 30% and stays lit:
# obviously alive from three metres, nearly the same power saved, and no reason
# to reach for anything. Black then means off, and the power button is right.
[org/gnome/desktop/screensaver]
lock-enabled=false

[org/gnome/desktop/session]
idle-delay=uint32 0

# The dim replaces the blank. idle-brightness is a percentage, not a raw value.
[org/gnome/settings-daemon/plugins/power]
idle-dim=true
idle-brightness=30

# AND THE AMBIENT LIGHT SENSOR STOPS DRIVING IT. Measured on the tablet at 19%
# of maximum in a flat, in daylight. A counter's light changes all day — the
# street door, the ceiling lights, the season — and a till whose brightness
# follows it is a till that is unreadable at the wrong moment. Step A4 of the
# counter sheet was written to catch this; it is not hypothetical.
ambient-enabled=false

# A SHORT PRESS OF THE POWER BUTTON NO LONGER SUSPENDS. It asks. A long press
# still forces the machine off at the firmware, below anything software can
# change, so there is always a way out — it just is not an accident any more.
power-button-action='interactive'

# 'nothing' on BOTH, not just on mains. On battery the tempting answer is to let
# it sleep and save the charge — but an unplugged tablet that sleeps is a till
# that is gone, and at a counter the cable is the answer to a flat battery, not
# a suspend nobody can wake without the power button.
[org/gnome/settings-daemon/plugins/power]
sleep-inactive-ac-type='nothing'
sleep-inactive-battery-type='nothing'

# PrtScr TAKES THE WHOLE SCREEN, straight to ~/Pictures/Screenshots.
# GNOME 48 ships the other way round: Print opens the interactive picker with a
# selection box, and the whole screen is Shift+Print. On a touchscreen the picker
# means dragging a rectangle with a finger before you have anything at all, and
# every screenshot on the 2026-09-02 test sheets was a WHOLE screen — the thing
# that repeatedly showed what the DOM would not. Angel: "the PrtScr feature has
# been a life saver today."
# So they swap. The picker is still there on Shift+Print for when a crop is what
# you want. NOT locked: this is a preference, not a hazard, and locking it would
# take the choice away for no safety reason. Setting it as a system default means
# a wiped profile comes back with it, which is the whole point of this file.
[org/gnome/shell/keybindings]
screenshot=['Print']
show-screenshot-ui=['<Shift>Print']
screenshot-window=['<Alt>Print']
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
/org/gnome/desktop/screensaver/lock-enabled
/org/gnome/desktop/session/idle-delay
/org/gnome/settings-daemon/plugins/power/idle-dim
/org/gnome/settings-daemon/plugins/power/idle-brightness
/org/gnome/settings-daemon/plugins/power/ambient-enabled
/org/gnome/settings-daemon/plugins/power/power-button-action
/org/gnome/settings-daemon/plugins/power/sleep-inactive-ac-type
/org/gnome/settings-daemon/plugins/power/sleep-inactive-battery-type
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
# ── AUTOLOGIN — OFF BY DEFAULT, AND THE REASON IS A DECISION, NOT A DEFAULT ──
#
# MEASURED ON THE TILL, 2026-09-05. Angel asked whether everything is in place
# when the tablet boots. It is — every file, every locked setting, the boot job,
# the till service. And the till still does not appear, because:
#
#     /etc/gdm3/daemon.conf   [daemon] is EMPTY — every AutomaticLogin line is
#                             commented out, so GDM stops at a login screen
#     loginctl Linger         no — user units do not start without a session
#     banco-till.service      WantedBy=graphical-session.target — it needs a
#                             logged-in desktop, because Chromium needs a display
#
# So after a power cut the tablet boots to a Debian login prompt and waits. The
# till starts only when somebody types the OS password. Nobody noticed because
# Angel has logged in every single time — LESSON #1 exactly: proved in the
# posture the tester had (a person present), not the posture the shop has
# (a cashier who does not have that password, at 08:00, with the door open).
#
# WHY IT IS NOT ON BY DEFAULT. Autologin means anyone who powers the tablet on
# reaches the desktop. On a counter machine that is the normal trade and the
# lockdown above is what constrains it — but it is a change to who can touch
# what, on somebody's shop tablet, and that belongs to Felix and Angel, not to
# a script that was run for a different reason.
#
#     ./scripts/tablet-lockdown.sh --push tablet --autologin
#
# The original file is backed up once, next to itself, before anything is
# changed. Passing it twice is a no-op.
AUTOLOGIN=0
for a in "$@"; do [ "$a" = "--autologin" ] && AUTOLOGIN=1; done
GDM_CONF="${BANCO_GDM_CONF:-/etc/gdm3/daemon.conf}"

if [ "$AUTOLOGIN" -eq 1 ]; then
  # WHO IS THE TILL USER? NOT "whoever ran sudo".
  #
  # This used to be $SUDO_USER, which is right exactly while one account is both
  # the cashier's desktop and the administrator — which is the arrangement we are
  # about to end. Once maintenance is pushed from a separate admin login, $SUDO_USER
  # is the ADMIN, and this would have set the tablet to log itself in as the admin
  # account: the opposite of the point, discovered a week later by someone standing
  # at a counter looking at the wrong desktop.
  #
  # So ask the machine instead: the till user is whoever owns banco-till.service.
  # That is a fact about this tablet, not about who happens to be typing.
  TILL_USER="${AUTOLOGIN_USER:-}"
  if [ -z "$TILL_USER" ]; then
    for h in /home/*; do
      [ -f "$h/.config/systemd/user/banco-till.service" ] || continue
      TILL_USER=$(basename "$h"); break
    done
  fi
  [ -n "$TILL_USER" ] || TILL_USER="${SUDO_USER:-}"      # last resort, and it says so
  if [ -z "$TILL_USER" ] || [ "$TILL_USER" = root ]; then
    say "  ⚠️  autologin asked for, but I cannot tell which user runs the till"
    say "      no banco-till.service under any /home, and \$SUDO_USER is unusable."
    say "      re-run as:  AUTOLOGIN_USER=<name> sudo -E $0 --autologin"
  elif set_autologin "$GDM_CONF" "$TILL_USER"; then
    say "  wrote $GDM_CONF  (autologin as $TILL_USER — the till returns after a power cut)"
  else
    say "  ⚠️  could not set autologin in $GDM_CONF — no [daemon] section? check it by hand"
  fi
fi

# ── POWER PROFILE: BALANCED, NOT POWER-SAVER ──────────────────────────────
# Found 2026-09-05 because Angel asked whether the idle test should be repeated
# on battery. It should not — sleep-inactive-battery-type is already locked to
# 'nothing' — but the question turned this up:
#
#     power-profiles-daemon: active
#     current profile:       power-saver     <- on MAINS, battery at 100%
#
# A throttled CPU on a machine that is plugged into a wall and whose whole job is
# to answer instantly when somebody is standing at the counter. It almost
# certainly flipped there during some past stint on battery
# (power-saver-profile-on-low-battery=true) and never flipped back — which is the
# point: it is not a setting anyone chose, it is a setting that DRIFTED, and
# nothing was watching.
#
# Set at every boot rather than once, because that is exactly the drift this unit
# exists to undo. Not 'performance': balanced is what a till needs, and
# performance costs fan noise and heat at a counter for nothing.
if command -v powerprofilesctl >/dev/null 2>&1; then
  cur=$(powerprofilesctl get 2>/dev/null)
  if [ "$cur" = "balanced" ]; then
    say "  power profile: already balanced"
  elif powerprofilesctl set balanced 2>/dev/null; then
    say "  power profile: ${cur:-unknown} → balanced"
  else
    say "  ⚠️  could not set the power profile (daemon not up yet?) — currently ${cur:-unknown}"
  fi
fi

# ── BASE BRIGHTNESS ───────────────────────────────────────────────────────
# Turning the ambient sensor off freezes the brightness wherever it happened to
# be — and on this tablet that was 19% of maximum, in a flat, in daylight. Under
# shop lights at arm's length that is the "readable without leaning in" test
# failing before anyone has walked in.
#
# So set a floor. 80% rather than 100%: full brightness on an LCD buys little
# visible contrast over 80 and costs backlight hours, and the counter sheet will
# find the real number by looking at it under their lights. systemd-backlight
# saves this at shutdown and restores it at boot, so it is set once, not nagged.
BRIGHTNESS_PCT="${BRIGHTNESS_PCT:-80}"
for bl in /sys/class/backlight/*/; do
  [ -w "$bl/brightness" ] || continue
  max=$(cat "$bl/max_brightness" 2>/dev/null) || continue
  [ -n "$max" ] && [ "$max" -gt 0 ] 2>/dev/null || continue
  was=$(cat "$bl/brightness" 2>/dev/null)
  want=$(( max * BRIGHTNESS_PCT / 100 ))
  if [ "$was" -lt "$want" ] 2>/dev/null; then
    echo "$want" > "$bl/brightness" 2>/dev/null \
      && say "  brightness $(basename "$bl"): $((was * 100 / max))% → ${BRIGHTNESS_PCT}%"
  else
    say "  brightness $(basename "$bl"): already $((was * 100 / max))% — left alone"
  fi
done

# NO KIOSK MODE HERE — AND THIS BLOCK EXISTS TO REMOVE IT AGAIN.
#
# 2026-09-05, 00:12. I added a --kiosk launcher and a system autostart to this
# script, to fix Layla's window walking off the right of the screen. It put the
# tablet into a restart loop within a minute of the reboot: 48 restarts, a new
# Chromium every three seconds, and Angel watching sessions pile up.
#
# TWO THINGS WERE ALREADY TRUE ON THAT MACHINE AND I DID NOT LOOK.
#
# 1. THERE WAS ALREADY A LAUNCHER. `~/.config/systemd/user/banco-till.service`
#    starts the till and restarts it if it is closed. Adding a second launcher
#    is what caused the loop: my kiosk window opened first, so the till service's
#    Chromium found a running instance, printed "Opening in existing browser
#    session", exited 0 — and Restart=always started it again. Forever.
#
# 2. --kiosk HAD ALREADY BEEN TRIED AND REJECTED, with the reason written in
#    that unit file, in these words:
#
#        --start-maximized, NOT --kiosk: kiosk hides GNOME's own bar, which is
#        why nobody could see the battery, which is why the top-right corner got
#        dragged, which is how the window ended up two-thirds wide with no way
#        back.
#
#    So kiosk is not merely a different choice — it is the CAUSE of the exact
#    symptom I was trying to fix. Layla's off-screen window is what happens when
#    a cashier drags a title bar to reach a status bar that kiosk took away.
#
# The standing rule is "use what exists — never invent a second one", and I
# applied it to the repo and not to the machine. The answer was on the tablet,
# in a file, in plain words.
#
# So this block now UNDOES the experiment, so that one --push cleans a machine
# that got it. It is idempotent and harmless on a machine that never did.
# If you are ever tempted again: the launcher is banco-till.service, and the
# window-dragging fix belongs there, not here.
# ---------------------------------------------------------------------------
for f in /usr/local/bin/banco-kiosk \
         /usr/share/applications/banco-kiosk.desktop \
         /etc/xdg/autostart/banco-kiosk.desktop \
         /etc/default/banco-kiosk; do
  if [ -e "$f" ]; then rm -f "$f" && say "  removed $f  (the 2026-09-05 kiosk experiment)"; fi
done

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
