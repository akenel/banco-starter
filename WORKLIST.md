# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

*Last updated: 2026-08-07 — money-safety week shipped to prod. Everything below is machine-green
and waiting on Angel's hands.*

---

## ▶️ START HERE — put a human on the till, then price the 79

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

**🔴 STILL THE GO-LIVE BLOCKER:** prod authenticates against the **DEMO realm** — those passwords
are in a public GitHub repo. Nothing else on this list matters if the shop goes live on it.

*The catalogue-enrichment work below is still valid and still unrun; it just is not the top of the
deck any more. Counts in it are from 2026-08-03 (5,173); prod now holds **5,389**.*

---

## 📋 THEN — the two bulk catalogue scripts

*Set 2026-08-03 at the end of a long day. **Items 1 and 2 are DONE and on prod** — the 5-rappen
cash rounding and the shop-owned cash box, both human-tested by Angel. Their history is in
[`onboarding/12-the-cash-box.md`](onboarding/12-the-cash-box.md) and in `Done` below. This is the
work now.*

**▶️ 3 · Run the two bulk catalogue scripts ON THE PROD BOX.**
   Local dev has **6 products**; the **5,173** live on prod, so these were never runnable here.
   Testsheet ready and unticked:
   [`onboarding/testsheets/ENRICHER-TESTSHEET.html`](onboarding/testsheets/ENRICHER-TESTSHEET.html)
   — 20 real pages through the real parser: 20/20 DE and EN agree, 6 ladders found, 0 footer junk.
   **Angel ticks the 6 ladder rows before `--apply` runs.**

   **How to run things on prod — learned the hard way 2026-08-03:**
   ```
   ssh root@159.69.198.85          # /root/banco-starter, branch main
   git pull --ff-only origin main && ./scripts/deploy-prod.sh   # backs up to B2 FIRST
   ```
   - `deploy-prod.sh` always prints a **false ❌ NOT READY** — its gate probes `localhost:8000`
     and prod sits behind Caddy. Verify with `curl https://banco.wolfhold.app/health/healthz`.
   - **`httpx` is NOT installed on the prod host** — run Python that needs it *inside* the app
     container: `docker compose -f compose.yml -f compose.prod.yml exec -T app python3 - < script.py`
   - Passwords are Angel's to type; scripts take `BANCO_USER` / `BANCO_PASS` from the env, and
     `-e VAR` (no `=value`) passes them through without landing in shell history.

   **Then, in order:**
   1. `scripts/enrich-from-source.py --apply` — ~90 min unattended. 5,111 products carry a
      `source_url`; their own pages publish the retail tier ladder + spec table. **The CHF 1,190
      overcharge guard is in** (refuses a ladder whose first tier costs more than one unit);
      `--report /tmp/suspects.json` lists every refusal. Also what makes `Breite 4.4 cm` vs
      `5.2 cm` visible in Banco instead of needing two web fetches to settle a duplicate.
   2. `scripts/adopt-images.py --apply` — ~137 min. 5,150 covers hotlinked across 18 servers.
      Capture already adopts new ones; this is the back-catalogue.
   3. **Dedupe** — same-description AND same-name found 11 real pairs out of 572 groups. Worth
      running after every import. *(Tell Felix: those 11 are duplicated on artemisluzern.ch too,
      so the next import brings them back.)*

   **Also open, smaller:** 151 uncategorised (Accessories 73 · Other 66 · Unsorted 12) · 45
   rolling papers wrongly classed `cbd_hemp`/18+ — **do not bulk-unfix, loosening an age gate is
   the one direction where a wrong script is a compliance failure** · tell Felix about
   `TAM-11884` (his page says CHF 3 for one, CHF 11.90 for 100).

---

### 🟡 SHIPPED 2026-08-03, NOT YET HUMAN-GREEN — the re-scan cleanup path

*Angel simulating a cashier: a customer spots a new grinder on the counter, the scan misses, Pam
types `grinder / 15.00` and sells it. All correct with someone waiting — and the till binds the
real EAN (`3661075283438`) while it does it. Then someone has to go back and enter it properly.*

**Three screens each dropped that row, none of them with an error.** All three are fixed:

1. **The cockpit's Sold tab now leads with what just sold.** It sorted `(qty_sold, revenue)`
   desc, so a row sold ONCE sat below 37 busier ones — `last_sold` was computed, returned and
   printed on the card the whole time and never sorted on. `🔥 Busiest` is still one click away.
2. **Shelf intake has a third bucket: "scan fine — but the row is still a stub."** Re-scan the
   packet and it no longer lands in the green *nothing to do* pile. Carries the readiness badge,
   a **🔎 Look it up** link on the bare EAN, and **✏️ Finish it** → `/pos/cleanup?pid=…`.
3. **The bench card can edit the NAME and the BARCODE.** It could fix category, price, cost,
   description, photo and 18+ — everything except the one thing actually wrong with "grinder".
   Description + photo now show in the Sold tab too, since the badge names those gaps out loud.

4. **The card fills itself from the product's own page.** Paste the link → name, description,
   category, barcode, price and photo-link drop into the boxes → you check them → Save. Same
   `/catalog/page-facts` shelf intake uses for unknowns (it is *pure*, so pointing it at an
   existing row needed no server change). **It writes nothing**, and ↩️ Undo restores every box.
   Rules, because each one can be quietly wrong: the **name is always replaced** (that is the
   point) · a **price the till already took is never overwritten**, and a foreign-currency page
   says so out loud instead of leaving a figure in the box · **18+ can only be turned ON** ·
   a description or category someone wrote **wins over a scraped one** · the **scanned barcode
   outranks the page** · the photo is *offered*, not fetched.

**Proof so far:** 27 tests (`test_cleanup_rescan.py` + `test_bench_fill_from_page.py`, both
running the real client code in node) — **sabotaged on purpose** (scraped price overwriting the
till price; a page switching an 18+ gate off) to confirm they fail · full suite 2238 pass, the 6
failures pre-existing · `scripts/probe-rescan-cleanup.py` 13/13, twice, self-sweeping.
**⛔ That probe writes real completed sales — `BANCO_ALLOW_FAKE_SALES=1` guards it. NEVER on the
shop's books.**

**Settled 2026-08-03 — "discontinue it and re-enter properly" DOES NOT WORK.** Tested: a
discontinued row **keeps its barcode** (`ix_products_barcode` is a plain UNIQUE index, no
`WHERE is_active`), and `_find_product_by_any_barcode` ignores `is_active` — so intake triages
the EAN as **known**, pointing at the dead row, and never reaches the create path. A second row
with that barcode is refused by Postgres. It also splits the sales history of one physical
product across two rows, and throws away the bind — the one thing the rushed quick-add got
right. **Fix the row in place.** (The exception: a genuine MIS-scan, where the barcode itself is
wrong. Then the bind is the broken part and discontinuing is correct.)

**✅ Human-confirmed on prod, 2026-08-03 (Angel):**
- The **18+ counter reads 1097**, not 3. Data was fine all along; the counter was page-scoped.
- **Get the facts** fills a row from a page — and Angel caught it writing
  `…Grinder [40506209] - Jelly-Joker` over a good name he had typed. Fixed both ends (title
  cleaning server-side, full before → after on the card) and redeployed. **That defect existed
  for about an hour and was found by a person in one use.**

**⛔ Still not seen by anybody** — every one is a screen:
- Sell something from a rushed quick-add → **Cleanup → Sold & unfinished → is it at the top?**
- Re-scan that packet in **Shelf Intake** → does it land in the amber bucket, not the green one?
- **🔎 Look it up** → does the bare EAN name the packet? (`3661075283438` → three shops agree:
  Champ High White Leaf Grinder, 4-part, Ø50mm)
- **↩️ Undo** after a fill — does every box go back?
- The new **before → after** rename line: is it impossible to miss now?
- Type a barcode already on another row → the toast must say *"already exists"*, not *"Save failed"*.
- Clear the name and save → must refuse, not silently keep the old one.
- **Read the German** (`🆕 Gerade verkauft`, `Name — was ist es wirklich?`) as a shopkeeper.

---

### ✅ MERGE FROM THE CATALOG ROW — BUILT 2026-08-03, needs a human

*Angel, holding two rows: `Canna Cannazym 1L` at **CHF 43.90** (`OTF-…`, no barcode, Grow
Supplies) and `Canna Cannazym 1L` at **CHF 21.00** (`LZ-8717524956387`, real EAN, Unsorted).
Same pair as the TXN-0006 receipt below. He asked how to fix it with today's tools — and the
answer turned out to be "not with the tool built for it".*

`POST /catalog/merge` works, is tested, and is called from **exactly one place**:
`shelf_intake.html:923`, on an **unknown**-code card. So the tool for duplicates is reachable
only while a code is *unbound*. Bind the EAN — which is the whole point of shelf intake — and it
vanishes. From the catalog screen, where duplicates are actually *seen*, there is no merge at all.

Two smaller things the same case exposed:
- **Merge never resolves the price** (`_FILLABLE` excludes it, on purpose). So even a reachable
  merge leaves the CHF 21.00 vs CHF 43.90 question to a human. Fine — but the UI should say so
  rather than let someone expect it.
- **Merge only points one way** (hand-made row donates its EAN to the wholesale row). Here the
  hand-made row had *no* barcode, so there was nothing to donate and the answer was simply
  *discontinue the twin*. A merge screen should recognise that case and say it.

**BUILT.** Any product → *Tap for details* → **🔗 Duplicate of…** (manager only). Search the
twin, see both rows side by side with their prices and categories, **⇄ Swap** to choose which
survives, **Show me what would happen** runs `dry_run` and prints the plan, then confirm. Both
things the case exposed are said out loud on the screen: a **price gap** warns that merging will
not change the price and that a big gap usually means two different products; a twin with **no
barcode** is called what it is — a tidy discontinue, not a merge.

9 probe checks in `scripts/probe-rescan-cleanup.py` §5, modelling this exact Cannazym pair:
dry_run leaves the database untouched · the EAN lands on the survivor · **its price and category
are untouched** · the twin is switched off, never deleted · scanning the EAN finds the survivor.

**⛔ Not human-green.** Nobody has merged a real pair from this screen. The ~40 duplicates from
2026-07-30 are the reason it exists — that backlog is now workable.

**The rule that came out of it, worth keeping:** *a 2× price gap on two rows with the same name
is not a typo — it is the signature of two different products.* The OTF row carried no barcode,
so nothing in the database could say what it physically was. Only the bottle knew.

---

### 🔻 Carried over from 2026-08-03 — small, and two are Angel's hands only

- **F3 · Reconcile the cash box on prod.** It may still be open with test sales in it, and
  **whatever it is reconciled to becomes the next morning's expected**. `/pos/shift` → count out.
- **H1 · Set the tolerance to ±0.05?** Now reachable (Settings → Discounts → 💰 The cash box).
  One coin — as tight as physical cash allows. It was blocked until the rounding shipped.
- **E4 · Read the German cash-box screens as a shopkeeper**, not a developer. `Kasse` /
  `Kassensturz` are confirmed; the rest of the wording has never been read by a native speaker.
- **H2–H6** in the testsheet: baseline value · who may force-close · does the X-report need a
  better home · which paid-out reasons Artemis actually uses · who reads the morning note.
- 🔴 **Prod authenticates against the DEMO realm** (`kc-pos-realm-dev`, users felix/pam/ralph/…)
  imported from `keycloak/import/realm-export.json` — **which is in a public GitHub repo**.
  Change the passwords or stand up a real realm before the shop trades on it.
- The five OTF test products are **deactivated, not deleted** (two were sold). Nothing to do.
- Re-test the **gun roles** — the Netum has the multi-scan store mode, the Inateck does single
  scans. The deck used to say the reverse; anything planning the 10× inventory path must re-check.

---

## 🎯 On deck (next actionable, in order)

0. **🔴 THE CASH BOX IS SHARED — Banco assumes one drawer PER CASHIER. Design agreed 2026-08-03,
   not built.** → **[`onboarding/12-the-cash-box.md`](onboarding/12-the-cash-box.md)**

   Artemis has **one** cash box. Everyone sells into it, it is never emptied (~CHF 600 carries
   over), it sleeps in the safe and comes back out the same. `cash_shift_model.py` says in its own
   docstring *"per-cashier drawer accountability … THEIR drawer"*, and `pos_router.py:8632` sums
   `TransactionModel.cashier_id == user_id`.

   **So: Felix opens with 200, Pam sells 150 cash into the same box, Felix counts out → expected
   counts only Felix's sales → variance +150 → he writes a note explaining money that was never
   missing.** The "already have an open shift" guard is per-user too, so two people can hold open
   drawers on one physical box.

   **The fix is smaller than it looks — the arithmetic is right, the SCOPE of one query is wrong.**
   Drop the cashier filter, make the till shop-owned, and link last night's counted total to this
   morning's expected (the "slope"). Per-cashier *sales* reporting is untouched.

   **The one genuinely new idea, and it is Felix's own:** he counts the box **before** looking at
   what it should hold — *"a little test I play with myself"*. That is correct practice (seeing
   `555` first makes you count until you find `555`), so **Banco should enforce the order**: count
   blind → reveal → explain, and the discrepancy is filed against *yesterday's* reconcile while
   today starts from what is really in the box.

   Also resolves **G8**'s two-meanings-of-shift: session = who is logged in (per person), till =
   the money (one, shop-owned). Cashiers stop touching the drawer entirely — A4 leaves their day.

   **✅ NOT BLOCKED — all four answered by Angel, 2026-08-03** (in the doc): a **cashier may do
   everything**; a skipped night gets a banner listing every cash movement since the last
   reconcile so the total is *reconstructed*, not asserted; tolerance **±0.05** (one coin — but
   only after the rounding wiring ships, see ▶️ START HERE); foreign notes counted at reconcile,
   and paid-**IN** is home currency only while paid-**OUT** may be foreign, so the euros can leave
   to the safe.


