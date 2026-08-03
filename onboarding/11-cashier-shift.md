# 11 · The cashier's day — open to close

*The daily cycle, in order, as the person at the counter lives it. Written 2026-08-03 from the
running code (every URL and rule below was read out of `src/routes/pos_router.py`, not assumed).*

**This document has two lives:**

1. **Now — the test protocol.** Angel plays the cashier, morning to close, before go-live. Run the
   day as written and fill in the ⏱ and the ✋ column. What you cannot do is the finding.
2. **After — the till card.** Once the gaps are closed, sections **A / B / C / F** print on one page
   and get laminated at the counter. Nobody at the till reads a manual.

> **The contract, from [`10-devices-and-roles.md`](10-devices-and-roles.md):** the cashier makes
> **no decisions** and each item takes **2 seconds, or it is broken**. Every place this document
> asks the cashier to think is either a gap in the catalogue or a gap in the training. Both get
> fixed *before* the shift, never during one.

---

## Who does what

| | **Cashier** (Leandra, Roger, Nathan) | **Manager** (Felix, Angel) |
|---|---|---|
| Keycloak role | `💰️ pos-cashier` | `👔️ pos-manager` / `👑️ pos-admin` |
| Sell, scan, take payment | ✅ | ✅ |
| Own a drawer (float in, count out) | ✅ | ✅ |
| Paid-in / paid-out (petty cash) | ✅ with a reason | ✅ |
| **Refund** | ❌ **blocked — manager only** | ✅ |
| Reports, product sales, category sales | ❌ | ✅ |
| Change a price, edit the catalogue | ❌ | ✅ |
| Banana export | ❌ | ✅ |

The refund gate is deliberate and it is the single most important line in the table — **a return
with no manager in the shop currently has no path.** See gap **G6**.

---

## A · Opening — before the first customer

Target: **under 5 minutes.** Do it in this order; each step proves the one before.

| # | Do | Where | Proof it worked |
|---|---|---|---|
| A1 | Log in as yourself — not the shop's shared login | `/pos` | Your name is on the screen |
| A2 | Dongle in, scan the test code | `/pos/hardware` | **Green.** Do this per machine, every time a gun moves |
| A3 | Second gun on the charger | the cradle | It is physically there |
| A4 | **Open your drawer — count the float in** | `/pos/shift` | Shift shows OPEN with your float |
| A5 | Card terminal on, test it if the shop's rule says so | terminal | Its own screen says ready |

**A4 is the one people will skip, and skipping it is silent.** Banco will happily let you sell all
day with no drawer open — and the shift tally only counts sales rung *after* the drawer opened, so
those sales vanish from your count-out. Nothing warns you. See gap **G3**.

> Count the float into the drawer denomination by denomination, not as a remembered total. The
> whole close depends on this number being real.

---

## B · Selling — the whole job, 99% of the day

```
scan → scan → scan → take payment → receipt → next customer
```

1. `/pos/scan` on the till. Gun at the barcode.
2. It rings up. Repeat.
3. Payment: **cash · Visa · debit · TWINT · bank transfer · crypto · other**.
4. Receipt if they want one.

That is the entire happy path and it needs no training. **If the till asks the cashier a question
mid-sale, that is a bug in yesterday's setup, not a slow cashier.**

### 🔞 The one question the till is allowed to ask

Age-restricted lines will not check out unless the cashier either attaches an of-age loyalty member
or explicitly attests the walk-in is 18+ (ID checked). This is enforced **server-side** — it cannot
be clicked past, and every clearance is logged with who cleared it and how.

**Train this one properly. It is the only place a cashier can personally create a legal problem for
Felix.** The rule at the counter: *no ID, no sale.* A member proven under 18 by date of birth is
blocked outright and no attestation overrides it.

---

## C · When it goes wrong — the exceptions

**This is where the training earns its money.** The happy path teaches itself; these do not. Each
one is a stopwatch item in the role-play.

