# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short.** It hit **1,734 lines** on 2026-08-13, at which point it
> stopped being a list you can open and act on. The narrative moved to
> [`worklist-archive/`](worklist-archive/) — **nothing was deleted**, and the split was verified
> line-for-line. **Keep it under ~150 lines**: when an item is finished, move it to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread
> grows a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-08-21.*

---

## 🔴 THE FOURTWENTY LOOKUP WAS NEVER LOADED — 2026-08-21 → [the measurement](worklist-archive/2026-08-21-fourtwenty-reference.md)

Angel: *"FourTwenty has the items, we just don't get matches… I have the feeling that they are
the proper numbers."* **Both halves are right, and he was doing nothing wrong.**

```
reference_products   Felix's shop 0 rows · sandbox 0 · lapiazza 0 · wolfhold: no table
scripts/import_reference_catalog.py — the only writer, per the model's own docstring
                     DOES NOT EXIST, and never has (git log --all finds nothing)
```

Every FourTwenty path in the app — `/reference/search`, `reference_matches`, `adopt`,
`_reference_best_match` — has queried an **empty table on every machine, for its whole life.**
Pattern 1 at its purest. And `web_product_lookup.py` (the thing he thinks is the FourTwenty
search) hits UPCitemdb and OpenFoodFacts — **it never touches 420.ch.**

**The data is real and it is in the monster repo:**
`helixnet/debllm/feeds/fourtwenty/products_latest.csv` — 10,082 rows, **9,977 with a real GTIN
(99.8%)**, prices and photos. Two of his three failed scans yesterday are in it with everything
(`4002450223400` Pueblo · `7666563986873` Sasso Hash); the actiTube genuinely is not.

⚠️ **Loading it is necessary, not sufficient.** Shelf-intake triage refuses to match unknowns
because *"a bare EAN carries no name"* — true only while the table was empty. And
`_find_catalog_matches` searches the reference **by title only, never by barcode**, though the
column is indexed and two other endpoints do use it.

**① THE IMPORTER IS BUILT AND PROVEN** — `scripts/import_reference_catalog.py` (`a9dda04`).
Sandbox: 0 → **10,082 rows**, idempotent on a second run, and `_reference_best_match` now
answers `4002450223400 → Pueblo Classic Tabak Dose 100g CHF 26.50 how=barcode`. Dry run unless
`--apply`. ⚠️ **Not run on prod — that is Angel's call.** It cannot change a price or a live
product; `reference_products` is read-only at the counter.

Three things its first dry run caught, each of which would have shipped:
- **FourTwenty's 18+ flag is their checkout policy, not the product** — they mark a USB wall
  plug `mindestalter: 18`. Importing it would have gated 2,220 rows, and `adopt` copies
  `age_restricted` straight onto the live product. **A till that IDs a phone charger teaches
  the cashier to click through the age gate.** Our classifier decides (829); theirs is kept in
  `raw` and printed as a disagreement.
- **`classify()` was already written for this table and had no caller** — its docstring says
  *"Map a REFERENCE ITEM to (our_category, our_class, age_restricted)"*.
- **Layer 2 had no alcohol branch.** A bottle's title is a brand, so 17 of 44 "Spirituosen"
  and **all 5** of "Bier, Wein & Champagner" would have loaded **un-gated**. Fixed; measured
  across all 10,082 rows: **22 newly gated, 0 un-gated.** 4 new tests.

**Still to do:** ② make an EAN miss CONSULT the reference by barcode — the scan miss and
shelf-intake triage; the endpoint exists, the flow does not use it. ③ then reverse-lookup
feed-title → live catalogue, human confirms, bind. ④ copy the feed out of `helixnet`.

*Reverse-matching by name is weak and now measured: "Tabak Beutel Sasso Tobaccos Hash 25gr."
does not reach "Sasso Tabaccos Brazil Hash BIO" at the 0.5 threshold. **Scan-time beats bulk.***

---

## 🔴 SIX REPORTS FROM THE TILL — 2026-08-20 (BL-9…BL-14) → [the evidence](worklist-archive/2026-08-20-till-reports.md)

**All six tagged `annoying`. Not one `blocking`.** Read that before reading Felix's verdict.

