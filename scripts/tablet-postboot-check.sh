#!/usr/bin/env bash
# ============================================================================
# tablet-postboot-check — did the till come up the way it is supposed to?
#
#   ./scripts/tablet-postboot-check.sh            (defaults to host `tablet`)
#   ./scripts/tablet-postboot-check.sh counter2
#
# Run it FROM THE LAPTOP. Read-only, no sudo anywhere: everything it looks at
# is world-readable or belongs to the till user, on purpose — a check that
# needs a password is a check nobody runs.
#
# WHY THIS FILE EXISTS. `postboot-check.py` asks "is the SERVER up and safe to
# test?". Nothing asked the same question of the machine a cashier actually
# touches. The lockdown script prints eleven confident "wrote …" lines and then
# nobody looks again — and on 2026-09-05 a kiosk autostart I added put that
# machine into a 48-restart loop a minute after a reboot, which is precisely
# the window this covers and precisely the window nothing watched.
#
# IT CHECKS THE SETTING, NOT THE FILE. This is the whole point and it is
# LESSON #1: a dconf keyfile on disk is the layer I can reach; whether the
# magnifier is actually off and actually locked is the layer Layla stands on.
# `dconf update` has to have compiled the keyfile into /etc/dconf/db/local, and
# the user's session has to have read it. So every settings check reads the
# LIVE value through gsettings and asks dconf whether it is still writable —
# a value that is right but unlocked is one accidental pinch-zoom from wrong.
#
# It also asserts things are ABSENT. The boot job removes the kiosk experiment
# at every start; a check that only looks for what should be there would pass
# happily while the thing that caused the loop crept back.
set -uo pipefail

