# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short — and it has now been cut back three times.** 1,734 lines on
> 2026-08-13, **1,201 on 2026-08-27**, and **2,307 on 2026-09-04** — the biggest yet, grown in a
> single week of shipping. Every pass was verified line-for-line and **nothing was deleted**:
> [`2026-08-27`](worklist-archive/2026-08-27-archive-pass.md) ·
> [`2026-09-04`](worklist-archive/2026-09-04-archive-pass.md) (1,730 lines out, 0 lost).
> **The rule is 500 lines, and since 2026-09-05 it has an alarm** — `python3 scripts/worklist-check.py`,
> run as step 4 of SESSION START. The 150 was set before item ⓪ existed and 280 was never met either;
> a measurement that changes what the shop does next earns its space, and 500 is honestly what this
> file needs to hold. The trigger is what matters, not the number:
> **when a thread closes, it moves the same day — and its header gets marked in the same commit,
> because the marked header is the only thing the alarm can see.** Growing back to four figures is what happens when
> "I'll archive it later" is the plan. When an item is finished it goes to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread grows
> a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-09-15 — **fifth archive pass, 507 → 409**, the alarm's first catch on a file
that had merely drifted rather than exploded: nine closed or parked threads, 129 lines out, 0 lost.
Before that: 2026-09-10, Angel worked the counter and found four defects himself.
Live on the shop: `b754 · 4e3cb17`.*

---

## ▶️ THE DECK — READ THIS FIRST · last touched 2026-09-10

**Live on the shop: `b754 · 4e3cb17`.** Reload the tablet TWICE after any deploy — the first load
activates the new service worker, the second serves from it.

### 🔴 2026-09-10 — ANGEL WORKED THE COUNTER, 11:33–13:04. START HERE.

**Four defects closed, and he found every one of them.** Pack pricing read as 5.14 + 5.14 + 1.72
(right money, unreadable); two rows both called Subtotal showed different numbers; **the five-rappen
cash rounding had never run on any machine** (checkout said change 2.04, the drawer said 2.05); and a
discount refusal blamed tobacco on a basket of rolling papers. Shipped `6513fb3` `d2c49a9` `b64b8b0`.
Two sheets run: **9 pass · 0 fail**, then **25 pass · 2 issue · 0 fail**.
→ **the full record, and everything still open:**
[`2026-09-10-the-counter-and-the-afternoon.html`](worklist-archive/2026-09-10-the-counter-and-the-afternoon.html)

**What is still open, in the order it matters** (detail in that file, do not re-derive it here):