```
5,446 products live · 4,998 carry a MINTED 2000000… barcode (92%)
  414 findable by scanning the real packet (7.6%)
   29 of 107 sold catalogue lines had a real EAN (27%)
```

**Three of every four things Felix rings up cannot be scanned off the pack.** The buttons he
hates — department strip + "new item" form + pending-code banner, stacked at once — *only
appear because the scan missed.* Fewer buttons is the wrong fix; a scan that hits is the fix.

1. **🩸 THE LEAK — `scan.html:1385`.** `createNoCodeItem()` always mints, even when
   `pendingBarcode` holds the code that just 404'd and the screen is *displaying* it. Every
   item created today adds another unscannable row. = BL-9, BL-12, BL-13.
   Sibling: `catalog.html:1297` never seeds Barcode from the search box, and its hint
   *"leave it blank — a code is generated automatically"* is the bug written down as a feature.
2. **📷 `catalog.html:1692`** — `if (!this.snapPreview)` plus an `openCreate()` that never
   clears `snapPreview`/`snapName`/`pageUrl` ⇒ the panel shows the **previous** product's photo
   under the words "read from this photo". = BL-10, BL-11.
3. **BL-14 · the cursor** — title and body point opposite ways; needs 30 seconds of Angel
   showing me. Plus two unlabelled buttons in his screenshot — **unverified**, could be an
   html2canvas artifact, and a screen is checked in a browser.
4. **The tablet** — no Chrome by default, Firefox search "no good". Not specified yet.

The 4,998 already in there: bind-on-scan is built (BL-90); 18 real aliases bound so far.
Tamar publishes no EAN — but **FourTwenty does**, and that feed was never loaded. See the item
above; it is the same problem seen from the other end.

---

## 🔴 The silent-refresh bug — CLOSED 2026-08-13 → [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md)

Fixed in `9f34f85`; now pattern 6 in `CLAUDE.md` and a lesson in `LESSONS.md`.

---

## 🔍 OPEN, NOT REPRODUCED — the till felt slow in Angel's browser

`[Violation] 'click' handler took 1144–2077ms`, seven times between 13:05 and 13:14 on
2026-08-13. **Measured here and could not reproduce it:** Add-to-cart, quantity, payment
select all run **80–100 ms**, and Checkout 500 ms (a page navigation), with zero
violations — in headless *and* in a fully rendered browser under Xvfb. One "Add" click
fires **no** network at all.

Two theories ruled out by checking rather than guessing: no rebuild was running during
that window (the app container last started 12:52, his violations begin 13:05), and the
i18n MutationObserver is already scoped to `childList`+`subtree` on *added* nodes only,
with a comment naming this exact hazard.

**What is left, and it is testable in 30 seconds:** his screenshot shows **DevTools open**
with the Elements panel live, plus several browser extensions. Alpine mutates the DOM on
every keystroke and every cart change, and a live Elements panel re-renders on each one.
→ Close DevTools, ring the same cart, and see whether it still lags. If it does,
`scratchpad/click-probe.js` names the offending handler in his own browser.

*Not a defect until it reproduces without DevTools — but not closed either.*

---

## ✅ PROD IS LIVE ON TODAY'S CODE — 2026-08-14, ALL GREEN

Felix's shop is deployed and every readiness check passes:

```
✅ silent token refresh works — a session survives past the 5-min access token
✅ 18+ evidence is append-only (trg_ace_append_only installed)
✅ ALL GREEN.        banco.wolfhold.app 200 · banco-auth.wolfhold.app 200
```

**The 18+ evidence is now genuinely permanent on prod** — that trigger had never been
installed there, and until this deploy the table any screen called "append-only" could have
been rewritten by a single UPDATE. 13 compliance rules seeded, 0 active by design.
Felix rang a sale immediately afterwards; the audit cockpit caught it.

**Two things went wrong on the way, both mine, both now guarded:**

1. **The deploy silently did not run the first time.** `deploy-prod.sh` was typed without
   `./scripts/`, and the *command not found* scrolled past under 37 files of successful pull.