0. **🟢 CASHIER SHIFT ROLE-PLAY RUN — 2026-08-03, 64 minutes, UAT b170.** Angel played the day
   open-to-close on the tablet. Sheet: [`onboarding/testsheets/CASHIER-SHIFT-E2E-TESTSHEET.html`](onboarding/testsheets/CASHIER-SHIFT-E2E-TESTSHEET.html).

   **✅ Proven for the first time by a human:**
   - **Foreign cash works end to end.** EUR 100 tendered at 0.9 → CHF 90.00, change CHF 15.90,
     receipt shows `EUR 100.00 @ 0.900000`, and the drawer lists `EUR 120.00 ≈ CHF 108.00` to be
     counted separately. This had never been tested by anyone.
   - **Shift close balanced on real data** — expected CHF 283.09, counted CHF 283.00,
     variance −0.09, inside tolerance, Z-report and 209-hour shift report rendered.
   - **The 18+ gate refuses and cleanly removes the line.** Manager refund works.
   - **G3 IS NOT A GAP — the guide was wrong.** *"if you try to make a cash sale with a closed
     drawer it stops and warns."* Checkout already enforces an open drawer. Strike G3.
   - **G1 has an answer, and it is good:** Angel built the unknown product **on the fly in ~10
     seconds**, with category and description, and sold it (`OTF-1785752266675-826`, TXN-0005).
     "Create it OTF" is the cashier move — it just needs writing on the till card.

   **🔴 Fixed same day:** `PUT /api/v1/customers/{id}` **500** on saving a member with blank
   contact boxes — `''` collides on the UNIQUE `email` / `instagram` index. Looked like the age
   gate; wasn't. Reproduced, fixed, 20 tests. **The under-18 rule itself was correct all along.**

   **🔴 STILL OPEN — the close-out is the real risk (G8), now with evidence:**
   - **Three closing screens disagree on the numbers.** `/pos/shift` says 17 transactions /
     CHF 540.79 cash; `/pos/closeout` says 7 transactions / CHF 316.75; `/pos/cash-count` says
     expected **0**.
   - **`/pos/cash-count` shows the WRONG CASHIER** — "Pam" while logged in as felix.
   - **`/pos/cash-count` notes field renders `[object Object],[object Object],…`** — a real
     rendering bug.
   - **It let the drawer close with no note.** Because expected was 0 it declared *"Perfect
     balance! Pam's bonus pool +1 point"* on an uncounted drawer. `/pos/shift` gets this right
     (refuses to close outside ±0.20 without a note); `/pos/cash-count` does not.
   - **Decision: `/pos/shift` is the real one** — it is the one Angel reached for, it has the
     float, the foreign cash, the variance rule and the report. Take the other two out of the
     cashier's navigation.

   **🟡 New features the day asked for (not bugs):**
   - **Split payment (G7) — confirmed needed.** *"basically really poor workaround … super messy."*
   - **Hold queue (G5)** — a HOLD button; today it's cancel-and-restart. Not a showstopper.
   - **Print button on the device-check page** — Angel scanned the screen and *"it kinda works"*.
   - **G2 answer:** create a new product with the correct price. Receipt TXN-0006 shows the
     problem plainly: *Canna Cannazym 1L at CHF 21.00 and CHF 43.90 on the same receipt.*

   **🔵 Hardware / cutover, for the shop not the code:**
   - **The gun roles are the reverse of what this deck says.** Angel: *"netum scan gun has store
     mode for multi scans and the inatech only does single scans."* **Item 1 below assumes the
     Inateck BCST-35 does the inventory dump — re-test before planning around it.**
   - Netum was still in store mode at A2 — **its config barcodes need to be in the testsheets**.
   - Charging stations for both guns, **within arm's reach behind the counter**, on a reserved plug.
   - Connect the office printer to the tablet; labeller to the back-office desktop.
   - Worldline still pending — terminal is simulation-only, so A5 can't be truly tested yet.


0. **🟢 SHELF INTAKE IS PROVEN — 2026-08-02.** ~1 min/product sustained, 5× the counter, and the
   output is four times better. Last section: 18 scanned, 16 already known, 2 skipped — and both
   skips were CORRECT (a Landi battery pack; an OCB 3-pack Felix doesn't stock, whose singles
   `30058569` resolved instantly). **On real shop stock the hit rate was 100%.**

   **DO THIS FIRST — the verify pass is now step 3 of the workflow.** Scan a section → bind them
   all → **walk back and re-scan the SAME products with the packets in hand.** A wrong bind looks
   exactly like a right one in the database; only a person holding the packet can tell. It caught
   Cannazym bound to Cannaboost (CHF 12 vs CHF 35) and surfaced 11 duplicate Tamar rows.

   **Still untested:** the gun's **inventory-mode dump**. Everything so far was typed/scanned one
   code at a time. `Inventurmodus` → 20–30 facings → `Anzahl der gescannten Barcodes` → type the
   count → `Daten hochladen`. Whether the burst survives a browser textarea is the last unknown.

   **⛔ BOTH BULK SCRIPTS ARE BLOCKED ON WHERE THEY RUN — 2026-08-03.** The local dev DB has
   **6 products** (the seeded treats; `source_url IS NOT NULL` matches zero rows). The 5,111
   live on the prod/UAT box behind `banco.wolfhold.app`, and `deploy-prod.sh` is written to run
   *on* that server. So `enrich-from-source` and `adopt-images` need either a shell on prod or a
   dump pulled down here. **Not a code problem — a location problem.** Decide which and they go.

   **Then, in order:**
   - `scripts/enrich-from-source.py --apply` — 5,111 products carry a `source_url`; their own
     pages publish the retail tier ladder + spec table. ~90 min unattended. **This is also what
     makes `Breite 4.4 cm` vs `5.2 cm` visible in Banco** instead of needing two web fetches to
     settle whether two rows are duplicates.
     **Sampled first, 2026-08-03** — `scripts/make-enricher-testsheet.py` →
     [`onboarding/testsheets/enricher-testsheet.md`](onboarding/testsheets/enricher-testsheet.md).
     20 real pages through the real parser: **20/20 DE and EN agree on the ladder**, 6 ladders
     found, 0 footer junk, 0 dead fetches. Angel ticks the 6 ladder rows before `--apply` runs.
   - `scripts/adopt-images.py --apply` — 5,150 covers hotlinked across **18 different servers**.
     ~137 min. Capture already adopts new ones; this is the back-catalogue.
   - ~~**Write the English packet name as an alias.**~~ **✅ DONE 2026-08-03.**
     `record_name_alias()` + wired into `POST /catalog/merge`, which was binning the hand-typed
     packet name at the exact moment it learned which product it belonged to. 10 tests.
     **The first version didn't work and every test was green:** the alias was written, the SQL
     matched it at 1.000, and both post-filters then judged the row by `products.name` — so
     `brands_conflict("Purize Xtra Slim…", "Aktivkohlefilter 6mm 50er…")` killed it one line
     after it was found. The SQL now carries the *matched* name through (`DISTINCT ON`) and the
     filters judge that. Proven live end to end by `scripts/prove-name-alias.py`.
     *Still open: the scan-miss bind (`POST /products/{id}/barcodes`) sends only a barcode, so
     recording the searched name there needs a front-end change too.*
   - **151 uncategorised** — Accessories (general) 73 · Other 66 · Unsorted 12.
   - **45 rolling papers classed `cbd_hemp` / 18+** from the 07-07 import trusting Artemis's
     `CBD · Diverses` breadcrumb. **Do not bulk-unfix** — loosening an age gate is the one
     direction where a wrong script is a compliance failure.
   - **Dedupe script** — same-description AND same-name found 11 real pairs out of 572 groups
     (562 were legitimate families). Worth running after every import. Angel asked for it.
   - ~~Spec parser loses fields on `/en/` pages (Quöllfrisch 16 → 1)~~ — **this note was
     backwards; re-checked 2026-08-03.** Quöllfrisch (`TAM-20067`) reads **1 spec on BOTH**
     languages, and 1 is the CORRECT answer: that page states exactly one (`Hersteller:
     Quöllfrisch`) before the site footer begins. A 16 would have been one real spec plus
     fifteen rows of footer (`Kontakt: Jugendschutz`, `AGB: Seit 1999`). So the risk was never
     the EN page losing fields — it is the parser running *past* the specs and INVENTING them
     wherever a footer heading is missing from the stop list. Audited on 60 pages: **zero junk**,
     the stop list holds. Left here because the failure mode is worth knowing, not fixing.
   - `TAM-19233`
     `barcode_is_internal` anomaly; the `file:///api/…` link in the audit diff; `deploy-prod.sh`
     false ❌ NOT READY.

   **Tell Felix:** the 11 duplicate pairs are duplicated on artemisluzern.ch too, so the next
   import brings them back. And `TAM-21669`'s description says "King Size Slim format" on a
   **5.2 cm** paper — wrong on his own site.



0. **🟢 SHELF INTAKE IS HUMAN-GREEN — 2026-07-31.** Angel bound ~10 real products on the tablet at
   UAT and sold them. Receipt TXN-20260731-0003: six lines, CHF 76.90, and
   `Gizeh King Size Slim 12 × CHF 1.30 = CHF 15.60` — a quantity break that did not exist that
   morning, scraped from the shop's own page, firing at the till on its own.

   **What is NOT yet tested — do this first:** the gun's **inventory-mode dump**. Everything so far
   was one code at a time. Scan `Inventurmodus`, walk a shelf, `Anzahl der gescannten Barcodes`,
   type that number into the count box, `Daten hochladen`. The open question is whether the
   BCST-35's burst lands intact in a browser textarea. That is the 10× path and it is unproven.

   **Then, in order:**
   - `scripts/enrich-from-source.py --apply` for the rest — 5,111 products carry a `source_url`
     and their own pages publish the retail tier ladder + a spec table. ~90 min at 1s apart,
     dry-run first. Six done so far.
   - **Write the English packet name as an alias at capture.** Search across `product_translations`
     now works (2026-07-31) but *nothing writes to it* — so the feature is still half a loop.
   - **45 rolling papers are classed `cbd_hemp` / 18+** (Greengo, Filterpapier, Old School…). The
     07-07 import trusted Artemis's `CBD · Diverses · Papers & CO` breadcrumb. Not a money bug
     (`cbd_hemp` VAT = standard) but the `🌿 CBD` badge is plainly false. **Do not bulk-unfix** —
     loosening an age gate is the one direction where a wrong script is a compliance failure.
   - **Spec parser loses fields on the /en/ pages** — Quöllfrisch went 16 facets → 1. The block
     boundary keys off German headings. Tiers are money and are correct; specs are informational.
   - `TAM-19233` still has `barcode_is_internal = true` with two real codes (Blow pack levels).
     Cosmetic, not a scan problem.

   **Eight silent-failure bugs found today, every one by Angel using it, none by a test:**
   HTML entities (0.429 vs 1.000) · `pc.` vs `Stk.` · absent-size discarding every variant ·
   `KingSize` at exactly 0.500 · an unbroken score tie hiding the exact match · a live 3× tier
   overcharge · a service worker that could never deliver a JS fix · a 400 KB fetch cap that made
   a page with perfect JSON-LD look empty. **They all failed the same way: the right data was
   there and something quietly threw it away.**



