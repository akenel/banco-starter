#!/usr/bin/env python3
"""The worklist alarm — says out loud when WORKLIST.md is due an archive pass.

    python3 scripts/worklist-check.py            # the repo's WORKLIST.md
    python3 scripts/worklist-check.py FILE       # any other copy, e.g. an old revision

WHY A SCRIPT, AND WHY IT IS NOT JUST A BIGGER NUMBER. The file has carried a length
rule since the day it was written. The rule was 150 lines, then 280. The file has been
1,734 · 1,201 · 2,307 — cut back three times and never once actually met. On 2026-09-04
it grew a thousand lines in a single session while the rule sat unread at the top of
the file it governed.

A rule broken three times is not fixed by being made easier. It is fixed by being
TRIGGERED. So the limit becomes 500 — honestly what the live file needs to hold — and
it gets something that says so without being asked. Angel, 2026-09-04 23:40:
"i think a 500 line worklist should be a reasonable limit or time to archive."

THE SECOND TRIGGER IS THE REAL ONE. The file's own rule was never the count, it was
"when a thread closes, it moves the same day" — and that is the one that got ignored.
So this also counts the sections still sitting in the LIVE file whose header says they
are finished. More than two → an archive pass is due even if the file is short.

⚠️ IT CAN ONLY SEE WHAT THE HEADER SAYS. On the night of 2026-09-04 nine threads were
closed and only two of their headers said so — the rest were bug titles that never
changed when the bug died. So this under-counts by design, and the convention it
depends on is: WHEN YOU CLOSE A THREAD, MARK ITS HEADER — ~~struck~~, **FIXED** or
**CLOSED**. The alarm then chases you to move it. An unmarked header is invisible here,
which is the honest limit of a fifteen-line check and the reason the line count exists
as a backstop.
"""
import pathlib
import re
import sys

def s(n, word):                       # "1 line", "2 lines" — an alarm that cannot count reads as noise
    return f"{n} {word}{'' if n == 1 else 's'}"


LIMIT = 500          # lines in the live file
MAX_CLOSED = 2       # finished threads still sitting in it
MARKERS = re.compile(r"FIXED|CLOSED|~~")

path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "WORKLIST.md")
if not path.is_file():                # run from the repo root; a traceback at SESSION START reads as breakage
    sys.exit(f"worklist-check: no {path} in {pathlib.Path.cwd()} — run it from the repo root")
lines = path.read_text().splitlines()   # splitlines, not split("\n") — must agree with `wc -l`

heads = [(i, ln) for i, ln in enumerate(lines) if ln.startswith("## ")]
bounds = [i for i, _ in heads] + [len(lines)]
sizes = {i: b - a for (i, _), a, b in zip(heads, bounds, bounds[1:])}
closed = [(i, ln) for i, ln in heads if MARKERS.search(ln)]

over_lines = len(lines) > LIMIT
over_closed = len(closed) > MAX_CLOSED

print(f"{path.name} — {s(len(lines), 'line')} (limit {LIMIT}) · "
      f"{s(len(closed), 'closed thread')} still here (limit {MAX_CLOSED}) · "
      f"{s(len(heads), 'section')}")

if not (over_lines or over_closed):
    sys.exit(0)

print("\n  ⚠️  ARCHIVE PASS DUE — " + " and ".join(
    ([s(len(lines) - LIMIT, "line") + " over"] if over_lines else [])
    + ([s(len(closed), "finished thread") + " not moved"] if over_closed else [])))

for i, ln in closed:
    print(f"      move · L{i + 1:<5} {sizes[i]:>4} lines  {ln[3:][:64]}")
if over_lines:
    print("      longest sections:")
    for i, ln in sorted(heads, key=lambda h: -sizes[h[0]])[:3]:
        print(f"             L{i + 1:<5} {sizes[i]:>4} lines  {ln[3:][:64]}")
print("\n  → worklist-archive/<date>-archive-pass.md, verbatim, nothing deleted.")
