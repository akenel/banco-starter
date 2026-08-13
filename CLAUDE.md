# CLAUDE.md — Persistent Context (Banco POS starter)

*This file loads every session. It is your copilot's permanent memory for this repo. Keep it short, true, and current. Method: [Ground Control](https://github.com/akenel/ground-control) — see `STANDING-RULES.md` and `MEMORY-SYSTEM.md`.*

---

## RESUME CODE WORD — "OPEN SHOP"

When Angel says **OPEN SHOP** after a reboot, compaction, or fresh start, it means:
**stop, open `WORKLIST.md`, state the top items, and start executing the first actionable one — do not re-plan or re-ask what's already decided.**

- `WORKLIST.md` is the single source of truth for what's next, in order.
- Detail lives in `memory/` (see `MEMORY-SYSTEM.md`); the index is `MEMORY.md`.
- Change the code word or the deck anytime — update this section and `WORKLIST.md`.

> The code word = read the worklist and GO. No fumbling, no re-deriving — act on the top item.

---

## WHO WE ARE

**Angel (Angelo Kenel)** — the captain. Solo operator / second-career founder. Steers, decides, owns the direction.
- Building Banco to be *owned*, not rented. Runs a real Swiss shop on it today.

**Claude** — the pilot. Executes, reads before editing, proves before claiming done.
- Small trusted context over a firehose. Write to files, not chat.

---

## CURRENT SITUATION (2026-08-13)

- **Location:** `/home/angel/repos/banco-starter` (branch `main`, trunk-based).
- **Mission:** a production-grade, self-hostable POS a shop owner can stand up and own outright.
- **Status:** in acceptance testing with its first Swiss retail shop — not live yet. Card payments (Worldline), label printing and the kiosk are still being wired up. Meanwhile the *starter* is being hardened for others to self-host (go-live path, backups, restore, onboarding kit).
- **Open fronts:** see `WORKLIST.md`.

---

## STANDING RULES

*Full text in `STANDING-RULES.md` — these are the non-negotiables.*

1. **Write to files, not chat.** If it matters and it's only in chat, it didn't happen.
2. **Execute, don't note.** If it can be done this turn, do it this turn.
3. **Read before edit.** Never modify or overwrite a file not looked at this session.
4. **Prove, don't assume.** "Fixed" is a claim until the output is verified. Re-probe after every restart.
5. **Human-green beats machine-green.** Tests passing ≠ done. A human confirming it works is done.
6. **When you find one problem, check for the pattern.** One bad endpoint → check its siblings.
7. **Own the mistake, don't say "good enough."** Name it plainly and fix it, or say honestly it isn't done.

---

## THE PROJECT

**What it is:** a point-of-sale you stand up with one `docker compose up` and own outright — code, data, and runbook.
**Why it exists:** kill the "what if the vendor vanishes?" fear with ownership, not a promise. You can't clone SAP; you can clone this.
**Tech / tools:** FastAPI · SQLAlchemy (async, asyncpg) · Postgres 17 · Keycloak 24 (OIDC/RS256) · MinIO (S3) · Jinja2 + Alpine.js (vendored — no node build). Python 3.11.

### Key paths
```
banco-starter/
├── WORKLIST.md            # what's next, in order  ← code word opens this (keep it < 150 lines)
├── worklist-archive/      # the narrative, once an item is finished or a thread grows long
├── LESSONS.md             # the 45 lessons in full; CLAUDE.md keeps only the patterns
├── CATALOG-IDENTITY.md    # what actually names a product (EAN = identity, names = labels)
├── CLAUDE.md              # this file (loads every session)
├── MEMORY.md              # the memory index (one line per fact)
├── memory/                # one fact per file
├── STANDING-RULES.md      # the operating contract (source of truth)
├── MEMORY-SYSTEM.md       # how memory works
├── QUICKSTART.md          # the whole run + recovery runbook
├── compose.yml            # dev stack: postgres + keycloak + minio + app
├── compose.prod.yml       # prod stack (+ Caddy HTTPS)
├── scripts/               # init-banco, standup, doctor, backup/restore-to-b2, go-live, …
├── onboarding/            # demo → your-shop kit (roadmap, checklist, guides, testsheet)
├── keycloak/import/       # the POS realm (clients, roles, demo users) — auto-imported
└── src/                   # the FastAPI application
```

---

## HOW WE WORK (the operating loop)

1. **Steer, don't paste.** Point at the thing; the copilot fetches and reads it.
2. **One driver.** One session steers at a time. Orchestrate; don't juggle terminals.
3. **Cadence.** Trunk-based on `main`, small honest commits (see the conventional-commit log).
4. **Human-green, not machine-green.** For anything a shop owner will touch, a human confirms it.

---

## LESSONS — the patterns

*45 lessons and counting live in [`LESSONS.md`](LESSONS.md), each with the evidence that earned
it. **This list is the distillation** — the shapes that have bitten more than once. Read these;
open `LESSONS.md` when one of them is about to apply.*

**When something bites: add the narrative to `LESSONS.md`, and if it is a new instance of a
pattern below, bump the count here. A pattern at ×7 is telling you something a paragraph cannot.**

1. **×7 · Green on the layer you can reach says nothing about the layer the user stands on.**
   `cash_box_float`, the force-close, `POST /catalog/merge`, honest confidence, `best_match_score`,
   the 18+ refusals, the evidence with no screen — each existed on every layer a test could reach
   and on **no screen**. *Ask where the person is STANDING when they need it.*
2. **×4 · A downstream filter quietly discards the row the fix existed to find.** The dedup guard's
   same-size rule, the alias filters judging `products.name`, the category "boost" that was a sort
   key above `score`. *When you add a thing to match on, check every filter downstream still knows
   which one it is judging. A tier is a filter with extra steps.*
3. **×3 · A remembered failure is a hypothesis with a timestamp on it.** The Brother driver that had
   been fixed upstream; the spec-parser note that was backwards for three days; the bfcache cart bug
   I predicted from a missing guard and Angel disproved in ten seconds. *Re-measure before repeating
   a verdict — and before acting on a note you wrote last week.*
4. **×3 · Break the guard on purpose before claiming it holds.** A test that counted occurrences
   matched its own `def` line. Reverting each guard one at a time has caught something every time it
   has been done. *If you did not watch it go red, you do not know it works.*
5. **×2 · A script that recomputes what the server computes will accuse working code.** The rounding
   proof, and the partial prod copy that manufactured a 24-product compliance scare. *Get the
   reference figure FROM the system, and copy the columns that make a row TRUE, not the ones your
   task reads.*
6. **Anything a person touches is verified by a human or a browser — never by reading the template.**
   For server work, reading the code IS the verification. For a screen it is a guess with citations.
   `scripts/prove-till-18plus.js` exists because I got this wrong twice in one day.
7. **Verification against REALITY finds a class of error that verification against the database
   cannot.** A wrong barcode bind looks exactly like a right one; only re-scanning the packet tells
   them apart. Same for anything physical — "CUPS drained the job" is not "a label came out".
8. **Never invent an identifier that exists in the physical world.** 5,103 minted EANs made an
   otherwise excellent catalogue unusable at a till. Leave it blank; let the first scan bind it.
9. **Before filling an empty field, grep for its name in the comments.** A design that rejected
   something usually left a note saying so — `stock_quantity = 1` is the zero-perpetual design, not
   missing data.
10. **A validation nobody can see is a silent failure, and a green summary over an unchecked box is
    a lie.** Put the outcome where the button is, and never demand words a dropdown already said.

---

*Last updated: 2026-08-13*
*"You can't clone SAP. You can clone this."*
