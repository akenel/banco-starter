# 12 · The cash box — one box, one slope, reconciled daily

*Design note, 2026-08-03. Written from Angel's account of how Artemis actually runs its cash,
after the cashier role-play showed Banco assumes something different. **Not built yet** — this is
the proposal Felix should agree before code changes.*

---

## What Banco assumes today (and why it is wrong here)

`cash_shift_model.py` says it plainly in its own docstring: *"per-cashier drawer accountability
(the lockbox model) … Cashier OPENS a shift by counting the float into **THEIR** drawer."*

That is a real and common retail model — every cashier gets their own till insert, and a variance
belongs to a named person. **Artemis does not work that way.**

The damage is one line, `pos_router.py:8632`:

```python
TransactionModel.cashier_id == user_id,   # sums only THIS cashier's takings
```

So: Felix opens with CHF 200. Pam sells CHF 150 cash into the same physical box. Felix counts out
and Banco expects `200 + only Felix's sales`. Pam's 150 francs are **in the box but not in the
expectation** → variance +150 → Felix writes a note explaining money that was never missing.

Worse, the "already have an open shift" guard is **per user**, so Felix and Pam can each hold an
open drawer on the same physical box at once, each blind to the other's sales.

---

## How the shop actually works

> Angel, 2026-08-03: *"They never really take all the money out of the cash box. The cash box is a
> slope."*

- **One physical cash box.** One terminal, one checkout area. Everybody sells into it — Felix,
  Pam, Ralph, Leandra, Nathan.
- **It is never emptied.** It carries roughly **CHF 600**, in mixed denominations and more than one
  currency, because that float is what makes change possible. Biggest note realistically seen is
  **CHF 200**.
- **Overnight it goes into a safe** and comes back out the next morning with the same money in it.
- **When it gets heavy** (~CHF 1,000–2,000) someone counts an amount out and puts it in the safe —
  so a robbery costs less. **This is a paid-out with a reason.** Banco does not track the safe.
- **Safe → bank** is Felix's own business, weekly or monthly. **Outside Banco entirely.**
- **Handover is a sheet of paper.** Felix writes what he sold, Ralph joins halfway through and
  keeps writing on the same sheet, Ralph counts the box at the end.

### The morning ritual — and why it matters

Felix opens up, and **counts the box before he looks at what it should contain.** Only then does
he check what yesterday's close said. He calls it a little test he plays with himself.

He is right, and it should be the enforced order. **Showing the expected figure first anchors the
count** — a tired person who sees `555` will keep counting until they find `555`. Count blind,
then reveal, then explain the difference.

And when it does not match, he does not stop trading:

> *"I only found five hundred in the cash box, and he said there was five hundred and fifty five.
> So where's the fifty five? … I'm just gonna work with the five hundred I got and go from there."*

That is the correct call, and it tells us where the discrepancy belongs: **against yesterday's
close, not today's trading.** Today starts from what is really in the box.

---

## The proposal

### 1 · The drawer belongs to the SHOP, not to a person

One open drawer at a time, shop-wide. It records **who opened it** and **who reconciled it**, but
nobody owns it and no variance is attributed to an individual.

**This is not a downgrade in accountability — it is honesty.** With one shared box, nobody can
truthfully say whose twenty francs went astray. Per-cashier *sales* reporting is untouched: every
transaction still carries `cashier_id`, so "who sold what" works exactly as it does now.

> It also kills a bad idea: the retired `/pos/cash-count` screen announced *"Perfect balance!
> **Pam's** bonus pool +1 point"*. In a shared-box shop that rewards or blames whoever happens to
> be holding the box at closing time.

### 2 · "Reconcile", not "close"

Angel: *"reconcile, I think, is the word we have to say."* Right — because nothing is being closed
down. The money stays. Two moments a day:

**Morning — OPEN (count blind, then reveal)**

1. Count the box, denomination by denomination. **Banco shows no expected figure yet.**
2. Submit the count. *Then* Banco reveals what last night's reconcile recorded.
3. Difference → a note is required, and it is filed **against yesterday's reconcile**.
4. **The counted amount becomes today's opening float.** Not the expected amount — the real one.

**Evening — RECONCILE**

1. Count the box.
2. `expected = opening float + ALL cash sales by everyone + paid-in − paid-out − cash refunds`
3. Outside ±0.20 → a note is required. (This rule already works today.)
4. **The counted amount is recorded as tomorrow's expected.** That is the slope.

The chain — *last night's counted → this morning's expected* — is the whole structural change.

### 3 · Cashiers stop touching the drawer

Only the person who opens and the person who reconciles do. Everyone else just sells.

