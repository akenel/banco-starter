"""Round every total DOWN to a payable amount. One rule, no settings, no exceptions.

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

THE RULE — Angel, 2026-08-03, twice and deliberately:

    "just round down to the nearest five cents in all cases. Give the customer the benefit of
     the doubt and move on. It's just easier for the human to reason out and understand, and
     it all tallies up."

So: **always down, every total, every payment method.** Not a setting, not a mode, not a
per-currency policy. He was offered the setting and turned it down: *"you could have this
option in the settings, but that's, again, not simple."*

WHY "ALL CASES" IS THE RIGHT SIMPLIFICATION, not a lazy one. The obvious "correct" design
rounds only CASH, because card and TWINT settle the exact cent. But then the same basket is
62.99 on card and 62.95 in cash, and **the total on screen changes when the cashier picks a
payment method** — a genuinely confusing thing to put in front of someone with a queue. The
cost of avoiding it is up to four rappen on a card sale. Angel: *"they give the guy a two penny
break every once in a while. What's the difference?"*

One number. It never moves. It is always in the customer's favour, so it can never cause an
argument at a counter. That is worth more than four rappen.

WHY ONLY DOWN, never nearest. Nearest (.01/.02 down, .03/.04 up) is the Swiss retail
convention and is cost-neutral — but it can charge 1-2 rappen MORE than the shelf label, and
"the sticker said 9.90 and you charged me 9.92" is a conversation nobody at a till should have
to have. Down is never wrong for the customer, and a rule with no branches is one a human can
hold in their head.

AND IT IS ALREADY WHAT THE SHOP DOES. This is the argument that actually settles it. Artemis
runs on paper today, and Angel: *"they don't have the pennies, so they're not gonna overcharge.
The guy at the checkout is gonna go into the little cash box and find out what coins he's got.
Half the time the guy just waives his hand anyway."* The cashier already rounds down, because
the coins to do anything else do not exist. So this is not a policy Banco is introducing — it
is the existing practice, written down and made consistent. A till that asked for CHF 62.99
would be the thing behaving strangely.

THE ADJUSTMENT IS RETURNED, NEVER ABSORBED. Callers store it, so the books can show
`total 62.99 · rounding −0.04 · to pay 62.95` rather than an unexplained rappen. A rounding
difference that vanishes into a total is exactly what makes a tax inspection unpleasant.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

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
    """Round a total DOWN to something payable.

    Returns ``{original, rounded, adjustment}`` — Decimals quantized to cents, where
    ``adjustment = rounded - original`` and is therefore never positive.

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
    # the raw value straight down would take 4.5 rappen off a total that was already fine — and
    # that is a mistake I actually made here first; the tests caught it.
    units = (original / step).quantize(Decimal("1"), rounding=ROUND_DOWN)
    rounded = (units * step).quantize(CENTS, rounding=ROUND_HALF_UP)

    return {"original": original, "rounded": rounded,
            "adjustment": (rounded - original).quantize(CENTS, rounding=ROUND_HALF_UP)}


def is_payable(amount, step) -> bool:
    """Can this amount be handed over in coins? Used to assert the fix actually took."""
    step = _d(step)
    if step <= 0:
        return True
    return (_d(amount).quantize(CENTS, rounding=ROUND_HALF_UP) % step) == 0