1. **🟡 SHELF SCAN → BATCH ENRICH — BUILT, NEEDS A SHOP TEST.** *(shop floor · Angel's idea 2026-07-30)*

   **Built 2026-07-31 and proven on the API; NOT yet human-green.** What exists:
   - `/pos/shelf-intake` (manager, linked from the dashboard) — dump box → triage → batches of ten.
   - `POST /catalog/shelf-intake/triage` — parses the keystroke dump, splits known/unknown, warns on
     a short upload / junk / bad check digits. `POST /catalog/shelf-intake/candidates` — "is it one
     of these?", brand-filtered, proposals only.
   - `src/services/shelf_intake.py` + 23 tests (every gun terminator, repeats, junk, GTIN checks).
   - Guide: [`onboarding/09-shelf-intake.md`](onboarding/09-shelf-intake.md).

   **Verified locally, end to end:** triage a 5-token dump → 3 unique, 1 repeat, junk reported →
   candidates proposed a real match at 0.536 → bound the EAN via `POST /products/{id}/barcodes` →
   re-triaged the same dump and the code came back **known**. Then the test binding was undone.

   **⛔ What is NOT done — the only thing that counts (standing rule 5):** nobody has walked a shelf
   with the gun in inventory mode, dumped it into this screen, and worked a real batch of ten. Until
   Angel does that at Artemis, this is machine-green. Specifically unproven: whether the BCST-35's
   dump arrives in one keystroke burst a browser textarea can hold, and whether 15–25% really bind.

   **The inversion:** stop trying to repair a 5,178-product wholesale import. **Let the shelf define
   the catalogue.** Start clean (the 6 seeded treats), walk the shop scanning every packet, then
   enrich at a desk in batch.

   **The gun already does the hard part.** Inateck BCST-35 §4.6 "Inventurmodus" (manual p.20, in
   `onboarding/testsheets/Scanners/`): stores **3,000 codes offline**, uploads as keystrokes later,
   *"weder an die Zeit noch an den Ort gebunden"*. The five inventory barcodes need **no** Enter
   Setup / Save and Exit — scan the one you want on its own.

   **Why this beats everything else we discussed:**
   | Problem | How this dissolves it |
   |---|---|
   | 5,103 minted barcodes | never imported — nothing to un-fake |
   | 5,178 rows vs ~800 stocked | the shelf **is** the stock list |
   | 5 min/product hunting at the till | ~2 sec/product scanning; hunting moves to a desk |
   | German/English name matching | irrelevant — the EAN is the key from the start |

   Separates PHYSICAL work (20 min at the shelves, no thinking, no queue behind you) from DESK work
   (enrichment, batched, two screens, coffee). Today both happened at once, at the counter, under
   pressure — which is why it was 5 minutes a product.

   **To build:**
   - **Intake UI** — one big focused box, receives the keystroke dump, parses + dedupes into a code
     list. Show the count so a half-upload can't masquerade as a finished shelf (scan *Anzahl der
     gescannten Barcodes* first and compare).
   - **Triage** — for each code: already known (bind/skip) · in the imported catalogue under a fake
     barcode (bind the real EAN to it — reuses the cross-language match) · genuinely new (enrich).
   - **Batch enrich** — per unknown code, the human does the 5–30 s "that's it" pick (see
     `CATALOG-IDENTITY.md`: the machine must not choose), then `POST /catalog/page-facts` fills
     title/description/image/price/GTIN from the chosen page.

   **THE CONSTRAINT THAT DECIDES THE DESIGN — the catalogue must be ready BEFORE go-live.**
   Leandra, Roger and Nathan are serving customers now. A till that misses half its scans does not
   degrade gracefully: the failure lands on whoever is holding the product with someone waiting.
   "Scan-as-you-sell will fill it in over a few weeks" is fine for a slow tail and **not acceptable
   as the primary mechanism**. Angel: *"a person has the product in their hand, they scanned it —
   it needs to be already in the system, previous to them starting and go live. For 90% of the stuff
   or more."*

   **Validate in BATCHES OF TEN, not one at a time.** Angel: *"You scan ten of them. This is what we
   think it is. That's correct. That's not. Now we have to go into the deep dive."* The machine
   proposes, the human judges in 5–30 s (see `CATALOG-IDENTITY.md` — the machine must never choose).
   Ten at a time keeps context; one at a time means re-orienting on every product, which is where
   most of the 5 minutes went.

   **Wipe the minted BARCODES, keep the TAM SKUs.** Two different things wear that name and only one
   is the lie:
   - `TAM-19238` (sku) — Tamar's real article number, and the join key back to `source_url`
     (`artemisluzern.ch/.../19238`). **Keep it** — it is what makes batch enrichment possible at all,
     because every row can re-find its own source page.
   - `2000000192352` (barcode) — invented by Banco, on no packet. **Wipe it** (or at least set
     `barcode_is_internal`), so a known-unknown stops masquerading as a real code.

   **MEASURED 2026-07-31 — what to actually expect.** Took the 59 products Angel captured by hand
   (real EANs) and matched them back against the 07-07 import (minted barcodes), using the
   cross-language folding:

   | | |
   |---|---|
   | captured by hand | 59 |
   | scored ≥0.5 against an imported row | 20 (34%) |
   | of those, genuinely the SAME product on inspection | **~8–10** |

   So expect **15–25% bound instantly**, not the 60% first guessed. Correcting that now so an
   evening is not planned around a wrong number.

   **The proposals must NEVER auto-apply.** Roughly half the 0.5–0.7 matches are wrong, and wrong in
   ways a character-based score cannot see:
   ```
   0.50  Canna Coco A 1L               <-> Beamer Candles Cocanna Banana
   0.50  Juicy Jays Raspberry Incense  <-> Juicy Jays Rolls Raspberry     (incense vs papers)
   0.43  Aperol Spritz                 <-> Dosier Spritze 1ml
   0.70  Blow pure                     <-> Local Weed vorgebauter ...     (wrong brand)
   ```
   `Canna` matching `Cocanna`; `Spritz` matching `Spritze`. This is exactly why Angel's
   confirm-in-tens is required rather than merely nicer.

   **Brand weighting: DONE** (`src/services/catalog_brands.py`, 2026-07-31) and wired into both the
   create guard and the intake screen through one shared matcher, `_name_match_candidates`.

   Also seen: several "matches" are SIBLINGS, not duplicates (`Gizeh ... + Tips` vs
   `Gizeh ... mit Aktivkohle` are different products). That is the variant problem, and why
   `POST /products/{id}/clone` exists.

   **Done =** 20 minutes of shelf scanning produces a work list; an evening at a desk turns it into a
   catalogue where every product on the shelf scans — *before* staff rely on it.

2. **🟡 SCAN MISS SEARCHES THE CATALOGUE — BUILT, NEEDS A TILL TEST.** *(shop floor · the one thing that matters)*

   **Built 2026-07-31.** The scan-miss modal already let you type a name and tap to bind; what it
   could not do was cross a language, because it called plain `/search`. It now calls **both** —
   ranked search *and* `POST /catalog/match-candidates` (the folding + brand filter that until now
   only ran in the create guard) — merges them, and flags the cross-language rows `DE/EN` so a
   `schwarz` row answering a `black` search explains itself. Request-sequenced, and a failure in
   either half is logged and ignored rather than blanking a working search at a till.

   **Found while proving it — a bug that had been live since the folding shipped:** `_product_size`
   knew `pcs` but not the singular `pc.`, so the English packet name yielded *no* size token while
   the German yielded `1stk`; the same-size rule then discarded the match the folding had just
   scored 0.857. **The create guard was dead for this exact pair the whole time.** Fixed in the size
   table (server + client mirror + query boost), 5 regression tests. Verified live: candidates now
   returns the German row at 0.857, and `POST /products` 409s with it offered.

   **⛔ Still not human-green:** nobody has scanned an unknown EAN at a real till and bound it.

   *(original write-up below)*

   **→ Read [`CATALOG-IDENTITY.md`](CATALOG-IDENTITY.md) first** — the why behind this item, and the product thesis it comes from.

   **The problem, from a full day at Artemis 2026-07-30:** ~50% of scans find nothing, so the
   operator rebuilds a product that was already there. 40 products ≈ 3.3 hours. Angel:
   *"Everything is in the catalog already. It's there... either look in our catalogue properly
   or look on the internet properly."*

   **Root cause (measured, not guessed):**
   - The 2026-07-07 import created 5,111 products. Tamar publishes **no EAN**, so Banco minted
     internal `2xxxxxxxxxxxx` codes for **5,103** of them. Those appear on **no packet anywhere**.
   - So a real scan can never match. Confirmed: 5,103 minted vs 63 real EANs.
   - **There is no bulk fix.** Verified 2026-07-30: Tamar's API has no EAN field; Felix's own
     site (artemisluzern.ch) serves 83 KB pages with **zero** structured data / no GTIN; free
     barcode DBs run barcode→product, the wrong direction. The EANs exist only on the packets.

   **Therefore the fix is not to acquire EANs in bulk — it is to make binding one take 30 seconds:**
   ```
   today:   scan miss → hunt → CREATE a new product   ~5 min   × 40 = 3.3 h
   wanted:  scan miss → "is it this one?" → tap        ~30 sec × 40 = 20 min
   ```
   The product already has description, image, category and price. Only the barcode is missing.

   **Everything needed is already built and tested — it just runs on the wrong screen:**
   | Piece | Where | State |
   |---|---|---|
   | Cross-language name match (schwarz↔black, Stk.↔pc) | `pos_router._norm_name_for_match` / `_sql_norm_name` | ✅ built, 6 tests |
   | Alias binding ("scan once, known forever") | `POST /products/{id}/barcodes`, table `product_barcodes` | ✅ exists |
   | Search ranking | `/products/search` | ✅ verified: "smoking blue king size" → correct product at **rank 1** |

   **The gap:** the cross-language match only runs in the **create** guard (`POST /products`,
   ~line 380) — i.e. *after* the operator has typed everything. It must fire at **scan miss**,
   before any typing.

   **Plan:** on a barcode miss, call the search with the scanned code's context, show top ~5
   candidates with picture + price, one tap → bind the scanned EAN as an alias → done. "Create
   new" becomes the last resort, not the first.

   **Done =** scan an unknown EAN on a product that exists → it is offered → one tap → it scans
   forever after. Verified at the shop, not in a report.

3. **✅ MERGE BUTTON — DONE 2026-07-31.** `POST /catalog/merge` (manager) + a *Merge into a
   catalogue row* action on any row you created in shelf intake. Keeps the wholesale row, moves
   the real EAN onto it as PRIMARY, demotes the minted code to an alias (a printed shelf label
   must keep scanning), fills only BLANK fields on the survivor, and DEACTIVATES the twin rather
   than deleting it — its line items are someone's sales history. `dry_run` reports the plan.
   Proven end to end on a live DB: both barcodes resolve to the survivor afterwards. 7 tests.
   *Still to do: the ~40 duplicates from 2026-07-30 have not been merged yet — that is now a
   matter of working the list, not building anything.*

   **⚠️ Correction 2026-08-03 — "working the list" is NOT possible from the catalog.** This
   action exists only on a shelf-intake card for an **unknown** code. Once the EAN is bound the
   button is gone, and the catalog screen — where you actually *see* two identical rows — has no
   merge at all. So the ~40 duplicates cannot be worked with today's UI. See
   **🟠 THE MERGE BUTTON DISAPPEARS THE MOMENT YOU NEED IT** near the top.

4. **Retire the 2026-07-30 duplicate rows.** *(now just usage of the merge button, above)*
   - ~40 products were hand-created that already existed (e.g. `Blow Pre-built CBD Joint Pure "V1" 1 pc. black` = `Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz`, TAM-20350).
   - The **imported** row has the good data; the **hand-made** row has the real EAN. So move the barcode onto the imported row and drop the twin. Angel: *"you just delete them"*.
   - Dry-run-first script, same shape as `scripts/reclass-age-gate.py`.

4. **✅ Debounce the sale-screen product search — DONE 2026-07-31.**
   - `@input.debounce.300ms` on the search box, plus real request sequencing in `searchProducts()`
     (and in the scan-miss `searchExisting()`), so a slow reply to an early keystroke can no longer
     overwrite a fast reply to a late one — including the empty-query reply the SQL short-circuits
     to "return everything", which is how a full barcode typed into Search showed all 24 products.

5. **Keep `ipp-usb` fresh — the last thing between the labeler and daily use.** *(shop floor)*
   - Everything prints: CLI, barcodes, scanning, and the browser UI at any size. But `ipp-usb`'s USB session dies after **6–13 minutes idle** and jobs then queue silently. `print-label.py` heals itself; **Chrome cannot**.
   - A systemd timer that restarts `ipp-usb` *only when it has stopped relaying* — reuse `ipp_usb_alive()` from `print-label.py`. Passwordless sudoers rule already installed.
   - Then the freebie: `google-chrome --kiosk-printing` to drop the print dialog.

6. **Harden go-live — DNS preflight + default-secret gate.** *(Roadmap Phase A)*
   - Add a preflight to `scripts/deploy-prod.sh` that resolves `APP_PUBLIC_HOST` + `KC_PUBLIC_HOST` against the server IP **before** cert issuance, and refuses if a starter-default secret is still in place.

7. **DR restore (Move B) — ⛔ BLOCKED on B2 read creds.** *(Roadmap Phase A · the ownership proof)*
   - Needs a read-only B2 key + bucket + passphrase. Then: infra up → `restore-from-b2.sh` with creds as **env vars** → row-check prints a real product count → app up → `standup.sh`.

8. **Feed labels from the catalog.** *(shop floor)*
   - Barcode + name + price by product ID, so a shelf label is one command and a re-price is a re-print.

- **Log the unknown EANs that get hit at the till.** *(Angel, 2026-08-05, deciding the 300-hottest
  scope — [`onboarding/16-bom-artemis-luzern.md`](onboarding/16-bom-artemis-luzern.md))* The
  catalogue tail is ~4,800 products nobody will validate by hand, and the right answer is to let the
  till bind them on first scan. **But record the misses**: a scan that resolves to nothing is real
  demand data, and it turns the tail from a wall into a **ranked queue** — validate what customers
  actually brought to the counter, not what we guessed. Cheap to capture (the miss already happens),
  and it makes every later catalogue session evidence-led. *(shop floor · catalogue)*

