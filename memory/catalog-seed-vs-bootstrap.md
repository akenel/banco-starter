---
name: catalog-seed-vs-bootstrap
description: Design principle — demo seed (throwaway) and real-catalog bootstrap (load-once) are different things and must not entangle.
type: project
---

Angel's insight (2026-07-22): a real shop's DB should be **their** data. The starter's demo catalog is only a throwaway to *try* Banco; the real need is a **one-time bootstrap** that pre-loads the owner's actual catalog, after which it's their living POS data (edited in the POS, backed up, restored).

**Two concepts that are currently entangled:**
1. **Demo seed** — fictional showcase data (Artemis products, ISOTTO Sport merch, camper/tour, HR, sourcing, …). Purpose: let a tourist click around. Should be 100% behind one flag, all-or-nothing, cleanly removable.
2. **Real-catalog bootstrap** — the owner's products, loaded **once** to initialize, then living data. The tool already exists: `src/services/catalog_workbook.py` (BL-131 "Migration Workbench" — export .xlsx → walk the shelf filling barcode/price/variant → import back → AI enrichment fills image/description/specs). It just isn't *framed* as "the initialization path."

**Concrete gap found (main.py:104–243):** `HX_SEED_DEMO=false` only gates `seed_artemis_products` (145) and `seed_customers` (164). Nine other seeders — sourcing, HR, camper, ISOTTO + ISOTTO catalog, QA checklist, backlog, compute grants, and store_settings — run regardless. So the guide's promise ("HX_SEED_DEMO=false → boots with an EMPTY catalogue") is only half-true; a real shop still boots polluted with other demo domains.

**Principle to hold:** demo is a costume you take off cleanly; the bootstrap is how the shop puts on its own clothes. Keep them separate. Refinement on "read once": make the bootstrap **idempotent/re-runnable** (upsert by barcode), not literally fire-once — owners will re-run to add the long tail and fix mistakes; the seeders already use check-before-insert, which is the right instinct.

**Open decision (for Angel):** which of the nine always-on seeders are "demo" (die with the flag) vs genuine app-core (store_settings, maybe QA/backlog/compute). Relates to [[banco-is-real-production]], [[no-pivot-prove-and-harden]].