This removes step **A4** from the cashier's daily routine entirely, and it resolves gap **G8**'s
"two meanings of shift" cleanly:

| | is about | scope |
|---|---|---|
| **Session** (`shift_session`) | who is logged in and working | per person |
| **The till** (`cash_shift`) | the money in the box | one, shop-owned |

A cashier signing off no longer has anything to do with the box. That was the tangle.

### 4 · Money to the safe is a paid-out

Confirmed with Angel: **no safe balance in Banco.** Skimming CHF 1,000 into the safe is a paid-out
with the reason "to safe". It leaves the drawer, the drawer still balances, and what happens in the
safe is Felix's business.

*(Worth a named reason button rather than free text, so it does not land in petty-cash expenses in
the Banana export alongside milk and window cleaner.)*

### 5 · When nobody counted — the administrative close

The design above assumes a person and a box in the same room. **Sometimes there is neither**, and
answer 2's skipped-night banner does not cover it: that chases a reconcile that *can still happen*.
This is the other case — a shift that must be closed when counting it is no longer possible.

**The rule: a close may be forced, but it must never be able to read as a count.**

Setting `counted = expected` is the only way to close such a row without inventing a number. That
produces a variance of 0.00 — and a zero variance is precisely the thing an auditor reads as *"the
drawer balanced"*. It didn't balance. Nobody looked. So the note must carry the whole story, and
the words "never physically counted" have to be in it.

This is the same failure the retired `/pos/cash-count` screen shipped — *"Perfect balance! Pam's
bonus pool +1 point"* announced over an uncounted drawer — arriving by a different door. **A number
that was never observed must say so where the number is stored**, not in a chat log or a commit
message that nobody reading the books will ever see.

> **Worked example — the first one, on prod, 2026-08-03 14:12.**
>
> Found while verifying the 5-rappen deploy: a shift open since 09:59, labelled `pam`, holding
> five real transactions — CHF 167.95 cash and CHF 65.70 TWINT — from that morning's cashier
> role-play. Expected CHF 168.00 on a CHF 0.05 opening float. Nobody was at the shop.
>
> Closed at `counted = expected = 168.00` **by a direct database UPDATE**, writing the same
> columns `POST /shift/close` writes (`cash_sales`, `card_sales`, `cash_refunds`,
> `transaction_count`, `expected_cash`, `counted_cash`, `variance`, `within_tolerance`,
> `status`, `closed_at`) with its exact semantics — `count` is COMPLETED only, only CASH touches
> the drawer — inside a transaction guarded on `AND status = 'open'`.
>
> The stored `variance_note` reads, in full:
>
> > ADMINISTRATIVE CLOSE — THE DRAWER WAS NEVER PHYSICALLY COUNTED. Opened 09:59 during the
> > 2026-08-03 cashier role-play and left open; found 2026-08-03 14:12 while verifying the
> > 5-rappen rounding deploy. counted_cash was SET EQUAL TO expected (CHF 168.00) to close the
> > row, so the zero variance is arithmetic, NOT an observation — nobody counted this box.
> > Closed by a direct database UPDATE, not through the till, because no one was at the shop to
> > count it. Authorised by Angel. Do not read this as a balanced count.
>
> **That shift is also the clearest evidence for this whole document.** `user_id`
> `00000000-…-0001` wearing the name `pam` while Angel was logged in as felix is the same
> wrong-cashier bug the role-play hit at `/pos/cash-count`. And an hour earlier, opening a drawer
> to run the rounding proof created a **second** open shift on the same physical box without a
> murmur of complaint — the per-user guard, failing live on production, exactly as predicted.

**To build:** a manager-only *force-close* that demands a reason, stamps `counted_cash` as
**unverified** in its own column rather than leaning on prose, and never counts toward any
balanced-drawer statistic. Until that exists, the note above is the pattern to copy verbatim.

### 6 · What the box starts with — a baseline, and a guard that is not a lock

*Angel, 2026-08-03, after finding pam's shift opened on a CHF 0.05 float:* **"when a system starts
maybe we need a way to say, ok here is what the float cash box has to start."**

Yes — and pam's row is the gap happening. `store_settings` carries **no cash-box configuration at
all**: no float, no baseline, and even `tolerance` sits on each shift row rather than shop-wide.
`opening_float` is free-typed at every open by whoever opens, so `{"0.05": 1}` — one 5-rappen coin
clicked in the grid — was accepted as the day's starting float on a box that carries ~CHF 600.

#### The two things one field is currently doing