1. ~~🔞 **The age gate misses siblings.**~~ **CLOSED `9c292b8` · 14 live rows applied, gated 1157→1171.**
   5 hashish were sellable with no ID. Ratchet proof, 5,436 swept, 0 un-gated. Split clusters 15→2.
   ⚠️ **3 rows need Angel's EYE, not a regex** — titles carrying only a brand: `Cannabees Purple Fuel
   4g`, `Qualicann Habanero Kush`, and `ELFBAR 4in1 Pod Cherry ICE` (no strength on the label).
1b. 🔓 **NEW — the gate fires on ~50 ACCESSORIES** (`Zigaretten-Filter`/`-Hülsen`/`-Stopfmaschine`).
   `_TOBACCO_ACCESSORY` runs only on the supplier-tag path. Naive fix un-gates real blunts (`filter`
   is in *Holzfilter*). Treuhänder call. LESSON #12 — over-gating teaches staff to wave it away.
2. ⚠️ **The placeholder guard is still two values wide.** ▶️ **2026-09-17 — the list is now REACHABLE:**
   `/pos/cleanup` → The Bench → **🚫 Can't be sold**. The server had `_bench_gap_expr("price")`
   (`price IN (99.00, 999.99)`) and was returning `gap_counts["price"]` on every page load, with
   **no chip on the screen** — LESSON #1 again, the same shape as `allow_nonstandard`. **84 live
   products** on the shop: 34 at 99.00 (ALL created 07.07.26, all big-ticket — 12 bongs at exactly
   99.00 is not a coincidence) and 50 at 999.99.
   ✅ **Angel judged that batch: all 34 were placeholders.** *"i was wrong to do 99 and should of
   made the place holder 999.99 which is an obvious place holder."* `UPDATE 34` on the shop;
   **zero rows at 99.00 anywhere**, 84 at 999.99, all still refused at the till. None had ever
   sold — the guard held, so no receipt carries that number.
   ⏳ **THE FOLLOW-UP THAT IS THE ACTUAL PRIZE, and it needs Angel's word:** with nothing left on
   99.00, take it OUT of `UNVERIFIED_PRICES`. Today a bong that genuinely costs **CHF 99.00 cannot
   be sold** — the till refuses a real price. One obvious placeholder (999.99), one honest guard.
   🔎 **Also unreachable and worth a second chip:** `till_priced` — a price a cashier guessed
   mid-sale, on something that has actually sold. Counted, returned, no button. Felix's margin list.
    `UNVERIFIED_PRICES = (99.00, 999.99)`. The
   six live rows at 999.00 were moved to 999.99 on 2026-09-10 (Angel likes the guard: *"it basically
   forced the user to put the right price in"*), **but type 999.00 tomorrow and it walks through.**
   The four rows at 0.00 are his `SEPARATOR-001…004` shelf markers — an intake aid for testing without
   selling. **Deliberate. Leave them.**
3. ~~🔗 **A URL is bound as a product barcode.**~~ **CLOSED 2026-09-17.** `AlpenBreeze` carried
   `https://vqr.vc/BiWfnR9bv` — Angel scanned the QR on a packet with no stripe, deliberately,
   *"like a silly cashier might do"*. It got in because the format guard gave the WRONG REASON
   (letters → "probably a LOT number") and offered the override, which a cashier staring at a
   packet with no other code will press. Now a hard refusal with **no way past it**, at all three
   screens plus the unattended reference-adoption path — while `2024VL099B` on the JaJa Noir packet
   still saves with its override, asserted by a rectangle, not by `page.$`. At the till a scanned
   QR **no longer stops the sale**: the item goes in the cart, the code is not saved, and the toast
   says which. `UPDATE 1` on the shop, 0 URLs left. `prove-a-qr-is-not-a-barcode.js` 10/0, 12 unit
   tests.
4. 🗣️ **English on the selling path**, and Shelf Intake is now ON it — Angel used it at the counter at
   12:36, so *"nobody sells with any of it"* is retired. Plus `Invalid price tiers: … min_qty 1` in the
   manager panel (English, and it quotes a DB column at a shop owner) and a `Price updated` toast.
5. 🖥️ **The till fell out of fullscreen** at 11:48 and stayed out until 13:04, Chromium's own Esc bar
   over the total. Angel's read is kiosk mode. ⚠️ **KIOSK DOES COST THE SCREENSHOTS, and I said
   otherwise — that was wrong.** `tablet-lockdown.sh` does bind `Print` at the GNOME level, but
   **a key binding needs a key**: with the folio detached there is no Print key, and in kiosk
   fullscreen you cannot pull down the shell to reach the screenshot UI either. Angel, 2026-09-10:
   *"on the tablet, if there's no keyboard attached, you can't do a screenshot. It just won't
   work."* So the kiosk decision costs the evidence trail on the ONE device that keeps producing
   findings — unless something else takes the picture (a gesture binding, a corner tap, a
   Banco-side capture button, or simply leaving the folio on, which item 10 now argues for anyway).
6. 🧾 **The cart says `incl. VAT 1.05`, the receipt says `1.04`** on the same sale. The books are right
   (`tax_amount` == sum of line VAT); the cart's estimate is the odd one out. Predates 5 August.
7. 💤 **A paper outside a deal says nothing.** *Rips Extra Dünn*, CHF 2.00, same shelf as six papers on
   3-for-5 — correct price, no explanation, because `dealInfo()` returns null when a product has no
   tiers at all.
8. 📦 **NEW IDEA — the box code.** A filter packet has no code; the code on the shelf is the outer box.
   Bind the box, record how many singles are in it, let the till break it down. Angel's, not designed.
