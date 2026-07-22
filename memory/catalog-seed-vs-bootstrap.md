---
name: catalog-seed-vs-bootstrap
description: Design principle — demo seed (throwaway) and real-catalog bootstrap (load-once) are different things and must not entangle.
type: project
---

Angel's insight (2026-07-22): a real shop's DB should be **their** data. The starter's demo catalog is only a throwaway to *try* Banco; the real need is a **one-time bootstrap** that pre-loads the owner's actual catalog, after which it's their living POS data (edited in the POS, backed up, restored).

**Two concepts that are currently entangled:**
1. **Demo seed** — fictional showcase data (Artemis products, ISOTTO Sport merch, camper/tour, HR, sourcing, …). Purpose: let a tourist click around. Should be 100% behind one flag, all-or-nothing, cleanly removable.
2. **Real-catalog bootstrap** — the owner's products, loaded **once** to initialize, then living data. The tool already exists: `src/services/catalog_workbook.py` (BL-131 "Migration Workbench" — export .xlsx → walk the shelf filling barcode/price/variant → import back → AI enrichment fills image/description/specs). It just isn't *framed* as "the initialization path."

**Concrete gap found (main.py:104–243) — FIXED 2026-07-22:** `HX_SEED_DEMO=false` used to gate only `seed_artemis_products` and `seed_customers`; the 5 fictional-business seeders leaked through. Now the demo-shop domains (sourcing, HR, camper, ISOTTO + ISOTTO catalog) are gated behind the flag too, so demo-off boots as the shop's own data. **Resolved split (Angel's call):** demo = products/customers/sourcing/HR/camper/ISOTTO×2; always-on = staff + login users + store_settings (needed so Pam can log in and VAT is right) and QA/backlog/compute (dev scaffolding). **Runtime-verified 2026-07-22** on an isolated throwaway (`banco-drill` project, live stack untouched): with `HX_SEED_DEMO=false` the drill DB had products=0, isotto_catalog_products=0, camper_vehicles=0 — vs the live stack (demo on) at 6/10/4 — while `store_settings=1` confirmed seeders still ran. The gate works.

**Principle to hold:** demo is a costume you take off cleanly; the bootstrap is how the shop puts on its own clothes. Keep them separate. Refinement on "read once": make the bootstrap **idempotent/re-runnable** (upsert by barcode), not literally fire-once — owners will re-run to add the long tail and fix mistakes; the seeders already use check-before-insert, which is the right instinct.

Relates to [[banco-is-real-production]], [[no-pivot-prove-and-harden]].
