"""
Cash-shift math -- pure, no DB, no HTTP, so it's trivially unit-testable.

The whole honest loop in three functions:
  expected_cash(...)  -> what SHOULD be in the drawer at close
  close_result(...)   -> variance + within-tolerance verdict
  denoms_total(...)   -> sum a denomination breakdown into a total

Money is Decimal end-to-end, quantized to CHF cents (ROUND_HALF_UP). Only CASH
touches the drawer -- card/twint/debit are reported but never part of the count.
"""
from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")

# Swiss franc denominations (notes + coins), in CHF. Used to total a count grid.
# BYTE-IDENTICAL to the original set: keeps the 1000 note + 0.05 coin,
# EXCLUDES 0.01/0.02 (Switzerland has no Rappen below 5). Do NOT reorder/reformat.
CHF_DENOMINATIONS = [
    Decimal("1000"), Decimal("200"), Decimal("100"), Decimal("50"),
    Decimal("20"), Decimal("10"),                       # notes
    Decimal("5"), Decimal("2"), Decimal("1"),
    Decimal("0.50"), Decimal("0.20"), Decimal("0.10"), Decimal("0.05"),  # coins
]

# Euro denominations (notes + coins), in EUR. Includes the 500 note and 1c/2c
# coins -- all legal tender, so all must be countable at closeout or they vanish.
EUR_DENOMINATIONS = [
    Decimal("500"), Decimal("200"), Decimal("100"), Decimal("50"),
    Decimal("20"), Decimal("10"), Decimal("5"),          # notes
    Decimal("2"), Decimal("1"),
    Decimal("0.50"), Decimal("0.20"), Decimal("0.10"),
    Decimal("0.05"), Decimal("0.02"), Decimal("0.01"),   # coins
]

# US dollar denominations (notes + coins), in USD.
USD_DENOMINATIONS = [
    Decimal("100"), Decimal("50"), Decimal("20"), Decimal("10"),
    Decimal("5"), Decimal("1"),                          # notes
    Decimal("0.25"), Decimal("0.10"), Decimal("0.05"), Decimal("0.01"),  # coins
]

_DENOMS_BY_CURRENCY = {
    "CHF": CHF_DENOMINATIONS,
    "EUR": EUR_DENOMINATIONS,
    "USD": USD_DENOMINATIONS,
}


def denoms_for(currency="CHF"):
    """Ordered face-value list for a currency (falls back to CHF for unknowns)."""
    return _DENOMS_BY_CURRENCY.get((currency or "CHF").upper(), CHF_DENOMINATIONS)


# Back-compat: the CHF whitelist, for anything that imported it directly.
_VALID_DENOMS = {str(d) for d in CHF_DENOMINATIONS}


def _d(v) -> Decimal:
    """Coerce anything moneyish to a Decimal; None/'' -> 0."""
    if v is None or v == "":
        return Decimal("0")
    return v if isinstance(v, Decimal) else Decimal(str(v))


def money(v) -> Decimal:
    """Quantize to CHF cents, half-up."""
    return _d(v).quantize(CENTS, rounding=ROUND_HALF_UP)


def expected_cash(opening_float, cash_sales, paid_in, paid_out, cash_refunds) -> Decimal:
    """What should physically be in the drawer at close.

    float you started with
      + cash you took from sales
      + cash brought in (float top-ups)
      - cash taken out (petty cash)
      - cash you refunded to customers
    """
    total = (_d(opening_float) + _d(cash_sales) + _d(paid_in)
             - _d(paid_out) - _d(cash_refunds))
    return money(total)


def close_result(expected, counted, tolerance=Decimal("0.20")) -> dict:
    """Compare the counted drawer to expectation.

    variance = counted - expected   (negative = short, positive = over)
    within   = abs(variance) <= tolerance
    """
    exp = money(expected)
    cnt = money(counted)
    tol = money(tolerance)
    variance = money(cnt - exp)
    return {
        "expected": exp,
        "counted": cnt,
        "variance": variance,
        "tolerance": tol,
        "within_tolerance": abs(variance) <= tol,
        "short": variance < 0,
    }


# How far off the baseline a count has to be before the open guard speaks up. Proportional,
# not absolute: the point is to catch 0.05-where-600-was-expected, not to nag about 580.
BASELINE_GUARD_FRACTION = Decimal("0.5")


