"""Cash rounding — a total someone can actually hand over in coins.

WHY THIS EXISTS. Found 2026-08-03 while answering "how tight should the cash-box tolerance
be?". Banco quantizes every total to 0.01. Undiscounted Swiss prices land on 0.05 anyway
(4.90, 9.90, 40.00) so nothing ever looked wrong — but a discount breaks it. Measured on
real Artemis prices, FIVE OF SIX discounted totals cannot be paid in coins:

    10% off  9.90 = 8.91        15% off 74.10 = 62.99
     5% off 44.90 = 42.66       15% off 19.90 = 16.92
    10% off  6.90 = 6.21         5% off 74.10 = 70.40   <- the one lucky case

**Switzerland has no 1- or 2-rappen coin.** They were withdrawn in 2007 and 1978. So a cash
total of CHF 62.99 cannot be handed over. The cashier takes 63.00, Banco expects 62.99, and
the box is a rappen over — silently, on every such sale, forever. Set a ±0.05 tolerance on
top of that and the drawer drifts a few rappen a day with nobody able to explain it.

WHAT ROUNDS AND WHAT DOES NOT:

    CASH        rounds to the coin step. It is a physical constraint.
    CARD/TWINT  never rounds. They settle the exact cent.

So the SAME basket can be CHF 70.39 on card and 70.40 in cash. That is normal in Switzerland
and it is why rounding belongs at the PAYMENT step, not at the cart total — the cart cannot
know yet.

THE ADJUSTMENT IS RECORDED, NEVER ABSORBED. `round_cash_total` hands back both numbers and
the difference so the transaction can store it. A rounding difference that vanishes into a
total is exactly the kind of unexplained rappen that makes a tax inspection unpleasant; a
recorded one is a line item with a reason.

MODES. `down` never charges the customer more than the marked price — Angel's call, 2026-08-03:
*"the customer should not pay the 5 rappens IMHO"*. `nearest` is the Swiss retail convention and
is roughly cost-neutral over time. Both are honest; see `ROUNDING_MODES` for the trade.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

CENTS = Decimal("0.01")

ROUNDING_MODES = {
    # mode      -> (human label, what it costs the shop)
    "down": ("Always in the customer's favour",
             "Costs the shop up to one step per affected cash sale (~2 rappen average). "
             "Never charges more than the marked price, so it can never generate a complaint."),
    "nearest": ("Swiss retail convention",
                "Roughly cost-neutral over many sales — .01/.02 down, .03/.04 up. "
                "Occasionally charges 1-2 rappen MORE than the shelf price."),
    "none": ("No cash rounding",
             "Correct outside the 5-cent countries. The till will ask for amounts that cannot "
             "be paid in coins where 1- and 2-cent pieces no longer circulate."),
}

DEFAULT_MODE = "down"


def _d(v) -> Decimal:
    """Decimal, or zero. Never raises — this runs on the checkout path, and a malformed
    store setting must not be the reason a customer cannot pay for a lighter."""
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v if v is not None else "0"))
    except (ArithmeticError, ValueError, TypeError):
        return Decimal("0")


def cash_rounding_step(regime: dict | None) -> Decimal:
    """The smallest coin, from the resolved fiscal regime. 0 disables rounding."""
    if not regime:
        return Decimal("0")
    try:
        return _d(regime.get("cash_rounding_step") or "0")
    except Exception:                      # a malformed setting must never block a sale
        return Decimal("0")


def round_cash_total(total, step, mode: str = DEFAULT_MODE) -> dict:
    """Round a CASH total to the nearest payable coin amount.

    Returns ``{original, rounded, adjustment, step, mode}`` — all Decimals quantized to cents,
    where ``adjustment = rounded - original`` (negative when the customer pays less).

    NEVER RAISES. A rounding helper that throws would block a checkout over a rappen, so an
    unusable step or mode falls through to "no rounding" and the exact total stands.
    """
    original = _d(total).quantize(CENTS, rounding=ROUND_HALF_UP)
    step = _d(step)

    if step <= 0 or mode == "none":
        return {"original": original, "rounded": original,
                "adjustment": Decimal("0.00"), "step": step, "mode": "none"}

    # Work in whole steps: 70.395 / 0.05 = 7879.0 steps. Decimal throughout — a float here
    # would reintroduce the very sub-rappen dust this function exists to remove.
    units = original / step
    if mode == "nearest":
        units = units.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    else:                                   # "down" — and anything unrecognised, which is the
        units = units.quantize(Decimal("1"), rounding=ROUND_DOWN)   # customer-safe direction
    rounded = (units * step).quantize(CENTS, rounding=ROUND_HALF_UP)

    # A total is never rounded below zero, and a refund (negative total) keeps its sign
    # rather than being dragged further from zero by ROUND_DOWN.
    if original >= 0 and rounded < 0:
        rounded = Decimal("0.00")

    return {"original": original, "rounded": rounded,
            "adjustment": (rounded - original).quantize(CENTS, rounding=ROUND_HALF_UP),
            "step": step, "mode": mode if mode in ROUNDING_MODES else "down"}


def is_payable(amount, step) -> bool:
    """Can this amount be handed over in coins? Used to assert the fix actually took."""
    step = _d(step)
    if step <= 0:
        return True
    return (_d(amount).quantize(CENTS, rounding=ROUND_HALF_UP) % step) == 0
