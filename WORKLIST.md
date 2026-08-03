# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

*Last updated: 2026-07-31 (after the Artemis shop day)*

---

## 🎯 On deck (next actionable, in order)

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

## 🔭 Backlog (not yet scheduled)

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
