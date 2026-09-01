---
name: banco-is-real-production
description: banco.wolfhold.app is PRE-PROD, not the shop's future box — guard the catalogue like production, treat the ledger as a rehearsal.
type: project
---

Banco is not a toy or a pure demo: a real Swiss retail shop is in acceptance testing on it (barcode checkout, catalog/inventory, VAT-correct receipts, daily close-out, audit log), with card payments, label printing and the kiosk still to come. It is not live yet — do not describe it as running or in production. This repo (`banco-starter`) is the *same* application, packaged so others can self-host and own it.

**Why:** Mistakes here can touch a running business's data. The whole selling point is ownership + recoverability, so anything that weakens backup/restore/audit is a bigger deal than a missing feature.

**Pre-prod, not prod (stated 2026-09-01).** `banco.wolfhold.app/pos` is deliberately built to be
exactly what production will be, and is treated as production — but at go-live (proposed 1 October
2026) the shop moves to a **fresh Hetzner VPS on its own domain**, rooted to our Keycloak. The
**catalogue and its barcode bindings carry over; transactions, stock movements and the cash box
start empty**, with the float counted on the day. So: **guard the catalogue like production, treat
the ledger as a rehearsal** — a stray test row is worth fixing, not worth a panic, because it does
not cross the cutover. The cutover needs its own runbook and a rehearsal on a throwaway box; see
ROADMAP.md.

**How to apply:** Favor safe, reversible changes; verify against the live stack (`scripts/standup.sh`, `postboot-check.py`, `banco-doctor.py`) rather than assuming. Re-probe after restarts. Don't inflate demo data into "real" claims. Relates to [[who-is-angel]].
