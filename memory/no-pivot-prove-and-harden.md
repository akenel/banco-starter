---
name: no-pivot-prove-and-harden
description: Strategic call (2026-07-22) — no pivot; phase is prove + harden, not rebuild or new features.
type: project
---

Angel asked "are we in good shape or should we pivot?" (2026-07-22). Assessment after reading the go-live pipeline, restore script, and onboarding kit: **no pivot.**

The product is coherent and real (a live Swiss shop runs on it) and the engineering is mature — `deploy-prod.sh` gates on backup + build-stamp + live-HTTPS; `go-live.py` and `restore-from-b2.sh` are carefully built. The risk is **not** direction.

**North star:** a stranger can stand Banco up and own it — code, data, runbook — without Angel in the loop.

**The real risk:** a deep solo-built starter only pays off when *someone who isn't the author* succeeds with it, and that loop is under-tested — specifically the B2 restore has never been drilled from zero, and no external person has completed the onboarding kit.

**How to apply:** Favor proof and hardening over features. Phase A = prove the ownership promise (DR drill + close go-live's last gaps). Phase B = a stranger self-hosts unaided. Distribution comes only after. Full arc in `ROADMAP.md`. Relates to [[banco-is-real-production]], [[who-is-angel]].