- **Fixing a wrong product mid-sale means signing out — and the cart dies with the session.**
  *(Angel, 2026-08-05, from the UAT sim: "if a product was wrong I would sign out to felix and fix the
  catalog and then relog in again as pam to complete the sale — and that was awkward.")* He is right
  that the answer is to **fix the catalogue before the sale**, not invent something at the till. **But
  a cashier at 17:00 cannot do that**, and this is exactly the moment a shop gets a bad row: one-word
  name, no category, no cost — the Pam-and-the-grinder path from 2026-08-03. Worse, the cart lives in
  `sessionStorage`, so **signing out loses the sale in progress** and the customer waits through a
  re-scan.
  **Note Felix does not discount** — he holds the price and gives a **free treat** instead
  (`line_item.is_giveaway`, already working and seen in today's data). So this is *not* a discount
  feature; it is "the price on the row is wrong and someone must be able to proceed honestly".
  **Wanted:** a manager-reviewable one-off price at the till, or an in-place edit that does not
  destroy the cart. Needs Felix's answer on what a cashier may do with price — asked on the UAT
  sheet. *(shop floor · Phase A)*

- **🔁 CONSUMABLE vs DURABLE — answered: VELOCITY already does this, and it is already built.**
  *(Angel, 2026-08-05: "you don't buy a grinder every day … but papers, filters, more CBD … we don't
  have a category for that per se.")*
  **✅ THE ANSWER: nothing to build, and nothing to declare.** A consumable is not a flag — it is a
  product that keeps reappearing in sales. The till already knows:
  - **`GET /reorder/suggestions`** (`pos_router.py:2625`) — *"fastest-selling products over the last
    `days` that are NOT already on the Order Book. **Velocity is rock-solid even with zero-perpetual —
    the till knows exactly what sold.** Suggest, don't decide."*
  - **`ReorderItemModel`** — the Order Book, `to_order → on_order → received`, with the supplier a
    human picked per line (one product can be ordered from several suppliers).
  **Why this beats a declared flag:** it cannot be wrong about a product you *thought* was slow, and
  it needs no maintenance. Papers come back weekly; a grinder does not. The only input it needs is
  **sales history**, and there are 8 transactions so far. So the sequence is: trade → velocity
  accumulates → the Order Book fills itself.
  > ### ⛔ Do NOT set `min_stock` / `max_stock` / reorder points. Tigs proposed this on 2026-08-05 and
  > it was wrong twice over.
  > **First**, `stock_quantity` is `1` on 5,099 of 5,163 rows — so any reorder point fires instantly
  > and produces ~2,200 false alerts on day one, teaching the shop to ignore its own alarm.
  > **Second and more important, the design deliberately rejects the whole mechanism**, and says so:
  > - `reorder_item_model.py:4` — *"Banco is ZERO-PERPETUAL — we never compute reorder from an
  >   on-hand count (**it's a lie**)."*
  > - `catalog.html:732` — *"**No min/max/reorder thresholds**: Banco runs zero perpetual inventory.
  >   Reorder guidance comes from sales velocity, not a count."*
  > - `pos_router.py:5180` — *"a sale never decrements a stock count."*
  > - `catalog_enrichment.py:571` — `stock_quantity=1  # zero-perpetual: the shelf is the stock check`
  >
  > `stock_quantity = 1` is **not missing data**. It is the design. **Shelf intake is confirmed
  > master-data-only** — its `count` fields mean "this barcode was seen ×3 in one scan batch" and
  > "unknown codes still to resolve", never inventory. **Anyone reading a stock count in Banco as a
  > stock claim is reading it wrong.**
  Retained below only as a record of what was checked and ruled out:
  - ❌ **Do not reuse `product_class`.** It is `standard` / `tobacco_nicotine` / `cbd_hemp` /
    `cbd_open` / `alcohol` and **drives the 18+ gate and VAT**. Repurposing it breaks the age gate.
  - ❌ **`consumption` on `line_items` is a red herring** — it means `dine_in` / `takeaway` for café
    VAT. Confusing name, unrelated job.
  - ❌ **`product_group` is merchandising** (Vape 1885 · Smoking Gear 1511 · Papers & Rolling 593 …),
    populated on 5,157/5,163. It answers *"where does it hang?"*, not *"how fast does it go?"*
  - ⛔ **`min_stock`, `max_stock`, `lead_time_days`, `stock_alert_threshold` exist on `products` and
    are populated on 0, 0, 0 and 6 rows — because they are DELIBERATELY unused.** Legacy columns the
    zero-perpetual design walked away from, **not machinery waiting to be switched on.**
  **If a human ever wants to eyeball the split** (e.g. to pick the 300 hottest before there is enough
  sales history), the categories already separate it: consumables ≈
  `E-Liquids` (699) · `Coils & Pods` (349) · `Prefilled & Disposables` (292) · `Filters & Tips` (258)
  · `CBD Flower` (205) · `Shisha Tobacco` (126) · `Tobacco` (126) · `Rolling Papers` (94) ·
  `Blunts & Wraps` (57); durables ≈ `Vape Devices` · `Vaporizers` · `Bongs` · `Grinders` · `Pipes` ·
  `Rolling Trays` · `Ashtrays` · `Decor`. **That is a reading aid for choosing where to scan first —
  not a field to write.** Velocity replaces it the moment the till has history.
  ⚠️ **Related and worse: `cost` is set on 61 of 5,163 products.** No cost, no margin — that weakens
  reorder decisions, the offline kit's whole "know your margin" value, and any slow-mover review.
  *(shop floor · master data)*

- **📚 A real training manual — business process, workflow, layout, schedule.** *(Angel, 2026-08-05:
  "we really need a proper training manual covering the business process and a plan and workflow and
  layout and schedule … training the people and testing them in UAT is key.")* The onboarding kit
  today explains **Banco**; it does not explain **the shop's day**. Missing: who does what and when
  (open, trade, shift change, close), the counter layout and where each device lives, the weekly
  rhythm (catalogue work, label runs, backups), and **how a new cashier is trained and then tested**.
  Angel's point is that UAT is not only about finding defects — *he* is learning the way of working at
  the same time, and that knowledge is currently only in his head and in scattered testsheets.
  Should end with a **sign-off**: a new cashier runs a scripted day and someone confirms they can do
  it. Pairs with [`10-devices-and-roles.md`](onboarding/10-devices-and-roles.md) (roles),
  [`14-when-it-goes-down.md`](onboarding/14-when-it-goes-down.md) (the ladder) and
  [`16-bom-artemis-luzern.md`](onboarding/16-bom-artemis-luzern.md) (the layout). *(Phase B ·
  onboarding · the thing a second shop would need most)*

- **📦 Receiving today is a spot-check, and the delivery slip carries the COST nobody else has.**
  *(Angel, after talking to Rafi 2026-08-05: when a delivery arrives he "looks at the delivery slip
  and says okay, that's about there" — a spot-check, not a count — then prices it with his own
  stickers and restocks. **Nothing item-level is captured.**)*
  Angel's own read is that a pile of slips would give the same *shape* of information the day book
  gave — what to focus on, not which item. **True for quantities. Not true for cost.** The slip is the
  one place a wholesale price is written down, and cost is precisely the field Felix may never enter
  by hand (see the threshold item below).
  **So: grab slips for HARDWARE deliveries only** — bongs, vaporizers, grinders, dab gear. Per
  [`19`](onboarding/19-what-actually-sells.md) that is where the money is (398.– · 307.– · 300.–), and
  per the threshold item it is where cost actually matters. **Papers do not need it.**
  Also worth noting for the grinder work: **grinders often DO have an EAN**, just not findable without
  the slip or the outer box. That does **not** block minting — the alias table already carries a
  minted code and a real EAN on the same product (proved 2026-08-05: `TAM-10886` holds both
  `2000000108865` and `716165280286`, and both scan). **Mint now; if the real EAN surfaces off a slip
  later, it joins as an alias and nothing is redone.** *(shop floor · catalogue · Phase B)*

- **💵 COST above a price threshold, optional below it — so the queue can actually reach zero.**
  *(Angel, 2026-08-05: "that final check was when he puts in the cost, then we know it's done" — then,
  the same evening: "**he might not do costs**.")* Both are true, and together they are a trap.
  **If cost is the completion signal and Felix never supplies it, nothing ever completes** — and a
  queue that can never empty is a queue people stop opening. That is the inverse of the
  green-that-cannot-turn-red already rejected twice in `compose.yml`: **a red that can never turn
  green carries no information either.**
  `catalog_health` already splits `sellable` / `scannable` / `costed` for exactly this reason — a
  single score once read **1% complete** over a catalogue that was 99% priced, categorised and
  pictured, purely because cost was missing on 5,099 rows.
  **Proposal: require cost only above a price threshold.** Nobody needs margin on a CHF 1.40 packet of
  papers. Everybody wants it on a **CHF 398 vaporizer** — and per
  [`19`](onboarding/19-what-actually-sells.md) that is exactly where the money is (biggest sales of
  the month: 398.– · 378.– · 307.– · 300.–). A threshold makes the bench **drain to zero** while still
  protecting the decisions worth protecting.
  **Angel's framing to keep:** *"it leaves it hanging in the queue all the time that it still needs to
  be fixed. It's only 75% correct. I think that's fair."* A row that scans and has a name, price and
  picture **is** sellable — say so, and keep flagging what is missing, rather than choosing between a
  green tick and a permanent red. *(Phase A · catalogue · Felix's call on the threshold)*

- **📋 THE PAPER BUNDLE PRICES EXIST — ON A SIGN ON THE WALL, AND NOWHERE ELSE.** *(Angel
  photographed it 2026-08-06 — `onboarding/testsheets/grinders/2026-08-06-shelf-wall/w02.jpg`.)*
  ```
  !! Preise gesenkt !!            Bundle Preise — ALLE HERSTELLER
     3x Longpape      5.-            3x Rollenpape    10.-
  Boxen — ALLE HERSTELLER
     Box Longpape    39.-            Box Rollen       49.-
  Budget Papes Rockies Box:  25.- Rollen · 17.- Longpape weiss/braun · 19.- Longpape weiss mit Filter
  ```
  **"Alle Hersteller" makes it a RULE, not a per-product price** — which is exactly what
  `price_tiers` + `tier_mode='bundle'` model, and it is the missing half of the 30-July item below
  (*"retail tier prices aren't reaching the POS"*). That item assumed the answer had to be scraped
  off artemisluzern.ch. **It did not: it is on the wall, and it is four numbers.**
  **State today: 6 of 155 rolling papers carry any tier, and none of them is this one.** The six hold
  ladders like `1.40 → 1.30 @10 → 0.95 @50 → 0.80 @150` — **Tamar's WHOLESALE ladder, what Felix
  pays**, which is precisely the confusion the 30-July item names.
  ⚠️ **Do NOT bulk-apply this without Angel.** The sign speaks Artemis's own language, and the
  mapping is a judgement only he can make: `Rips Hemp King Size rolling papers 5m` is a 5-metre roll,
  yet he priced it `3 for 6.00` — not the sign's `3x Rollenpape 10.-` — because at CHF 2.50 a single,
  3-for-10 would cost MORE than three singles. **So "Longpape" and "Rollenpape" do not map onto the
  catalogue by name.** The sign is the rule; deciding which products it covers is human work.
  **Wanted:** Angel tags which products are Longpape vs Rollenpape (a category or a tag), then one
  script applies the ladder to each group. ✅ He has already done the first one by hand from the till
  using the new manager price panel — `TAM-2834`, 2.50, bundle, 3/6.00 · 5/9.00 · 10/17.00.
  ✅ **Fixed on the way:** `Papers & Filters` is **not** in `CANONICAL_CATEGORIES` and 2 rows carried
  it (both Rips), making them invisible to a `Rolling Papers` filter. Moved. *(shop floor ·
  money-correctness)*

- **🔇 THE CATALOG SEARCH NEVER SAYS "no strong match" — 69 weak rows look exactly like a hit.**
  *(Angel, 2026-08-06: searched `hempsana salbe 75ml`, got 69 results led by a Chubby Gorilla bottle
  and a tube of toothpaste, concluded "the look up is not good".)*
  **Diagnosed, and the ranking is NOT broken.** `salbe` expands via BL-101 synonyms to
  `balm · cosmetic · cream · creme · kosmetik · salbe · topical`, which deliberately widens the
  search to the whole cosmetics shelf — the same machinery that lets an English `lighter` find a
  German `Feuerzeug`. His query held one rare word (`hempsana`, 2 rows) and one floodgate (`salbe`).
  **And the product genuinely was not there** — only `Hempsana Hanf Gel Roller` and
  `Hempsana Hanftee` exist; no Salbe, no sheabutter, nothing. Creating it was correct.
  **So the gap is not relevance, it is CONFIDENCE.** `snap-find` already has the doctrine —
  `best_match_score`, *"found it"* vs *"no strong match → search or create new"*, described in its own
  docstring as *never a confident wrong answer*. The catalog search has no equivalent, so **69 loose
  matches are presented exactly like 69 good ones**, and the operator scrolls and doubts the tool.
  **Wanted:** return a top-match score and say it out loud — *"no strong match · 69 loose results"*
  above the list when the best row scores below a threshold. Angel would have known in one second
  that the Salbe was absent instead of hunting for it.
  ⚠️ **A ranking change is NOT the fix** — one was tried and reverted the same day for failing
  standing rule 4: it reordered nothing on either test query, so it could not be shown to help.
  *(shop floor · till speed · honest-confidence doctrine)*

- **📄 LET THE AI READ THE PAGE when the shop publishes no structured data.** *(Angel, 2026-08-06,
  after pasting a Purize Com Cruncher page: "It read that page. It just picked up the title and
  pretty much discarded everything else… that page had a lot of details, the type of grinder, the
  material, the dimensions. It should really enrich and give it a robust description and everything
  else, tags, the whole thing.")*
  **He is right, and the cause is structural.** `_page_product_facts` reads **schema.org JSON-LD**
  first and falls back to **`og:description`**. `drehmoment-headshop.de` publishes no JSON-LD, so
  what came back was its marketing meta tag —
  *"Zweiteilige Kräutermühle – Blitzschneller Versand ✔ Spitzenpreis ✔"* — while the real specs sit
  in the page **body**, which the reader never touches.
  **A generic body parser is the wrong fix.** Every shop structures its page differently; the
  enricher only manages it for `artemisluzern.ch` because it targets one known site. Writing one
  parser per supplier does not scale and rots silently.
  **➡️ The right fix: feed the page TEXT to the model we already pay for.** Gemini is wired up and
  reads text as happily as photos. One call turns any shop's page into
  name · specs · material · dimensions · category · tags, with the **honest-note contract already in
  `vision.py`** (never raises, returns a `note` when it could not).
  ⚠️ **Structured data must still WIN** where it exists — JSON-LD is the shop *stating* its facts,
  the model is *inferring* them, and per `/catalog/page-facts`'s own docstring *"a page is evidence,
  not truth"*. Model output goes in the description and tags; **never the price and never the EAN.**
  **What already works:** the ✅ photo (fixed 2026-08-06 — it was queued but never attached), the
  title with its SEO tail stripped, and a CHF price when stated. *(shop floor · catalogue)*

- **🤝 THE TWO READS DISAGREEING IS A SIGNAL — and it is currently thrown away.** *(Found 2026-08-06
  proving the two-stage read on the real endpoint.)* The safety argument for stage 1 was *"brand-led
  is what recognises a non-grinder"*. **It is only usually right.** On Angel's stash tin the brand
  read returned `Tightvac Vacuum Storage Container` / `Storage & Stash` on one run — correct — and
  **`Egatvec Grinder` / `Grinders`** on the next. When it miscategorises, stage 2 inherits the error
  and searches the wrong shelf.
  **The interesting part:** on that same run the *form* read answered **`Dose Silikon 2teilig 35mm`**
  — a **tin**, not a grinder. It resisted the framing it was given and described what it actually
  saw. **The two reads contradicted each other, and nothing noticed.**
  **Wanted:** when the form read's own noun disagrees with the brand read's category (`Dose` under
  `Grinders`), **say so on screen** — "the two reads disagree, check the category". Cheap, and it is
  the same doctrine as the honest match score: *never a confident wrong answer.* A disagreement is
  the system knowing something is off; swallowing it is the silent-failure shape again.
  *(shop floor · catalogue)*

- **🔬 ASK THE AI FOR THE FORM, NOT THE BRAND — measured, and it roughly doubles the match score.**
  *(Angel's insight, 2026-08-06: "you have a style of grinder in 3 sizes that a manufacturer white-
  labels and sells plain or in 15 colours — I was hoping it would recognise the shape.")*
  He is right, and the catalogue names already encode exactly that:
  `Grinder Alu CNC 4teilig mit Sieb 62mm Rasta` = material · parts · feature · size · artwork. The
  prompt asks for a **brand-led shelf name**, which is right for branded retail and wrong for
  white-label goods where the print is decoration and the **form is the signal**.
  **Measured on prod via the existing `hint` param, same photos, same code:**
  | photo | brand-led | form-led |
  |---|---|---|
  | g00 Champ High | 0.552 | **0.895** |
  | g02 Garden Highpro | 0.368 | **0.895** |
  | g04 Barney's Farm | 0.370 | **0.744** |
  | g03 Birdy | 0.393 | **0.613** |
  | g05 Master The Grow | 0.619 | **0.700** |
  Form-led won on **every** photo, and the matches were the right form —
  `Grinder Alu CNC 4teilig mit Sieb 50mm …`.
  **⚠️ It is a SECOND read, not a replacement.** The hint presupposes the category: told "this is a
  white-label grinder", the model dutifully turned Angel's **stash tin** into
  `Grinder Acryl 2teilig 50mm`, while the brand-led read correctly called it
  `Tightvac Vacuum Storage Container`. **Brand-led is what recognises a non-grinder.**
  **Design: two-stage.** ① brand-led → category (and the non-grinder catch) ② if the category is a
  white-label class (grinders · trays · plain glass), re-read form-led and search on that — or just
  run both queries and merge. Two calls, ~5 s.
  **🔴 Do NOT trust the size it returns.** Angel predicted this before the test: *"on the pictures
  there is no way to know relative sizes."* Confirmed — the model answered `50mm` for nearly
  everything. It helps the match because most grinders are ~50mm, but it is **a guess wearing a
  number**, which is this project's most-repeated bug shape. If a form-led read ever WRITES a
  product, the mm comes off a caliper or the packaging, never the model. *(shop floor · catalogue)*

- **⬇️ DEMOTE the photo/batch tooling — "less is more" already solves this.** *(Angel, 2026-08-06,
  while the AI runs were being measured.)* He typed **`Champ High White Leaf` + category Grinders**
  and got **2 of 2 matches, the right one first** — the same product snap-find missed on two runs
  out of three. **No AI, no photo, no batch tool.**
  **The mistake in how the AI route was judged:** the model was made to generate a *long descriptive*
  query and the search was scored on that. A human types **two words and a category**, and the
  shorter query is *more* selective. **An AI produces a DESCRIPTION; a human produces a BRAND** —
  `Rasta Leaf Metal Grinder` vs `Champ High` — and the catalogue is indexed by the second.
  **➡️ So the photo route only earns its keep when the brand is READABLE on the object.** Still worth
  the ten-item measurement, but **it is no longer on the critical path**, and a batch upload tool
  should not be built before the spec filters below. *(shop floor · priorities)*

- **📷 snap-find throws away the CATEGORY the AI just told it.** *(Found 2026-08-06 proving the
  vision path end to end on Angel's real grinder photo.)* Gemini read the photo as
  `"Rasta Leaf Metal Grinder"` **with `category: "Grinders"`**, and `snap_find_product`
  (`pos_router.py`) builds its query from **name + brand only** — the category is dropped.
  **Result on the real photo:** the right grinder (`LZ-3661075283438`) came back at **rank 5 of 6**,
  and **rank 1 was `Acryl Bong Atomic - Smoke Blower`**. A bong, above the grinder, on a photo of a
  grinder.
  **Fix:** pass the AI's category into `_find_catalog_matches` as a scope (or at least a ranking
  boost). It would drop the bong and lift the real match several places — and the AI is already
  constrained to the canonical tree by the prompt (`CANONICAL_CATEGORIES`), so the value is safe to
  trust. **Cheap, and it directly improves the hit rate that decides the batch-tool question.**
  *(shop floor · catalogue)*

- **✅ RESOLVED 2026-08-06 — snap-find had no working AI on prod.** *(Angel at the shop 2026-08-06:
  photographed a grinder, got an empty create form, reasonably concluded the AI could not identify
  it.)* **It was never called.** The grinder was in the catalogue the whole time
  (`LZ-3661075283438`, *Ø50mm - 4-teiliger Champ High White Leaf Grinder*), and every plausible read
  of that photo — `grinder` · `leaf grinder` · `white leaf grinder` · `Champ High` — finds it by name
  search. **The search was never the problem.**
  **✅ Already fixed and deployed:** the screen now surfaces the vision service's `note` as a warning
  toast, so an AI that did not run says so instead of looking like an AI that found nothing; and a
  scheme-less provider URL is normalised rather than trusted (prod had
  `OLLAMA_TURBO_URL=www.ollama.com`, which httpx refuses outright).
  **⛔ Still blocked — neither provider works on this box:**
  | Provider | State |
  |---|---|
  | `gemini` (the default) | **`BH_GOOGLE_API_KEY` not set** |
  | `ollama` | key + URL set, but `https://ollama.com/api/chat` returns **404** — endpoint unverified, and `.env.example` leaves `OLLAMA_TURBO_URL` blank so it was hand-set |
  **✅ FIXED — `BH_GOOGLE_API_KEY` is now set on prod** (2026-08-06). Verified end to end on Angel's
  real grinder photo: `gemini-2.5-flash`, ~2.7 s, no error note, and the correct product returned.
  `BANCO_VISION_PROVIDER` is deliberately left **unset** so the code default (gemini) applies with no
  second setting.
  **Ollama is a dead end for this and that is settled** — Angel: *"Ollama IMHO has no vision
  models."* Turbo returns **404** on `/api/chat`. The key and URL stay in `.env` harmlessly; do not
  spend time on them.
  **The photo route in [`20`](onboarding/20-no-barcode-items.md) is now testable** — the ten-grinder
  hit rate can be measured. *(Phase A)*

- **🔎 SPEC FILTERS at the till — the real answer for no-barcode goods.** *(Angel, 2026-08-06: "when
  a cashier searches for an item they either have a working EAN barcode or they don't, and then they
  need to search via cat or name or part number **and have filters for ss or plastic or types of
  grinders based on their specs**.")* That is the correct shape, and it replaces the A/B/C idea below.
  **The search ladder, in order of speed:** ① barcode ② **article number** (built 2026-08-06, exact
  match now ranks first) ③ category + name ④ **filters on specs** ← this item.
  **⛔ Do NOT store an A/B/C price class.** Measured on the 192 grinders: `>50` = 18 (9%),
  `20–50` = **125 (65%)**, `<20` = 49 (26%). **A class where two-thirds of stock lands in one letter
  cannot help anyone choose.** And the quality hypothesis fails outright — **plastic averages 34.30
  and reaches 69.–**, non-CNC alu (55.59) beats CNC alu (32.59), and **3-teilig (51.56) averages more
  than 4-teilig (33.12)**. Neither material nor part count predicts price. A stored class would also
  be a field someone must set on every new product, and it would be wrong within a month.
  **Price is already a column** — a range filter (`20–30`) needs no new data, cannot drift, and
  answers what a customer actually asks. Note the shop prices at *points*, not ranges: **25.– (40
  products) · 29.– (25) · 39.– (23) · 49.– (15) · 19.– (14) = 61% of all grinders.**
  **✅ The spec data mostly EXISTS — it is just not in a filterable column.** Parsed from the names
  today: **diameter mm 165/192 (86%)** · material 143 (74%) · parts 126 (66%) · all three 107 (56%).
  And **191/192 carry a `source_url`**, i.e. a supplier page with a spec table — which is exactly what
  `scripts/enrich-from-source.py` (item 3) already reads. `attributes` jsonb exists and holds
  `{"brand": …}` on 8 rows; **no migration needed.**
  **Three steps, cheapest first:**
  1. **Backfill `attributes` from the names** by regex — free, no network, covers 56% fully and 86%
     for diameter alone.
  2. **Run the enricher over the grinders** to fill the rest from the real spec table.
  3. **Filter chips on the catalog/scan screen** — material · parts · Ø mm · price range.
  ⚠️ **Fix `_query_size_regex` to understand `mm` while doing this** — it handles pack sizes (g/ml/stk)
  and not diameters, so `62mm` gets no size boost today even though 165 grinders carry mm in the name.
  It is the single most-covered spec on the shelf. *(shop floor · till speed · catalogue)*

- **🔢 A NUMERIC query should return the exact SKU first — it is the fastest route to a no-barcode
  product and today it is unranked.** *(Angel, 2026-08-06: "every grinder already has a 4-5 digit
  number unique in the system… if you type 1002 well then good luck.")*
  **His idea is right and the data backs it hard.** Grinders: **191/192 carry a `TAM-` SKU, all 192
  distinct**, and `supplier_sku` holds the bare digits. Measured across the catalogue:
  | Typed | Hits |
  |---|---|
  | bare 4 digits | **worst 15**, avg 3.53, unique only 30% of the time |
  | **full 5 digits** | **worst 1, avg 1.00, 300/300 sampled unique** |
  **So "type the full number" is already a working answer** — it needs no label, no sticker and no
  permission from Felix, which is exactly the constraint (see
  [`20`](onboarding/20-no-barcode-items.md)).
  **The gap:** `pos_router.py:3741` matches `sku ILIKE '%q%'`, and the ranking
  (`pos_router.py:3704`) only boosts rows whose **NAME** starts with the query. **A number never
  matches a name**, so `relevance` — a name/description trigram — decides the order of numeric hits.
  It is noise. An exact `TAM-1002` is not guaranteed to beat `TAM-10027`.
  **Fix (small, high value):** when the query is **pure digits** or `TAM-<digits>`, put
  `CASE WHEN sku = 'TAM-'||:q OR sku = :q OR supplier_sku = :q THEN 0 ELSE 1 END` at the FRONT of the
  order clause. Turns "type the number, scan a list" into "type the number, done" — the difference
  between a 3-second and a 15-second sale.
  ⚠️ **694 products carry 4-digit TAMs**, and a 4-digit full number is a substring of any 5-digit one
  starting the same way — which is precisely the case Angel hit. Exact-first is what fixes it; nothing
  else does. *(shop floor · till speed)*

- **📷 The AI snap-find is buried behind "Create new product" — but its whole job is to tell you
  whether you need one.** *(Found 2026-08-06 when Angel tried to photograph a grinder and got
  `No MultiFormat Readers were able to detect the code`.)*
  **Not a bug — two different photo controls, and the discoverable one is the wrong one:**
  - `onScanFile` (`catalog.html:970`, inside the **scan** overlay) — the barcode reader's no-camera
    fallback. Decodes a **barcode** out of a still. On a grinder it correctly reports "no barcode in
    photo", which reads like the AI failed.
  - `aiSuggest` → `POST /products/snap-find` (`catalog.html:527`) — the one he wants. **Lives inside
    the Create/Edit modal, gated `x-show="!editing"`, so it is create-mode only.**
  **The contradiction:** snap-find's own comment says *"FIND-FIRST … if it's already in the shop (or
  the FourTwenty reference), show the picker so the cashier picks the existing row instead of creating
  a duplicate."* **You must declare you are creating a new product before the tool that tells you
  whether to create one will run.** For the grinder pass — 192 rows, and Angel does not know which
  already exist — that is backwards.
  **Same shape as the merge button** (2026-08-03): a tool reachable only from where the problem is
  invisible. *Ask where the person is STANDING when they need it.*
  **Wanted:** a photo entry point on the catalog screen itself — "I have a picture, what is this?" —
  that lands on the same find-first picker, with *create* as the outcome rather than the prerequisite.
  ⚠️ Also worth a look: `catalog:41` logs an **i18n key-parity warning, `it` vs `en`, 1 extra key**.
  Harmless today, but it is the kind of thing that becomes a blank label on a screen later. *(shop
  floor · UX)*

- **🌀 GRINDERS — the no-barcode workflow, and the pilot for trays and bongs.** *(Angel, 2026-08-05.
  Full workflow: [`onboarding/20-no-barcode-items.md`](onboarding/20-no-barcode-items.md))* The day
  book ranks grinders **4th** — roughly one a day, not the slow mover we assumed — and **none of them
  carry an EAN**, so the scan-and-bind loop that worked on papers does not apply. Neither do trays or
  bongs. **And it is the expensive end of the shop:** the month's biggest single sales were a `Mighty`
  vaporizer at 398.–, a bong-plus-kit at 307.–, `Hanfsalbe` at 300.–.
  **Angel's plan, and it is the right one:** photograph every grinder, match the picture (most come
  from **420**; they rarely sell online, which is *why* people buy them in the shop and why picture
  matching beats a web search), then **mint a code and print a label**.
  **⚖️ Minting is CORRECT here** — the 2026-07-30 lesson says *never invent an identifier that
  EXISTS*, and a grinder has none. `barcode_is_internal` is exactly this case. Do not let that lesson
  block the only workable route.
  **The step that is cheap now and expensive later: a naming convention, decided once.** Proposal
  `Grinder · <brand> · <material> · <parts> · <Ø mm>` — size, parts, material and brand are what a
  customer actually asks for. Without one, nobody can find a grinder by typing.
  **Open and needs a PHYSICAL test, not a decision:** does an 18 mm QR label fit the *smallest*
  grinder (18 mm read as cleanly as 20 mm in the 2026-07-29 tests), and will Felix accept a sticker on
  goods a customer picks up? Fallbacks if not: a **shelf-edge label** to scan, or a **PLU button** for
  the few that sell most. *(shop floor · catalogue)*

- **✏️ Let a MANAGER fix a price from the checkout screen.** *(Angel's idea, 2026-08-05: "the cashier
  sees, hey Felix, it's wrong — can you fix it for me, and they can just jump in and fix it.")*
  The cashier is the one who **discovers** a wrong price, with the customer standing there, and today
  the only route is sign out → fix as manager → sign back in, **which loses the cart** (`sessionStorage`).
  **Wanted:** on the checkout line item, an **edit/override button that only renders for a manager**.
  The cashier calls Felix or Ralph over, they tap, fix, and the sale continues — cart intact, no
  re-scan, and the fix lands in the catalogue instead of being a one-off.
  **Why it fits now:** every one of the 173 rows touched 2026-08-05 has an unverified price, so
  wrong prices *will* surface at the till over the coming weeks. This turns each one into a
  five-second correction by the right person instead of a lost sale or a bad row.
  ⚠️ **Keep the roles honest** — a cashier must not be able to change a price; the button appears for
  a manager only, and the change is audited. Same shape as the force-close: *ask where the person is
  STANDING when they need it.* *(shop floor · Phase A)*

- **🔴🔴 74 PRODUCTS RING UP AT CHF 99.00 — 40 of them created tonight, all scannable.**
  *(Found 2026-08-05 while fixing the junk names. **This is money, and it is live on prod.**)*
  A packet of OCB papers worth ~1.50 currently asks the customer for **99.00**. Also affected:
  `RAW Original Filtertips` · `CLIPPER GAS 300 ML` · `Cigarettes Tabac Fred Roses` ·
  `Blue Cyclone Hemp Cones` — across Rolling Papers, Tobacco, CBD Flower, Lighters and Other.
  **Why it happened, and it is not carelessness:** shelf intake *requires* a sale price (correctly —
  `10-devices-and-roles.md`), so `99` is what you type to get past the field with a shelf to finish.
  **Why nothing caught it:** every gap detector asks *"what is MISSING?"* and 99.00 is not missing. It
  is the 0.00 doctrine wearing a plausible number —
  > *"an item that rings up at 0.00 is worse than one that is missing, because the missing one gets
  > noticed"*
  — except **99.00 does not even get noticed**, because it looks like a price. The shelf-intake stub
  list flags `no cost`; it says nothing about an absurd `price`.
  **Two jobs:**
  1. **Price the 74** — human only. Tigs will not invent prices; guessing on 40 rows is how a shop
     overcharges. `SELECT sku, name, category FROM products WHERE is_active AND price = 99.00`.
  2. **Detect the class.** Catalog Health should flag *"74 products share the exact price 99.00 across
     8 unrelated categories"* — a placeholder betrays itself by being **identical across products that
     have nothing in common**. Also worth a "capture without a real price yet" state, so the operator
     is not forced to invent one to move on. *(Phase A · money-correctness · shop floor)*

- **✅ FIXED 2026-08-05 — a barcode with letters in it can never be scanned.**
  ~~`ITEM-0070` `2024VL099B` and `ITEM-0072` `2024Vl099b`~~ — a website's article number captured from
  a pasted page. Both set to **`NULL`** (not `''` — `''` is not NULL to a unique index, per
  2026-08-03), so the first real scan can bind them. Verified: **zero** barcodes in prod now contain a
  non-digit. **The pair still needs merging** — same product, two rows, and it is a good first real
  test of the merge screen, which no human has yet used on a real pair. **The validation is still
  open**: the barcode field should refuse non-digits at the point of entry, in shelf intake and in the
  catalogue form, or this recurs.

- **✅ FIXED 2026-08-05 — six product names carried SEO page titles.** ~~`Elements Connoisseur Paper +
  Tips - Headshop - scorpio-shop.de, 1,50 €`~~ and five like it. Marketing tail stripped, nothing
  invented. Verified zero remaining. **The cause is still open** — the shelf-intake web-paste path
  takes a `<title>` raw, so it recurs on the next pasted page. Wanted: strip the shop-name tail
  (`- Headshop -`, `| shopname`, `jetzt günstig online kaufen`, a trailing price) and **show the
  operator the name before saving**, not after.

- **(original note, for the record) A barcode with letters in it can never be scanned.**
  *(Found 2026-08-05 auditing Angel's shelf-intake session.)*
  ```
  ITEM-0070 | 2024VL099B | JaJa Noir King Size XXL Black Zigarettenpapier
  ITEM-0072 | 2024Vl099b | JaJa Noir King Size XXL Black Zigarettenpapier - H…
  ```
  `2024VL099B` is **a website's article number**, captured into the barcode field from a pasted page.
  It contains letters, so **no scanner will ever resolve it** — a dead row that looks alive, and the
  cruelest kind because nothing reports it. It happened **twice for the same packet**, differing only
  in letter case, so there are also two rows for one product.
  This is the 2026-07-30 lesson from the other side: that one was *"never invent an identifier that
  exists in the physical world"*; this is **Banco accepting someone else's identifier**.
  **Fix: validate the barcode field — digits only.** Real EANs are 8, 12, 13 or 14 digits (verified:
  every other real barcode in prod is 8, 12 or 13). Reject at the point of entry, in shelf intake and
  in the catalogue form. **Cheap, and it closes the class, not just these two rows.**
  Then merge `ITEM-0070` + `ITEM-0072` and bind the real EAN off the packet. *(shop floor ·
  money-correctness · catalogue integrity)*

- **A pasted page can put a competitor's shop name and price into the product NAME.** *(2026-08-05 —
  six rows, four created tonight.)* `ITEM-0049 · 0060 · 0072 · 0075 · 0106 · 0111` carry SEO page
  titles: `Elements Connoisseur Paper + Tips - Headshop - scorpio-shop.de, 1,50 €` ·
  `Blue Cyclone Hemp Cones jetzt günstig online kaufen` ·
  `50 Stück Aktivkohlefilter-Cones von PURIZE jetzt günstig online kaufe` (truncated mid-word).
  Same shape as `650b3ee` ("a competitor's shop name and article number landed in the catalogue"), so
  **that fix does not cover the shelf-intake web-paste path.** Cosmetic next to the barcode bug —
  `CATALOG-IDENTITY.md` makes names labels, not identity — but a competitor's domain and price in the
  catalogue is not a good look, and the truncation shows the title was taken raw.
  **Wanted:** strip the shop-name tail from a scraped `<title>` (`- Headshop -`, `| shopname`,
  `jetzt günstig online kaufen`, a trailing price), and **show the operator the name before it is
  saved** rather than after. *(shop floor · catalogue)*

## 🔭 Backlog (not yet scheduled)

- **👤 `store_settings.owner_name` — stop hardcoding a person into the UI.** *(Angel, 2026-08-07:
  "leave it for now, we can do the owner_name thing later")* **34 user-facing strings name a person**
  across `my_day.html`, the closeout flow and all three languages in `src/static/pos/pos-i18n.js` —
  `"Sent to Felix"`, `"Ask Felix to add you in Staff…"`, `"e.g. box is locked in the safe and Felix
  has the key"`, `"p. ex. la caisse est au coffre et Felix a la clé"`. It is **deliberate**: the
  i18n header lists `Felix/Ralph` alongside TWINT and Gizeh as names preserved across translations.
  For Artemis it reads warmly and beats "your manager" — Pam knows who Felix is. For anyone cloning
  the starter it is a stranger's name in their till.
  **The fix:** add `owner_name` to `store_settings` (default `"your manager"`), render it through
  the `{placeholder}` machinery the i18n file already supports, sweep the 34. Artemis keeps "Felix",
  a fresh install reads sensibly. ~1 hour across three languages.
  **Already done:** the cashier first-price panel and toast say *"a manager to check"* / *"flagged
  for review"*, pinned by a test in `src/tests/test_cashier_first_price.py`. Code COMMENTS naming
  Felix are provenance and stay — this is only about text on a screen.

- **📦 THE OFFLINE KIT — a daily bundle that works with no Banco at all.** *(Angel, 2026-08-04. Full
  reasoning: [`onboarding/14-when-it-goes-down.md`](onboarding/14-when-it-goes-down.md))* A dated
  export on the back-office laptop: the whole catalogue with **barcodes, sale prices AND costs** as a
  real `.xlsx`, product images in a subfolder the sheet links to by **relative path**, and a simple
  order form. Outage: Felix opens the file, looks a product up, prices a basket, fills the form,
  prints it or saves a PDF to email. Nothing on that path needs a server or a network.
  **Most of it exists.** `src/services/catalog_workbook.py` already writes a genuine `.xlsx` with
  formulas, dropdowns and conditional formatting, and its design rules were chosen for exactly this —
  **formulas and validation, never macros**, so it opens in Excel, LibreOffice *and* Google Sheets.
  This is a **second export profile**, not a build.
  **Make the order form a VLOOKUP, not a blank page:** scan the barcode into a cell, the name and
  price appear from the catalogue tab. A working till in a spreadsheet, with the gun already owned,
  no code and no network. (`catalog_workbook.py`'s own docstring: *"the BARCODE — scanned straight
  into the cell, since a scanner gun is just a keyboard"*.)
  **⭐ This is the project's premise made testable.** `CLAUDE.md`: *"kill the 'what if the vendor
  vanishes?' fear with ownership, not a promise."* Not a licence clause — a file on his laptop that
  opens without us and would still open in twenty years. Angel: *"The day he says I've had enough,
  Angelo — I'm taking my CSV file and going onto a spreadsheet version of this whole thing."* **That
  has to be true or the premise is marketing.** An owner who *can* walk away with a working
  spreadsheet is an owner who chose to stay.
  **Requirements:** generated **daily and automatically** (`scripts/install-backup-cron.sh` sets the
  pattern — a bundle nobody refreshes is stale on the one day it matters); **relative** image paths,
  zipped with the sheet; **costs included**, since half the value of owning a catalogue is knowing the
  margin. **Proof: open the bundle on a machine with the network off and price a real basket.** A
  green export script proves nothing — same rule as the label printer.
  **🔻 NOT high priority (Angel, 2026-08-04).** Item 3 and the shop scan come first. Filed with the
  groundwork done so it starts fast whenever it starts.
  **Gap analysis — code read 2026-08-04, so tomorrow is not discovery.** What exists: the Migration
  Workbench export at `pos_router.py:6285` + `src/services/catalog_workbook.py`, already carrying
  SKU · name · brand · **barcode** · category · **price** · **cost** · size · source URL · notes, with
  formulas, dropdowns and a working import back (`parse_worklist_workbook`, `pos_router.py:6395`).
  **Four things block it being the offline kit:**
  1. **It exports only UNFINISHED rows** — `_bench_gap_clause()` at `pos_router.py:6301`. That is the
     point of a worklist; the kit needs everything. Needs an "all products" profile.
  2. **⚠️ It silently caps at 2,000** — `min(limit, 2000)`, `pos_router.py:6303`. The catalogue is
     **5,173**, so a "full" export today drops ~3,000 products **and looks complete**. Exactly the
     shape the no-silent-caps rule exists for. Fix or paginate before anything else.
  3. **No images** — there is a `Photo?` yes/no column, not a link. The subfolder + relative paths +
     zip is the genuinely new part.
  4. **On demand, not daily.** Copy the pattern in `scripts/install-backup-cron.sh`.
  **Performance trap:** `_reference_best_match` runs **per row** (`pos_router.py:6330`) — one query
  each. Fine for a few hundred worklist rows, ~5,173 queries on a full export, and it will likely time
  out. That lookup is an enrichment aid, not catalogue data — **skip it in the offline profile** and
  the export gets fast. *(Phase B · the "own it" premise · shop floor)*

- **Scan into a text file during an outage — test it, and fix the line format.** *(2026-08-04)* The
  gun is a keyboard; it works with no internet. A plain text editor on the tablet beats paper because
  `CATALOG-IDENTITY.md` makes the **barcode the identity**, and a hand-copied 13-digit EAN with one
  transposed digit is a worthless line. Two small jobs, both while it is calm: **(a)** scan a
  **hyphenated** test code into a text editor on the tablet and confirm it lands clean — digits sit in
  the same place on every layout and prove nothing; **(b)** agree the line format, `EAN, qty, price`,
  so re-entry is a paste rather than transcription work, which is what scanning was supposed to
  remove. *(shop floor · ~30 min)*

- **🏠 ❄️ PARKED — run Banco in the shop.** *(raised and then argued down 2026-08-04. Full reasoning:
  [`onboarding/14-when-it-goes-down.md`](onboarding/14-when-it-goes-down.md) — read that before
  reviving this.)*
  **Verdict: do not build it.** Angel's objection is the right one — *"Hetzner servers are extremely
  good, probably more reliable than some laptop."* On-prem does **not** buy reliability, it buys
  independence from the WAN, and the proposed box is a 2015 rubbish-find laptop against a data centre
  with redundant power, ECC and staff on site. Expect **more** downtime, just downtime you can walk
  over to. It also does nothing for the likeliest failure of all — a bad deploy or an app bug follows
  you on-prem — and barely helps in a power cut, when the card terminal and the lights are out
  anyway. The one case it uniquely fixes is *internet down, power up, for hours*, and four
  independent paths (two on separate mobile networks) already make that unlikely.
  **Revive only if** the shop's internet proves unreliable **measured, not feared**, or the shop
  grows past absorbing a lost hour. Kept below because the implementation notes are worth having if
  that day comes.
  ---
  Four network paths all reach the same box in a data centre, so a Hetzner outage, a bad
  deploy or an expired cert still stops every till at once. Offline-capable tills would fix it and
  cost a **rewrite** — Banco is server-rendered Jinja, so offline means turning the till screen into
  a client-side app with a service worker, a local database and a sync layer, on top of stock
  conflicts, catalogue drift, shift boundaries and cash-only-because-Worldline-needs-the-network.
  **On-prem dodges nearly all of it.** "The internet is down" becomes "the WAN is down"; the till
  talks to a local server over the LAN exactly as it does today. No offline mode, no sync, no
  conflict resolution, **no line of the till screen changes.** Weeks, not months. And it is what the
  project claims to be: *a self-hostable POS a shop owner stands up and owns outright.* A shop that
  cannot sell when a data centre sneezes does not own it yet.
  **The hardware already exists.** Angel's CHF 40 rubbish-find HP: ~2015, **8 GB RAM**, **250 GB SSD**
  (he fitted it). Enough for one shop — Keycloak's JVM is the hungry one and worth a heap cap.
  **A laptop is a better shop server than a desktop: the battery is a built-in UPS**, so a power
  blip does not take the shop down.
  **The fiddly parts are NOT the app — they are these:**
  - **HTTPS on a LAN.** Caddy's normal Let's Encrypt flow needs public reachability. On a private
    address you need **DNS-01**, Tailscale certs, or a local CA. Not optional: plain `http://192.168…`
    is **not a secure context**, so the phone's camera snap-fill and anything else needing one
    **breaks**. Get this wrong and it looks like the app regressed.
  - **Remote access for Angel.** Deploys, restores and debugging all currently go over `ssh` to a
    public IP. Tailscale or WireGuard replaces that cleanly; port-forwarding on the shop router does
    not (and per 2026-08-04, the router is not always ours to configure).
  - **It becomes the single point of failure.** Off-site backups stop being hygiene and start being
    the whole recovery plan — see the untested-restore item above, which this promotes from "should"
    to "must".
  - **Theft and fire.** A shop box can walk. Off-site B2 covers the data loss; disclosure is a
    separate question, and disk encryption on a headless box has the same no-keyboard-at-boot trap
    that made us refuse it on the tablet.
  - **Pick ONE source of truth.** Running prod and on-prem together is split-brain. On-prem primary
    plus off-site backup is the clean shape. *(Phase A/B · architecture · the "own it" premise)*

- **Nobody is watching prod. Felix is the monitoring.** *(2026-08-04, from the client-vs-server
  crash review)* `restart: unless-stopped` is on every service and there are real healthchecks on the
  app and Postgres, so an app crash or a host reboot self-heals. **None of that covers host death,
  disk failure, a Hetzner outage, a bad deploy or an expired cert** — and in every one of those cases
  the way we find out is a phone call from the shop.
  **Wanted:** an external check on `https://banco.wolfhold.app/health/healthz` with an SMS or push
  alert. Free tier is fine; a till does not need five-nines, it needs *someone to know*.
  ⚠️ **It must run OFF the box.** A monitor living on the same host tells you nothing at the exact
  moment it matters — the classic green-that-cannot-turn-red, same call already made about the
  Keycloak and MinIO healthchecks in `compose.yml`. Cheapest item on this list by a distance and the
  biggest return. *(Phase A · ops)*

- **The backup has never been restored, so it is a belief.** *(2026-08-04)* `backup-to-b2` and
  `restore-to-b2` exist and run. Nothing has ever come *back*. Standing rule 4 says "Fixed" is a
  claim until the output is verified, and a backup is the purest example: it looks identical whether
  it works or not, right up to the day you need it.
  **Wanted: a restore drill, written down.** Restore the latest B2 backup to a scratch container,
  then check three things a human recognises — **the product count matches prod**, **a known
  transaction is present with the right total**, and **a login actually works** (Keycloak realm data
  is the part most likely to be missed). **Record how long it took** — that number is the real
  recovery time, and today nobody knows it. *(Phase A · ops · money-correctness)*

- **A crashed tablet loses the cart, and the spare tablet cannot pick it up.** *(2026-08-04)* The
  in-progress cart lives in **`sessionStorage`** — `pos_cart`, `checkout_customer`, `pos_sale_uuid`
  (`checkout.html:761`, `scan.html:1775`). Completed sales are safe on the server and `pos_sale_uuid`
  already prevents a double-charge on retry. But `sessionStorage` is scoped to the browser tab: it
  survives a reload and the scan↔checkout hop, and **dies with a browser crash, a reboot or a flat
  battery.**
  **The bit that undercuts the two-tablet plan:** `sessionStorage` does not travel, so tablet B
  **cannot resume tablet A's cart**. The spare is a fresh start and a re-scan, not a handover — worth
  saying out loud before a cashier is told otherwise. `held_orders` is the manual park-it-safely tool
  that exists today.
  **Wanted:** the cart survives a crash — either auto-hold server-side, or move it to `localStorage`.
  ⚠️ **Not a find-and-replace:** `localStorage` is shared across tabs and never expires, so a naive
  swap trades a lost cart for a stale or bleeding one. Needs a decision, not a rename. *(shop floor ·
  Phase A)*

- **Paper-and-pen is the real last resort — and Banco has no way back from it.** *(Angel,
  2026-08-04, listing the failover stack: shop Wi-Fi → phone hotspot → two tablet SIMs on two
  different networks → paper and pen)* The connectivity side is now genuinely hard to break. The
  tail is what happens **after** the shop sells on paper for an hour: someone has to key those sales
  in, and today they land with **today's timestamp, in the current shift, under whoever is typing** —
  not when, where or by whom the money was actually taken.
  **That breaks the cash box.** The drawer holds cash the shift never recorded, so §5's tolerance
  check flags a discrepancy that is not one, and the shift report disagrees with the money in the
  box — the exact failure [`12-the-cash-box.md`](onboarding/12-the-cash-box.md) exists to prevent.
  **Wanted:** enter a sale after the fact — backdated, attributed to the right cashier and the right
  shift, and **marked as an offline sale** so the audit trail says why it arrived late. Needs a
  permission story (backdating is a money-editing power) and a decision on whether a closed shift can
  be reopened or the sale attaches some other way.
  **Note it is the same problem as offline selling.** If the till ever queues sales locally during an
  outage and syncs them later, it needs exactly this re-entry path. Solve it once.
  **⚖️ Scope it CHEAP first — Angel's read on the cost of getting it slightly wrong (2026-08-04):**
  *"It would be the wrong time, when the sale didn't happen — but it wouldn't really be that bad,
  because it doesn't ever happen."* So true backdating, shift reattribution, reopening a closed shift
  and a permission story for editing money are **not** justified by an event this rare. The cheap
  version probably is: key the sales in when the system is back and **use the cash box's existing
  named reasons and note field** to say why the drawer and the shift disagree. An explained
  discrepancy is not a discrepancy; an unexplained one costs somebody an evening. Build the cheap one,
  and only reach for the expensive one if it happens twice. *(Phase A · money-correctness · shop
  floor)*

- **The transactions PDF export stops after page one.** *(Angel, 2026-08-04)* Exported the
  transactions report both ways: **CSV came out perfect**, the **PDF produced only the first page**
  when it should have been two or three. So the data is right and the PDF renderer is truncating —
  pagination, not content. **Reproducible locally; no printer needed.** The bug is in generating the
  PDF, not in printing it, so "open the PDF and count the pages" is a complete test — Felix's
  Windows printer at the shop is a separate, later question about drivers and paper. Worth doing
  before any report is put in front of an accountant, because a report that silently drops pages is
  worse than one that fails. *(Phase A · reports)*

- **TARGET SALE PRICE — the cashier names the total, not the discount.** *(shop floor · Angel's
  idea 2026-08-03)* Felix **deliberately does not discount** — he holds the selling price and
  gives a **free treat** instead (papers for CHF 3 plus a lollipop, rather than CHF 2.95). That
  mechanism already exists and works: `line_item.is_treat`, and the Z-report prints
  *"Treats given (free) — 4 · cost CHF 0.45"*.
  But a cashier still needs a way to close the deal in front of her: *"62.99? ok just give me
  60 and it's a deal."* Today the only tool is a **percentage**, which is the wrong shape — she
  is not thinking "15% off", she is thinking "sixty francs".
  **Wanted:** type the TARGET TOTAL; Banco derives the discount and records it as one. Should
  also accept a price **above** catalogue (Angel: *"if she enters a new higher price for a
  catalog sale that would be possible too"*) — worth its own discussion, since that is a price
  override and needs a permission story.
  **Bonus: it dissolves the rounding edge case.** A target is a number a human types — 60, 55,
  12.50 — so it is payable by construction. Percentage discounts are the *only* thing producing
  unpayable totals like 62.99.


- **⚠️ 7 Blow "Pure" products carry the "Mix" description — and it contradicts itself.** e.g. `Blow vorgebauter CBD Joint Pure "Diesel"` (TAM-19238, real EAN 7640183261763) reads *"JOINTS NEXT GENERATION (without tobacco) ... a wonderfully balanced **mix between tobacco and cannabis**"* — both claims in one paragraph. The Pure copy was cloned from the Mix and only the header changed. **17 products share that sentence.** This is not cosmetic: tobacco content is a legal fact in Switzerland, and Pure vs Mix is also a CHF 9.90 vs CHF 6.90 price difference, so a customer reading the description gets the wrong product. The error is UPSTREAM (Artemis's own site) — Banco imported it faithfully — so fixing it here means either correcting the source or overriding locally, and that is a decision for Felix. Also note this now interacts with classification, which reads descriptions since 2026-07-30. *(shop floor · data quality)*


- **Retail tier prices aren't reaching the POS.** Banco fully supports quantity breaks — `products.price_tiers` is `[{min_qty, unit_price}]` with `tier_mode` per_unit/bundle, and `test_pricing_tiers.py` covers it. The gap is the DATA SOURCE: `supplier_search/tamar.py::_tiers()` scrapes Tamar's `<table class="BulkPrices">`, which is what Felix **pays** (wholesale). What the till needs is what the customer **pays** — the breaks on **artemisluzern.ch** (e.g. Gizeh Air Plus 200er `TAM-23153`: CHF 3.90 / 3.70 ab 10 / 3.50 ab 50). There is no handler for that site. **This is a consistency problem, not a feature request:** the shop's own website advertises a price the till won't honour, and a regular buying ten boxes of tubes will notice. Scope to consumables (papers, tubes, filters, tips, lighters) — the same set that already has breaks online, so the list picks itself. *(shop floor · customer-facing)*


- **Reports disagree on which timestamp defines a sale.** `/transactions` filters `created_at`, `/reports/product-sales` filters `completed_at`. For a cart opened at 23:58 and paid at 00:02 those land on different days, so the two pages can still disagree by one transaction even now the timezone is consistent. `completed_at` is probably right for revenue (that's when money moved) but it needs a decision, not a swap — and open carts have no `completed_at` at all. *(Phase A · money-correctness)*

- **Red leaf on the QR (two-colour printing).** The QL-820NWB is a genuine black/red printer and Angel bought it for that. Three things must line up and only one does today: ✅ hardware supports it · ❌ needs **DK-22251** black/red media (current DK-44205 is black-only) · ❌ the CUPS driverless path exposes `ColorModel: *Gray` only, no red. `brother_ql` does support red (`62red` label type) but is one of the three drivers that printed **zero** labels on this machine — so red via Linux means re-walking a proven dead end. **Easiest route: a Windows till**, where Brother's own driver handles two-colour natively. Worth knowing: a red leaf would NOT hurt scanning — cheap 1D laser guns can't see red ink at all, but both our guns are 2D imagers, and the leaf is a *hole* in the code either way, so error correction fills it regardless of colour. `make-leaf-mark.py --colour` already takes any colour, so the artwork side is free. *(shop floor · nice-to-have)*
- **More label sizes than Small/Medium.** Angel's idea after the leaf-QR sizing tests: the label screen has two buttons, but the scan test showed **18mm QR (variant D) reads just as cleanly as 20mm** — so a genuinely small sticker is available for small items where a 62×28mm label is overkill. Wants a few more buttons: e.g. Tiny (18mm QR, short), Small (20mm QR — current), Medium (shelf-talker, EAN-13). Pairs naturally with the labeller settings section, since the sizes should be shop-configurable rather than hardcoded in the template. *(shop floor)*
- **Label printer settings section (store settings).** Today the queue name `BancoLabel`, the roll width and the label sizes are hardcoded — in `print-label.py`, in `product_label.html`, and in the guide. On the shop ProBook the queue that actually worked was the auto-discovered *Brother QL-820NWB* one, NOT `BancoLabel`, which is exactly the assumption breaking. Wanted: a settings block for queue name, roll width, default size (small/medium), and named templates. Turns "Angel's laptop prints labels" into "any shop configures this". *(shop floor)*
- **`deploy-prod.sh` reports failure on a healthy prod deploy.** Its gate runs `postboot-check.py`, which probes `http://localhost:8000` — but in production the app sits behind Caddy and isn't published on host port 8000, so it prints `❌ NOT READY / the new code is NOT serving` while the site is perfectly fine (verified: `/health/healthz` 200, `/pos` 200, correct build stamp). A false alarm at exactly the moment someone is most anxious. Make the check use `APP_PUBLIC_HOST` over HTTPS when it's set. *(Phase A)*
- **Debounce the sale-screen product search.** `scan.html:85` fires `searchProducts()` on *every* keystroke with no debounce and no request sequencing, so a scanner burst (13 chars in milliseconds) launches ~13 overlapping searches and whichever lands last wins — including the `q=''` one, which the SQL short-circuits to "return everything" (`pos_router.py:2690`). That's why searching a full barcode in the **Search** tab showed all 24 products instead of one. Not urgent: the **Barcode** tab is the right field for a gun and works correctly. Fix is one attribute, matching the pattern already used at `scan.html:530`: `@input.debounce.300ms="searchProducts()"`. Also saves ~12 wasted API calls per typed word on a till. *(shop floor)*
- **Two search boxes side by side invite the wrong one.** On the sale screen the 🔍 Search tab (names) and 📊 Barcode tab (scanner) look alike; a barcode typed into Search silently misbehaves. Worth making the gun-shaped one the obvious default, or having Search notice it was handed 13 digits. *(UX)*
- **Put the label printer on the network.** It's a QL-820NW**B** — Ethernet/Wi-Fi on board. Not needed for Docker (containers already reach `ipp-usb` at `172.17.0.1:60000` — verified), but it removes the USB/`ipp-usb` layer entirely and lets any till on the shop LAN print. *(shop floor)*
- **Reframe the catalog workbook as THE bootstrap path.** `catalog_workbook.py` is the real "load your own catalog once" tool but guide 05 buries it under "Way 4 · ask for the import guide." Document it as the initialization step; make the import idempotent (upsert by barcode). *(Phase B)*
- Verify the firewall actually closed the raw ports (5432/8080/8000) — turn the instruction into a check. *(Phase A)*
- Assert Keycloak runs in production mode (`start`, not `start-dev`) in `compose.prod.yml`. *(Phase A)*
- Onboarding dry-run as a brand-new owner; close the gaps it exposes. *(Phase B)*
- Sharpen the AI setup coach for a non-technical owner. *(Phase B)*

## ✅ Done (most recent first)

- 2026-08-07 — **Money safety: a photo cannot set a price, and the till cannot sell a placeholder.**
  `976eb0a` `45085a3` `3a28a87` `b4d31ce` `dff36bc`. Four things, one thread. (1) The `product`
  vision domain asked the model for `"price_estimate" — a number in CHF if you can GUESS`, and
  **four screens auto-filled it**: `scan.html`→the TILL, `catalog.html`, `receiving.html`,
  `kiosk.html`. Angel photographed three wooden grinders with a `10.-` sticker in frame and marked
  it FAIL twice; the model did not even have to guess. `read_product_page` 140 lines down the same
  file had refused a price since it shipped — *"a wrong price overcharges a customer"*. Removed
  from prompt, coerce, schema and all four screens. (2) **110 active products** were priced 999.99
  / 99.00 / 0.00 and every one scannable — the RAW Mason Jar asked for CHF 999.99. Now a 400 on
  BOTH sale paths (`/sales` and `/transactions/{id}/items`; `/scan` inherits it). (3) Angel then
  showed the guard's real-world hole: Pam re-created the item on the fly in 10 s and sold **that**
  — sale saved, duplicate row, minted barcode, correct row still unpriced. So `POST
  /products/{id}/first-price` lets a cashier fill a **blank** price once; 409 if one exists, so it
  can never become a discount. Flagged `price_set_at_till` + a work note naming who typed it —
  `audit_log.changed_by` is `'system'` for every row and could not do that job. New bench gap kind
  `till_priced`. (4) 79 placeholders normalised to 999.99 — and **34 real Tamar CHF 99.00 prices
  left alone**, because 99.00 is a genuine price point there (79:31 · 89:23 · 99:34 · 119:27 ·
  129:19) and a blanket UPDATE would have destroyed them with no undo.
  33 tests, every guard confirmed failing on a revert. **Machine-green only — see START HERE.**

- 2026-08-06 — **A perfect brand match lost to six mediocre shelf-mates.** `7bfb431`. The category
  hint shipped as `ORDER BY <category>, <prefix>, score DESC` — score fourth, under a comment
  reading "⚠️ BOOST, NEVER FILTER". A photographed **Greengo** grinder returned ten generic
  grinders at 0.625 and **not one Greengo**, while the shop's six real Greengo rows sat at 1.000,
  filed under `Other`. A sort key above `score` IS a filter; `LIMIT` turns "ranked lower" into
  "does not exist". Now additive (+0.15 category, +0.10 prefix). Greengo absent → 1..6, and
  champ high / Holz Grinder / Poker Chip / Purize / Rick and Morty all keep #1.
  **Angel's verdict on the wider idea, after 35 minutes of testing: the AI lookup route does not
  work for grinders and will not work for bongs** — 4% of 203 grinders and **0% of 179 bongs**
  carry a real EAN, versus 54% of rolling papers. A grinder has no identity in the world. Filed
  42 shelf photos renamed and sorted with an `INDEX.md`, and 7 draft rows (`ITEM-0235..0241`)
  written **by eye** — no lookup, no invented barcode, no invented price, created inactive.
  Still open: `Pokerchip Grinder` (one word) drops the right row out of the top 6 at 0.450 while
  `Poker Chip Grinder` ranks it #1 at 0.611 — German compounds, not yet fixed.

- 2026-08-03 — **The cash box belongs to the SHOP, and it is human-tested.** `_shift_sales`
  carried `cashier_id == user_id`: Felix opened with 200, Pam sold 150 into the same box, and
  Felix's close expected only his own takings. Now: one box · shop-wide open guard *and* checkout
  gate (Pam could not take cash at all before) · blind count → reveal → note filed against
  yesterday · the slope · §6 baseline + guard (asks, never refuses) · X-report · `to_safe` reason
  code · force-close with `counted_verified` in its own column. 35 tests +
  `scripts/prove-cash-box.py`. **Angel's 62-minute tablet run with two browsers found SEVEN
  defects that none of that caught — every one a screen.** See the lessons in `CLAUDE.md`.
- 2026-08-03 — **Cash totals round to 5 rappen at checkout, and nothing else does.** CHF 62.99
  cannot be handed over; on real prices five of six discounted totals were unpayable. `total` is
  now what was actually charged, `rounding_adjustment` records the move, and the Banana export
  splits `Cash (at ticket price)` + `Rundungsdifferenz` only on days it fired. Cash only — cards
  settle the exact cent. Proven on prod by Angel: 12/12 checks, books left as found.

- 2026-07-30 — **Age-gate compliance fix, applied to UAT.** Four CBD products were sellable with **no 18+ check** because the classifier keyed on the literal word "CBD" and titles either omitted it or transposed it to "CDB" (Angel's own typo, copying off a packet). Now reads brand context and the **description** — a strain name says nothing about what a thing legally is. `scripts/reclass-age-gate.py` (dry-run default, tighten-only) applied 4 fixes; accessories left alone. The dry run first proposed **16** changes of which **12 were wrong** — storage tins, filters, empty cones — and caught my over-reach before a row was written. 27 tests, both directions.
- 2026-07-30 — **Cross-language duplicate detection.** `Blow Pre-built ... "V1" 1 pc. black` vs `Blow vorgebauter ... "V1" 1 Stk. schwarz` scored **0.417** — under the 0.5 guard, so no warning, so a duplicate. Folding both sides through a DE↔EN dictionary takes it to **0.857** (folded strings identical). Cost measured before shipping: ~300 ms per create.
- 2026-07-29 — **Both scanner guns fixed.** They shipped set to a US keyboard while the sessions run Swiss German, so `-` arrived as `'` and every SKU lookup would have failed. Inateck BCST-35 set via the manual's config barcodes (no Swiss option — German works, same hyphen key); Netum NS L8 via doc1.netum.net/L8/en/keyboard. Verified returning `-`. Banco also retries layout-corrected candidates on a miss, for shops running guns we didn't choose.

- 2026-07-29 — **QR shelf labels live on prod (b77), and both scanner guns fixed.** Small label went 38mm-wide-on-a-62mm-roll with an unreadable 9mm EAN-13 → **62×24mm with a 15mm QR carrying the shop's logo**, pulled from `receipt_logo_url` so it's per-shop. Verified rendering on prod with the Artemis leaf in the middle. Scan-tested first: **48 scans, zero failures**, at 12/15/20mm and with an oversized 30% logo, on both guns. Separately found and fixed the guns typing `-` as `'` (shipped set to US, sessions are Swiss German) — both now on German and returning `-`; Banco also retries layout-corrected candidates on a scan miss as a safety net for shops running guns we didn't choose. Full write-up in the guide, including the five faults that all *looked* like a broken printer and weren't.
- 2026-07-28 — **Browser printing works — the full loop is closed.** Product page → 🏷️ Label → Print → a shelf label on the roll, at any of the ~20 sizes. The blocker was `@page{ size:62mm auto }`: **invalid CSS** (the spec allows `auto` OR one/two lengths, never both), so browsers silently fell back to A4 and the QL discarded every job — no error, clean drain, green LED, nothing printed. Chrome's own *Save as PDF* + `pdfinfo` exposed it in one command after three hours of theories. Fixed in `product_label.html` **and** `product_labels_batch.html` (same bug), deployed to `banco.wolfhold.app` (b65). Second gotcha: inline print CSS rides along with a cached page — hard-refresh or the fix looks like it didn't work.
- 2026-07-28 — **First Banco shelf label printed AND scanned.** Curaprox Naturally CBD toothpaste (TAM-21796, `2000000217963` — a `2`-prefix store-internal code, fitting for a 500-tube Felix × Curaprox one-off sold only at Artemis). Printed on 62 mm tape, read back correctly by the shop's scanner. That closes the loop: rendered → printed → machine-readable. The barcodes are no longer "untested". Banco not *finding* the product from that scan turned out to be no bug at all — the 📊 Barcode tab is the right field for a gun; the 🔍 Search tab is for names.
- 2026-07-28 — **Label printer is shop-ready over the USB cable — proven unattended.** Soak test: printer left idle 14 min until `ipp-usb` went stale, then a print with **zero human intervention** — the script caught the dead session, restarted the daemon passwordlessly, label came out, LED green. That's the difference between a demo and something that can sit on a counter. Also: `cups-browsed` disabled (its phantom queue had been silently swallowing jobs all evening), DK-44205 62 mm continuous, and **barcodes** (EAN-13/Code128) now render on printed labels. Three dead ends documented so nobody re-walks them: `printer-driver-ptouch` and both `brother_ql` versions produced **zero** labels — every raw-raster path is rejected by this printer, only its own IPP service accepts jobs.
- 2026-07-28 — **Brother QL-820NWBc label printer online — human-green.** Angel read three physical labels back off the roll ("label printer online", "Espresso Beans 250g / CHF 12.50", "SECOND TEST"). No Brother software needed: Debian's `ipp-usb` + CUPS `everywhere` driver drive it at 300 dpi over USB. Created the permanent `BancoLabel` queue (the auto-created `cups-browsed` one is temporary and *vanished* mid-session), set Auto Power Off = Off on the device, wrote `scripts/print-label.py` and `onboarding/08-label-printer.md`. Media confirmed by the device itself: DK-11201, 29×90 mm. Timing: first job after wake ~25–30 s, then ~4 s.
- 2026-07-22 — **Verified the seed-gate fix on a clean throwaway** (isolated `banco-drill` project, live stack untouched): with `HX_SEED_DEMO=false`, drill DB had products=0, isotto_catalog_products=0, camper_vehicles=0 vs live (demo on) 6/10/4, while `store_settings=1` proved seeders still ran. Runtime proof of `fec8748`.
- 2026-07-22 — Fixed the `HX_SEED_DEMO` leak: gated the 5 demo-shop domains (sourcing/HR/camper/ISOTTO×2) behind the flag so demo-off boots with a real shop's own data. QA/backlog/compute kept always-on (dev scaffolding, per Angel). See [[catalog-seed-vs-bootstrap]].
- 2026-07-22 — Wrote `ROADMAP.md`; loaded the deck with the two Phase-A tasks (DR drill, harden go-live).
- 2026-07-22 — Installed the Ground Control method (CLAUDE.md, memory system, standing rules).

---

*This deck is yours to edit. When something's decided, write it here. When it's done, move it to Done with the date.*
