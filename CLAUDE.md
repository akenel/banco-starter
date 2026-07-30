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

## CURRENT SITUATION (2026-07-22)

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
├── WORKLIST.md            # what's next, in order  ← code word opens this
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

## LESSONS (append-only)

When something bites you, write the lesson here in one line so it never bites twice.

- 2026-07-22 — Inline comments on `.env` value lines get parsed as the value; keep comments on their own line.
- 2026-07-28 — `lsusb` lists the Brother QL-820NWB **even when it's switched off** (USB chip runs on bus power). "Device is present" ≠ "device is on" — confirm the LCD is lit before debugging anything else.
- 2026-07-28 — CUPS queues auto-made by `cups-browsed` (`implicitclass://…`) are **temporary and disappear**. For anything a shop depends on, create a permanent queue with `lpadmin` pointed straight at the real device URI.
- 2026-07-28 — The QL-820NWB's **first job after waking takes ~25–30 s** (roll calibration); later jobs take ~4 s. A slow first label is not a stuck queue — don't cancel it early and go hunting for a bug that isn't there.
- 2026-07-28 — **`ipp-usb` goes stale after minutes and never recovers**: `0 bytes` on every request, blank web page, print jobs hang — while the printer sits there lit and `READY`. `sudo systemctl restart ipp-usb` fixes it *without touching the printer*, and that's also the diagnostic. A blanked LCD + blinking LED reads exactly like standby and sent me chasing the printer's Auto Power Off for an hour. **Suspect the daemon before the hardware.**
- 2026-07-28 — **"CUPS drained the job" is NOT "a label came out."** The printer accepts the data in ~3 s and only *then* rejects it, so a clean `lpstat` proves nothing. I called success on several jobs that printed nothing. For anything physical, the only proof is a human holding the thing.
- 2026-07-28 — When a device's behaviour makes no sense, **read its own status registers before touching settings**. The QL answers `ESC i S` over raw USB with media width, media type and error bits. One read ended hours of guessing between roll types — and proved the settings had been right all along. Hunt for the device's diagnostic channel early.
- 2026-07-28 — **`@page{ size: 62mm auto }` is INVALID CSS** — the spec allows `auto` OR one/two lengths, never a length plus `auto`. Browsers drop the declaration and silently fall back to **A4**, so a label renders in the corner of a sheet and the label printer discards it: no error, clean CUPS drain, green LED, nothing printed. **When a browser print does nothing, `Save as PDF` and run `pdfinfo` on it** — it shows what the browser actually decided, not what you assumed. That one command ended a three-hour hunt.
- 2026-07-28 — After changing print CSS, **hard-refresh (`Ctrl+Shift+R`) or use a private window**. Inline styles ride along with a cached page, so we kept testing a fix that was already deployed.
- 2026-07-28 — Three Brother-specific drivers (`printer-driver-ptouch` 1.6, `brother_ql` 0.9.4, `brother_ql_next` 0.12.0) printed **zero** labels on the QL-820NWBc — every raw-raster job rejected as "wrong roll type" — while the generic CUPS `everywhere`/IPP path worked. **The vendor-specific driver is not automatically the better bet.** Prefer the path with verified output over the one that looks more purpose-built.
- 2026-07-28 — `ipp-usb` redirects every request to `http://localhost:60000/` regardless of the address you use, so "use 127.0.0.1 instead" does *not* dodge an IPv6-first `localhost`. This box's `/etc/hosts` was also missing the standard `127.0.0.1 localhost` / `::1 localhost` lines entirely — worth checking with `getent ahosts localhost` when a local service hangs.

- 2026-07-30 — **A catalogue full of MINTED barcodes is a catalogue you cannot scan.** The July import created 5,111 products; Tamar publishes no EAN, so Banco fabricated `2xxx` codes for 5,103 of them. Every field was excellent (99% prices/images/categories) and the one fabricated column made the whole thing unusable at a till. **Never invent an identifier that exists in the physical world** — leave it blank and let the first scan bind it.
- 2026-07-30 — **"The data is good" and "the data is usable" are different claims.** Spent hours proving search worked while Angel kept saying it didn't. Both true: search ranked his product #1, but he wasn't searching — he was *scanning*, and a scan can't fall back to a name. Answer the job the person is doing, not the one you can measure.

---

*Last updated: 2026-07-30*
*"You can't clone SAP. You can clone this."*