9. 🎤 **Dictation.** ~~Paste key~~ **WITHDRAWN 2026-09-17 — Angel's call, and it is right.**
   Chromium's own long-press → Paste already works on the tablet; a list of *your own past
   entries* helps only on the second identical entry, on a screen called **New item**. A second
   clipboard beside a working one. Gone: 16 `data-recall` attributes, the store, the panel, the
   strings — and the pad now clears `banco.recall.*` off devices that already used it.
   ⚠️ **What it cost is the part worth keeping.** The key ran `press()` on POINTERDOWN and redrew
   the pad there, so the pad collapsed while the finger was down and the RELEASE landed on the
   page underneath — **on New Item that is the 18+ checkbox.** The paste key toggled the age gate.
   20 green checks never saw it: they fired `dispatchEvent(new PointerEvent(...))` at the button,
   and a synthetic event cannot MISS. `prove-keypad.js` §N is now that regression, aimed at the
   two keys that still redraw (`shift`, `123`), driven by `page.tap()`. LESSON #5 → ×11.
   🔴 **ANSWERED 2026-09-17 — free browser dictation is CLOSED.** `network` on the tablet
   (Debian Chromium 152, `b761`, 16:09) **and** on the desktop (Google Chrome 152), both verified
   online — the tablet reached `google.com` and the shop, 200 each, minutes before. Two builds,
   two key sets, one refusal. The card now carries that verdict and prints the build/host/context
   beside any future answer, because the first run happened on the desktop and a result you cannot
   attribute to a machine is not a measurement.
   **If we ever want dictation it is our own model, and I would NOT build it now:** banco has
   **2 vCPU · 1.66 GB available · NO SWAP · 19 GB free**, `whisper.cpp base` is ~142 MB on disk and
   ~0.5 GB live, ~3–5 s for a 3-second phrase, and it mangles brand names anyway — so it could only
   ever feed SEARCH, which the gun and the catalogue already serve. Item 11 also says Layla starts
   on a keyboard. ~~**The one thing worth doing regardless: the box has no swap.**~~ **DONE** —
   2 GB swapfile on banco, `vm.swappiness=10`, fstab line proved by `swapoff && swapon -a`, and
   `banco-doctor.py` now WARNS when a box has none. It had run a real shop's till for 58 days
   with no spare tyre and nothing in this repo said so.
