"""Every total must be payable in coins that exist. Always down, no exceptions.

Found 2026-08-03 while answering "how tight should the cash-box tolerance be?". Banco
quantizes totals to 0.01 and Switzerland has no 1- or 2-rappen coin. Undiscounted prices land
on 0.05 anyway so it never showed — but on real Artemis prices FIVE OF SIX discounted totals
cannot be paid: 8.91, 42.66, 62.99, 16.92, 6.21.

The cashier takes 63.00, Banco expects 62.99, the box is a rappen over. Every such sale, for
ever — and a tight cash-box tolerance on top would drift with nothing to explain it.

Angel chose the rule and declined the setting: always down, one direction, no modes. And CASH
ONLY — the constraint is physical and only coins have it, so rounding a card sale would give
away margin for nothing. The screen worry ("the total changes when you pick a method") is
solved by showing a Rounding line, not by rounding everything.

These pin the arithmetic. The property at the bottom is the one the books depend on: the
adjustment is recorded, never absorbed.
"""
from decimal import Decimal

import pytest

from src.services.total_rounding import round_total, rounding_step, is_payable
from src.services.fiscal_regime import resolve_regime

STEP = Decimal("0.05")


def _r(total):
    return round_total(total, STEP)


# ── the real cases ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("total,payable", [
    ("8.91", False),    # 10% off 9.90
    ("42.66", False),   # 5%  off 44.90
    ("62.99", False),   # 15% off 74.10
    ("16.92", False),   # 15% off 19.90
    ("6.21", False),    # 10% off 6.90
    ("70.40", True),    # 5%  off 74.10 — lands on the step by luck
])
def test_real_discounted_totals_become_payable(total, payable):
    assert is_payable(total, STEP) is payable
    assert is_payable(_r(total)["rounded"], STEP), "rounding must always produce a payable total"


def test_the_case_that_started_this():
    """15% off CHF 74.10 = 62.99. There is no 4-rappen coin, so nobody can hand that over."""
    out = _r("62.99")
    assert out["rounded"] == Decimal("62.95")
    assert out["adjustment"] == Decimal("-0.04")


def test_angels_own_example():
    """His words: "if it comes out to nine eighty three, then we just say, okay. Fine. Nine
    eighty." One rule, no branches, easy to hold in your head at a counter."""
    assert _r("9.83")["rounded"] == Decimal("9.80")


# ── one rule, every ending ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cents,expected", [
    ("0.00", "0.00"), ("0.01", "0.00"), ("0.02", "0.00"), ("0.03", "0.00"), ("0.04", "0.00"),
    ("0.05", "0.05"), ("0.06", "0.05"), ("0.07", "0.05"), ("0.08", "0.05"), ("0.09", "0.05"),
])
def test_every_rappen_ending_goes_down(cents, expected):
    base = Decimal("10.00")
    assert _r(base + Decimal(cents))["rounded"] == base + Decimal(expected)


def test_the_customer_is_never_charged_more_than_the_marked_price():
    """The whole reason `down` beat the Swiss `nearest` convention: the adjustment is never
    positive, so "the sticker said 9.90 and you charged me 9.92" cannot happen."""
    t = Decimal("10.00")
    while t < Decimal("10.30"):
        assert _r(t)["adjustment"] <= 0
        t += Decimal("0.01")


def test_a_total_already_on_the_step_is_untouched():
    """The common case by far — undiscounted Swiss prices are all 0.05 multiples, so the vast
    majority of sales pass through with adjustment exactly 0 and no line on the receipt."""
    for t in ("4.90", "9.90", "40.00", "74.10", "0.05", "1234.55"):
        out = _r(t)
        assert out["rounded"] == Decimal(t) and out["adjustment"] == Decimal("0.00")


def test_sub_rappen_input_is_treated_as_its_cent_value_first():
    """70.395 is intermediate discount arithmetic, not a price anyone quotes. It quantizes to
    70.40, which is already payable, and must be LEFT ALONE — not dragged down to 70.35.
    Rounding twice would take 4.5 rappen off a total that was fine. I got this wrong first and
    the tests caught it."""
    out = _r("70.395")
    assert out["rounded"] == Decimal("70.40") and out["adjustment"] == Decimal("0.00")


# ── outside Switzerland ──────────────────────────────────────────────────────────────────

def test_step_zero_disables_it_entirely():
    """A shop self-hosting where 1-cent coins still circulate. Nothing to configure."""
    out = round_total("70.39", Decimal("0"))
    assert out["rounded"] == Decimal("70.39") and out["adjustment"] == Decimal("0.00")


def test_a_swiss_shop_gets_five_rappen_from_the_regime():
    assert rounding_step(resolve_regime(None)) == STEP


def test_a_missing_regime_disables_rather_than_guesses():
    assert rounding_step(None) == Decimal("0")
    assert rounding_step({}) == Decimal("0")


# ── it must never be the thing that breaks a sale ────────────────────────────────────────

def test_junk_never_raises():
    """A malformed value must never be why a customer cannot pay for a lighter."""
    for junk in (None, "", "abc", object()):
        assert round_total("70.39", junk)["rounded"] == Decimal("70.39")
        assert round_total(junk, STEP)["rounded"] == Decimal("0.00")


def test_zero_and_tiny_totals():
    assert _r("0.00")["rounded"] == Decimal("0.00")
    assert _r("0.04")["rounded"] == Decimal("0.00")   # a 4-rappen basket becomes free
    assert _r("0.01")["rounded"] >= 0


def test_float_input_does_not_reintroduce_dust():
    out = _r(62.99)
    assert out["rounded"] == Decimal("62.95")
    assert out["rounded"].as_tuple().exponent >= -2


# ── the part that keeps the tax man calm ─────────────────────────────────────────────────

def test_the_adjustment_always_reconciles_exactly():
    """original + adjustment == rounded, to the rappen, across 300 totals — and every result
    is payable in coins. This is the property the books rely on: nothing is absorbed, so a
    rounding difference is always a recordable line rather than a gap in the drawer."""
    base = Decimal("10.00")
    for i in range(300):
        out = round_total(base + (Decimal(i) / Decimal("100")), STEP)
        assert out["original"] + out["adjustment"] == out["rounded"]
        assert is_payable(out["rounded"], STEP), f"{out['rounded']} cannot be paid in coins"
        assert Decimal("0") >= out["adjustment"] > -STEP   # never up, never a whole step


def test_the_adjustment_is_always_smaller_than_one_coin():
    """Giving away 5 rappen or more would be a bug, not a courtesy."""
    for t in ("62.99", "9.83", "0.04", "1000.01"):
        assert abs(_r(t)["adjustment"]) < STEP
