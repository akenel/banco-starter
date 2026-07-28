# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

*Last updated: 2026-07-28*

---

## 🎯 On deck (next actionable, in order)

1. **Harden go-live — DNS preflight + default-secret gate.** *(Roadmap Phase A)*
   - First move: add a preflight to `scripts/deploy-prod.sh` (or `go-live.py`) that resolves `APP_PUBLIC_HOST` + `KC_PUBLIC_HOST` and checks they point at the server IP **before** cert issuance, and refuses/loudly-warns if a starter-default secret is still in place (reuse `banco-doctor.py`'s default detection).
   - Done = a misconfigured DNS record or an unchanged default secret is caught *before* the box is exposed, not after.

2. **DR restore (Move B) — ⛔ BLOCKED on B2 read creds.** *(Roadmap Phase A · the ownership proof)*
   - Move A (seed gate) is ✅ **proven at runtime** (2026-07-22) — see Done below. Move B (the real restore) needs a read-only B2 key + bucket + passphrase (Angel deferred this session).
   - When creds are ready: infra up (`docker compose up -d postgres keycloak minio`) → `restore-from-b2.sh` with creds as **env vars** (never written to `.env`) → row-check prints a real product count → app up → `standup.sh`. Green-ticks the checklist's "practiced a restore" box. See [[catalog-seed-vs-bootstrap]].

3. **Label printer — add barcodes.** *(shop floor)*
   - The printer is online and proven (see Done); Auto Power Off is now **Off**. What's missing is the thing that makes a label a *shelf* label: **Code128/EAN barcodes** in `scripts/print-label.py`. Text-only isn't enough — a price label the scanner can't read is decoration.
   - Feed it from the catalog (barcode + name + price) so a shelf label is one command per product, and a re-price is a re-print.
   - Done = a printed label that Banco's own scanner reads back to the right product.

## 🔭 Backlog (not yet scheduled)

- **Put the label printer on the network.** It's a QL-820NW**B** — Ethernet/Wi-Fi on board. Containers can't reach `localhost:60000` on the host, so the app can't print from Docker today. Point the queue at the printer's IP and that's solved for every container. *(shop floor)*
- **Reframe the catalog workbook as THE bootstrap path.** `catalog_workbook.py` is the real "load your own catalog once" tool but guide 05 buries it under "Way 4 · ask for the import guide." Document it as the initialization step; make the import idempotent (upsert by barcode). *(Phase B)*
- Verify the firewall actually closed the raw ports (5432/8080/8000) — turn the instruction into a check. *(Phase A)*
- Assert Keycloak runs in production mode (`start`, not `start-dev`) in `compose.prod.yml`. *(Phase A)*
- Onboarding dry-run as a brand-new owner; close the gaps it exposes. *(Phase B)*
- Sharpen the AI setup coach for a non-technical owner. *(Phase B)*

## ✅ Done (most recent first)

- 2026-07-28 — **Brother QL-820NWBc label printer online — human-green.** Angel read three physical labels back off the roll ("label printer online", "Espresso Beans 250g / CHF 12.50", "SECOND TEST"). No Brother software needed: Debian's `ipp-usb` + CUPS `everywhere` driver drive it at 300 dpi over USB. Created the permanent `BancoLabel` queue (the auto-created `cups-browsed` one is temporary and *vanished* mid-session), set Auto Power Off = Off on the device, wrote `scripts/print-label.py` and `onboarding/08-label-printer.md`. Media confirmed by the device itself: DK-11201, 29×90 mm. Timing: first job after wake ~25–30 s, then ~4 s.
- 2026-07-22 — **Verified the seed-gate fix on a clean throwaway** (isolated `banco-drill` project, live stack untouched): with `HX_SEED_DEMO=false`, drill DB had products=0, isotto_catalog_products=0, camper_vehicles=0 vs live (demo on) 6/10/4, while `store_settings=1` proved seeders still ran. Runtime proof of `fec8748`.
- 2026-07-22 — Fixed the `HX_SEED_DEMO` leak: gated the 5 demo-shop domains (sourcing/HR/camper/ISOTTO×2) behind the flag so demo-off boots with a real shop's own data. QA/backlog/compute kept always-on (dev scaffolding, per Angel). See [[catalog-seed-vs-bootstrap]].
- 2026-07-22 — Wrote `ROADMAP.md`; loaded the deck with the two Phase-A tasks (DR drill, harden go-live).
- 2026-07-22 — Installed the Ground Control method (CLAUDE.md, memory system, standing rules).

---

*This deck is yours to edit. When something's decided, write it here. When it's done, move it to Done with the date.*