9b. 📐 `.status-section` (`pos/base.html:2613`) overflows 23px at phone portrait on `/pos/selftest`.10. 📷 **THE TABLET CAMERA — diagnosed 2026-09-10, and it is NOT broken hardware.** `ov2740` sensor
   bound · `ipu3` loaded · libcamera 0.4.0 · pipewire up — and **`cam --list` returns zero cameras.**
   Every `/dev/video*` belongs to `ipu3-imgu` (processing, not capture). An Intel **IPU3 MIPI** sensor
   never presents a plain V4L2 node; libcamera must build the pipeline, and that is the failing step.
   **Banco's side is correct — do not touch `posShowWebcam()`.** Pull the libcamera IPU3 pipeline
   handler, not the kernel driver. **Untried cheap unblock: a powered USB hub (~CHF 20)** — the tablet
   has one port and the gun owns it. (LESSON #3: the 2026-08-05 "nothing attached" verdict was wrong
   too — ACPI declares two fitted sensors. Angel's instinct has now been right twice.)


11. 💻 **ROLLOUT DECISION — do NOT hand them the tablet in week one.** Angel, after two hours behind
   the counter: *"really, it's not the best idea to give them the tablet to start… they should use a
   desktop, like a laptop. Or at least the unit with the keyboard intact for the first week or the
   first month, because it's just cumbersome."* **Note this cuts against the UAT guidance**, which is
   folio OFF — that is right for TESTING the on-screen pad and wrong for a cashier's first week. Two
   different questions: *does the pad work* vs *what does Layla learn on*. Decide before go-live.

*Older deck notes below. The 2026-09-04 method note, and what went in that night (four fixes, five suites, three sheets,
54 pass · 5 issue · 0 fail), are in [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md).*

### What is actually a CODING task — asked and answered 2026-09-06

**Very little, and almost none of it on the selling path.** ① wire triage → the KB (medium, and
the only genuinely valuable software left) · ~~② the receipt QR~~ **DONE `ab527e4`** · ③ a
re-triage button (small) · ④ ~19 server strings in `pos_router.py` · ⑤ the bench, 275 strings, a
slog nobody sells with · ⑥ My Day's red `failed to fetch`.
**Everything else below is a DECISION, a TRIP, or a LOOK.**

### Pick up here, in this order

0️⃣ ~~**The cash box**~~ — **all four shipped `b693`**, drawer balanced at CHF 1'216.00. ⚠️ **The
   morning guard's translated body has still never fired on a screen.** → [`09-06`](worklist-archive/2026-09-06-archive-pass.md)

0️⃣b **▶️ START HERE 2026-09-07 — the bench is all that is left of the language work.**
   `shelf_intake` 173 · `hardware` 59 · `catalog` 22 · `catalog_health` 21 = **275 strings, and
   nobody sells with any of it.** Everything a cashier or Felix touches is CLEAN.
   Harness: `python3 scripts/prove-one-box-one-language.py` — 9 checks, **wrong eight times in one
   day**, every correction in the file. **Never pipe it through `grep`:** that eats the traceback
   AND the exit code, and it spent several commits crashing while printing partial results.
   Guards: never translate the gun's German firmware words, category names, the de-CH numeric
   dates, a language picker, or anything marked `data-i18n-exempt`.
   → [`2026-09-06-archive-pass.md`](worklist-archive/2026-09-06-archive-pass.md) · [`LESSONS.md`](LESSONS.md)
0️⃣c ~~**THE 💬 → TRIAGE LOOP**~~ — **PROVEN 2026-09-06** on the real brain (`gpt-oss:120b`); it
   found a live regression of mine off an unrelated ticket. Sheets: `scripts/make-language-walk.py`.
   → [`09-06`](worklist-archive/2026-09-06-archive-pass.md)
0️⃣d **Gaps found by USING triage.** (1) **No re-triage button** — it is idempotent, so re-reading
   a ticket after a prompt change means impersonating the reporter with a `reporter-note`. The
   prompt changed four times in one afternoon. (2) **Triage does not feed the KB** —
   `kb_contribution_model` and `/pos/kb-approvals` exist; `feedback_triage.py` touches neither.
0️⃣e ~~**English built in `pos_router.py`**~~ — **reporter timeline FIXED, `11559c1`**; Layla
   reads *Ricevuta · Abbiamo capito · In correzione · Risolta!* about her own ticket.
   ⚠️ **~19 more remain** in that file — check (9) lists them, and it has never failed.
0️⃣f ⚠️ **DO THE WALK AT 100% BROWSER ZOOM.** BL-038's garbled numbers (`13R`, a franc figure
   "missing its decimal separator") came from a capture at **Pixel ratio 0.667** — the model read
   compression, not the screen. Triage now distrusts fine detail below ratio 1; the cheap fix is
   not to zoom out.
0️⃣a ~~**FR/IT**~~ — **RETIRED as a blocker 2026-09-06.** ~20–30 REGISTER calls out of ~1,100 (`Titolare`
   or `Proprietario`?), a minute each for Angel or Felix. A footnote. → [`09-15`](worklist-archive/2026-09-15-archive-pass.md)

0 · 1–3 · 4 · 6. ~~**Startup · keyboard · Pam's picker · kiosk leftovers · the tablet · Worldline**~~
   — **ALL CLOSED.** Worldline: **Phase 1 integrates NOTHING, Banco replaces the CALCULATOR.**
   → [`09-05`](worklist-archive/2026-09-05-archive-pass.md) · [`09-15`](worklist-archive/2026-09-15-archive-pass.md)

0c. **Do they log out at night?** Raised, not decided. · 0f. **My Day: red `failed to fetch`
   offline**, under a banner that said so. LESSON #12. · 0g. ✅ **Three clean cold boots** —
   57.8/58.3/58.2s. **The cashier does nothing at all in the morning.**
5. ~~🔴 **THE COUNTER VISIT**~~ — **CLOSED 2026-09-10**, the day Angel worked the till. Both sheets run.
   → [`2026-09-10-the-counter-and-the-afternoon.html`](worklist-archive/2026-09-10-the-counter-and-the-afternoon.html)

