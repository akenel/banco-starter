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

---

## What actually changes in the code

Smaller than it sounds. **The arithmetic is already right; only the scope of one query is wrong.**

| | change |
|---|---|
| `_shift_sales` (`pos_router.py:8628`) | drop the `cashier_id == user_id` filter — sum everyone's takings in the window |
| open guard (`~8690`) | "you already have an open shift" → "**the till** is already open" (shop-wide, not per user) |
| open flow | count first, reveal after; counted becomes the float; note filed against yesterday |
| reconcile | store the counted total as the next expected — the overnight link |
| wording | "My Drawer" → "The Till"; cashier → *opened by* / *reconciled by* |
| paid-out | a named "to safe" reason, kept out of petty-cash expense reporting |

Untouched: float maths, paid in/out, foreign-currency tracking, the ±0.20 note rule, per-cashier
sales reports.

---

## Open questions for Felix

1. **Can anyone reconcile, or only a manager?** Angel: *"one person does that, takes ownership."*
   A cashier probably can — but the note on a discrepancy should be readable by Felix next morning.
2. **What if nobody reconciles?** The box goes in the safe uncounted and the chain breaks. Warn
   loudly on the next open, or refuse to open until the missing night is explained?
3. **Is ±0.20 still right for a shared box** several people have been in all day? It may want to be
   wider — and a tolerance that is too tight teaches people to write meaningless notes.
4. **The foreign notes** sitting in the box: counted every time, or only at reconcile?

---

*One box. Everyone sells into it. Whoever closes counts it, and whoever opens counts it again
before being told what to expect. Nothing else was ever true here.*