2. **I crash-looped Keycloak** — `You can not set both 'hostname' and 'hostname-url' options`.
   My own preflight, written that morning, **passed the broken config**, because it validated
   each value alone and never the pair. The app served 200 throughout, so **the shop looked
   alive while nobody could log in** — the nastier failure shape. Fixed, and the preflight now
   refuses the combination (proven by restoring the exact broken file).

⚠️ **The box is on `999800d`.** The two commits since — `250053f`, `b0cf512` — are compose and
script changes only, no app code. A `git pull` picks them up; **nothing needs redeploying.**

**Left over from the B2 detour:** the storage cap is lifted (31 GB, no cap, ~13¢/month). Still
worth doing when convenient — a lifecycle rule on `wolfhold-banco-backups` (229 dumps since
20 July, "keep all versions", nothing ages out), and a look at
`wolfhold-freehold-backups` (35 files, **30.7 GB** — that was what blew the cap, not Banco).

---

## ▶️ NOW — needs Angel's hands

1. **⛔ The two bulk catalogue scripts are blocked on WHERE they run, not on code.**
   Local dev has **6 products**; the 5,111 live on the prod/UAT box, and `deploy-prod.sh` is
   written to run *on* that server. Decide: a shell on prod, or a dump pulled down here. Then
   `enrich-from-source.py --apply` (~90 min) and `adopt-images.py --apply` (~137 min).
   → detail in [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md)

2. **🔫 The gun's inventory-mode dump is still unproven** — the last unknown in shelf intake, and
   the whole 10× path. Does a 20–30 code burst survive a browser textarea? ⚠️ The gun roles are
   **the reverse** of what the old deck assumed: the Netum has store mode, the Inateck does single
   scans. Re-test before planning around either.

---

## ✅ The 18+ evidence work — DONE, human-green 2026-08-13 → [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md)

Angel ran it and called it: *"it's working fine."* **Do not reopen it for another pass.**
`scripts/prove-till-18plus.js` (45 checks, rings as `ralph`) still runs before a promote.

---

## 🔜 NEXT

3. **🔐 Go-live hardening** — DNS preflight + a default-secret gate in `deploy-prod.sh`; and the DR
   restore (Move B), still **blocked on read-only B2 credentials**. The backup has never been
   restored, so it is a belief, not a capability.

4. **🌱 Seeded realm users are published — DEFERRED ON PURPOSE 2026-08-14, not forgotten.**
   `keycloak/import/realm-export.json` carries **six users with plaintext, non-hashed
   passwords**, and `github.com/akenel/banco-starter` is **public** (HTTP 200 unauthenticated):
   `felix` (`pos-admin`), `ralph` (`pos-manager`), `michael`, `pam`, `pos-developer`,
   `pos-auditor`. Both `compose.yml:39` and `compose.prod.yml:35` boot Keycloak with
   `--import-realm` from that same file — prod and dev seed from one export.
   **Angel's call, 2026-08-14: leave them.** The usernames aren't the secret, these are seeded
   demo accounts, and **he rotated `felix`'s password on the live box**, so the published one is
   dead for the account that actually has privilege. Reasonable.
   ⚠️ **The one mechanism that could quietly undo that:** Keycloak's `--import-realm` only seeds
   when the realm doesn't already exist. So today's rotation holds — *until the Keycloak DB
   volume is ever recreated* (`down -v`, a fresh box, a restore drill onto a clean box). Then the
   export re-imports and **`felix`'s password silently reverts to the published one**. The
   DR restore in item 3 is exactly that scenario. Whoever drills it: check `felix` afterwards.
   When it comes up the list: strip the six users from the export (freehold did this in
   `a202c32` — `kc-prd` ships `"users": []` and the first admin is made by hand), and treat all
   six published passwords as burned regardless. The other five still have live published
   passwords today.

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

## ⏲️ A decision the logs raised — how long may a till sit idle?

Angel's 15:46 logout was **correct**: 152 minutes idle against a 60-minute
`ssoSessionIdleTimeout`. Not the refresh bug returning — refresh verified 200 at the time
of writing. But it is worth deciding deliberately for the shop rather than inheriting it:
**60 minutes of a backgrounded tab and the cashier is logged out.** In the foreground the
till polls and the session stays warm; a tablet asleep over lunch does not. Overnight
logout is *desirable*; a quiet Tuesday afternoon one is not.

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