7. **The Felix conversation — four decisions that are HIS, written up, none agreed yet.**
   [`the-felix-conversation.html`](onboarding/the-felix-conversation.html): the payment buttons,
   Worldline as **Phase 2**, split tender parked, and the trial terms — **FAIL = free defect ·
   ISSUE = quoted change**, agreed BEFORE the trial starts. Plus the two cheap asks: a day of
   Banana CSV via his Treuhänder, and his real chart-of-accounts codes.
8. ~~**The receipt QR**~~ — **BUILT 2026-09-07, `ab527e4`, 13 checks pass.** The QR is ours, drawn
   by `_qr_data_uri()`, pointing at the shop's own website; **blank `website` prints NO QR** —
   Angel's call, and it settles [`receipt-qr-spec.html`](onboarding/receipt-qr-spec.html) §4. Also
   gone from the sheet: two hardcoded *Artemis* fallbacks (one of them a **legal name**), the fake
   barcode, `api.qrserver.com`, and — found by the proof, not by me — **Google Fonts**, which the
   whole till was still fetching Inter from. Print type ladder fixed: `text-xs` printed at 12px,
   larger than the 9px above it, on every receipt ever printed.
   ⚠️ **Human-green is owed: it has not come off a printer.** Sheet cut and ready, 19 steps:
   [`2026-09-07-the-receipt-is-the-shops-own.html`](onboarding/testsheets/2026-09-07-the-receipt-is-the-shops-own.html)
   🔴 **SETTINGS EDITS LEFT ON THE LIVE SHOP** — nothing here is code, and all of it prints.
   (1) ~~`store_name`~~ **saved 19:0x — now `Artemis Kräuter & Düfte`.** ⚠️ That is the wording
   INSIDE the logo sitting directly above it, so the sheet says it twice; Angel's call. (2) `email` reads
   `contact@artemis-gmbh.ch`; **Felix asked for `contact@artemisluzern.ch`**, which is also what
   his site prints. (3) blank `country` — "Switzerland" is English on a German sheet and their
   own footer stops at Luzern. ~~website~~ already www; ~~vat_number~~ is Felix's real
   **CHE-105.401.803** (the receipt hides that line while it is a placeholder; it is printing).
   📸 `onboarding/evidence/receipt-print-2026-09-07.png` · `scripts/prove-the-receipt-is-the-shops-own.js`
8b. **The OTHER apps in this repo still fetch Inter from Google** — `templates/base.html`,
   `index`, `sitemap`, `home`, `submit_form`, `isotto`, `camper`, `backlog`, `testing`,
   `compute/*`. Banco POS is fixed; those are not. One-line swap each to `/static/vendor/fonts.css`.
   Nobody sells with them, so it is a tidy, not a blocker.

---

