"""Round a CASH total to the nearest payable amount. One rule, no settings, no exceptions.

WHY IT EXISTS. Switzerland withdrew the 1-rappen coin in 2007 and the 2-rappen in 1978, so
the smallest coin is 5 rappen and **CHF 62.99 cannot be handed over.** Banco quantizes totals
to 0.01. Undiscounted Swiss prices happen to land on 0.05 (4.90, 9.90, 40.00), which is why
this stayed invisible — but a discount breaks it. Measured on real Artemis prices, five of six
discounted totals are unpayable:

    10% off  9.90 = 8.91        15% off 74.10 = 62.99
     5% off 44.90 = 42.66       15% off 19.90 = 16.92
    10% off  6.90 = 6.21         5% off 74.10 = 70.40   <- the one that happens to work

Left alone, the cashier takes 63.00, Banco expects 62.99, and the cash box is a rappen over on
every such sale, for ever.

THE RULE: round to the NEAREST step. 2.99 -> 3.00, 2.91 -> 2.90. No modes, no setting —
Angel turned the setting down twice: *"you could have this option in the settings, but that's,
again, not simple."*

WHY NEAREST AND NOT DOWN — this went round twice and the second answer is the right one.

Down was chosen first, to give the customer the benefit of the doubt. Then Angel supplied the
fact that changes it: **Felix deliberately does not discount.** He holds the line on the
selling price and gives a free treat instead — papers for CHF 3 and a lollipop, rather than
CHF 2.95. That mechanism is already built and already tracked (`line_item.is_treat`, and the
Z-report prints "Treats given (free) - 4 - cost CHF 0.45").

So rounding DOWN would be a silent, unrequested discount on every odd total — quietly
implementing the exact pricing policy the owner rejected, in a place nobody would ever look.
Angel: *"the 2.99 becoming 2.95 is not good, but a pack of papers for 3 and a lollipop are
fine — that's how he does it actually."*

**Rounding is physics. Treats are pricing. They must not be the same lever.** A rule that is
neutral leaves the giving to Felix, deliberately, where he can see and cost it.

Not "always up" either: that systematically charges above the marked price to gain two rappen,
and "the sticker said 9.90 and you paid 9.92" is the one conversation nobody at a till should
have to have. Nearest is neutral over many sales, is the Swiss retail convention, and gives
2.99 -> 3.00 — which was the case Angel actually cared about.

**CASH ONLY.** Settled 2026-08-03. The first cut rounded every payment method, to keep one
number on screen that never moved. Angel pulled it back, and he is right:

  - The constraint is **physical and applies only to coins.** TWINT, debit and card settle the
    exact cent perfectly well. Rounding them solves nothing.
  - **Felix has margins and costs to the rappen.** Giving away up to four rappen on every
    discounted card sale is pure loss for no benefit — small, but indefensible when someone
    asks why.

The worry that drove the first version — *the total changes when the cashier picks a payment
method* — is real, but the fix is to stop it being SILENT, not to round everything. Show it:

    Total     CHF 62.99
    Rounding  −CHF 0.04
    TO PAY    CHF 62.95

That is explanatory, not confusing, and it appears only on a cash sale that actually rounded.
A card checkout looks exactly as it does today.

There is deliberately **no config flag for which methods round.** Cash is the only payment
method with a coin constraint; that is a fact, not a preference, so there is nothing to
configure and nothing to get wrong.

HOW OFTEN DOES THIS EVEN FIRE? Rarely, and that is worth knowing before anyone worries about
the direction. Every Artemis shelf price is already a 0.05 multiple (4.90, 9.90, 40.00), so an
unroundable total only appears when a PERCENTAGE discount produces one. Felix avoids those on
principle. And the replacement he and Angel discussed — a TARGET SALE PRICE, "just give me 60
and it's a deal" — is a number a human types, so it is payable by construction. The rounding
is a safety net for an edge case, not a daily event.

THE ADJUSTMENT IS RETURNED, NEVER ABSORBED. Callers store it, so the books can show
`total 62.99 · rounding −0.04 · to pay 62.95` rather than an unexplained rappen. A rounding
difference that vanishes into a total is exactly what makes a tax inspection unpleasant.

VAT, when this is wired up. Compute VAT on the amount ACTUALLY PAID — Banco already derives
the "incl. VAT" figure from the total, so this is no change of approach and the receipt stays
internally consistent. The effect is a fraction of a rappen. **But carry the adjustment as its
own line into the Banana export**: as a `Rundungsdifferenz` it is a thing every Swiss
bookkeeper recognises, whereas dissolved into the VAT figure it is an unexplained few rappen a
day. Explainable beats invisible.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")


def _d(v) -> Decimal:
    """Decimal, or zero. Never raises — this runs on the checkout path, and a malformed
    value must not be the reason a customer cannot pay for a lighter."""
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v if v is not None else "0"))
    except (ArithmeticError, ValueError, TypeError):
        return Decimal("0")


def rounding_step(regime: dict | None) -> Decimal:
    """The smallest coin, from the resolved fiscal regime. 0 disables rounding entirely.

    This is a JURISDICTION fact, not a shop preference — it is which coins exist — which is why
    it lives in the regime and never appears in store settings. A shop self-hosting Banco
    somewhere that still has 1-cent coins gets step 0 and exact totals, with nothing to
    configure and nothing to get wrong.
    """
    if not regime:
        return Decimal("0")
    return _d(regime.get("cash_rounding_step") or "0")


def round_total(total, step) -> dict:
    """Round a total to the NEAREST payable amount.

    Returns ``{original, rounded, adjustment}`` — Decimals quantized to cents, where
    ``adjustment = rounded - original``. It may be negative or positive, and is always
    smaller than one step.

    NEVER RAISES. A rounding helper that throws would block a checkout over a rappen, so an
    unusable step falls through to "no rounding" and the exact total stands.
    """
    original = _d(total).quantize(CENTS, rounding=ROUND_HALF_UP)
    step = _d(step)

    if step <= 0:
        return {"original": original, "rounded": original, "adjustment": Decimal("0.00")}

    # Whole steps, Decimal throughout — a float here would reintroduce the very sub-rappen dust
    # this function exists to remove.
    #
    # Note the quantize-to-cents FIRST: 70.395 is intermediate discount arithmetic, not a price
    # anyone quotes. It becomes 70.40, which is already payable and must be left alone. Rounding
    # the raw value straight to a step would take 4.5 rappen off a total that was already fine —
    # a mistake I actually made here first; the tests caught it.
    units = (original / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    rounded = (units * step).quantize(CENTS, rounding=ROUND_HALF_UP)

    return {"original": original, "rounded": rounded,
            "adjustment": (rounded - original).quantize(CENTS, rounding=ROUND_HALF_UP)}


def is_payable(amount, step) -> bool:
    """Can this amount be handed over in coins? Used to assert the fix actually took."""
    step = _d(step)
    if step <= 0:
        return True
    return (_d(amount).quantize(CENTS, rounding=ROUND_HALF_UP) % step) == 0