| | | |
|---|---|---|
| **float** | what is in the box *right now* | a **measurement** — belongs to whoever is holding it |
| **baseline** | what the shop *intends* it to carry (~CHF 600) | a **policy** — belongs in settings |

Banco has one typed number doing both jobs. That conflation is the whole bug: nothing in the
system knows CHF 0.05 is absurd, because nothing has ever been told what normal looks like.

#### But note where this does NOT bite

**In the target design nobody types the float at all.** §2 makes the morning a count — *"the
counted amount becomes today's opening float, not the expected amount, the real one"* — so the
everyday case already self-heals. A wrong number lives exactly one day and the next morning's
count replaces it. **So the real gap is BOOTSTRAP, not everyday:** on day one there is no "last
night's counted" to seed the slope. That is where "here is what the box starts with" belongs —
asked **once**, at stand-up, alongside the other `init-banco.py` questions.

#### The rule: admin owns the BASELINE, the cashier owns the COUNT

Angel's instinct was *"admin sets it once and then only admin can override to make corrections."*
Half of that is right and the other half collides with his own **answer 1** — *a cashier may do
everything*, no manager gate on opening, reconciling, paid-in or paid-out. An admin-only
correction means a cashier facing a wrong baseline at 07:00 on a Sunday either cannot open the
shop or trades on a number they know is false. Both are worse than the typo.

It splits cleanly, and then both halves are true at once:

| | who | why |
|---|---|---|
| the **baseline** (`cash_box_float` in store settings) | **admin only**, like the VAT rate or the rounding step | it is a shop policy, not a per-shift observation |
| the **count** at open / reconcile | **any cashier**, always, never gated | it is the truth of what is physically there — and §2 rebuilds it every morning anyway |

#### So: a guard, not a lock

When the count is wildly off the baseline, **ask — do not refuse**:

```
  The box normally holds around CHF 600.00.
  You counted CHF 0.05.

  Is that right?     [ Yes, that's what's in it ]     [ Let me recount ]
```

It catches the fat finger, gates nobody, and the answer is recorded either way — a confirmed
"yes" is itself worth having in the record. **A hard block here would fail the shop on the one
morning the box really has been emptied**, which is precisely the morning you most want it opened
and the discrepancy written down.

*(Threshold: proportional, not absolute — something like ±50% of baseline. The point is to catch
0.05-for-600, not to nag about 580.)*

**Sequencing: this is part of item 2, not its own job.** The shop-owned rebuild rewrites the open
flow anyway, and the guard has to hang off count-blind-then-reveal to make sense. Building it
standalone means touching the same code twice.

**Still open for Angel:** whether an admin editing the baseline mid-life needs anything more than
a settings change — e.g. if Felix raises the box from 600 to 800, does that want a dated note so
next week's variance has an explanation, or is the daily count enough on its own?

---

## What actually changes in the code

Smaller than it sounds. **The arithmetic is already right; only the scope of one query is wrong.**

| | change |
|---|---|
| `_shift_sales` (`pos_router.py:8628`) | drop the `cashier_id == user_id` filter — sum everyone's takings in the window |
| open guard (`~8690`) | "you already have an open shift" → "**the till** is already open" (shop-wide, not per user) |
| open flow | count first, reveal after; counted becomes the float; note filed against yesterday |
| reconcile | store the counted total as the next expected — the overnight link |
| wording | "My Drawer" → **"Cash Box"**; cashier → *opened by* / *reconciled by* |
| paid-out | a named "to safe" reason, kept out of petty-cash expense reporting; **may be in a foreign currency**, paid-IN is home currency only |
| **cash rounding** | **round cash totals to 0.05 at checkout** — prerequisite for any tight tolerance (see below) |
| skipped night | banner on next login, listing every cash movement since the last reconcile |
| **force-close** | manager-only, reason required, `counted_cash` flagged **unverified** in its own column — never in prose, and never counted as a balanced drawer (§5) |
| **baseline** | `store_settings.cash_box_float` — admin-only, asked once at stand-up; seeds the slope on day one and backs the open-count guard (§6) |
| **the guard** | count wildly off the baseline → **ask, never refuse**; the answer is recorded either way (§6) |

Untouched: float maths, paid in/out, foreign-currency tracking, the ±0.20 note rule, per-cashier
sales reports.

---

## Answered — Angel, 2026-08-03

**1 · Who may reconcile? A cashier. All of it.** No manager gate on opening, reconciling, paid-in
or paid-out. The person holding the box is the person who counts it.

**2 · A skipped night gets chased, not forgiven.** On the next login (or at a set hour) a banner:
*"Yesterday's cash box was never reconciled. It should hold CHF 600.00. Please reconcile, then open
for the day."* And it must show **enough to reconstruct**, not just a number:

