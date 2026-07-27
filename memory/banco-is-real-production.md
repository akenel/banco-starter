---
name: banco-is-real-production
description: A real Swiss shop is in acceptance testing on Banco — treat its data as production.
type: project
---

Banco is not a toy or a pure demo: a real Swiss retail shop is in acceptance testing on it (barcode checkout, catalog/inventory, VAT-correct receipts, daily close-out, audit log), with card payments, label printing and the kiosk still to come. It is not live yet — do not describe it as running or in production. This repo (`banco-starter`) is the *same* application, packaged so others can self-host and own it.

**Why:** Mistakes here can touch a running business's data. The whole selling point is ownership + recoverability, so anything that weakens backup/restore/audit is a bigger deal than a missing feature.

**How to apply:** Favor safe, reversible changes; verify against the live stack (`scripts/standup.sh`, `postboot-check.py`, `banco-doctor.py`) rather than assuming. Re-probe after restarts. Don't inflate demo data into "real" claims. Relates to [[who-is-angel]].
