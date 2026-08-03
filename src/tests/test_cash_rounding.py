"""A cash total must be payable in coins that exist.

Found 2026-08-03, answering "how tight should the cash-box tolerance be?". Banco quantizes
totals to 0.01, and Switzerland has no 1- or 2-rappen coin. Undiscounted prices land on 0.05
anyway so it never showed — but a discount breaks it, and on real Artemis prices FIVE OF SIX
discounted totals cannot be paid: 8.91, 42.66, 62.99, 16.92, 6.21.

The cashier takes 63.00, Banco expects 62.99, the box is a rappen over. Every such sale,
silently, for ever — and a ±0.05 tolerance on top would drift with no explanation.

These pin the arithmetic. The rule that matters most is the last group: the adjustment is
always RECORDED, never absorbed.
"""
from decimal import Decimal

import pytest

from src.services.cash_rounding import (
    round_cash_total, cash_rounding_step, is_payable, ROUNDING_MODES,
)
from src.services.fiscal_regime import resolve_regime

STEP = Decimal("0.05")


def _r(total, mode="down"):
    return round_cash_total(total, STEP, mode)


# ── the live case ────────────────────────────────────────────────────────────────────────

# Real discounted totals off Artemis prices. Five of these six cannot be paid in coins —
# which is the bug. (The first draft of this test used 5% off 74.10, which quantizes to
# 70.40 and IS payable: the one lucky case out of six. The tests caught it, not me.)
@pytest.mark.parametrize("total,payable", [
    ("8.91", False),    # 10% off 9.90
    ("42.66", False),   # 5%  off 44.90
    ("62.99", False),   # 15% off 74.10
    ("16.92", False),   # 15% off 19.90
    ("6.21", False),    # 10% off 6.90
    ("70.40", True),    # 5%  off 74.10 — lands on the step by luck
])
def test_real_discounted_totals(total, payable):
    assert is_payable(total, STEP) is payable
    out = _r(total, "down")
    assert is_payable(out["rounded"], STEP), "rounding must always produce a payable total"


def test_the_case_that_started_this():
    """15% off CHF 74.10 = 62.99. Nobody can hand over 62.99 — there is no 4-rappen coin."""
    assert not is_payable("62.99", STEP)
    down = _r("62.99", "down")
    assert down["rounded"] == Decimal("62.95") and down["adjustment"] == Decimal("-0.04")
    near = _r("62.99", "nearest")
    assert near["rounded"] == Decimal("63.00") and near["adjustment"] == Decimal("0.01")


# ── every ending, both directions ────────────────────────────────────────────────────────

@pytest.mark.parametrize("cents,down,nearest", [
    ("0.00", "0.00", "0.00"),   # already payable — untouched by both
    ("0.01", "0.00", "0.00"),
    ("0.02", "0.00", "0.00"),
    ("0.03", "0.00", "0.05"),   # nearest goes UP here; down never does
    ("0.04", "0.00", "0.05"),
    ("0.05", "0.05", "0.05"),   # already payable
    ("0.06", "0.05", "0.05"),
    ("0.07", "0.05", "0.05"),
    ("0.08", "0.05", "0.10"),
    ("0.09", "0.05", "0.10"),
])
def test_each_rappen_ending(cents, down, nearest):
    base = Decimal("10.00")
    assert _r(base + Decimal(cents), "down")["rounded"] == base + Decimal(down)
    assert _r(base + Decimal(cents), "nearest")["rounded"] == base + Decimal(nearest)


def test_down_never_charges_more_than_the_marked_price():
    """Angel's rule: the customer should not pay the 5 rappen. So the adjustment is never
    positive — that is the whole point of choosing `down` over the convention."""
    t = Decimal("10.00")
    while t < Decimal("10.20"):
        assert _r(t, "down")["adjustment"] <= 0
        t += Decimal("0.01")


def test_nearest_is_the_one_that_can_charge_more():
    """Stated so the trade is visible in the tests, not just the docstring."""
    assert _r("10.03", "nearest")["adjustment"] == Decimal("0.02")
    assert _r("10.03", "down")["adjustment"] == Decimal("-0.03")


