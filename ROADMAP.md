# ROADMAP — Banco POS starter (the dev/product arc)

*This is our roadmap — where the **starter** is going, not the shop-owner's setup journey (that's [`onboarding/IMPLEMENTATION-ROADMAP.md`](onboarding/IMPLEMENTATION-ROADMAP.md)). Living draft; Angel edits freely. Day-to-day tasks live in [`WORKLIST.md`](WORKLIST.md).*

*Last reviewed: 2026-07-22*

---

## 🎯 North star

**A stranger can stand Banco up and own it outright — code, data, and runbook — without you in the loop.**

Everything below serves that one sentence. The product direction is settled; the work is making the ownership promise *demonstrably* true and *repeatable by someone who isn't you*.

## 📅 GO-LIVE: 1 OCTOBER 2026 — proposed, and it depends on nothing Felix has not already done

*Set 2026-09-01. The point is not the date. The point is that it is a DATE.*

**The rule that chose it: go-live must not depend on the lease.** Felix has to be out of the shop by
**March 2027**, has known for eighteen months, and as of tonight has **no signed lease and no decided
location**. A move is a tempting go-live moment — but a date that does not exist cannot be a
deadline, and the version where we wait for March is the version where March becomes May and the
winter went on polishing.

**So: run it from 1 October. Treat the move as the CATALOGUE COMPLETION event, not the start.**

### Why the move is still the prize — it is the shelf-count moment

A move means **every product is picked up, carried and put down again**. That is the one moment in a
decade when scanning the whole shelf costs nothing extra, because it is already in somebody's hand.
Walk the old shop with the gun in inventory mode as it is packed; walk the new shelves as it is
unpacked. The shop would finish with a catalogue of **what it actually sells**, and
`pos_stock_movements` would have its first rows ever.

⚠️ **Neither Angel nor Felix had realised this.** If the move happens without Banco in the room, it
does not come round again.

### And the job is far smaller than the database suggests

| | |
|---|---|
| rows in the catalogue | **5,447** — Tamar's dropship *range* |
| products actually on the shelf | **~1,500–2,000** (Angel's estimate, 2026-09-01) |
| of those, already carrying a real EAN | **~75%** |
| genuinely with no barcode at all | **~400–500** |

**The August measurement sized the work against a catalogue that is mostly stock the shop has never
touched.** ~450 no-barcode items is a weekend with a gun, not a fourteen-hour matching project.
**Establish the shelf count before spending another day on bulk EAN work.**

### If Felix pushes back

**1 November or 1 January are both fine.** What is not fine is no date. A date makes training,
parallel running and the testsheets into a plan; without one they are hobbies. Angel's own words:
*"as long as we had an actual date."*

### Who goes first — and it is not Felix

**Layla.** She is part-time, she was present and attentive through every test, she asked questions
and followed the screens. Rafi is the manager and has the computer background, but by Angel's read
wants to work *less*, not more. **The person who adopts a system decides whether it lives**, and
that is not the owner — it is whoever reaches for it on a Tuesday afternoon. Layla should be given
ownership, not handed a test script.

### What we run on today is PRE-PROD, not prod — and go-live is a CUTOVER, not a switch

*Stated by Angel the evening of 2026-09-01, because it was about to be missed.*

`banco.wolfhold.app/pos` is **pre-production**. It is treated as production in every way that
matters — real catalogue, real bindings, real money-shaped numbers, no careless writes — and that
is deliberate, because *it is meant to be exactly what production will be*. But it is **not** the
box the shop will run on.

**Go-live means a new machine.** On the date, Angel stands up a **fresh Hetzner VPS, exclusively
for the shop**, on the shop's own domain — `artemisluzern.ch/pos` or whatever Felix picks — rooted
to our Keycloak. Then a clean-slate build:

| carried over | started empty |
|---|---|
| the **catalogue**, with every barcode binding earned since July | **transactions** — not one row |
| products, prices, age classes, pack tiers | the **cash box**, opened on the go-live date with the real counted float |
| users and roles | stock movements, day-closes, the audit log |

**Why this matters to every decision before 1 October:** the pre-prod box is not something to be
protected forever — it is something to be *learned from*. Test rows, a wrong price, a duplicate:
annoying, worth fixing, **not fatal**, because none of it crosses the cutover except the catalogue.
The catalogue is the one thing that does. **Guard the catalogue like production; treat the ledger
as a rehearsal.**

⚠️ **And the cutover itself is a piece of work nobody has scoped yet** — a catalogue export from
pre-prod, a clean import on the new box, DNS, certs, the cash box opening balance, and a rollback if
it does not come up. It is not a `deploy-prod.sh` run. It needs its own runbook and its own
rehearsal, on a throwaway box, *before* the date. That is a WORKLIST item, not a morning.

## 🧭 What Banco is actually for — the catalogue is the business

*Added 2026-09-01. Mosey of fourtwenty.ch, in Angel's recollection: **"the whole business is the
bloody catalogue."** He is right, and it is the clearest statement of what this project sells.*

**The north star above is about owning the SOFTWARE. This is about owning the DATA, and it is the
half that actually decides whether a shop is free.** Look at what the reference shop owns today:

| what it sells | who owns the identity data | what it costs |
|---|---|---|
| the Tamar range | **Tamar** — their platform, their skin, EANs withheld | CHF ~25k up front + **10–15% of every sale** through it |
| the FourTwenty range | Mosey — but he **publishes a feed with EANs** | supply relationship |
| 12–15 other suppliers | nobody, effectively | — |
| items with no barcode at all | nobody | — |

**The shop does not have a catalogue. It has four fragments, three of which belong to other people.**
That is not a till problem, and it is why no product on the market fixes it: **Orange, Shopify and
Lightspeed all BEGIN by assuming you already own your product data.** They sell a till for a
catalogue you are presumed to have.

**So the pitch is not "a nicer till". It is: at the end of this, the list is yours — whoever you buy
from next year.** Everything hard about 2026 (the 91% minted-barcode measurement, the EAN request
email, the image matcher, the merge tooling, never inventing an identifier) is one piece of work:
**moving the catalogue from somebody else's asset to the shop's own.**

It also explains the commercial shape without anyone behaving badly. A supplier who hands over the
EAN list is handing over the key that lets the shop scan **anyone's** goods. Withholding it is not
spite; it is the same logic as a channel commission. *Expect the resistance and frame the ask as
operational — "when you ship me goods, what do you scan?" — not as a data request.*
See [`onboarding/supplier-ean-request.md`](onboarding/supplier-ean-request.md).

### Why the vertical is real

A general POS cannot serve this trade, and the reasons are regulatory and structural rather than
cosmetic:

1. **18+ evidence as an append-only record** (`trg_ace_append_only`) — a Swiss compliance artefact,
   not a checkbox.
2. **Products with no barcode**, and the discipline of never minting a fake one (LESSON #9).
3. **Supplier feeds from wholesalers who will not give you identity data** — the whole of August.
4. **CBD / tobacco / nicotine tax classes driving the age gate**, derived rather than stored.

⚠️ **Unverified:** that no head-shop-specific POS exists. Worth an hour of checking before the claim
is made to anyone. *A remembered verdict is a hypothesis with a timestamp on it* (LESSON #3).

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