- who last reconciled it, and when
- who has touched it since
- **every cash movement since that reconcile, listed** — "2 cash sales, CHF 10.00 and CHF 5.00,
  one paid-out CHF 500.00 to safe" — so the total is arrived at rather than asserted

**3 · Foreign notes are counted at reconcile**, when there are any.

**4 · Currency has a DIRECTION on paid in/out.** *"Never pull in EUR, but pull out makes sense."*
Foreign notes arrive only as change-less takings from a sale; nobody tops the float up in euros.
So:

| | |
|---|---|
| **paid IN** | home currency only (CHF). No currency picker — one less thing to get wrong. |
| **paid OUT** | may be CHF **or** any foreign currency sitting in the box, so the EUR that has piled up can leave. |

Paid-out to the safe is where foreign notes go. **Banco never tracks the safe** — impossible to know
and not our business.

**5 · Call it the CASH BOX.** Not "till", not "drawer" — there is one box and everybody says box.

**German: `Kasse` for the thing, `Kassensturz` for the reconcile action.** ✅ Confirmed by a
native speaker (Sylvken), 2026-08-03 — so this is settled, not a guess. `Kassensturz machen` is
what a shopkeeper actually says for counting the till down, which is exactly the operation in
section 2. Use those two words in the German UI rather than a translation of "reconcile the cash
box", which would read as software-German.

*(`Geldkassette` is the precise word for the physical lockable box that goes in the safe, but it
is formal — nobody says it across a counter.)*

---

## Tolerance — the part worth getting right

Angel: *"the tax man wants the calc to the 2nd decimal point to the penny and we can get in big
trouble … Felix says they want it to the penny or 5 rappens maybe, otherwise it's a game of hide
and seek."*

### These are two different things, and conflating them is the risk

| | |
|---|---|
| **The record** | **Always exact, to the rappen. Always.** Every variance is stored with the amount, who counted, when, and the reason. Nothing is ever rounded away, absorbed, or hidden. |
| **The tolerance** | Only decides **whether a human must type a reason.** It changes no number. |

So "to the penny" is already true and is not negotiable — it is what the books hold. The tolerance
is a *workflow* setting: how big a difference may pass without someone explaining it.

**An auditor wants a complete, reasoned record — not a drawer that is always perfect.** A cash box
that balances to 0.00 every single day for a year is a red flag, not a gold star; real cash drifts,
and forced perfection is exactly the hide-and-seek Felix is worried about, pointed the other way.

### The natural floor is 5 rappen

Switzerland has no 1- or 2-rappen coin in circulation. **The smallest coin is 0.05.** A pure cash
variance therefore cannot be finer than 5 rappen, and any tolerance below that is meaningless —
±0.05 means "one coin".

**Recommendation: ±0.05, shop-configurable.** It is as tight as physical cash allows, it matches
Felix's instinct, and it is honest. If notes start reading "dunno", widen it — that is a signal,
not a failure.

### ⛔ But there is a blocker, and it is a real bug

**Banco does not round cash totals to 5 rappen.** Totals are quantized to `0.01`
(`cash_shift_service.py:68`, and the discount maths at `pos_router.py:4793`). Swiss rounding exists
in this codebase **only in payroll** (`payroll_service.py:74`).

Undiscounted prices land on 0.05 anyway, so this has been invisible. **A discount breaks it:**
5% off CHF 74.10 = CHF 70.395 → stored as **70.40 or 70.39**. A 1-rappen total *cannot be paid in
Swiss coins.* The cashier takes 70.40, Banco expects 70.39, and the box is 1 rappen over — on every
such sale, silently, for ever.

**So the order matters: round cash totals to 0.05 at checkout FIRST, then a ±0.05 tolerance is
achievable.** Set a tight tolerance before that and the drawer will drift a few rappen a day and
nobody will know why. Card and TWINT are unaffected — they take the exact cent, which is why this
only ever shows up in the box.

> **✅ BUILT 2026-08-03 — and not yet on prod.** `_apply_cash_rounding()` now runs on both sale
> paths for cash only; `transactions.rounding_adjustment` records the move so the receipt prints
> `Rounding (5 Rp.)` and Banana gets a `Rundungsdifferenz` rather than an unexplained rappen.
> Proven end to end on dev by `scripts/prove-cash-rounding.py`. **The ±0.05 tolerance still waits
> on the prod deploy**, not on the code — and on somebody watching a real receipt come out.

---

*One box. Everyone sells into it. Whoever closes counts it, and whoever opens counts it again
before being told what to expect. Nothing else was ever true here.*
