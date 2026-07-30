# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

*Last updated: 2026-07-31 (after the Artemis shop day)*

---

## 🎯 On deck (next actionable, in order)

1. **⛔ SHELF SCAN → BATCH ENRICH.** *(shop floor · Angel's idea 2026-07-30, and it replaces item 1 below)*

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

   **Done =** 20 minutes of shelf scanning produces a work list, and an evening at a desk turns it
   into a catalogue where every product scans.

2. **SCAN MISS MUST SEARCH THE CATALOGUE.** *(shop floor · the one thing that matters)*

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

3. **Retire the 2026-07-30 duplicate rows.** *(small, straight after item 1)*
   - ~40 products were hand-created that already existed (e.g. `Blow Pre-built CBD Joint Pure "V1" 1 pc. black` = `Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz`, TAM-20350).
   - The **imported** row has the good data; the **hand-made** row has the real EAN. So move the barcode onto the imported row and drop the twin. Angel: *"you just delete them"*.
   - Dry-run-first script, same shape as `scripts/reclass-age-gate.py`.

4. **Debounce the sale-screen product search.** *(shop floor · small, contributes to item 1)*
   - `scan.html:85` fires `searchProducts()` per keystroke with no debounce and no request sequencing, so the last response wins — including an empty query that returns everything. This is how a search looks like it "found nothing useful". One attribute: `@input.debounce.300ms`, matching the pattern already at `scan.html:530`.

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
