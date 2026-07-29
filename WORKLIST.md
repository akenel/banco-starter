# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

*Last updated: 2026-07-28 (22:35 — label printer day)*

---

## 🎯 On deck (next actionable, in order)

1. **⛔ Scanner guns type `-` as `'` — keyboard layout mismatch.** *(shop floor · do before scanning any SKU)*
   - Found 2026-07-29 in the logo-QR scan test: the page shows `QR-LOGO-15`, the gun typed **`QR'LOGO'15`**. Confirmed across 48 scans on both guns — every hyphen became an apostrophe.
   - **Why it hasn't hurt yet:** EAN-13 is pure digits, and digits map identically across layouts, so till scanning works today. **Every SKU has a hyphen** (`TAM-21796`, `TAM-5381`) — the moment a Code128 SKU label is scanned, the gun types `TAM'21796` and the product is not found.
   - Fix is in the gun, not Banco: its manual has configuration barcodes for keyboard layout. Set **Swiss German** (or set the gun to US *and* match the machine's layout). Do **both guns**, then re-run `onboarding/testsheets/SCANNER-GUN-TEST.html` and confirm hyphens survive.
   - Worth a defensive fix in Banco too: normalise likely layout substitutions on the scan path before lookup, so a mis-set gun degrades instead of failing. See `_clean_barcode` (pos_router.py:272), which already exists for scanner junk.

2. **Keep `ipp-usb` fresh — the last thing between the labeler and daily use.** *(shop floor · small, do it first)*
   - Everything prints: CLI, barcodes, scanning, and the browser UI at any size. But `ipp-usb`'s USB session dies after **6–13 minutes idle** and then jobs queue silently and nothing comes out. `print-label.py` heals itself; **Chrome cannot**, so the browser path dies every quarter hour.
   - First move: a **systemd timer** (say every 5 min) that restarts `ipp-usb` *only when it has stopped relaying* — reuse the check in `print-label.py` (`ipp_usb_alive()`, an `ipptool` get-printer-attributes that returns `0 bytes` when stale). The passwordless sudoers rule is already installed at `/etc/sudoers.d/banco-label-printer`.
   - Manual recovery meanwhile: `sudo systemctl restart ipp-usb` — takes ~5 s, then queued jobs flush immediately.
   - Done = leave it an hour, print from the browser, a label comes out with nobody touching anything.
   - Then the freebie: `google-chrome --kiosk-printing` to drop the print dialog. `BancoLabel` is already the only queue and the system default, so nothing else is needed.

3. **Harden go-live — DNS preflight + default-secret gate.** *(Roadmap Phase A)*
   - First move: add a preflight to `scripts/deploy-prod.sh` (or `go-live.py`) that resolves `APP_PUBLIC_HOST` + `KC_PUBLIC_HOST` and checks they point at the server IP **before** cert issuance, and refuses/loudly-warns if a starter-default secret is still in place (reuse `banco-doctor.py`'s default detection).
   - Done = a misconfigured DNS record or an unchanged default secret is caught *before* the box is exposed, not after.

4. **DR restore (Move B) — ⛔ BLOCKED on B2 read creds.** *(Roadmap Phase A · the ownership proof)*
   - Move A (seed gate) is ✅ **proven at runtime** (2026-07-22) — see Done below. Move B (the real restore) needs a read-only B2 key + bucket + passphrase (Angel deferred this session).
   - When creds are ready: infra up (`docker compose up -d postgres keycloak minio`) → `restore-from-b2.sh` with creds as **env vars** (never written to `.env`) → row-check prints a real product count → app up → `standup.sh`. Green-ticks the checklist's "practiced a restore" box. See [[catalog-seed-vs-bootstrap]].

5. **Feed labels from the catalog.** *(shop floor)*
   - Barcode + name + price by product ID, so a shelf label is one command and a re-price is a re-print. The pieces all exist now — `print-label.py -c <barcode> <name> <price>` and the web Label button.

## 🔭 Backlog (not yet scheduled)

- **Label printer settings section (store settings).** Today the queue name `BancoLabel`, the roll width and the label sizes are hardcoded — in `print-label.py`, in `product_label.html`, and in the guide. On the shop ProBook the queue that actually worked was the auto-discovered *Brother QL-820NWB* one, NOT `BancoLabel`, which is exactly the assumption breaking. Wanted: a settings block for queue name, roll width, default size (small/medium), and named templates. Turns "Angel's laptop prints labels" into "any shop configures this". *(shop floor)*
- **"Small" label prints 38mm wide on a 62mm roll** — throws away a third of the width AND squeezes the EAN-13 into ~34mm at 9mm bar height, which is why it won't scan with either gun. Small should mean *shorter*, not *narrower*: `62mm 32mm` with ~14mm bar height. One line in `product_label.html` + the `svg.code` height. Possibly replace with a QR once the gun test confirms 2D support and the practical size floor — see `onboarding/testsheets/SCANNER-GUN-TEST.html`. *(shop floor)*
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
