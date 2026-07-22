# The Memory System

*How to keep a growing, file-based memory that doesn't rot. This is the engine that lets your copilot pick up exactly where you left off — a week or a month later.*

---

## The shape

Two layers:

1. **The index** — one file (`MEMORY.md`) the copilot loads every session. One line per memory. This is the map.
2. **The memories** — one file per fact, in a `memory/` folder. This is the territory. The copilot opens a memory file only when the index line tells it that fact is relevant *right now*.

The split matters: the index stays cheap to load, the detail stays out of the way until needed.

---

## One fact, one file

Each memory is a single markdown file holding **one fact** — a decision, a lesson, a piece of project state, a person, a reference. Small and single-purpose. When a fact changes, you update its file; you don't hunt through a wall of text.

Suggested frontmatter:

```markdown
---
name: <short-kebab-case-slug>
description: <one line — used to decide relevance when scanning the index>
type: user | feedback | project | reference
---

<The fact. For feedback/project memories, follow with:>
**Why:** <why this matters>
**How to apply:** <what to actually do about it>

<Link related memories with [[their-slug]]. Link liberally.>
```

## The four types

| Type | What it captures | Example |
|------|------------------|---------|
| **user** | Who you are — role, expertise, preferences | "Prefers Python for all new tooling" |
| **feedback** | How the copilot should work — corrections and confirmed approaches, *with the why* | "Present URLs as single clickable lines" |
| **project** | Ongoing work, goals, constraints not visible in the code or history | "One real user, not a paying customer yet — don't inflate metrics" |
| **reference** | Pointers to external things — URLs, dashboards, tickets, credentials-location | "Infra box IP + where the SOPs live" |

## The index line

After you write a memory file, add exactly one line to `MEMORY.md`:

```
- [Short Title](file-slug.md) — one-line hook so future-you knows when to open it
```

That's it. The index is never the place for memory *content* — just pointers.

---

## Hygiene — how it stays healthy

**Before saving, check for a duplicate.** If a file already covers this, update *that* file. Don't spawn a second memory saying almost the same thing — that's how memory rots into contradiction.

**Delete what turns out wrong.** A memory reflects what was true when written. When it's proven false, remove it. A wrong memory is worse than no memory.

**Don't save what the code already records.** File structure, past fixes, commit history — the repo already holds those. Memory is for what you *can't* re-derive from the work itself: decisions, reasons, corrections, the non-obvious.

**Convert relative dates to absolute.** "Next week" is a landmine in a file read three months later. Write the actual date.

**Link liberally.** A `[[slug]]` that doesn't exist yet isn't an error — it's a note that there's a memory worth writing later. Links turn a pile of files into a web you can navigate.

---

## The habit that powers it

At the end of a working session, ask one question:

> *What did I learn or decide today that future-me will need and can't re-derive from the code?*

Whatever the answer is — write it to a memory file, add the index line, done. Thirty seconds. That thirty seconds is the difference between a copilot that grows with you and one that forgets you every morning.