HOST="${1:-tablet}"
PASS=0; FAIL=0; WARN=0
ok()   { PASS=$((PASS+1)); printf '  ✅ %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  ❌ %s\n' "$1"; [ $# -gt 1 ] && printf '       %s\n' "$2"; }
warn() { WARN=$((WARN+1)); printf '  ⚠️  %s\n' "$1"; [ $# -gt 1 ] && printf '       %s\n' "$2"; }

# One ssh, one round trip, everything gathered as key=value. Twenty separate
# ssh calls take twenty seconds and each one is another chance for the network
# to be the thing under test instead of the tablet.
R=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST" '
  say() { printf "%s=%s\n" "$1" "$2"; }
  say uptime_s   "$(cut -d. -f1 /proc/uptime)"
  say boot_id    "$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)"
  say last_boot  "$(who -b 2>/dev/null | awk "{print \$(NF-1), \$NF}")"

  # ── files the lockdown lays down ──────────────────────────────────────────
  for f in /etc/dconf/profile/user \
           /etc/dconf/db/local.d/00-banco-counter \
           /etc/dconf/db/local.d/locks/banco-counter \
           /etc/dconf/db/local \
           /etc/chromium/policies/managed/00-banco-search.json \
           /usr/local/sbin/banco-counter-lockdown \
           /etc/systemd/system/banco-lockdown.service; do
    [ -e "$f" ] && say "file:$f" yes || say "file:$f" NO
  done
  # the compiled db must be NEWER than the keyfile, or dconf update never ran
  if [ -e /etc/dconf/db/local ] && [ -e /etc/dconf/db/local.d/00-banco-counter ]; then
    [ /etc/dconf/db/local -nt /etc/dconf/db/local.d/00-banco-counter ] \
      && say db_newer yes || say db_newer NO
  else
    say db_newer missing
  fi

  # ── the kiosk experiment must STAY gone ───────────────────────────────────
  for f in /usr/local/bin/banco-kiosk \
           /usr/share/applications/banco-kiosk.desktop \
           /etc/xdg/autostart/banco-kiosk.desktop \
           /etc/default/banco-kiosk \
           "$HOME/.config/autostart/banco-kiosk.desktop"; do
    # KEY ON THE BASENAME, NOT THE PATH. $HOME expands on THIS side, so a key of
    # "gone:$HOME/..." came back as /home/art/... while the laptop looked up the
    # literal string — no match, empty value, and this script announced that the
    # file which caused the 48-restart loop WAS BACK. It was not. A checker that
    # cries wolf about the worst thing it knows about is worse than no checker.
    [ -e "$f" ] && say "gone:$(basename "$f")@$(dirname "$f")" STILL_THERE \
                || say "gone:$(basename "$f")@$(dirname "$f")" yes
  done

  # ── the settings AS THE SESSION SEES THEM, and whether they are locked ────
  for k in "org.gnome.desktop.a11y.applications screen-magnifier-enabled" \
           "org.gnome.desktop.a11y.applications screen-reader-enabled" \
           "org.gnome.desktop.a11y.applications screen-keyboard-enabled" \
           "org.gnome.desktop.a11y always-show-universal-access-status" \
           "org.gnome.desktop.interface enable-hot-corners"; do
    set -- $k
    say "gset:$1/$2" "$(gsettings get "$1" "$2" 2>/dev/null || echo ERR)"
    say "lock:$1/$2" "$(gsettings writable "$1" "$2" 2>/dev/null || echo ERR)"
  done

  # ── services ──────────────────────────────────────────────────────────────
  say lockdown_enabled "$(systemctl is-enabled banco-lockdown.service 2>&1)"
  say lockdown_result  "$(systemctl show banco-lockdown.service -p Result --value 2>&1)"
  say lockdown_exec    "$(systemctl show banco-lockdown.service -p ExecMainStatus --value 2>&1)"
  say till_active      "$(systemctl --user is-active banco-till.service 2>&1)"
  say till_enabled     "$(systemctl --user is-enabled banco-till.service 2>&1)"
  say till_restarts    "$(systemctl --user show banco-till.service -p NRestarts --value 2>&1)"
  say till_since       "$(systemctl --user show banco-till.service -p ActiveEnterTimestamp --value 2>&1)"
  say chromium_procs   "$(pgrep -c chromium 2>/dev/null || echo 0)"
  # WILL IT COME BACK BY ITSELF? banco-till.service is a USER unit wanted by
  # graphical-session.target, so it needs a logged-in desktop. Without autologin
  # the tablet boots to a GDM prompt and waits for a password nobody at the
  # counter has.
  say autologin_on   "$(grep -m1 "^AutomaticLoginEnable" /etc/gdm3/daemon.conf 2>/dev/null | cut -d= -f2 | tr -d " ")"
  say autologin_user "$(grep -m1 "^AutomaticLogin=" /etc/gdm3/daemon.conf 2>/dev/null | cut -d= -f2 | tr -d " ")"
  say linger         "$(loginctl show-user "$USER" -p Linger --value 2>/dev/null)"
  # DID IT ACTUALLY HAPPEN, though. Reading AutomaticLoginEnable out of a config file
  # says what was ASKED for. On 2026-09-05 this script reported "GDM logs in as art by
  # itself" from the config alone, on a boot where that happened to be true — and it
  # would have printed the identical line if autologin had silently failed and a human
  # had typed the password during the 45 seconds before the check ran. Which is exactly
  # the fault this same file calls out two checks higher up. So: ask the SESSION which
  # PAM service created it, and how long after boot.
  say gsession_svc  "$(loginctl list-sessions --no-legend 2>/dev/null | awk "\$5==\"user\"||\$3==\"$USER\" {print \$1}" | while read -r i; do t=$(loginctl show-session "$i" -p Type --value); [ "$t" = wayland ] || [ "$t" = x11 ] && loginctl show-session "$i" -p Service --value; done | head -1)"
  say gsession_at   "$(loginctl list-sessions --no-legend 2>/dev/null | awk "\$5==\"user\"||\$3==\"$USER\" {print \$1}" | while read -r i; do t=$(loginctl show-session "$i" -p Type --value); [ "$t" = wayland ] || [ "$t" = x11 ] && loginctl show-session "$i" -p TimestampMonotonic --value; done | head -1)"
  # and the three settings that decide whether it is still awake in fifteen minutes
  for k in "org.gnome.desktop.screensaver lock-enabled" \
           "org.gnome.desktop.session idle-delay" \
           "org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type"; do
    set -- $k
    say "gset:$1/$2" "$(gsettings get "$1" "$2" 2>/dev/null || echo ERR)"
    say "lock:$1/$2" "$(gsettings writable "$1" "$2" 2>/dev/null || echo ERR)"
  done
  say whoami         "$USER"
  say failed_units     "$(systemctl --failed --no-legend 2>/dev/null | wc -l)"
  say failed_user      "$(systemctl --user --failed --no-legend 2>/dev/null | wc -l)"

  # ── can it actually reach the shop, from there ────────────────────────────
  # NOT curl. THE TABLET HAS NO CURL — checked, 2026-09-05: `command -v curl` is
  # empty on it. The first version of this line reported "the till has no network"
  # about a machine that was online, because the tool was missing, not the network.
  # python3 ships with the desktop and is already what everything else here needs.
  say shop_http "$(python3 -c "
import urllib.request
try:
    print(urllib.request.urlopen(\"https://banco.wolfhold.app/pos\", timeout=12).status)
except Exception as e:
    print(\"ERR:\" + type(e).__name__)" 2>/dev/null)"
  say shop_build "$(python3 -c "
import urllib.request
try:
    print(urllib.request.urlopen(\"https://banco.wolfhold.app/static/build-sha.txt\", timeout=12).read().decode().split()[0])
except Exception:
    print(\"\")" 2>/dev/null)"
' 2>&1)

if [ -z "$R" ] || printf '%s' "$R" | grep -qi "^ssh:"; then
  echo "cannot reach '$HOST' — $R" >&2; exit 2
fi
get() { printf '%s\n' "$R" | grep -m1 "^$1=" | cut -d= -f2-; }

echo
echo "══ $HOST · up $(( $(get uptime_s) / 60 )) min (booted $(get last_boot)) ══"

echo
echo "── the lockdown is on disk ──"
for f in /etc/dconf/profile/user /etc/dconf/db/local.d/00-banco-counter \
         /etc/dconf/db/local.d/locks/banco-counter /etc/dconf/db/local \
         /etc/chromium/policies/managed/00-banco-search.json \
         /usr/local/sbin/banco-counter-lockdown /etc/systemd/system/banco-lockdown.service; do
  [ "$(get "file:$f")" = yes ] && ok "$f" || bad "$f is MISSING" "the lockdown did not run, or something removed it"
done
case "$(get db_newer)" in
  yes) ok "the compiled dconf db is newer than the keyfile — \`dconf update\` really ran" ;;
  NO)  bad "the keyfile is NEWER than the compiled db" "the settings on disk are not the settings in force — run: ssh -t $HOST 'sudo dconf update'" ;;
  *)   bad "cannot compare the dconf db with its keyfile" ;;
esac

echo
echo "── and the kiosk experiment stayed gone ──"
for k in "banco-kiosk@/usr/local/bin" \
         "banco-kiosk.desktop@/usr/share/applications" \
         "banco-kiosk.desktop@/etc/xdg/autostart" \
         "banco-kiosk@/etc/default" \
         "banco-kiosk.desktop@$(printf '%s' "$R" | grep -m1 '^gone:banco-kiosk.desktop@/home' | sed 's/^gone:[^@]*@//; s/=.*//')"; do
  n=${k%@*}; d=${k#*@}
  v=$(get "gone:$k")
  if [ -z "$v" ]; then warn "could not check $d/$n" "no answer for that path"
  elif [ "$v" = yes ]; then ok "no $d/$n"
  else bad "$d/$n IS BACK" "this is what put the till in a 48-restart loop on 2026-09-05"; fi
done

echo
echo "── the settings a cashier actually meets ──"
chk() { # key · expected · plain english
  local v l; v=$(get "gset:$1"); l=$(get "lock:$1")
  if [ "$v" != "$2" ]; then bad "$3 — reads $v, expected $2" "the file may be right; this is the value the session is using"
  elif [ "$l" != "false" ]; then bad "$3 is correct but NOT LOCKED (writable=$l)" "one accidental tap changes it and nothing puts it back until the next boot"
  else ok "$3 (locked)"; fi
}
chk "org.gnome.desktop.a11y.applications/screen-magnifier-enabled"        false "the magnifier is off"
chk "org.gnome.desktop.a11y.applications/screen-reader-enabled"           false "the screen reader is off"
chk "org.gnome.desktop.a11y.applications/screen-keyboard-enabled"         true  "the on-screen keyboard is available"
chk "org.gnome.desktop.a11y/always-show-universal-access-status"          false "the accessibility icon is hidden"
chk "org.gnome.desktop.interface/enable-hot-corners"                      false "hot corners are off"

echo
echo "── services ──"
[ "$(get lockdown_enabled)" = enabled ] && ok "banco-lockdown.service is enabled — it re-applies all of this at every boot" \
  || bad "banco-lockdown.service is $(get lockdown_enabled)" "nothing will repair the tablet after the next boot"
[ "$(get lockdown_result)" = success ] && ok "and its last run succeeded" \
  || bad "its last run ended: $(get lockdown_result) (exit $(get lockdown_exec))"
[ "$(get till_active)" = active ] && ok "banco-till.service is running" \
  || bad "banco-till.service is $(get till_active)" "the till is not on the screen"
[ "$(get till_enabled)" = enabled ] && ok "and it starts itself at boot" \
  || bad "banco-till.service is $(get till_enabled) — it will not come back by itself"

# THE LOOP CHECK. Restarts are not failures in themselves — Restart=always is
# how the till heals — but restarts CLIMBING right after boot is the 00:12 bug,
# and it looked "active" the whole time it was happening.
r=$(get till_restarts); u=$(get uptime_s)
if [ "$r" -eq 0 ]; then ok "0 restarts since boot"
elif [ "$u" -gt 0 ] && [ "$r" -gt 5 ] && [ "$u" -lt 600 ]; then
  bad "$r restarts in the first $((u/60)) minutes" "this is the shape of the 48-restart loop — something else is opening a browser"
else warn "$r restarts since boot" "not a loop at this rate, but worth knowing why"; fi

c=$(get chromium_procs)
[ "${c:-0}" -gt 0 ] && ok "chromium is up ($c processes — one browser is many)" \
  || bad "no chromium process" "the service says active but nothing is drawing the till"
[ "$(get failed_units)" = 0 ] && ok "no failed system units" || warn "$(get failed_units) failed system unit(s)"
[ "$(get failed_user)" = 0 ] && ok "no failed user units"   || warn "$(get failed_user) failed user unit(s)"

echo
echo "── and would it come back on its own after a power cut? ──"
# THE QUESTION ANGEL ACTUALLY ASKED, 2026-09-05: "make sure when the tablet boots
# up that all the configurations are in place." Everything above can be perfect
# and the till still not appear, because the till is a user service and a user
# service needs somebody to log in. Every check above passed on a machine that
# would have booted to a login prompt and stopped.
al=$(get autologin_on); au=$(get autologin_user); me=$(get whoami)
svc=$(get gsession_svc); at=$(get gsession_at)
if [ -n "$at" ] && [ "$at" -gt 0 ] 2>/dev/null; then
  secs=$(( at / 1000000 ))
  if [ "$svc" = gdm-autologin ] && [ "$secs" -lt 120 ]; then
    ok "the desktop session was created by gdm-autologin, ${secs}s after boot — nobody typed anything"
  elif [ "$svc" = gdm-autologin ]; then
    warn "gdm-autologin created the session, but ${secs}s after boot" "that is late enough that something waited for a human"
  else
    bad "the desktop session came from \"$svc\", not gdm-autologin (${secs}s after boot)" \
        "somebody signed in; the till does NOT start unattended"
  fi
else
  warn "could not read when the desktop session started" "cannot tell whether autologin actually fired"
fi
if [ "$al" = true ] && [ -n "$au" ]; then
  if [ "$au" = "$me" ]; then ok "and it is configured to, as $au"
  else bad "GDM autologs in as \"$au\", but the till service belongs to \"$me\"" "the wrong user's session starts and banco-till.service never runs"; fi
else
  bad "NO AUTOLOGIN — the tablet boots to a login prompt and waits" \
      "banco-till.service is a user unit (WantedBy=graphical-session.target), so nothing starts the till until a person types the OS password. After a power cut at the counter the screen is a Debian login screen. Fix: ./scripts/tablet-lockdown.sh --push $HOST --autologin"
fi
[ "$(get linger)" = yes ] && warn "user lingering is on" "harmless here, but it is not what starts the till — a graphical session is" \
  || ok "user lingering is off (correct — the till needs a real desktop, not a headless unit)"

echo
echo "── and is it still awake in fifteen minutes? ──"
chk "org.gnome.desktop.screensaver/lock-enabled"                     false      "the till does not lock itself"
chk "org.gnome.desktop.session/idle-delay"                           "uint32 0" "the screen never blanks on idle"
chk "org.gnome.settings-daemon.plugins.power/sleep-inactive-ac-type" "'nothing'" "it does not suspend on mains"

echo
echo "── and it can reach the shop from where it sits ──"
[ "$(get shop_http)" = 200 ] && ok "banco.wolfhold.app answers (HTTP 200)" \
  || bad "the shop answered $(get shop_http)" "the till has no network, or the shop is down"
b=$(get shop_build); [ -n "$b" ] && ok "serving build $b" || warn "could not read the build stamp"

echo
echo "=========================================="
printf '  %s passed · %s failed · %s to look at\n' "$PASS" "$FAIL" "$WARN"
[ "$FAIL" -eq 0 ] || exit 1
