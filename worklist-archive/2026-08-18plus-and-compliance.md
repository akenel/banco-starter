# Archive — Gate Zero and the 18+ / compliance thread (2026-08-10 → 08-13)

*Moved out of `WORKLIST.md` on 2026-08-13 when it hit 1,734 lines. Nothing edited — this is the narrative as written. The live items live in [`../WORKLIST.md`](../WORKLIST.md).*

---

## 🚪 GATE ZERO — ANSWERED 2026-08-10

*`GO-LIVE-PLAN-felix.md` §0 refuses to let anything proceed until this is written
down, because the whole plan inverts on it. Here it is, in Felix's own words.*

> *"I just want to scan stuff and know what I sold. Today it's paper and pen."*
> — Felix, 2026-08-10

**Q: Is Felix already trading on BANCO in production? → NO.** He is on paper.
Corroborated below: the parallel run (D) has not happened, and prod still
authenticates against the DEMO realm.

**The good half.** The untested restore is *not* a live emergency. No shop is
running on an unproven recovery path. That was the nightmare branch and we are
not on it.

**The half that costs.** Per §0, a NO means there is a **data-migration
milestone — existing stock and till state → BANCO — that appears in none of the
source plans.** It is Phase 0, task zero.

- [ ] **Scope the data migration before any go-live date is spoken.** What is in
      the paper system today, what has to come across, and what is allowed to
      start empty. Perpetual inventory is deliberately zero, so this is smaller
      than it sounds — but it is not nothing, and it has never been sized.

**And the sentence that should govern the sequencing:** *"I just want to scan
stuff and know what I sold."* Scan → sell → know what left the shop. Anything on
this board that does not serve that is not go-live work.

---

## ✅ THE 18+ EVIDENCE WORK IS SANDBOX-PROVEN — 2026-08-12

*`d4144d4` ended with "NOT yet exercised against a live database — sandbox next."
That run has now happened, locally, on build `caaab67`.*

**Machine-green, 17/17.** `scripts/prove-age-evidence.py` (new) walks the whole gate
against the live stack: a clean cart records `not_required` (never NULL) · an attested
walk-in records `cashier_attest` and snapshots the line · a refusal returns 400 **and
the evidence row outlives it** · `member_dob` and `member_confirmed` are recorded apart
· a member proven 15 by DOB is refused **even with the cashier attesting** · no buyer
identity is stored · UPDATE and DELETE are refused on both evidence tables.

**Sabotaged on purpose first** (08-07 rule). Deleted the `commit` from
`_record_age_refusal` and rebuilt — the refusal check went red, then green again on
restore. The guard is real, not decoration.

> ⚠️ **And the sabotage taught the local-testing rule:** the app image **bakes `src/`
> in — there is no bind mount.** `docker compose restart app` restarts the OLD code and
> says nothing. My first sabotage run "passed" because the container never saw it.
> **Any change under `src/` needs `./scripts/rebuild.sh`.**

**🔴 THE FINDING — the evidence has no screen. Sixth instance of this repo's most
repeated bug** (`cash_box_float`, the force-close, `/catalog/merge`, honest confidence,
`best_match_score`). `grep` src/ for `age_check_outcome`, `was_age_restricted`,
`age_check_event` or any `compliance_*` table: **every hit is a WRITE.** No endpoint, no
template, no report. Every check in the probe had to read it with `psql`.

And it lands harder here than in any of the five, because **the entire point of this
work is that a person can be SHOWN the record.** The seed SQL itself calls "records
stored in editable folders" a standing nonconformity — records reachable only from a
database prompt are not obviously better. **Felix cannot run `psql`.** Ask where the
person is standing when they need it.

Also still missing: **nothing produces a verdict.** `compliance_check_run` is written by
no code — the schema, the append-only guarantee and the 13 seeded rules are real; the
engine is not. All 13 ship `is_active = false` deliberately, pending a human reading each
authority (`authority_checked_at`).

### 🔴 THE HUMAN RUN FOUND TWO THINGS THE PROBE COULD NOT — 2026-08-12, Angel

*He marked B, C and D all PASS. Both findings below are hiding inside a PASS, which is
why they needed a person: the screen answered correctly and the record still lies.*

