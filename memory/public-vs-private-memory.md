---
name: public-vs-private-memory
description: Two memory systems run here — repo memory/ is PUBLIC on GitHub, harness memory is private. Never merge across the line.
type: feedback
---

There are **two** memory systems in play on `banco-starter`, and only one of them is portable:

1. **Repo memory — `MEMORY.md` + `memory/`.** The Ground Control kit. Committed, and
   `github.com/akenel/banco-starter` is **public** (verified 2026-08-27, `isPrivate:false`) —
   so every word in `memory/` is world-readable. This is the one that ships, that a stranger
   cloning the starter inherits, and that survives changing tools. It is the canonical system.
2. **Harness memory — `~/.claude/projects/-home-angel-repos-banco-starter/memory/`.** Claude
   Code's own store. Private to this machine, auto-loads every session, and dies with the tool.

**Why:** the whole Ground Control claim is that you *own* your context rather than rent it to one
vendor — so project facts belong in the repo. But the harness store holds Angel's age, languages,
runway, pension and career direction, and the two server IPs. Sweeping those into `memory/` to
"dedupe" would publish them to the internet. The tidying instinct and the privacy boundary point
in opposite directions here, which is exactly why this is written down.

**How to apply:**
- **Project fact, public-safe** (design decisions, how the stack works, lessons about the code)
  → repo `memory/`. If it already exists in the harness store, leave a pointer there, not a copy.
- **Personal, financial, or infrastructure-identifying** (age, money, health, IPs, hostnames,
  credentials-location) → harness memory **only**. Never move it into `memory/`.
- **One fact, one owner.** When both stores touch the same subject, decide which one owns it and
  make the other a one-line pointer. Two full copies drift, and the stale one is invisible.
  Worked example: mechanics live in [[browser-tests-borrow-playwright]]; the harness twin
  `verify-screens-in-a-browser` keeps the lesson and points at it.
- Before writing to `memory/`, ask the one question: *would I put this in a GitHub issue?*

Relates to [[use-ground-control-method]], [[who-is-angel]], [[name-is-trademark-reserved]].