| # | What happens | What the cashier does | Status |
|---|---|---|---|
| C1 | **Barcode not found** | Banco says *"Product with barcode 'x' not found"* and stops | ⚠ **G1 — no defined move** |
| C2 | **Product found but inactive** | Banco says *"Product is inactive"* and stops | ⚠ **G1** |
| C3 | **Screen price ≠ shelf price** | Sell at… which? Who is allowed to decide? | ⚠ **G2 — undecided** |
| C4 | **Wrong item scanned into the basket** | Remove the line before checkout — no manager needed | ✅ works |
| C5 | **Customer changes mind after payment** | **Refund = manager only** | ⚠ **G6** |
| C6 | **Card declines** | Ask for another method — the basket is still open | ✅ works |
| C7 | **Split payment** (part cash, part card) | One method per transaction today | ⚠ **G7** |
| C8 | **Customer forgot their wallet, will be back** | No park-the-sale for a cashier | ⚠ **G5** |
| C9 | **Cash leaves the drawer** (milk, window cleaner) | `/pos/shift` → **paid-out**, with a reason | ✅ works — a reason is required |
| C10 | **Cash comes in** that isn't a sale (float top-up) | `/pos/shift` → **paid-in**, with a reason | ✅ works |
| C11 | **Gun goes flat mid-queue** | Swap the dongle to the charged gun | ✅ works — that's why there are two |
| C12 | **Foreign cash offered** | Banco tracks foreign cash per currency at close | ✅ exists — needs a human test |
| C13 | **18+ item, no ID** | Refuse the line. No override exists, correctly | ✅ works |

> **C1 is the big one.** It is not rare: it is every delivery that arrived since the last setup
> session, and at Felix's shop that is most weeks. A cashier hitting C1 with four people waiting
> and no written answer will invent one — and whatever they invent becomes the shop's policy.

---

## D · Closing — count the drawer out

Target: **under 10 minutes** (the paper version took 90).

1. `/pos/shift` → **close** → count the drawer out, denomination by denomination.
2. Banco computes:
   `expected = float + cash sales + paid-in − paid-out − cash refunds`
3. **Variance = counted − expected.** Tolerance is **CHF 0.20**.
   - Inside tolerance → closes clean.
   - Outside → **it will not close without a note.** That is deliberate: the note is the audit trail.
4. You get a one-page shift report: hours, transaction count, cash, card, expected, counted,
   variance. It survives a reload (`/pos/shift/last`) — closing does not lose it.

**Card sales are reported but are not in the drawer.** Do not count them and do not expect them to
balance against cash. Say this out loud in training; it is the classic first-week mistake.

---

## E · The manager's part — after the cashiers have gone

| # | Do | Where |
|---|---|---|
| E1 | Read the day: totals, per payment method, VAT | `/pos/reports` |
| E2 | Check each cashier's variance and read every note | shift reports |
| E3 | Process any refunds held over from the day | manager-only |
| E4 | **Export for Banana** | `/api/v1/pos/reports/daily-summary.csv` |
| E5 | Import into Banana Accounting | Banana |

### The Banana file — what's in it

One quoted line per payment method that actually took money, plus a giveaway-cost expense line if
treats went out, plus a **VAT summary block** (CH 8.1% / 2.6%) carried in its own `Turnover` and
`VAT` columns. The VAT rows leave Income/Expenses blank on purpose, so they are visible to Felix
without touching Banana's import sum. File lands as `banana-YYYY-MM-DD.csv`.

> ⚠ **`Account` and `VatCode` ship blank.** Felix maps them in Banana's import dialog every single
> day until he hands over his real chart-of-accounts codes and we pre-fill them. **This is a
> go-live item, not a detail** — a daily manual mapping step is exactly the kind of friction that
> gets abandoned in week three and takes the bookkeeping with it. See gap **G4**.

---

## F · The till card (the laminated version)

```
OPEN      hardware green → drawer open with float counted
SELL      scan · scan · pay · receipt
18+       no ID, no sale. Ever.
NOT FOUND  → [ to be decided — gap G1 ]
REFUND    → get a manager
CASH OUT  → /pos/shift → paid-out → say why
CLOSE     count out → note any difference → hand the report over
```

