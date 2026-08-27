# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short — and it has now been cut back twice.** 1,734 lines on
> 2026-08-13, and **1,201 again on 2026-08-27** despite a warning sitting inside it for three days.
> Both times the split was verified line-for-line and **nothing was deleted**; the second pass is in
> [`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md).
> **The rule is ~280 lines, not 150** — the 150 was set before item ⓪ existed, and a measurement
> that changes what the shop does next earns its space. The trigger is what matters, not the number:
> **when a thread closes, it moves the same day.** Growing back to four figures is what happens when
> "I'll archive it later" is the plan. When an item is finished it goes to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread grows
> a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-08-27, evening — second archive pass, done with Angel item by item.*

---

## ▶️ START HERE — the state at 18:30 on Thu 2026-08-27

**A whole day at the counter with Layla serving.** Nine deploys, every one proved on the live shop.
Prod is on build `b469`.

| | |
|---|---|
| `3d5f878` | the till resolves a **SKU**, so goods with no manufacturer EAN get a label that scans |
| `f3a4084` | the gun sends SHIFT late (`sKU-`). Case-tolerant lookup; the sticker WRAPS instead of clipping |
| `b273e71` | the page title IS the PDF filename — both label sizes shared one, so saving one destroyed the other |
| `c981a25` | a correct refusal rendered as an 8-second toast nobody could read. Now inside the modal, above the button |
| `a48a78f` | **UPC-A vs EAN-13**: one leading zero hid **2,632 supplier rows**, 24% of the FourTwenty feed |
| `a48a78f` | fourtwenty.ch publishes its description as ONE invisible character, which switched off the whole body read |
| `4968587` | **search the supplier catalogue from the Catalogue screen** — it was wired into Receiving and Scan, not there |

**Also today, and not code:** the cash box was reconciled on a real count (CHF 1216.90, sixteen days
open), all four Crank pipes ring, three JUICY wraps created, and the day's last bong went in with a
photo, a description, an article number and a label that scans.

### Open, in order

**⓪ THE 3% IS NOT A MATCHING PROBLEM — 91% OF THE CATALOGUE IS KEYED ON INVENTED CODES.**
→ the full measurement, and the reasoning that killed bulk name-matching:
[`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md)

**4,971 of 5,447 active products (91%) carry a minted `200…` barcode** — GS1's restricted-circulation
range, valid inside one building, by definition never on a packet. **Only 3.5% of shop barcodes exist
in the FourTwenty feed.** Angel's *"happens by luck 3% of the time"* was not a mood; it is the scan
hit-rate, and it is a property of the **seed data**, not of the idea. He is not failing at intake —
he is **re-creating products he already owns**, because the packet's code can never match the code
we filed it under.

