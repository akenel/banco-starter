---
name: use-ground-control-method
description: In this repo, operate the Ground Control way — files over chat, code word, memory loop.
type: feedback
---

Angel adopted the Ground Control method for `banco-starter` (2026-07-22) and asked the copilot to actually use it, not just install it.

**Why:** The whole point is to stop re-explaining the repo every session. It only pays off if the copilot lives by it — writes decisions to files, resumes from `WORKLIST.md` on the code word, and keeps `memory/` current.

**How to apply:**
- Write decisions, lessons, and situation changes to files (memory/, WORKLIST.md, CLAUDE.md) — not just chat.
- On **"OPEN SHOP"**, open `WORKLIST.md`, state the top items, execute the first actionable one.
- Hold the 11 standing rules in `STANDING-RULES.md` — read before edit, prove before "done", check for the pattern.
- End a working session by asking: what did I decide today that future-me can't re-derive? Write it.

**✅ PROVEN WORKING 2026-08-27 — and it had NOT been, for the repo's whole life.** `MEMORY-SYSTEM.md`
claimed the index "loads every session"; nothing made that happen (no `.claude/`, no hooks, no
`@`-ref), so `memory/` was decoration and every session started blind. Fixed by porting the kit's
**SESSION START** block + `@MEMORY.md` into `CLAUDE.md` (`1d95103`).

**How it was proved — the method matters, because a session that can read files will just go read
them and look like it worked:**
1. `claude -p '…' --disallowedTools 'Read,Grep,Glob,Bash,…'` — with every file tool DENIED it still
   listed all 8 index entries verbatim. It could only have had them at startup. **This is the test:
   deny the tools, then ask.**
2. `OPEN SHOP` with write tools denied → it opened `WORKLIST.md`, went to the top item, located the
   fix to a line, and refused to claim it worked without a browser. Correctly did **not** open a
   memory body, and said why: none was relevant.
3. A natural question about handing off the browser tests → it opened
   `memory/browser-tests-borrow-playwright.md` **first**. On-demand body reads work.

**How to apply:** re-run test 1 after any change to `CLAUDE.md`'s top matter or the index — the
whole system is silent when it breaks, which is how it stayed broken for months. Relates to
[[public-vs-private-memory]], [[who-is-angel]], [[banco-is-real-production]].
