# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

*Last updated: 2026-07-22*

---

## 🎯 On deck (next actionable, in order)

1. **DR drill — restore a B2 backup on a clean box.** *(Roadmap Phase A · the ownership proof)*
   - First move: on a clean stack (fresh box, or local with DB volume wiped), bring up infra only — `docker compose up -d postgres keycloak minio` — then run `./scripts/restore-from-b2.sh` with a **read-only** B2 key. Confirm the row-check prints a real product count, then `docker compose up -d app && ./scripts/standup.sh`.
   - Done = data came back from zero, timed, with every manual snag logged and fixed. This green-ticks the checklist's "practiced a restore" box.

2. **Harden go-live — DNS preflight + default-secret gate.** *(Roadmap Phase A)*
   - First move: add a preflight to `scripts/deploy-prod.sh` (or `go-live.py`) that resolves `APP_PUBLIC_HOST` + `KC_PUBLIC_HOST` and checks they point at the server IP **before** cert issuance, and refuses/loudly-warns if a starter-default secret is still in place (reuse `banco-doctor.py`'s default detection).
   - Done = a misconfigured DNS record or an unchanged default secret is caught *before* the box is exposed, not after.

## 🔭 Backlog (not yet scheduled)

- Verify the firewall actually closed the raw ports (5432/8080/8000) — turn the instruction into a check. *(Phase A)*
- Assert Keycloak runs in production mode (`start`, not `start-dev`) in `compose.prod.yml`. *(Phase A)*
- Onboarding dry-run as a brand-new owner; close the gaps it exposes. *(Phase B)*
- Sharpen the AI setup coach for a non-technical owner. *(Phase B)*

## ✅ Done (most recent first)

- 2026-07-22 — Wrote `ROADMAP.md`; loaded the deck with the two Phase-A tasks (DR drill, harden go-live).
- 2026-07-22 — Installed the Ground Control method (CLAUDE.md, memory system, standing rules).

---

*This deck is yours to edit. When something's decided, write it here. When it's done, move it to Done with the date.*
