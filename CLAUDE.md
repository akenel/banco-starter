# CLAUDE.md — Persistent Context (Banco POS starter)

*This file loads every session. It is your copilot's permanent memory for this repo. Keep it short, true, and current. Method: [Ground Control](https://github.com/akenel/ground-control) — see `STANDING-RULES.md` and `MEMORY-SYSTEM.md`.*

---

## SESSION START — read these, in this order

*Copilot: this section is addressed to you. Do it at the start of every session, before answering anything.*

1. **This file**, top to bottom — who we are and how we work.
2. **`MEMORY.md`** — the memory index, one line per fact. Read the whole index; open a
   `memory/*.md` file only when its line says that fact is relevant to what we are doing **right now**.
3. **`WORKLIST.md`** — what's next, in order.

Do not skip step 2. Memory that is written and never read is just a folder of notes.

@MEMORY.md

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
- Building Banco to be *owned*, not rented. His first Swiss shop is in acceptance testing on it (see CURRENT SITUATION — not live yet).

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

1. **Write to files, not chat.** If it matters and it's only in chat, it didn't happen — and it goes in the file that actually gets read, updated in the same commit.
2. **Execute, don't note.** If it can be done this turn, do it this turn.
3. **Read before edit.** Never modify or overwrite a file not looked at this session.
4. **Prove, don't assume.** "Fixed" is a claim until the output is verified. Re-probe after every restart — and reproduce a bug the way a shop owner hits it before fixing it.
5. **Human-green beats machine-green.** Tests passing ≠ done. A human confirming it works is done. Keep the proof with the change.
6. **Steer, I row.** Angel owns direction; the copilot owns execution.
7. **One driver per tree.** Never two copilots in one working directory. Parallel work gets its own checkout and its own worklist.
8. **Own the mistake.** "My input was wrong" beats "the tool can't handle it."
9. **When you find one problem, check for the pattern.** One bad endpoint → check its siblings.
10. **Don't say "good enough."** Do it right, or say honestly that it isn't done.
11. **Price the work like a machine.** "Overkill for now" is a trained-in bias, not a judgment — ask what it would choose if the build were nearly free.

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
├── LESSONS.md             # every lesson in full; CLAUDE.md keeps only the patterns
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
2. **One driver per tree.** Never two copilots in one working directory — separate checkouts, separate worklists, or sequential.
3. **Cadence.** Trunk-based on `main`, small honest commits (see the conventional-commit log).
4. **Human-green, not machine-green.** For anything a shop owner will touch, a human confirms it.

---

## LESSONS — the patterns

*Every lesson lives in [`LESSONS.md`](LESSONS.md) in full, each with the evidence that earned
it. **This list is the distillation** — the shapes that have bitten more than once. Read these;
open `LESSONS.md` when one of them is about to apply.*

**When something bites: add the narrative to `LESSONS.md`, and if it is a new instance of a
pattern below, bump the count here. A pattern at ×7 is telling you something a paragraph cannot.**

1. **×11 · Green on the layer you can reach says nothing about the layer the user stands on.**
   `cash_box_float`, the force-close, `POST /catalog/merge`, honest confidence, `best_match_score`,
   the 18+ refusals, the evidence with no screen — each existed on every layer a test could reach
   and on **no screen**; the tablet's LTE was proved on Angel's home Wi-Fi, in a flat, with a route
   metric set on an SSID Luzern does not have; the USB webcam worked in GNOME in ten seconds
   while Banco **hid its own camera button on any touchscreen**, leaving the one machine that had
   just grown a camera with no path to it; and on 2026-08-27 I proved a new SKU lookup by **TYPING
   the SKU** — the one way it would never be entered. The gun sends SHIFT a beat late, so it
   arrives as `sKU-`, and my fix was green everywhere I could reach and dead at the counter.
   That same evening Angel hunted a bong through his catalogue, the photo matcher and Google and
   said *"i have no chance"* — `GET /reference/search` finds it from the one word "rasta" and was
   wired into Receiving and Scan but **not into the screen that creates products**. Third this
   week, after the clone endpoint and the force-close.
   *Ask where the person is STANDING when they need it — which building, and which screen.*
2. **×7 · A downstream filter quietly discards the row the fix existed to find.** The dedup guard's
   same-size rule, the alias filters judging `products.name`, the category "boost" that was a sort
   key above `score`; on 2026-08-22 `eligible_subtotal` dropped two full-price papers because
   pooling them had set `tier_final`, so a manager's discount silently skipped them; and on
   2026-08-24 the new catalog export filtered `category` with `=` while the screen it sits on uses
   `ILIKE '%x%'` — so picking "Bongs" showed "Pipes & Bongs" on screen and left it out of the file;
   and on 2026-08-27 an **exact** barcode match discarded 2,632 supplier rows (24% of the feed),
   because a UPC-A and an EAN-13 are one code with and without a leading zero and nothing
   reconciled them. Super Wrap Gold was "not even on the internet" while sitting three tables away.
   *When you add a thing to match on, check every filter downstream still knows which one it is
   judging. A tier is a filter with extra steps, and a flag is a filter you cannot see. A SECOND
   way to ask the same question must be tested against the FIRST, never against your own
   expectations — pick the input where a wrong predicate has to differ.*
3. **×4 · A remembered failure is a hypothesis with a timestamp on it.** The Brother driver that had
   been fixed upstream; the spec-parser note that was backwards for three days; the bfcache cart bug
   I predicted from a missing guard and Angel disproved in ten seconds; and the tablet camera written
   off on 2026-08-05 as "nothing attached to the other end" — ACPI declares **two fitted sensors**,
   and the August verdict had inferred absent hardware from absent log lines. *Re-measure before
   repeating a verdict. Absence in a log is not absence in the world — ask the registry that knows,
   and write the expiry condition into the note.*
