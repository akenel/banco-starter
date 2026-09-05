#!/usr/bin/env bash
# tablet-lockdown-profile.sh — WHERE DO THE 51 SECONDS GO?
#
# banco-lockdown.service is Before=display-manager.service, so GDM cannot start
# until it finishes. Measured on the tablet 2026-09-05, twice, identically:
#
#     1min 11.257s  plymouth-quit-wait.service     <- waiting behind the next line
#          51.692s  banco-lockdown.service         <- ours
#
# That is 51.7s of a 1m46s boot sitting directly in front of the cashier, every
# morning. This script finds which lines spend it. It runs the REAL lockdown
# script under `set -x` with a clock on every line, then prints the biggest gaps.
#
# It changes nothing that lockdown would not change anyway — lockdown is
# idempotent and runs at every boot by design.
#
#     ssh -t tablet-admin 'sudo bash /home/art/tablet-lockdown-profile.sh'
#
# Angel, 2026-09-05.

set -uo pipefail

TARGET=${1:-/usr/local/sbin/banco-counter-lockdown}
RAW=$(mktemp /tmp/lockdown-trace.XXXXXX)

[ -r "$TARGET" ] || { echo "cannot read $TARGET (run me with sudo)" >&2; exit 1; }

echo "profiling $TARGET ..."
echo

START=$EPOCHREALTIME
# PS4 stamps every executed line with a high-resolution clock and its line number.
PS4='@@@${EPOCHREALTIME}|${LINENO}|'
export PS4
bash -x "$TARGET" --quiet >/dev/null 2>"$RAW"
RC=$?
END=$EPOCHREALTIME

echo "total: $(awk -v a="$START" -v b="$END" 'BEGIN{printf "%.2fs", b-a}')   (exit $RC)"
echo

awk -F'|' '
  /^@@@/ {
    t = substr($1, 4) + 0
    if (prev_t > 0) {
      gap = t - prev_t
      if (gap > 0.20) {
        printf "%7.2fs  line %-5s  %s\n", gap, prev_ln, prev_cmd
      }
    }
    prev_t = t; prev_ln = $2
    prev_cmd = $3
    for (i = 4; i <= NF; i++) prev_cmd = prev_cmd "|" $i
    if (length(prev_cmd) > 100) prev_cmd = substr(prev_cmd, 1, 100) "..."
  }
' "$RAW" | sort -rn | head -25

echo
echo "full trace kept at: $RAW"