def open_reveal(counted, expected, tolerance=Decimal("0.20")) -> dict:
    """The morning reveal: what was counted vs what last night's reconcile said.

    Called only AFTER the count is submitted -- §2 of the design note makes the blind count
    mandatory, because showing the expected figure first anchors it ("a tired person who sees
    555 will keep counting until they find 555").

    `expected` may be None: on the very first open there is no previous reconcile and no
    baseline, so there is nothing to compare against. Then no claim is made -- variance is
    None, not zero. A zero would assert a match that was never established.

    The difference belongs to YESTERDAY, not to today's trading. Today starts from what is
    really in the box.
    """
    cnt = money(counted)
    if expected is None:
        return {"counted": cnt, "expected": None, "variance": None,
                "within_tolerance": True, "short": False, "needs_note": False,
                "tolerance": money(tolerance)}
    exp = money(expected)
    variance = money(cnt - exp)
    within = abs(variance) <= money(tolerance)
    return {"counted": cnt, "expected": exp, "variance": variance,
            "within_tolerance": within, "short": variance < 0,
            "needs_note": not within, "tolerance": money(tolerance)}


def baseline_check(counted, baseline, expected=None, fraction=BASELINE_GUARD_FRACTION) -> dict:
    """§6 -- is this count wildly unlike what the box should hold? Ask if so.

    A GUARD, NOT A LOCK. It returns whether to ASK; the caller must never refuse on the
    strength of it. A hard block would fail the shop on the one morning the box really has
    been emptied -- which is precisely the morning you most want it opened and the
    discrepancy written down.

    THE REFERENCE IS THE SLOPE WHEN THERE IS ONE, the baseline only otherwise. Found by the
    live proof, 2026-08-03: after a CHF 500 skim to the safe the box legitimately holds ~100
    overnight, and measuring that against a CHF 600 baseline questioned a perfectly normal
    morning -- every morning, for as long as the box stayed light. Last night's counted total
    already knows about the skim; the baseline does not. So the baseline's real job is
    narrower than it first looked: seed day one, and catch an absurd count when there is
    nothing better to compare against.

    Returns off_baseline=False when there is neither: an unconfigured shop on its first day
    gets silence, never a guessed threshold.

    This is COARSE on purpose -- "did you fat-finger it?" -- and is a different question from
    the tolerance, which asks "explain this difference". A morning can pass this and still
    need a note.
    """
    cnt = money(counted)
    ref = expected if expected is not None else baseline
    if ref is None or money(ref) <= 0:
        return {"off_baseline": False, "reference": None, "reference_is": None, "counted": cnt}
    ref = money(ref)
    allowed = money(ref * money(fraction))
    # reference_is stays an English phrase for anything already reading it; reference_is_key
    # is the machine-readable twin, added 2026-09-05 so the CLIENT can build this sentence in
    # the reader's language and through the money seam. The server-built message was English
    # under a translated title ("È corretto?" then "The box should hold around…"), and its
    # amounts were raw Decimals — CHF 1216.90 where every other figure on that screen reads
    # CHF 1'216.90. Angel caught both in a screenshot of the morning open.
    return {"off_baseline": abs(cnt - ref) > allowed,
            "reference": ref,
            "reference_is": ("last night's reconcile" if expected is not None
                             else "the configured baseline"),
            "reference_is_key": ("last_reconcile" if expected is not None
                                 else "configured_baseline"),
            "counted": cnt, "allowed_gap": allowed}


def denoms_total(denoms, currency="CHF") -> Decimal:
    """Sum a {denomination: count} map into a total in the given currency.

    Keys are face values as strings ("50", "0.05"); values are counts. Validation
    is against the CURRENCY-APPROPRIATE denomination set -- a EUR 500 note or a
    1c/2c coin is valid under EUR but not under CHF. Unknown denominations and junk
    counts are ignored (robust to a noisy client). Default currency is CHF so every
    pre-existing call site keeps byte-identical behavior.
    """
    if not isinstance(denoms, dict):
        return Decimal("0")
    valid = {str(d) for d in denoms_for(currency)}
    total = Decimal("0")
    for face, count in denoms.items():
        if str(face) not in valid:
            continue
        try:
            n = int(count)
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        total += Decimal(str(face)) * n
    return money(total)
