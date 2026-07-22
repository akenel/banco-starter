# ROADMAP — Banco POS starter (the dev/product arc)

*This is our roadmap — where the **starter** is going, not the shop-owner's setup journey (that's [`onboarding/IMPLEMENTATION-ROADMAP.md`](onboarding/IMPLEMENTATION-ROADMAP.md)). Living draft; Angel edits freely. Day-to-day tasks live in [`WORKLIST.md`](WORKLIST.md).*

*Last reviewed: 2026-07-22*

---

## 🎯 North star

**A stranger can stand Banco up and own it outright — code, data, and runbook — without you in the loop.**

Everything below serves that one sentence. The product direction is settled; the work is making the ownership promise *demonstrably* true and *repeatable by someone who isn't you*.

## 📍 Honest state (2026-07-22)

**Solid.** A real Swiss shop runs on it today. The go-live pipeline is genuinely well-built: `deploy-prod.sh` gates on a fresh backup, a build-stamp match, and a live-HTTPS check; `go-live.py` validates hostnames, backs up `.env`, generates Caddy config, and prints the exact DNS/firewall steps; `restore-from-b2.sh` is careful (safe `.env` parsing, env-overrides-`.env`, newest-by-timestamp, row-count proof). The onboarding kit (roadmap + checklist + 7 guides + testsheet + AI coach) is thorough. The commit log is a steady stream of real hardening.

**Unproven / thin — this is the actual work:**
- The **ownership promise rests on a restore that hasn't been drilled from zero on a clean box.** A backup you've never restored isn't a backup.
- **Go-live has a few sharp edges left:** no DNS preflight before cert issuance (the #1 first-deploy failure); no hard gate that starter-default secrets were changed before a box goes public; firewall is instructions, not a verified state.
- The **onboarding kit's proof is a stranger completing it** — nobody outside your head has yet.

**Verdict: no pivot.** The thing is coherent and real. The risk isn't direction — it's that a deep solo-built starter's value only lands when someone else succeeds with it, and that loop is under-tested. Ahead is *hardening + proof + distribution*, not features.

---

## Phase A — Prove the promise *(now)*

Make "own your code, data, and runbook" demonstrably true, not asserted.

- **DR drill:** restore a real B2 backup onto a clean box → app serves → data returns. Time it, log every manual snag, fix each.
- **Harden go-live's remaining gaps:** DNS preflight (resolve app/kc hosts → server IP before cert issuance); refuse/loudly-warn on unchanged starter-default secrets; verify the firewall actually closed the raw ports.

**Exit:** a clean box goes zero → HTTPS-serving → restored real data, timed, with every snag found and fixed.

## Phase B — A stranger succeeds unaided

The onboarding kit is thorough; its proof is someone who isn't you finishing it.

- Dry-run the whole onboarding kit as a brand-new owner would; close every doc/tool gap it exposes.
- Sharpen the AI setup coach (`onboarding/ai-coach/`) so it can unblock a non-technical owner.

**Exit:** one external person self-hosts to a real sale without you touching their box.

## Phase C — Distribution & durability *(only after A+B)*

- Discoverability / "use this template" on-ramp.
- Versioning + a safe **upgrade path** for shops already live (migrations without data loss).
- A contribution on-ramp for forks.

**Exit:** a second shop runs on a fork you didn't hand-hold.

---

### The one rule for this roadmap
**Prove before you polish.** A restored backup and a stranger's successful install are worth more than any new feature. Phase A and B are the whole game; C is the reward.
