# Archive — done, most recent first

*Moved out of `WORKLIST.md` on 2026-08-13. Nothing edited. Append new entries at the top.*

---

- 2026-08-27 — **The second archive pass.** `WORKLIST.md` 1,201 → live-items-only; 889 lines moved
  out verbatim to [`2026-08-27-archive-pass.md`](2026-08-27-archive-pass.md), two blocks to
  [`backlog.md`](backlog.md). Everything below this line is indexed there.

- 2026-08-24 — **The member card is DEPLOYED** (Angel confirmed 2026-08-27). The 08-22 section
  saying `⬜ NOT DEPLOYED, NEEDS A HUMAN` had been stale for three days while a block 160 lines
  above it said the opposite. `1f379d5` catalogue CSV export · `85154c0` kiosk blank username ·
  `128cce4` join offer as a settings field · `571c94c` deactivated members stay gone · `ed20cfa`
  clear cart. The 18+ stop was witnessed firing on a real till (UAT C3, C5).

- 2026-08-22 — **BL-9 and BL-10, the mint leak, closed** (verified in code 2026-08-27).
  `scan.html:1814` binds `pendingBarcode` instead of always minting; `catalog.html:1639`
  `openCreate()` seeds the barcode from the search box when it is 8–14 digits, and the
  *"leave it blank — a code is generated automatically"* hint that invited 4,998 unscannable rows
  is rewritten to say when blank is actually right. **BL-11 was NOT closed with them** — see the
  live worklist.

- 2026-08-22 — **`adopt-images` finished the whole catalogue.** 5,395 of 5,422 actives serve a local
  image (99.5%); MinIO 18M → 163M in ~57 min; disk unmoved. The 14 that stayed external are dead
  links on other people's servers — the finding, not the failure.

- 2026-08-22 — **The price warning + the till explains the deal.** `25 pass · 0 fail · GO` on prod,
  then 17/17 and a 10/10 retest. Found and closed two live money leaks (Tycoon Gas −1.90/can,
  Greengo Wide Rolls) and two older bugs in a pasted screenshot: `pack ✓` on a fully-charged line
  took it out of `eligible_subtotal`, and the cart quoted a discount the drawer would not give.

- 2026-08-21 — **Bundle pricing, and the FourTwenty reference finally loaded.** Mixed papers pool
  (`a9dda04` `e66acb3` `cbc158d`); `reference_products` went 0 → 11,035 rows on prod after the
  table had been empty on every machine for the project's whole life. Ralph's whole-packs rule is
  the semantics everywhere.


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