---

## G · What is NOT settled — the gaps this document found

**These are decisions for Angel and Felix, not bugs.** Every one of them will surface in the
role-play, and each has to have an answer before a cashier meets a customer.

| | Gap | Why it matters |
|---|---|---|
| **G1** | ~~No defined move for an unknown barcode.~~ **ANSWERED 2026-08-03 — build it on the fly.** Angel created the product *with* category and description and sold it in **~10 seconds** (`OTF-1785752266675-826`, TXN-20260803-0005). | The move exists and is fast. What is left: put it on the till card, and confirm a **cashier** is allowed to do it — the catalog screen currently says creating and editing need a manager role. |
| **G2** | **No rule for shelf price ≠ screen price.** | A wrong bind shows up *here*, in front of a customer — Cannazym at CHF 12 instead of 35. Needs a stated rule. |
| ~~**G3**~~ | ~~Checkout does not require an open cash drawer.~~ **NOT A GAP — tested 2026-08-03.** A cash sale with a closed drawer *stops and warns*; checkout already enforces it. | Struck. This document asserted it from reading the code and was wrong. Ten seconds of role-play settled what a careful read got backwards. |
| **G4** | **Banana `Account` / `VatCode` are blank.** | Felix re-maps by hand daily until he hands over his codes. Get the chart of accounts. |
| **G5** | **No park-the-sale.** `/pos/held-orders` is the kiosk pre-order board, not a parked basket. | "I'll be back in ten minutes" has no home. |
| **G6** | **Refunds are manager-only, with no cashier path.** | Correct as a control, unworkable if Felix is out. Needs either a manager-present rule or a cashier-side escalation. |
| **G7** | **One payment method per transaction.** | Split cash/card is common. Confirm with Felix whether the shop needs it before go-live. |
| **G8** | **Three end-of-day screens exist:** `/pos/closeout`, `/pos/shift`, `/pos/cash-count` — plus a *second* shift concept (login sessions: `/shift/start`, `/shift/end`, handoff) alongside the cash drawer (`/shift/open`, `/shift/close`). | **A cashier cannot have three closing screens and two meanings of "shift".** Pick the one that is real, and make the others unreachable from the cashier's navigation. This is the biggest smoothness risk in the whole cycle. |

---

## H · The role-play run sheet

Play it as a cashier or it will prove nothing. **Your own lesson, 2026-07-30:** you kept proving
search worked while Felix was scanning — you will route around every pothole without noticing you
did it.

**Rules for the day:**

- Log in as a **cashier account**. Not admin, not your account.
- **The tablet only.** No ProBook, no terminal, no database, no Tigs.
- **When you get stuck: write down the stuck and do what a cashier would do.** Do not fix it. The
  fix is tomorrow's job — today you are collecting the list.
- **Stopwatch the exceptions, not the sales.** Nobody cares that a scan takes 2 s.

| Step | ⏱ target | ⏱ actual | ✋ could a cashier do it alone? | Notes |
|---|---|---|---|---|
| A · Open (A1–A5) | < 5 min | | | |
| B · 20 normal sales | 2 s / item | | | |
| B · One 18+ sale, ID checked | < 20 s | | | |
| C1 · Unknown barcode | ? | | | **no answer exists yet** |
| C3 · Price mismatch | ? | | | **no answer exists yet** |
| C4 · Remove a wrong line | < 15 s | | | |
| C5 · Refund (no manager present) | ? | | | **blocked by design** |
| C7 · Split payment | ? | | | |
| C9 · Paid-out for milk | < 30 s | | | |
| C11 · Swap to the spare gun | < 30 s | | | |
| D · Close and count out | < 10 min | | | |
| E · Manager reads the day | < 10 min | | | |
| E4/E5 · Export → into Banana | < 5 min | | | **does it actually import?** |

**Done means:** the whole cycle ran once, end to end, by one person with no help — and the drawer
balanced. Anything else is a finding, and findings are the point.

> Tests passing is not done. A human holding the shift report and a balanced drawer is done.