**1 · ✅ FIXED SAME DAY — `age_check_event.txn_ref` POINTED AT THE WRONG SALE.**
Not a missing link: a **false** one, in a compliance record, which is worse than NULL
because it reads as authoritative. *(Fix and re-test below.)*

`create_sale` (`pos_router.py:5957`) computes `TXN-{today}-{count+1:04d}` from the count
of **committed** transactions. A refusal raises 400 and never commits — so it never
consumes its number, and **the next sale takes it.** Proven end to end:

```
A · an 18+ sale is refused        -> refusal filed against TXN-20260812-0027
B · next customer buys a Lollipop -> completes as        TXN-20260812-0027
C · the evidence now reads: "18+ refusal on TXN-0027" — and TXN-0027 is a 0.50 lollipop
```

Across the whole sandbox: **12 of 13 refusals "belong" to a completed sale, and 3 of
those sales have no 18+ line at all.** Only 1 was a genuine turn-away.

⚠️ **Same column, two meanings.** On `checkout_transaction` the transaction is already
persisted, so `txn_ref` is real and correct. On `create_sale` — the modern till path —
it was a number destined for somebody else's purchase.

**THE FIX (2026-08-12, re-tested):** `refusal_txn_ref=None` on `/sales`, and a new
`age_check_event.cart_ref` carrying the cart's **`client_uuid`**. The checkout path is
untouched — there the reference is true.

`client_uuid` turned out to be **better than merely safer**, not just honest. The till
persists it in `sessionStorage` and **clears it only on success, keeping it across an
error so a retry reuses it** (`checkout.html:1141`). So a cashier who is refused, ticks
the 18+ box and completes the sale writes a refusal and a transaction carrying the
**same `cart_ref`** — while the next customer, on a fresh uuid, cannot be falsely joined
to it. **"Turned away, then sold anyway, same cart, seconds apart" is queryable for the
first time** — the single most audit-relevant pattern in the whole gate.

One subtlety worth keeping: `txn_ref` fed **two** things — the refusal row *and* the
clearance log line. Blanking it wholesale would have blanked the log too, where the
number IS real (a cleared sale commits). So they are split now: `txn_ref` for the log,
`refusal_txn_ref` for what gets persisted.

**Re-tested — probe now 24 checks, all green**, including two new ones that replay
Angel's exact finding (refuse, then ring a lollipop for the next customer → that sale
must carry no refusal). **Sabotaged on purpose:** restored `refusal_txn_ref=transaction_number`,
rebuilt, and the refusal landed on `TXN-0036` — the next customer's lollipop — with both
new checks red. Restored, green again.

⚠️ The false rows from before the fix **cannot be corrected — the table is append-only,
by design.** As of 2026-08-13 the sandbox holds **17 false links across 52 refusals, 7 of
them pointing at a sale with no 18+ line at all** (the count grew with each probe run
before the fix landed). They stay visible as history. Nothing shipped to prod, so there
is no bad shop data anywhere — but decide before promoting whether UAT starts clean.

**2 · "Remove member & continue" is a one-click path around the DOB block.** Verified
over HTTP: minor attached + attestation → **400 refused**; remove the member, attest as
a walk-in → **201, recorded `cashier_attest`.** The server keeps no memory that a proven
minor was on this cart three seconds earlier.

The button must exist — Pam scans the wrong loyalty card and the person really is an
adult. **But it is the FIRST button, worded "continue", sitting directly under
*"rook is under 18"*** — the path of least resistance is the one that sells to the minor,
and the completed sale looks like any other attested walk-in. This is a decision for
Angel + Felix, not obviously a bug: at minimum the refusal and the retry should be
joinable (see finding 1 — today they are not).

