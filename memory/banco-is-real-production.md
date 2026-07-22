---
name: banco-is-real-production
description: A live Swiss shop runs on Banco today — treat data and changes as production.
type: project
---

Banco is not a toy or a pure demo: a real Swiss head-shop runs on it today (barcode checkout, catalog/inventory, VAT-correct receipts, daily close-out, audit log). This repo (`banco-starter`) is the *same* application, packaged so others can self-host and own it.

**Why:** Mistakes here can touch a running business's data. The whole selling point is ownership + recoverability, so anything that weakens backup/restore/audit is a bigger deal than a missing feature.

**How to apply:** Favor safe, reversible changes; verify against the live stack (`scripts/standup.sh`, `postboot-check.py`, `banco-doctor.py`) rather than assuming. Re-probe after restarts. Don't inflate demo data into "real" claims. Relates to [[who-is-angel]].
