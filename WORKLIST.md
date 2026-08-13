# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short.** It hit **1,734 lines** on 2026-08-13, at which point it
> stopped being a list you can open and act on. The narrative moved to
> [`worklist-archive/`](worklist-archive/) — **nothing was deleted**, and the split was verified
> line-for-line. **Keep it under ~150 lines**: when an item is finished, move it to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread
> grows a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-08-13.*

---

## ▶️ NOW — needs Angel's hands

1. **🔞 The 18+ gate — the human-green run.**
   → [`onboarding/testsheets/AGE-GATE-HUMAN-HALF.html`](onboarding/testsheets/AGE-GATE-HUMAN-HALF.html)
   · 12 steps, ~20 min.
   Machine side is done: `prove-till-18plus.js` is **27 checks, 0 failed, 1 known gap**, sabotaged
   three times. The sheet carries only what a machine cannot judge — **wording, feel, and the
   German** (H5, open since 08-12 and explicitly not passable on a shrug). Then P1–P3 promote it.

2. **⚖️ F2 — "👤 Remove member & continue" turns the hard DOB block into a soft one.**
   *(Angel + Felix. Pinned as a KNOWN GAP in the test output so it cannot rot quietly.)*
   Verified: minor + attest → 400; remove the member, attest → 201 `cashier_attest`. The button
   **must** exist — Pam scans the wrong loyalty card and the person really is 40 — but it is the
   *first* button under *"rook is under 18"*, where a thumb lands. Move it below Refuse? Require a
   manager? Reword it? Not obviously a bug; genuinely a decision.

3. **✅ BUILT 2026-08-13 — the 18+ record has a screen, and Pam can open it.** Needs your eyes.
   `/pos/age-report`, a **cashier tile on the dashboard** (not manager-only — your D6: *"felix will
   not be in the shop when the inspector shows up"*), printable, EN + DE.
   Shows how each 18+ sale was cleared (the three bases in plain words, with **why one is weaker**),
   the refusals with reasons, and — first on the page — a **warning when refusals are zero**,
   because that is the reading an inspector makes on his own.
   **No schema value reaches the reader** and no buyer identity is in the payload (FADP).
   Proven by driving it as `pam` in both languages; suite is now **32 checks**, and the
   plain-words guarantee was sabotaged (`cbd_hemp` leaked → red) before being believed.
   ⚠️ **One thing I did not decide for you:** stored refusal notes are English — the row is the
   record and I will not rewrite an append-only table. The screen shows German for the three known
   reasons and the raw note otherwise. Say if you want it differently *before* many rows exist.

4. **📊 Nothing produces a compliance VERDICT.** `compliance_check_run` is written by no code, and
   all 13 rules ship `is_active = false` pending a human reading each authority
   (`authority_checked_at`). Who does that reading, and what is the evidence it happened?
   Two rules — `CBD-INGESTIBLE`, `THC-LAB-PAPER` — **can never be proven by query**: the evidence
   is a lab certificate and a supplier declaration, i.e. a document plus a dated human attestation.

---

## 🔜 NEXT

5. **⛔ The two bulk catalogue scripts are blocked on WHERE they run, not on code.**
   Local dev has **6 products**; the 5,111 live on the prod/UAT box, and `deploy-prod.sh` is
   written to run *on* that server. Decide: a shell on prod, or a dump pulled down here. Then
   `enrich-from-source.py --apply` (~90 min) and `adopt-images.py --apply` (~137 min).
   → detail in [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md)

6. **🔫 The gun's inventory-mode dump is still unproven** — the last unknown in shelf intake, and
   the whole 10× path. Everything so far was one code at a time. Does a 20–30 code burst survive a
   browser textarea? ⚠️ And the gun roles are **the reverse** of what the old deck assumed: the
   Netum has store mode, the Inateck does single scans. Re-test before planning around either.

7. **🔐 Go-live hardening** — DNS preflight + a default-secret gate in `deploy-prod.sh`; and the DR
   restore (Move B), still **blocked on read-only B2 credentials**. The backup has never been
   restored, so it is a belief, not a capability.

---

## 🧹 NEEDS TRIAGE — read before trusting

[`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) holds ~1,000
lines of catalogue, till and shelf-intake items written between 07-30 and 08-07. **Their status was
not re-verified when they were archived**, and at least one was already wrong:

> the shared cash box was filed as *"design agreed 2026-08-03, not built"* — it shipped in
> `fd035dd`, and the `cashier_id == user_id` filter it describes is gone from the code.

**So: check the code before acting on anything in there.** Promoting the still-live ones up to NOW
is a 20-minute job worth doing once, not a thing to re-derive every session.

---

## 📌 Standing facts worth not re-learning

- **The app image bakes `src/` in — there is no bind mount.** `docker compose restart app` restarts
  the **old** code and says nothing. Any change under `src/` needs `./scripts/rebuild.sh`.
- **Prod authenticates against the DEMO realm** (`kc-pos-realm-dev`, users felix/pam/ralph),
  imported from a file **in a public GitHub repo**. Still the go-live blocker.
- **Banco is zero-perpetual.** `stock_quantity = 1` is the *design*, not missing data. Never set
  `min_stock` / `max_stock` / reorder points — `/reorder/suggestions` ranks by what the till sold.
- **`age_check_event` is append-only** (a PL/pgSQL trigger, not `REVOKE` — which is a no-op against
  a table owner). Nothing can tidy a row away, including a mis-tap.

---

## 🧪 How to prove it before claiming it

| what | command |
|---|---|
| stand up | `./scripts/rebuild.sh` → `./scripts/standup.sh` |
| server-side 18+ evidence | `BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py` |
| **the actual screens** | `BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-till-18plus.js` |

⚠️ Both scripts **ring real completed sales** and refund them afterwards; a completed transaction is
a line in the Kassenbuch. `BANCO_ALLOW_FAKE_SALES=1` exists so it cannot happen by accident.
Playwright is **borrowed via `NODE_PATH`, not vendored** — this repo has no node build, on purpose.

---

## 📚 The archive

| file | what's in it |
|---|---|
| [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md) | Gate Zero, and the whole 18+ evidence thread 08-10 → 08-13 |
| [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) | catalogue, shelf intake, till and search, through 08-07 — **status unverified** |
| [`worklist-archive/backlog.md`](worklist-archive/backlog.md) | not yet scheduled — offline kit, monitoring, labels, exports |
| [`worklist-archive/done.md`](worklist-archive/done.md) | shipped, most recent first, with commit hashes |
