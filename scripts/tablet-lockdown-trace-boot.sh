#!/usr/bin/env bash
# tablet-lockdown-trace-boot.sh — TIME THE LOCKDOWN WHERE IT IS ACTUALLY SLOW
#
# banco-lockdown.service takes 51.7s at boot and 1.28s when you run it by hand
# (measured on the tablet, 2026-09-05, with scripts/tablet-lockdown-profile.sh).
# Forty times slower, same script, same machine — so whatever costs the time is
# a condition of BOOT, and no profiler run from a shell can reproduce it. This
# installs a drop-in that traces the real boot run, with a clock on every line.
#
#     sudo bash tablet-lockdown-trace-boot.sh --install   # then cold boot
#     sudo bash tablet-lockdown-trace-boot.sh --report    # after the boot
#     sudo bash tablet-lockdown-trace-boot.sh --revert    # put it back
#
# SAFE BY CONSTRUCTION: display-manager.service is only ordered After= this unit,
# it does not Require it. If the traced command fails, lockdown fails and the
# tablet still boots to the till — it just boots without the settings re-applied,
# which one --revert and one reboot puts right. Nothing else is touched.
#
# Angel, 2026-09-05.

set -uo pipefail

DIR=/etc/systemd/system/banco-lockdown.service.d
DROPIN=$DIR/99-trace.conf
LOG=/var/log/banco-lockdown-trace.log
TARGET=/usr/local/sbin/banco-counter-lockdown

[ "$(id -u)" = 0 ] || { echo "run me with sudo" >&2; exit 1; }

case "${1:-}" in
  --install)
    [ -x "$TARGET" ] || { echo "no $TARGET" >&2; exit 1; }
    mkdir -p "$DIR"
    cat > "$DROPIN" <<EOF
# TEMPORARY — installed by scripts/tablet-lockdown-trace-boot.sh to find where
# 51.7s of a 1m46s boot goes. Remove with --revert.
[Service]
ExecStart=
ExecStart=/bin/bash -c 'export PS4="@@@\${EPOCHREALTIME}|\${LINENO}|"; exec /bin/bash -x $TARGET --quiet 2>$LOG'
EOF
    systemctl daemon-reload
    echo "installed. now COLD BOOT the tablet (power off, power on), then run --report."
    ;;

  --report)
    [ -s "$LOG" ] || { echo "no trace at $LOG — was the tablet cold booted since --install?" >&2; exit 1; }
    echo "trace: $LOG   ($(wc -l < "$LOG") lines)"
    echo "unit:  $(systemd-analyze blame 2>/dev/null | grep banco-lockdown || echo '(not in blame)')"
    echo
    echo "  GAP    LINE   COMMAND"
    awk -F'|' '
      /^@@@/ {
        t = substr($1, 4) + 0
        if (prev_t > 0) {
          gap = t - prev_t
          if (gap > 0.20) printf "%7.2fs  %-5s  %s\n", gap, prev_ln, prev_cmd
        }
        prev_t = t; prev_ln = $2
        prev_cmd = $3; for (i = 4; i <= NF; i++) prev_cmd = prev_cmd "|" $i
        if (length(prev_cmd) > 90) prev_cmd = substr(prev_cmd, 1, 90) "..."
      }
    ' "$LOG" | sort -rn | head -25
    ;;

  --revert)
    rm -f "$DROPIN"
    rmdir "$DIR" 2>/dev/null
    systemctl daemon-reload
    echo "reverted. banco-lockdown.service is back to its normal ExecStart."
    systemctl cat banco-lockdown.service --no-pager | grep ExecStart
    ;;

  *)
    echo "usage: sudo bash $0 --install | --report | --revert" >&2; exit 2 ;;
esac