**3 · And one flaw in the sheet, mine.** E2 said "read the six critical statements" but
E1 only ever printed the `authority` column — the legal source, not the claim. Angel
answered from the authority list because the sentences were never on screen. Fixed: E2
now has its own command. The statements are plain English and perfectly answerable
(*"Every completed sale containing an age-restricted line carries a recorded basis on
which the buyer's age was cleared"*). **The step answered a question nobody asked — the
exact shape this sheet exists to catch, in the sheet itself.**

**Angel's answers that change the design:**
- **D6 · Felix will NOT be in the shop when the inspector arrives.** So the
  inspector-facing view must be operable by **Pam, a cashier** — not a manager-only
  report. *"lets write the process in docs and test it via PAM."*
- **E4 · "we need some reports for pam and felix IMHO"** — agrees with the no-screen
  finding above.
- **E3 · "not sure what this means — do we need more code?"** No. `CBD-INGESTIBLE` and
  `THC-LAB-PAPER` cannot be proven by any query because **the evidence lives outside
  Banco** (a lab certificate, a supplier declaration). They need a document + a dated
  human attestation, or they stay a permanent human sign-off. That is a design answer,
  not a coding one.

### 🔴🔴 NO PATH THROUGH THE TILL CAN PRODUCE A REFUSAL RECORD — 2026-08-13, v2 run

**`age_check_event` holds 52 rows. All 52 say `refused`. All 52 were written by my
probe over raw HTTP. Not one was ever created by a person at the till, and none can be.**

The v2 sheet told Angel to press **"✅ Confirm 18+ walk-in"** with a DOB-proven minor
attached — the one case where client and server disagree. **That button is not rendered
in that state.** `checkout.html:505` says so in its own comment: *"hidden when a
KNOWN-minor member is attached (it can't clear the server gate; would just loop)"*. It was
also visible in his 08-12 screenshot, which showed exactly two buttons. **I wrote an
instruction for a button I had already been shown does not exist.**

Every route to a server refusal is closed client-side:

| cashier does | POST? | server sees | evidence row |
|---|---|---|---|
| no member → 🚫 remove 18+ item | **no** | nothing | **none** |
| no member → ✅ confirm walk-in | 201 | cleared | none (by design) |
| minor member → 👤 remove member → ✅ confirm | 201 | cleared | none |
| minor member → 🚫 remove 18+ item | **no** | nothing | **none** |
| minor member → ✅ confirm walk-in | **button not rendered** | — | — |

**The half that DOES work:** clearances land on `transactions.age_check_outcome`, and
that is real and correct — his v2 run produced `TXN-20260813-0005` and `-0006` both
reading `cashier_attest`. That is the durable, sale-joined record `d4144d4` promised.
`age_check_event` is refusals-only by design (a refusal has no transaction to hang on) —
there is exactly one writer in the codebase, `_record_age_refusal`, and the till never
reaches it.

**Is `efbc056` still a real fix?** Yes — the 17 false links prove the defect was real, and
the probe proves it is gone. But it can only ever be exercised by the probe. From where
Angel stands, nothing improved, and he is right to say so.

**✅ FIXED 2026-08-13 (`f0a15fc`) — Angel chose the confirm step.** 🚫 Refuse now asks
*"Why? This is recorded."* with four answers; the fourth, *"↩︎ Just taking it off — not a
refusal"*, writes nothing. Reasons are a **closed list, validated server-side** (`400` on
anything else) — no free text, because 08-03 cost a CHF 500 skim by demanding a sentence
after a dropdown. `saleUuid()` was extracted so the refusal and any later sale on the same
cart share one `cart_ref`; minting a fresh uuid at sale time would have silently turned
*"turned away, produced ID, sold anyway"* into two unrelated customers.
**Three human-made refusal rows now exist — the first in this project's history.**

### ✅ THE "CART COMES BACK" SCARE — WRONG, AND CHECKED TWICE

I saw the previous sale's items on each of his receipts, found that `scan.html` has no
`pageshow`/bfcache guard while `checkout.html` has one whose comment names that exact
hazard, and called it a probable money bug. **It is not.**

Angel checked at the screen — *"the back button goes to a clean new sale, works fine"* —
and the browser suite now asserts it on every run: **Back from a receipt lands on
`/pos/scan` with an empty cart**, and a fresh New Sale is empty too. The accumulating
receipts were him re-adding items, not the till re-serving them.

**A code smell is a hypothesis.** Same lesson as the spec parser that was "backwards for
three days" and the Brother driver that had been fixed upstream: the missing guard is
real, the consequence I predicted from it is not.

*What IS real, and Angel found it:* the scan header shows the **previous** transaction
number at the top of a new sale until you refresh. Cosmetic — and worth noting that it is
the same fiction that caused `efbc056`: **the "next number" is a prediction, and a
prediction is not an identifier.**

### 🧪 NEW — `scripts/prove-till-18plus.js`: THE PROBE THAT CAN SEE A BUTTON

The Python probe was 25/25 green on a feature no cashier could reach. **A probe that posts
JSON cannot see an `x-show`.** So there is now a Playwright suite that drives the real
screens as `pam` — **27 checks, 0 failed, 1 pinned KNOWN GAP** — and it asserts the
things that actually bit us:

- the 🔞 modal fires and **no POST is made** (the client stops it)
- **the modal's buttons, enumerated in both states** — with a minor attached, "✅ Confirm
  18+ walk-in" is *absent*. That is the assertion that would have stopped me writing two
  bad testsheet steps.
- 🚫 Refuse asks why, writes the row, and the row is **read back and checked**: outcome,
  a NULL `txn_ref`, the cashier's own username, the reason, the cart thread. "Just taking
  it off" writes nothing. *(This check used to BE a pinned gap — that is what pins are for.)*
- ✅ attest → `cashier_attest`; of-age member → `member_dob` (both recorded, both correct)
- minor → remove member → attest → sale completes → **KNOWN GAP (F2)**
- `efbc056` from the UI: no sale rung carries another cart's refusal
- cart hygiene after a completed sale (the scare above, now a permanent guard)

**Sabotaged three times before being believed** (the 08-07 rule): the age item pointed at
a non-gated product → 5 red; the `x-show` guard removed from the walk-in button → check 4
red; `if (false)` around the new refusal POST → 5b red. Each on exactly the right line,
each reverted and rebuilt green. Plus the endpoint's own guards over HTTP:
`reason=whatever` → 400, empty → 400, no auth → 403.

It **refunds its own sales** (as manager — `pam` cannot refund, and should not be able to)
and never touches the evidence rows, which are append-only.

```
BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=/home/angel/repos/helixnet/node_modules \
  node scripts/prove-till-18plus.js
```

⚠️ Playwright is **borrowed, not vendored** — this repo has no node build on purpose, so
the suite reads it from a sibling repo via `NODE_PATH`. If that repo moves, point
`NODE_PATH` somewhere else; the script exits 2 with instructions rather than failing oddly.

### 🔴 THE RETEST FOUND SOMETHING BIGGER THAN THE THING IT WAS RETESTING — 2026-08-13

**THE REFUSAL A CASHIER ACTUALLY PERFORMS IS NEVER SENT TO THE SERVER.**

Angel ran the v1 retest, got `(0 rows)` where a refusal row should have been, and marked
it ISSUE with *"not sure if i am doing the tests right"*. He was doing them exactly right.
**The sheet was wrong, and being wrong is what exposed this.**

`ageRefuse()` (`checkout.html:1048`) is pure client-side JavaScript: it filters the 18+
line out of the cart, closes the modal, and **never calls the server**. And
`completeTransaction()` returns *before* the POST whenever `needsAgeGate()` is true. The
client mirrors the server's rule faithfully — so the client always wins first and **the
server is never troubled at all**.

**Proven from the app log, not inferred:** across his entire 14-minute run there were
exactly **three** `POST /api/v1/pos/sales`, all **201 Created**. Not one 400. His 0-row
readings were correct readings of a test that never happened.

```
what a cashier does 100×/week   no ID -> take the item off  -> NO RECORD
what the probe tested           HTTP POST with age_verified false -> 400 -> row
```

The only till path that reaches a server refusal is the **disagreement** case: a member
proven under 18 by DOB *plus* a cashier attestation — client allows, server refuses. That
is rare. **So `age_check_event` captures the exception and misses the rule**, and "we can
prove our refusals" is a far smaller claim than it sounded yesterday.

⚠️ **This is the repo's own lesson biting again** (2026-08-03, and again on 08-06): the
probe proved the *server* path, which is machine-reachable, and no test could reach the
button a human presses. It took a human pressing it, on a sheet whose expectation was
wrong, to surface it. **Not a regression** — it has been this way since the gate shipped.

**Not fixed — it is a decision, not a bug.** Recording every counter refusal means every
mis-tap becomes a permanent, un-deletable compliance row (the table is append-only by
design). That trade is F1 on the v2 sheet.

*Also observed, unexplained:* his three receipts each carried the previous cart's items
along (`TXN-0001` papers+sticker → `TXN-0002` +lollipop → `TXN-0003` +grinder cards).
`pos_cart` **is** cleared on success (`checkout.html:1207`) and kept on a 4xx (correct).
Most likely he re-added by hand; worth one look, not yet a finding.

**▶️ NEXT, and it needs Angel's hands — HUMAN-GREEN, THEN PROMOTE:**
[`onboarding/testsheets/AGE-GATE-HUMAN-HALF.html`](onboarding/testsheets/AGE-GATE-HUMAN-HALF.html)
— **11 steps, ~20 minutes.** One command to let the machine go first, then only what a
machine cannot judge: **wording, feel, and the German.** H2 asks him to read the refusal
out loud with a customer waiting; H3 asks whether "Refuse" is the honest word for a button
that removes an item and lets the rest of the sale through; H5 is the German, still open
from 08-12 (*"not sure my german not that good"*) and explicitly not passable on a shrug.
Then P1–P3 for promote, and the two decisions.

**The two earlier sheets are retired, both because of me:**
`REFUSAL-EVIDENCE-RETEST.html` — v1 and v2 each sent him to press a button that does not
exist in the state described. `AGE-EVIDENCE-TESTSHEET.html` (27 steps) is **done**, passed
08-12; do not re-run it. Everything either of them could still usefully assert is now in
`prove-till-18plus.js`, which runs in 90 seconds and cannot mis-remember a screen.

*Sandbox stand-up, in order:* `./scripts/rebuild.sh` → `./scripts/standup.sh` → seed the
pack → `BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py` (server) →
`BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=… node scripts/prove-till-18plus.js` (screens).

---

*Set 2026-08-07 after four days that were not in this file: the X1 tablet + Bluetooth label
printing (08-04), the shop-model audit and papers/filters shelf intake (08-05), catalogue search
and the no-barcode workflow (08-06), and a money-safety run (08-06→07). All shipped to prod. None
of it has been touched by a person yet, and **2026-08-03 cost 62 minutes and seven defects — every
one a screen, none reachable from the API.** So this is the work now, in this order.*

**▶️ A · FIVE MINUTES ON THE TABLET — the till guard and the cashier price panel.**
   Shipped `45085a3` + `976eb0a`, verified live server-side, **never seen by a human**.
   1. Sign in as **Pam** (cashier). Scan / search `ITEM-0212` (*Grandma's Baking Again*, 999.99).
      → expect a **red panel on the product**: "This item has no price yet", one price field,
      **Set price & add to cart**. Type a price → it saves, goes in the cart, sale completes.
   2. Sign in as a **manager**. Same item → the **amber** manager panel opens instead, price field
      **blank** (not prefilled with 999.99), cart survives.
   3. Try to change a price that already exists from the till → must refuse (409). Server-proved
      on `ITEM-0211` (CHF 18.00, unchanged), but confirm the screen says something useful.
   4. Ring a normal product → **nothing changed**, no new friction. This is the regression risk.
   If A fails, stop and fix it before anything else — it sits between the shop and every sale.

**▶️ B · 79 rows still priced `999.99`.** They are unsellable until priced (that is the point).
   All placeholders now — the 34 real Tamar CHF 99.00 prices were left alone deliberately
   (`scripts/normalise-placeholder-prices.py` explains why; 99.00 is a genuine Tamar price point:
   79:31 · 89:23 · 99:34 · 119:27 · 129:19).
   Bench filter: gap kind **`price`**. New gap kind **`till_priced`** lists anything a cashier
   priced at the counter — *sold, guessed price, no cost*, the shortest path to real margin.
   **Confirm both filters are actually reachable on the screen** — that is this repo's most
   repeated bug (`cash_box_float`, the force-close, `/catalog/merge`, honest confidence).

**▶️ C · Angel's hands only, small:**
   - Delete the duplicate `OTF-1786054495004-703` (*Grandma's Baking Again*, minted barcode).
   - Price `ITEM-0212`: its **26 Tamar siblings say MINI = 12.00, plain = 20.00**, no exceptions.
     Only Angel can say which jar sold. `ITEM-0211` (Nag Champa) is CHF **18.00** — matches
     neither; might be a third size, might be a typo.
   - The 7 photo drafts `ITEM-0235..0241` are **inactive** with no price and no barcode. Price
     them to make them sellable, or leave them parked.

**✅ DEPARTMENT KEYS ARE LIVE ON PROD (2026-08-07, `590c390`).** Ten buttons, the till, the
   day-close block, the miss log. Rollback target if needed: **`4497da5`**.
   ⚠️ **This makes the shadow day BETTER, and changes the tally sheet.** It was designed for a
   world without department keys — Pam writes a two-letter code guessing which button it would
   have been. Now she presses the actual button and the day-close block counts it. The paper
   `Key` column becomes a **cross-check**, not the primary record.
   ⚠️ **Never touched by a human:** the day-close block, the localised labels, the tooltips, and
   the session fix. Four of eleven commits. Ring two or three department lines and open Reports.

**▶️ D · THE PARALLEL RUN — [`onboarding/PARALLEL-RUN.md`](onboarding/PARALLEL-RUN.md).**
   *Set 2026-08-07: "i have coded enough and it needs a real one week test running parallel with
   his paper or at least one day and see if it performs."* **A, B and C above are now pre-flight
   for this**, not ends in themselves. The plan holds:
   - **The two questions for Felix** — *turnover or profit?* and *is a 30% catalogue a win or a
     fail?* Five minutes, and between them they halve or double this project. Blank lines are in
     the file to write his answers on.
   - **Run 1 = Angel shadows a real day. Paper stays the record; Felix risks nothing and types
     nothing.** The number nobody has: **how many sales hit a product that will not scan or has no
     price.** Under 10% → the till is ready. Over 25% → stop coding, start scanning.
   - **Run 2 = a cashier drives** (`Leila` · `Raphi` · `Lele` — not Felix, he owns the alternative).
   - **A simulation cannot replace this** and the rehearsal is not it: ring the paper book's real
     **477.– day** on the tablet first, alone, so the shop day does not die on a free defect.
   - ⚠️ **The ~30 names in tiers 1–2 of `19-what-actually-sells.md` are the real prep** — not 5,389
     rows. Drinks were never checked and `Zigi einzeln 1.–` has no EAN by definition.

**▶️ E · THE OTF ORPHAN — a sale with no link to what was sold.**
   *Angel 2026-08-07: "we sold bongs but no link to what it was … if no ean scanned and otf for
   30% of the sales IMHO."* The money is never wrong; what dies is **velocity**, and velocity is
   the whole of `/reorder/suggestions` — the one thing Banco does that paper cannot.
   - `POST /pos/products` **already** runs the name-dedup guard at 0.65 and returns
     `409 {"message": "A very similar item already exists — is it one of these?", "matches": […]}`.
   - ⚠️ **The till's on-the-fly panel does not appear to render those candidates** —
     `createNoCodeItem()` in `scan.html` has no 409/matches branch. Verify on the screen. If
     confirmed this is the FIFTH instance of the repo's most repeated bug (`cash_box_float`,
     the force-close, `/catalog/merge`, honest confidence): built on every layer a test can
     reach, and on no screen.
   - For bongs the answer is **not** an EAN — Tamar publishes none and never will. It is the
     article number, already built (`_query_code_exact`, measured unique **300/300** on the full
     5 digits) and documented in `onboarding/20-no-barcode-items.md`.

**🔴 STILL THE GO-LIVE BLOCKER:** prod authenticates against the **DEMO realm** — those passwords
are in a public GitHub repo. Nothing else on this list matters if the shop goes live on it.
A shadow day puts real sales on it — close it first, or shadow on a local instance, and **do not
let the parallel run quietly become go-live.**

*The catalogue-enrichment work below is still valid and still unrun; it just is not the top of the
deck any more. Counts in it are from 2026-08-03 (5,173); prod now holds **5,389**.*

---