4. **×4 · Break the guard on purpose before claiming it holds — and break the COMBINATION,
   not just the fields.** A test that counted occurrences matched its own `def` line. A deploy
   preflight that rejected "localhost" passed happily on `https://` with the host unset. And on
   2026-08-14 that same preflight passed a config that **could not boot** — because it checked
   each value alone and never whether setting *both* was legal. Keycloak crash-looped and the
   shop could not log in. *A guard that validates fields but not their relationship is half a
   guard, and it is the more confident half.* A test that counted occurrences
   matched its own `def` line. Reverting each guard one at a time has caught something every time it
   has been done. *If you did not watch it go red, you do not know it works.*
5. **×2 · A script that recomputes what the server computes will accuse working code.** The rounding
   proof, and the partial prod copy that manufactured a 24-product compliance scare. *Get the
   reference figure FROM the system, and copy the columns that make a row TRUE, not the ones your
   task reads.*
6. **×3 · A test that finishes inside five minutes cannot see a five-minute timeout.** Silent
   token refresh had NEVER worked in the sandbox — issuer mismatch, `localhost:8090` vs
   `keycloak:8080` — so every session hard-logged-out the moment the access token expired. Every
   probe I write runs in 90 seconds with a fresh token, so nothing I could build would have found
   it. **Angel found it in ten minutes of ordinary use, and lost a compliance record to it.**
   *Ask what your harness is structurally blind to: time, idleness, a second tab, a real day.*
   2026-08-22: `prove-cart-agrees-with-till` ran green all day over 320 quantities while the cart
   quoted a discount the drawer would not give — because it compares line totals and **never
   constructs a discounted basket**. Not a gap in coverage; a shape the harness cannot make.
7. **Anything a person touches is verified by a human or a browser — never by reading the template.**
   For server work, reading the code IS the verification. For a screen it is a guess with citations.
   `scripts/prove-till-18plus.js` exists because I got this wrong twice in one day.
8. **Verification against REALITY finds a class of error that verification against the database
   cannot.** A wrong barcode bind looks exactly like a right one; only re-scanning the packet tells
   them apart. Same for anything physical — "CUPS drained the job" is not "a label came out".
9. **Never invent an identifier that exists in the physical world.** 5,103 minted EANs made an
   otherwise excellent catalogue unusable at a till. Leave it blank; let the first scan bind it.
10. **Before filling an empty field, grep for its name in the comments.** A design that rejected
   something usually left a note saying so — `stock_quantity = 1` is the zero-perpetual design, not
   missing data.
11. **When the human says it works, it works — that is the finish line, not a new lap.** On
    2026-08-13 Angel ran the sheet, marked it PASS and asked *"do you agree?"*. I came back with
    three more findings, **two of which were my own mess** — my test rows sitting in his evidence,
    and a step whose question his flow never reached. He said: *"I don't know what you're looking
    for anymore."* Fair. Standing rule 5 cuts both ways: a human confirming it is DONE. Report
    what genuinely blocks a promote; log the rest and move on.
12. **×3 · A truth test has to answer the question a PERSON is asking.** A validation nobody can
    see is a silent failure, and a green summary over an unchecked box is a lie. 2026-08-27 added
    two: a correct, well-worded refusal rendered as an 8-second toast at the top of the viewport
    while the operator's eyes were on a modal — *"i could not actually read the error"*, and he
    zoomed to 40% to find it; and `fourtwenty.ch` publishes its description as ONE U+200C
    zero-width non-joiner, which is invisible, **truthy**, and survives `.strip()` — so
    `if description:` said "there is one" and the model was never asked to read the page body, on
    every page, for as long as that code existed. *Put the outcome where the button is; never
    demand words a dropdown already said; and make `is it empty?` mean what the human means.*
13. **×3 · The server is right, the tests are green, and the STORED COPY the screen renders from is
    wrong.** On 2026-08-24 in one afternoon: the kiosk refused a blank username the server accepts;
    `/customers/new-today` kept deactivated members because it filtered `created_at` and not
    `is_active`; and Clear cart emptied `this.cart` while leaving `pos_cart` in sessionStorage,
    which the page restores from on every load — so the cart came back and clearing twice could not
    help. Not logic errors; *synchronisation* errors between a truth and its cached shadow, and the
    shadow always wins because the shadow is what renders. *State written in one place and read in
    another needs an owner: ask of every reset/clear/cancel — what did this write, and does this
    delete ALL of it?* A clear that clears one key of three is not a clear.
14. **A mechanical failure in an easy case gets read as proof the hard case is impossible.**
    2026-08-27: a leading zero, a late shift key, a lookup that never read the SKU and a filename
    that overwrote itself stacked up until an *exact-identity* case — a product sitting in the
    catalogue with a valid code — presented itself as "it's not even on the internet". Angel spent
    half an hour with three windows open and concluded matching was hopeless. Matching genuinely IS
    hard (145 codes on >1 product; a right match at 0.46 scoring under a wrong one at 0.66) — but
    none of that was in play. *Before improving the fuzzy layer, prove the EXACT layer works end to
    end on the machine the person is standing at. The quiet failure of the easy path is what sends
    people reaching for cleverness, or for bulk, exactly where neither was needed.*

---

*Last updated: 2026-08-27*
*"You can't clone SAP. You can clone this."*