- **ⓐ–ⓛ · the 2026-09-03/04 contact-sheet threads — all twelve closed and archived** (scale factor · VAT · pack badge · the frozen stylesheet · the masked-box pad · the invisible refusal · the dead date effect · the red box that did not stop the save · the 131 no-op classes · the Search category picker · the gun pressing the button). → [`2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
## 🖥️ THE TABLET — fixed, locked and self-patching · 2026-09-05

*Eleven faults, **none of them Banco's code** — laptop defaults that are wrong for a till.
**Proven over fourteen cold boots:** on the glass in **~58s, unattended** · never sleeps ·
patches itself at 03:15. Two ssh doors: **`tablet` → art** (gsettings are per-SESSION),
**`tablet-admin` → admin** for `--push`. → [`09-05`](worklist-archive/2026-09-05-archive-pass.md)*

### ~~⚠️ PORTRAIT~~ · ~~⓪h–k the four portrait findings~~ — **ALL DONE**, b690–b693, proven on the glass.
**Do not lock rotation.** → [`09-05`](worklist-archive/2026-09-05-archive-pass.md) · [`09-15`](worklist-archive/2026-09-15-archive-pass.md)

### Still open on the tablet

- ~~**The title bar's close button**~~ — **NOT A BUG, A PRICED TRADE. Do not reopen.** It buys a
  permanently visible GNOME bar (battery, wifi) and `Restart=always`/`RestartSec=3` brings the till
  back in three seconds. → [`09-15`](worklist-archive/2026-09-15-archive-pass.md)
- ~~**Chromium security update + no patching policy**~~ — **DONE 2026-09-05.** 152.0.7977.75, and it
  now patches itself: security origin only, 03:15, reboot only when owed. `tablet-postboot-check.sh`
  is 46 checks. Three things nearly defeated it silently — read before touching the timer.
  → [`09-15`](worklist-archive/2026-09-15-archive-pass.md)
- **Wifi powersave is `default`** (likely on) — worth disabling for a till.
- ~~**The power profile had DRIFTED to `power-saver`**~~ — **FIXED**, `banco-lockdown.service` sets
  `balanced` at every boot. Nothing was watching a setting nobody chose.
  → [`09-15`](worklist-archive/2026-09-15-archive-pass.md)
- **`shop-lte` is ACTIVE alongside wifi** — the failover exists and is live. Decide whether it is
  meant to be always-on, and test it at the shop, not in a flat.
- **[`the-till-morning-to-night.html`](onboarding/the-till-morning-to-night.html)** — the card to
  pin by the till. **Needs Angel's corrections, then Layla's eyes** — see item 0.
- **These two scripts belong in the onboarding kit**, not just on Angel's tablet: anyone who clones
  Banco onto a tablet meets the identical defaults. → archive. The account split and the two
  coloured prompts belong in that write-up too — they are currently hand-made on this one machine.

---

## ⓜ BIRTH YEAR INSTEAD OF A FULL BIRTHDATE — **PARKED, DO NOT BUILD** — 2026-09-04

Angel's call: *"if somebody complains about it, fine, then we'll fix it."* The analysis is whole in
the archive — the design that works (≤ −19 pass · **= −18 ambiguous, falls through to the human**
· ≥ −17 refuse), what must NOT be done (never store `YYYY-01-01` in `birthdate`), and the question
for Felix: *what is the record FOR?* ~half a day if it is ever built.
→ [`09-15`](worklist-archive/2026-09-15-archive-pass.md)

---

- **ⓝ Close of 2026-09-04 (daytime)** — superseded by tonight’s close. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)

## 💡 FIRST-USE AGE CHECK + THE T&C PAGE — waiting on Angel, not on code

Angel's idea (2026-08-22): the first time a member buys, the cashier verifies their age once —
better than storing a date of birth, because no DOB is held at all and the check is a human looking
at a human. **Design notes moved to [`worklist-archive/backlog.md`](worklist-archive/backlog.md)**
(record HOW, a look does not self-correct, hang it off the SCAN never the spoken code).

▶️ **What is actually blocked here is the T&C wording, and it is Angel's to write.** He sketched it
— plain English, not lawyer talk — then said *"I'm just making stuff up."* A page telling a customer
what they agree to should not be invented by the copilot. Draft copy needed, then DE at minimum;
FR/IT need a speaker, not a guess.

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


## 🔭 SMALL, FOUND WHILE TALKING — 2026-09-04/05

- **`<select>` is the next native control to bite.** Seven date pickers, `type="date"`, `type="time"`
  and the keyboard have all had to be replaced because **the tablet's browser renders them and its
  locale is not ours to set**. A `<select>` on a touch device draws an OS picker by the same rule —
  the Find Product category picker is one. **Thirty seconds with the folio OFF** tells you whether
  it is an eighth item or a non-issue. Cheaper to check than to be surprised by.
- **Sweep the four locales for missing keys.** `[i18n] missing key: reorder.by` logs on every order
  book line, and `"8:00 AM"` shipped as an i18n VALUE in EN and FR. **Four working languages is a
  sales asset** — it is the differentiator for Romandie and Ticino, where the app can go but Angel
  cannot — and the first English string a French-speaking prospect finds discredits the rest.
- **Credits + cash is a split tender you already shipped.** A member paying CHF 12.00 with CHF 4.20
  of credits is a two-tender sale by any other name. If that path is not clean the cashier rings it
  full cash and adjusts credits by hand, and the member ledger and the cash book stop agreeing.
  Probe before the trial. (Real split tender stays parked — and is billable if Felix asks.)
- **A feature is not done until you can name the screen it is reachable from.** `/pos/kb-approvals`
  was the fifth or sixth instance of a working page with no door. At that count the fix is a rule in
  the definition of done, not another instance.
- **Banco's front door is another product's landing page.** `src/main.py:400` serves `home.html`
  unconditionally, so `GET /` on any Banco returns **La Piazza** — *"Got a skill the world stopped
  hiring?"*, a CV service. Proven by curl against the running app, not read off the template.
  **Angel's call 2026-09-14: not a showstopper** — he reaches the till at `/pos` and that route
  works. It matters for the *starter*: a shop that clones this gets a stranger's pitch at its root,
  which is the one URL a customer would type. Cheapest fix is a redirect `/` → `/pos` behind an env
  flag, so La Piazza keeps its own front door and a self-hosted Banco lands on the POS.


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

- **🔫 USE THE WIRED GUN. The Bluetooth one is not a second option.** Angel, 2026-09-10, after a full
  shift on the counter: *"I highly recommend that's the only gun to use, as I found out. The other
  one — you can get it going, but it doesn't just work on its own for some reason. I think it's
  because it's Bluetooth connected. That actually becomes cumbersome."* Scanning was **good all
  morning** with the wired one. Any scanning fault reported on the Bluetooth gun is a fault in the
  gun until proven otherwise — check which gun before debugging the till.

- **THE THREE NAMES ARE ROLES, AND THE ROLE IS THE POINT.** Angel runs every sheet signed in as whichever role it is about:

  | signed in as | the part being tested |
  |---|---|
  | **Felix** | owner / administrator — settings, staff cards, no discount ceiling |
  | **Layla** | cashier–manager — the counter, plus what a manager may override |
  | **Pam** | pure cashier — the narrowest permissions, the ones most easily got wrong |

  **This is deliberate role coverage, not a stand-in for absent people.** What the screen does
  depends on the role — the discount ceiling renders only for someone who HAS one, which is exactly
  what step A8 checked — and signing in as the person the feature is for is how you find out whether
  it appears correctly for them. It has never once thrown up a role bug, which is the result you
  want from it. Writing the sheet in that person's voice is also what keeps it about a counter
  instead of a codebase. **Keep doing it.**

  One thing to keep straight when reading a count on this page: **"a human confirmed it on the real
  hardware" is true; "independently confirmed" is not** — the author is also the tester. That is not
  a flaw in the method, it is the argument for ⓞ, getting the shop's own staff in front of it before
  the shift.
- **The app image bakes `src/` in — there is no bind mount.** `docker compose restart app` restarts
  the **old** code and says nothing. Any change under `src/` needs `./scripts/rebuild.sh`.
- **Prod authenticates against the DEMO realm** (`kc-pos-realm-dev`, users felix/pam/ralph),
  imported from a file **in a public GitHub repo**. Still the go-live blocker.
- **Banco is zero-perpetual.** `stock_quantity = 1` is the *design*, not missing data. Never set
  `min_stock` / `max_stock` / reorder points — `/reorder/suggestions` ranks by what the till sold.
- **`age_check_event` is append-only** (a PL/pgSQL trigger, not `REVOKE` — which is a no-op against
  a table owner). Nothing can tidy a row away, including a mis-tap.
- **Hardware gets a label when it earns one. Nothing to build, no binder.** Settled 2026-08-28:
  of 1,062 accessories only 20 carry a real EAN, and their minted `200…` code is the CORRECT answer.
  **The rule: something sells twice, it gets a label.** The shelf is the signal; MISC is
  self-correcting. Build a binder only if Ralph or Felix asks. Keep the department-code escape
  hatch. → [`09-15`](worklist-archive/2026-09-15-archive-pass.md)


---


## 🧪 How to prove it before claiming it

| what | command |
|---|---|
| stand up | `./scripts/rebuild.sh` → `./scripts/standup.sh` |
| server-side 18+ evidence | `BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py` |
| **the actual screens** | `BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-till-18plus.js` |
| **the unit tests** | `POSTGRES_HOST=localhost POSTGRES_PORT=5442 python3 -m pytest src/tests/ -q` |

⚠️ **`python3 -m pytest src/tests/` on its own looks half-broken, and is not.** 30 test files import
`pos_router`, which opens a DB connection at IMPORT time, and the app's default host is the
in-network name `postgres:5432` — which resolves only inside the container. From the host you must
point it at the mapped port (`POSTGRES_HOST_PORT` in `.env`, **5442** here, not 5432). Without it:
30 collection errors and 49 failures, none of them real. With it: **2,488 pass, 12 fail** — and
those 12 fail on a clean `HEAD` too. Found 2026-08-28 after reporting the bare run's numbers as if
they meant something.

⚠️ Both scripts **ring real completed sales** and refund them afterwards; a completed transaction is
a line in the Kassenbuch. `BANCO_ALLOW_FAKE_SALES=1` exists so it cannot happen by accident.
Playwright is **borrowed via `NODE_PATH`, not vendored** — this repo has no node build, on purpose.


---

## 📚 The archive

| file | what's in it |
|---|---|
| [`worklist-archive/2026-09-15-archive-pass.md`](worklist-archive/2026-09-15-archive-pass.md) | **the fifth cut** — 2026-09-15, 129 lines out, 0 lost, triggered by the alarm at 507. Nine blocks, all closed, settled or parked: **ⓜ the birth-year analysis** (parked whole — the 2008 January/December edge is the whole design), **item 5 the counter visit** (*stale* — it still said no sale had been rung on this build, four days after Angel rang them), the tablet's **portrait findings · title bar · Chromium self-patching · the drifted power profile**, **FR/IT retired as a blocker**, and the **hardware-label** standing fact |
| [`worklist-archive/2026-09-10-archive-pass.md`](worklist-archive/2026-09-10-archive-pass.md) | **the fourth cut** — 2026-09-10, verified line-for-line: **ⓞ THE COUNTER VISIT** (closed the day Angel worked the till — the prep prose; *the one code-touching decision it carried still stands: **LANDSCAPE, LOCKED**, every geometry proof runs at 1440 × 895*) and **ⓒ5 PAM'S RUN** (14 pass · 3 issue · 0 fail, 2026-09-04). The day itself is the HTML beside it |
| [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md) | **the third cut** — 1,730 lines moved out verbatim on the night of 2026-09-04, 0 lost: the 11-shot contact sheet, the 131 no-op classes (ⓔ + ⓙ), the masked-box pad bug (ⓕ), the invisible refusal (ⓖ), the dead effect (ⓗ), the ungreyed save (ⓘ), the category picker (ⓚ), the gun that pressed the button (ⓛ), the daytime close (ⓝ), the date-filter thread (ⓒ2–ⓒ4), and everything written before 2026-09-03 |
| [`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md) | **the second cut** — 889 lines moved out verbatim 2026-08-27: the member card, ART-AB12, the join offer, the counter card, bundle pricing, the price warning, the whole FourTwenty thread, the six till reports, adopt-images, both prod-live days |
| [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md) | Gate Zero, and the whole 18+ evidence thread 08-10 → 08-13 |
| [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) | catalogue, shelf intake, till and search, through 08-07 — **status unverified** |
| [`worklist-archive/2026-08-20-till-reports.md`](worklist-archive/2026-08-20-till-reports.md) | the evidence behind BL-9…BL-14 |
| [`worklist-archive/2026-08-21-fourtwenty-reference.md`](worklist-archive/2026-08-21-fourtwenty-reference.md) · [`2026-08-21-price-consistency/`](worklist-archive/2026-08-21-price-consistency/) · [`2026-08-22-pooling/`](worklist-archive/2026-08-22-pooling/) · [`2026-08-22-anon-member-card.md`](worklist-archive/2026-08-22-anon-member-card.md) | the days themselves |
| [`worklist-archive/backlog.md`](worklist-archive/backlog.md) | not yet scheduled — credits redemption (waiting on Felix), dark mode, the till that felt slow, the offline kit, monitoring, labels, exports |
| [`worklist-archive/done.md`](worklist-archive/done.md) | shipped, most recent first, with commit hashes |