def test_sub_rappen_input_is_treated_as_its_cent_value_first():
    """70.395 is not a price anyone quotes — it is intermediate discount arithmetic. It
    quantizes to 70.40 (a payable amount) and must then be left alone, NOT dragged down to
    70.35. Rounding twice would take 4.5 rappen off a total that was already fine."""
    out = _r("70.395", "down")
    assert out["rounded"] == Decimal("70.40")
    assert out["adjustment"] == Decimal("0.00")


# ── what must NOT round ──────────────────────────────────────────────────────────────────

def test_a_total_already_on_the_step_is_untouched():
    """The common case by far. Undiscounted Swiss prices are all 0.05 multiples, so the vast
    majority of sales must pass through with adjustment exactly 0."""
    for t in ("4.90", "9.90", "40.00", "74.10", "0.05", "1234.55"):
        out = _r(t)
        assert out["rounded"] == Decimal(t)
        assert out["adjustment"] == Decimal("0.00")


def test_step_zero_disables_it_entirely():
    """A shop outside the 5-cent countries. Card-only regimes and USD keep the exact cent."""
    out = round_cash_total("70.39", Decimal("0"), "down")
    assert out["rounded"] == Decimal("70.39") and out["adjustment"] == Decimal("0.00")
    assert out["mode"] == "none"


def test_mode_none_disables_it_even_with_a_step():
    out = round_cash_total("70.39", STEP, "none")
    assert out["rounded"] == Decimal("70.39")


# ── it must never be the thing that breaks a sale ────────────────────────────────────────

def test_an_unknown_mode_falls_back_to_the_customer_safe_direction():
    """A typo in a store setting must not overcharge anyone, and must not raise at a till."""
    out = round_cash_total("70.39", STEP, "sideways")
    assert out["rounded"] == Decimal("70.35")
    assert out["mode"] == "down"


def test_a_junk_step_does_not_raise():
    """A malformed store setting must never be why a customer cannot pay for a lighter."""
    for junk in (None, "", "abc", -1, object()):
        out = round_cash_total("70.39", junk, "down")
        assert out["rounded"] == Decimal("70.39")


def test_a_junk_total_does_not_raise_either():
    for junk in (None, "", "abc"):
        assert round_cash_total(junk, STEP, "down")["rounded"] == Decimal("0.00")


def test_zero_and_tiny_totals():
    assert _r("0.00")["rounded"] == Decimal("0.00")
    assert _r("0.04")["rounded"] == Decimal("0.00")     # a 4-rappen basket becomes free
    assert _r("0.00")["adjustment"] == Decimal("0.00")


def test_a_total_is_never_rounded_below_zero():
    assert _r("0.01")["rounded"] >= 0


def test_float_input_does_not_reintroduce_dust():
    """The bug was sub-rappen dust. Passing a float must not smuggle it back in."""
    out = _r(62.99)
    assert out["rounded"] == Decimal("62.95")
    assert out["rounded"].as_tuple().exponent >= -2


# ── the regime supplies the step ─────────────────────────────────────────────────────────

def test_a_swiss_shop_gets_five_rappen():
    assert cash_rounding_step(resolve_regime(None)) == STEP


def test_a_missing_regime_disables_rather_than_guesses():
    assert cash_rounding_step(None) == Decimal("0")
    assert cash_rounding_step({}) == Decimal("0")


# ── the part that keeps the tax man calm ─────────────────────────────────────────────────

def test_the_adjustment_always_reconciles_exactly():
    """original + adjustment == rounded, to the rappen, for every ending and both modes.
    This is the property the books rely on: nothing is absorbed, so a rounding difference is
    always a recordable line rather than an unexplained gap in the drawer."""
    base = Decimal("10.00")
    for i in range(200):
        t = base + (Decimal(i) / Decimal("100"))
        for mode in ("down", "nearest"):
            out = round_cash_total(t, STEP, mode)
            assert out["original"] + out["adjustment"] == out["rounded"]
            assert is_payable(out["rounded"], STEP), f"{out['rounded']} cannot be paid in coins"


def test_every_documented_mode_is_implemented():
    """ROUNDING_MODES is shown to a shop owner choosing a policy; it must not advertise a
    mode the function does not honour."""
    for mode in ROUNDING_MODES:
        out = round_cash_total("70.39", STEP, mode)
        assert out["mode"] in ("none", mode)