**The fix is a list, not an algorithm.** All 4,971 minted rows carry `supplier_sku` = Tamar's own
article number (100% populated, `TAM-` prefixed), and the minted barcode literally encodes it
(`2000000` + article no. + check digit). **Tamar's EAN list joins on one column, exactly** — no fuzzy
match, no review queue, no wrong-bind risk. Name-matching cannot substitute: measured at similarity
0.80, two different adapter sizes took the same EAN. **A wrong barcode looks exactly like a right
one (LESSON #9).**

⚠️ **And the job is much smaller than 5,447.** The catalogue is **Tamar's dropship range, not
Artemis's shelf** — `pos_stock_movements` holds **0 rows**, so nothing in Banco has ever recorded
what is physically in that store. Only what sits on the shelf has to scan. **Before any bulk EAN
work: establish what is actually in the room.**

▶️ **The next action is an email, not a sprint.** Ask Rafi/Felix for a **sample** first — "the EAN
for these 20 article numbers" needs no data-sharing decision and the reply measures the coverage
exactly. Better diagnostic question than *"do you have EANs?"*: **"when you receive goods from the
manufacturers, what do you scan?"** German text, export SQL and how to apply the list:
[`onboarding/supplier-ean-request.md`](onboarding/supplier-ean-request.md). The 4,971-row CSV is
generated and with Angel.

**The real UI bug behind it (small, still worth fixing).** On a PURE barcode miss `lazyLinkQuery` is
empty, so `openLazy()` skips `searchExisting()` — **our own catalogue is never searched** — and
`confirmAdopt()` then creates a new product. When the feed correctly identifies a packet we already
own under a minted code, **the till manufactures a duplicate.** Fix: take the winning reference/web
title, search our catalogue with it, offer "you already have this → bind" ABOVE "Add to shop". Never
auto-bind (LESSON #9). *(The bind plumbing itself is correct — `scan.html:2124 linkToExisting()`
promotes a real EAN to primary and demotes the minted code to an alias.)*


**① The gate audit — 42 blunts and wraps sell with NO ID check.**
[`onboarding/testsheets/2026-08-27-gate-audit.html`](onboarding/testsheets/2026-08-27-gate-audit.html)
· 35 near-identical products on the same shelf ARE gated. Angel checked the packet: it carries a
cigarette-style tobacco health warning, so the FourTwenty feed's `standard` is wrong. **Section C is
Felix's decision, not a fix to apply** — tick which should gate, then it is one update. *Angel has
fixed the wrap classes by hand; the other ~40 are still open.*

**② Layla's product-grouping idea is BUILT and unreachable.** `POST /products/{id}/clone` — its own
docstring describes her exact case. On no screen. She reinvented it from the counter without seeing
the code, which is the strongest argument for it. **This is the next feature.**

**③ The scanner gun is PARKED, deliberately.** ~8 reads in 14 corrupt a digit — but only ever the
digit immediately before an UPPERCASE letter, where the shift asserts early. Pure-numeric codes never
assert shift, so EAN-13/UPC-A are structurally immune, and Banco's SKUs put their letters at the
front. Safe for everything the shop scans. The NSL8 has **no inter-character delay setting** (all 28
pages read; manual now in `onboarding/testsheets/Scanners/`). Next test if it is ever picked up:
scan into a plain text editor, not Firefox — intermittent modifier corruption is as often the host's
input stack as the gun's.

**④ Label → PDF paginates wrong.** A sliver spills onto a second page and the first is cut.
`@page{62mm 28mm}` / `{62mm 55mm}` versus what Chrome lays out. Angel: *"we deal with that pdf later"*.

**⑤ The MEDIUM label's CODE128 is still unproven by a gun.** 17 characters in 62mm makes fine bars.
If it will not read, the answer is a SHORTER SKU, not a bigger label.

**⑥ The vocabulary gap has no fix yet.** Angel searched *rainbow*, the feed says *rasta*. The new
panel's empty state names the trade words (rasta, Kopf, Schliff, Kawumm) but nothing translates them.
A synonym table is the obvious next step and has NOT been thought through.

**⑦ Adopting from the supplier copies its 18+ answer with no safety net**, while the till's quick-add
applies one — same operation, two answers. And the classifier does not know the words "blunt" or
"wrap", so the safety net would not have caught the wraps anyway. Both real, both unfixed.

### Not bugs — decided today

- **58 products at CHF 999.99 are DELIBERATE.** Angel: *"the number is so high it can't be missed"*.
  A not-priced-yet marker with a human as the check. `/pos/cleanup?mode=bench&gap=price` lists them.
- **"A couple at a time" is the right shape for intake**, not a limitation to engineer around.
  5,430 products against 50 transactions in the box's whole life.


### Also open — smaller, each one verified in code on 2026-08-27

- **⑧ BL-11 — the stale snap panel, and it is LESSON #13 again.** `snapPreview` is cleared in
  **exactly one place**, `snapClose()` (`catalog.html:2088`). `openCreate()` resets `gallery`,
  `pendingPhotos`, `pendingImageUrl` and `_aiTail` — and **not** `snapPreview`, `snapName` or
  `pageUrl`. So the create panel can still show the *previous* product's photo under the words
  "read from this photo". A clear that clears four keys of seven. *(BL-9 and BL-10 ARE fixed —
  verified in the code, now in `done.md`.)* Needs a browser to confirm the screen effect (LESSON #7).
- **⑨ BL-14 — the cursor is not where the work is.** Now specified, by Angel: *"annoying when you
  have to put the cursor at the logical spot when the screen is refreshed."* After a refresh, focus
  lands nowhere useful and the cashier reaches for the mouse mid-sale. Find every screen that
  re-renders under Alpine and give it one deliberate focus target.
- **⑩ Run `GET /catalog/price-check` over the whole catalogue.** This replaces an 08-21 list of
  individual papers (OCB Premium Slim, OCB Virgin Slim, 8 King Size, 6 Rips, Old School) that Angel
  no longer recognised six days on. **Not dropped — those are money rows**, and a `per_unit` tick is
  exactly the CHF 6.00 bug. The sweep is the net that already caught two live leaks on its first run;
  it answers the whole list at once and does not depend on anyone remembering.
- **⑪ `--proxy-headers` on uvicorn** (plus `--forwarded-allow-ips`). Three call sites carry a
  forwarded-header workaround and **a fourth that forgets it will be wrong in a way nobody notices,
  because http works.** `entrypoint.sh` runs uvicorn without it, so `url_for` behind Caddy mints
  `http://` — it caught a printed `http://` QR on the counter card before anything went to paper.
- **⑫ `enrich-from-source.py --apply`** — dry run clean (40 fetched, 0 failed). The spec half is safe
  and is most of the value (~4,500 products). The tier half writes **~510 new ladders on a live
  till** against 92 today. **Run it, then run ⑩ before the shop opens.** Not a job for the end of a
  long day.
- **⑬ The tablet's LTE — Luzern-only, whenever Angel is next at the shop.** Working, and proved in
  Angel's flat, not on the counter: set `ipv4.route-metric 100` on the **shop** Wi-Fi profile,
  measure signal where the till stands (29% at home, concrete will be worse), and pull the Fritzbox
  WAN cable mid-sale. Cold boot and the FCC unlock are ✅ machine-level and do not need redoing.
  🔋 Still to buy: a **USB-C PD** power bank — this tablet refuses 5V, so a USB-A bank does literally
  nothing. Runbook: [`onboarding/13-tablet-x1-debian.md`](onboarding/13-tablet-x1-debian.md).
- **⑭ Mint `qr_code` for the live members.** The card is deployed, but 0 of 18 members had one when
  last measured — **no card exists to scan yet.** 🧹 Also: three `ZZTEST-*` members seeded in LOCAL
  dev only (never prod) — `DELETE FROM customers WHERE handle LIKE 'ZZTEST-%';`
- **⑮ The miss rate is still not recorded.** `catalog_miss` holds **1 row, ever.**
  `_record_catalog_miss` is gated `if ln.department_code and ln.unresolved_barcode`, so only a miss
  rung through the department strip counts — and the *good* path (create-and-bind) carries neither.
  ⓪'s "telemetry is blind" is this. Until it is fixed, "three of four scans miss" has no live
  measurement behind it; that figure is a stock, not a rate.
- **⑯ A cashier still cannot create an anonymous member at the till.** `customer_lookup.html:566` +
  `CustomerCreate` still demand a handle, the way the kiosk did before `85154c0` fixed it there.
  Same "invent a name at a counter with a queue" problem the ART code exists to kill. Sibling of a
  shipped fix, and standing rule 9 says check the siblings.
- **⑰ A second wholesale feed is the big lever** — Kings Castle took reach ~40% → ~56% as tier 3.
  neardark needs credentials.
- **⑱ The catalogue CSV eats a leading apostrophe** — barcodes export as `'7610…`; Excel eats it,
  LibreOffice shows it, and no fix is clean in both. **An .xlsx export sidesteps it entirely** and
  the openpyxl machinery already exists for the BL-131 worklist. Angel's call.


---

## 💡 FIRST-USE AGE CHECK + THE T&C PAGE — waiting on Angel, not on code

Angel's idea (2026-08-22): the first time a member buys, the cashier verifies their age once —
better than storing a date of birth, because no DOB is held at all and the check is a human looking
at a human. **Design notes moved to [`worklist-archive/backlog.md`](worklist-archive/backlog.md)**
(record HOW, a look does not self-correct, hang it off the SCAN never the spoken code).

▶️ **What is actually blocked here is the T&C wording, and it is Angel's to write.** He sketched it
— plain English, not lawyer talk — then said *"I'm just making stuff up."* A page telling a customer
what they agree to should not be invented by the copilot. Draft copy needed, then DE at minimum;
FR/IT need a speaker, not a guess.

## 🔜 NEXT

3. **🔐 Go-live hardening** — DNS preflight + a default-secret gate in `deploy-prod.sh`; and the DR
   restore (Move B), still **blocked on read-only B2 credentials**. The backup has never been
   restored, so it is a belief, not a capability.

4. **🌱 Seeded realm users are published — DEFERRED ON PURPOSE 2026-08-14, not forgotten.**
   `keycloak/import/realm-export.json` carries **six users with plaintext, non-hashed
   passwords**, and `github.com/akenel/banco-starter` is **public** (HTTP 200 unauthenticated):
   `felix` (`pos-admin`), `ralph` (`pos-manager`), `michael`, `pam`, `pos-developer`,
   `pos-auditor`. Both `compose.yml:39` and `compose.prod.yml:35` boot Keycloak with
   `--import-realm` from that same file — prod and dev seed from one export.
   **Angel's call, 2026-08-14: leave them.** The usernames aren't the secret, these are seeded
   demo accounts, and **he rotated `felix`'s password on the live box**, so the published one is
   dead for the account that actually has privilege. Reasonable.
   ⚠️ **The one mechanism that could quietly undo that:** Keycloak's `--import-realm` only seeds
   when the realm doesn't already exist. So today's rotation holds — *until the Keycloak DB
   volume is ever recreated* (`down -v`, a fresh box, a restore drill onto a clean box). Then the
   export re-imports and **`felix`'s password silently reverts to the published one**. The
   DR restore in item 3 is exactly that scenario. Whoever drills it: check `felix` afterwards.
   When it comes up the list: strip the six users from the export (freehold did this in
   `a202c32` — `kc-prd` ships `"users": []` and the first admin is made by hand), and treat all
   six published passwords as burned regardless. The other five still have live published
   passwords today.


---


## 🧹 NEEDS TRIAGE — read before trusting

[`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) holds ~1,000
lines of catalogue, till and shelf-intake items written between 07-30 and 08-07. **Their status was
not re-verified when they were archived**, and at least one was already wrong:

> the shared cash box was filed as *"design agreed 2026-08-03, not built"* — it shipped in
> `fd035dd`, and the `cashier_id == user_id` filter it describes is gone from the code.

**So: check the code before acting on anything in there.** Promoting the still-live ones up to NOW
is a 20-minute job worth doing once, not a thing to re-derive every session.


---


## ⏲️ A decision the logs raised — how long may a till sit idle?

Angel's 15:46 logout was **correct**: 152 minutes idle against a 60-minute
`ssoSessionIdleTimeout`. Not the refresh bug returning — refresh verified 200 at the time
of writing. But it is worth deciding deliberately for the shop rather than inheriting it:
**60 minutes of a backgrounded tab and the cashier is logged out.** In the foreground the
till polls and the session stays warm; a tablet asleep over lunch does not. Overnight
logout is *desirable*; a quiet Tuesday afternoon one is not.


---


## 📌 Standing facts worth not re-learning

- **The app image bakes `src/` in — there is no bind mount.** `docker compose restart app` restarts
  the **old** code and says nothing. Any change under `src/` needs `./scripts/rebuild.sh`.
- **Prod authenticates against the DEMO realm** (`kc-pos-realm-dev`, users felix/pam/ralph),
  imported from a file **in a public GitHub repo**. Still the go-live blocker.
- **Banco is zero-perpetual.** `stock_quantity = 1` is the *design*, not missing data. Never set
  `min_stock` / `max_stock` / reorder points — `/reorder/suggestions` ranks by what the till sold.
- **`age_check_event` is append-only** (a PL/pgSQL trigger, not `REVOKE` — which is a no-op against
  a table owner). Nothing can tidy a row away, including a mis-tap.


---


## 🧪 How to prove it before claiming it

| what | command |
|---|---|
| stand up | `./scripts/rebuild.sh` → `./scripts/standup.sh` |
| server-side 18+ evidence | `BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py` |
| **the actual screens** | `BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-till-18plus.js` |

⚠️ Both scripts **ring real completed sales** and refund them afterwards; a completed transaction is
a line in the Kassenbuch. `BANCO_ALLOW_FAKE_SALES=1` exists so it cannot happen by accident.
Playwright is **borrowed via `NODE_PATH`, not vendored** — this repo has no node build, on purpose.


---

## 📚 The archive

| file | what's in it |
|---|---|
| [`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md) | **the second cut** — 889 lines moved out verbatim 2026-08-27: the member card, ART-AB12, the join offer, the counter card, bundle pricing, the price warning, the whole FourTwenty thread, the six till reports, adopt-images, both prod-live days |
| [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md) | Gate Zero, and the whole 18+ evidence thread 08-10 → 08-13 |
| [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) | catalogue, shelf intake, till and search, through 08-07 — **status unverified** |
| [`worklist-archive/2026-08-20-till-reports.md`](worklist-archive/2026-08-20-till-reports.md) | the evidence behind BL-9…BL-14 |
| [`worklist-archive/2026-08-21-fourtwenty-reference.md`](worklist-archive/2026-08-21-fourtwenty-reference.md) · [`2026-08-21-price-consistency/`](worklist-archive/2026-08-21-price-consistency/) · [`2026-08-22-pooling/`](worklist-archive/2026-08-22-pooling/) · [`2026-08-22-anon-member-card.md`](worklist-archive/2026-08-22-anon-member-card.md) | the days themselves |
| [`worklist-archive/backlog.md`](worklist-archive/backlog.md) | not yet scheduled — credits redemption (waiting on Felix), dark mode, the till that felt slow, the offline kit, monitoring, labels, exports |
| [`worklist-archive/done.md`](worklist-archive/done.md) | shipped, most recent first, with commit hashes |
