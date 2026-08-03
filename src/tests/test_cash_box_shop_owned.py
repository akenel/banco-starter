"""The cash box belongs to the SHOP. One box, one open shift, everybody sells into it.

Built 2026-08-03 from `onboarding/12-the-cash-box.md`. The bug being killed is one line —
`_shift_sales` carried `TransactionModel.cashier_id == user_id`, so Felix opened with 200, Pam
sold 150 cash into the SAME physical box, and Felix's close expected only his own takings:
variance +150 and a note explaining money that was never missing.

It is not hypothetical. On production that same afternoon, opening a box to run the rounding
proof created a SECOND open shift while pam's had sat open since 09:59, and nothing objected.

These pin the DECISIONS, which is where the risk is — the arithmetic was always right:
  * the morning reveal comes AFTER the count, and says nothing when there is nothing to compare
  * the §6 guard ASKS and never refuses
  * a forced close can never masquerade as a real count
  * a skim to the safe is not an expense
"""
from decimal import Decimal

import pytest

from src.services.cash_shift_service import (
    open_reveal, baseline_check, expected_cash, close_result, money,
)
from src.db.models.cash_shift_model import REASON_CODES, NON_EXPENSE_REASON_CODES

TOL = Decimal("0.20")


# ── the shared box: expected must include EVERYONE ───────────────────────────────────────

def test_the_bug_this_whole_rebuild_exists_for():
    """Felix opens with 200. Pam sells 150 cash into the same box. Felix counts out 350.

    Under the old per-cashier scope the expectation counted only Felix's own takings, so a
    perfectly correct drawer reported +150 and demanded a note for money that was never
    missing. Summing EVERYBODY's cash is the fix, and it is one filter."""
    everyones_cash = Decimal("150.00")          # Pam's sales, into Felix's opened box
    exp = expected_cash(Decimal("200.00"), everyones_cash, 0, 0, 0)
    assert exp == Decimal("350.00")
    assert close_result(exp, Decimal("350.00"), TOL)["variance"] == Decimal("0.00")


def test_only_the_cashier_filter_was_wrong_not_the_arithmetic():
    """Float + cash + paid-in - paid-out - refunds was always correct. Guard against
    'fixing' the formula while removing the filter."""
    assert expected_cash("600.00", "250.00", "20.00", "1000.00", "15.00") == Decimal("-145.00")


# ── the morning: count blind, THEN reveal ────────────────────────────────────────────────

def test_the_reveal_reports_the_difference_against_yesterday():
    """Felix's real morning: the record said 555, the box held 500. The 55 belongs to
    YESTERDAY's reconcile — today starts from the 500 that is really there."""
    out = open_reveal("500.00", "555.00", TOL)
    assert out["variance"] == Decimal("-55.00")
    assert out["short"] is True and out["needs_note"] is True


def test_no_previous_reconcile_makes_NO_claim():
    """Day one. There is nothing to compare against, so variance is None — NOT zero.

    A zero would assert a match that was never established, which is the same lie as a forced
    close reading as a balanced drawer."""
    out = open_reveal("600.00", None, TOL)
    assert out["variance"] is None and out["expected"] is None
    assert out["needs_note"] is False, "nothing to explain when nothing was promised"


def test_a_matching_count_needs_no_note():
    out = open_reveal("600.00", "600.00", TOL)
    assert out["variance"] == Decimal("0.00") and out["needs_note"] is False


def test_inside_tolerance_passes_without_a_note():
    """A shared cash box drifts. Demanding prose for 5 rappen is how notes become 'dunno'."""
    assert open_reveal("600.05", "600.00", TOL)["needs_note"] is False


def test_the_five_rappen_tolerance_is_now_reachable():
    """±0.05 (one coin) only became meaningful once cash totals round to 0.05 at checkout —
    before that the drawer drifted a rappen on every discounted sale with nothing to explain."""
    tight = Decimal("0.05")
    assert open_reveal("600.05", "600.00", tight)["needs_note"] is False
    assert open_reveal("600.06", "600.00", tight)["needs_note"] is True


# ── §6 · the guard ASKS, it never refuses ────────────────────────────────────────────────

def test_the_guard_catches_the_real_case():
    """Prod, 2026-08-03: a shift opened on `{"0.05": 1}` — one 5-rappen coin — on a box that
    carries ~600. Nothing objected, because nothing had been told what normal looks like."""
    assert baseline_check("0.05", "600.00")["off_baseline"] is True


def test_the_guard_does_not_nag_about_normal_variation():
    for counted in ("580.00", "620.00", "400.00", "800.00"):
        assert baseline_check(counted, "600.00")["off_baseline"] is False, counted


def test_an_unconfigured_shop_gets_SILENCE_not_a_guess():
    """No baseline and no slope → no guard. Never invent a threshold."""
    assert baseline_check("0.05", None)["off_baseline"] is False
    assert baseline_check("0.05", "0")["off_baseline"] is False


def test_the_slope_outranks_the_baseline_as_the_reference():
    """Found by the live proof, 2026-08-03. After a CHF 500 skim to the safe the box
    legitimately holds ~100 overnight. Measured against a CHF 600 baseline that is a 'wildly
    off' count — so the guard questioned a perfectly normal morning, and would have gone on
    doing it every morning the box stayed light.

    Last night's counted total already knows about the skim. The baseline does not."""
    assert baseline_check("100.00", "600.00")["off_baseline"] is True, "vs baseline alone"
    out = baseline_check("100.00", "600.00", expected="101.00")
    assert out["off_baseline"] is False, "the slope knows about yesterday's skim"
    assert out["reference"] == Decimal("101.00")
    assert out["reference_is"] == "last night's reconcile"


def test_the_baseline_still_catches_an_absurd_count_against_the_slope():
    """The guard did not go soft — 0.05 against a 101 slope is still questioned."""
    assert baseline_check("0.05", "600.00", expected="101.00")["off_baseline"] is True


def test_the_guard_is_COARSE_and_the_tolerance_is_FINE():
    """Two different questions. 'Did you fat-finger it' can pass while 'explain this
    difference' still fires — a morning 55 short of 600 is plausible and still needs a note."""
    assert baseline_check("545.00", "600.00", expected="600.00")["off_baseline"] is False
    assert open_reveal("545.00", "600.00", TOL)["needs_note"] is True


def test_the_guard_is_advisory_by_construction():
    """It returns a flag; it cannot raise, refuse, or alter the count. A hard block would fail
    the shop on the one morning the box really HAS been emptied — precisely the morning you
    most want it opened and the discrepancy written down."""
    out = baseline_check("0.05", "600.00")
    assert set(out) == {"off_baseline", "reference", "reference_is", "counted", "allowed_gap"}
    assert out["counted"] == Decimal("0.05"), "the guard must never change what was counted"


# ── the slope: last night's counted is this morning's expected ───────────────────────────

def test_the_slope_chains_one_day_to_the_next():
    """Reconcile at 612.35 → tomorrow expects 612.35. The box is never emptied, so the
    expectation cannot reset to a float somebody typed once."""
    last_night_counted = close_result(Decimal("612.40"), Decimal("612.35"), TOL)["counted"]
    assert open_reveal(last_night_counted, last_night_counted, TOL)["variance"] == Decimal("0.00")


def test_todays_float_is_what_was_COUNTED_not_what_was_expected():
    """Felix: "I only found five hundred ... I'm just gonna work with the five hundred I got."
    Trading must start from reality, or every sale that day inherits yesterday's error."""
    counted, expected = Decimal("500.00"), Decimal("555.00")
    float_for_today = open_reveal(counted, expected, TOL)["counted"]
    assert float_for_today == counted
    # ... and a clean day on top of it balances, despite the morning being 55 short.
    assert close_result(expected_cash(float_for_today, "100.00", 0, 0, 0),
                        Decimal("600.00"), TOL)["variance"] == Decimal("0.00")


# ── §5 · a forced close must never read as a count ───────────────────────────────────────

def test_a_forced_close_produces_a_zero_variance_which_is_exactly_the_danger():
    """counted := expected is the only honest option (any other number is invented) — and it
    yields 0.00, which a reader takes for 'the drawer balanced'. It didn't; nobody looked.

    This test exists to state WHY the fact needs its own column: the numbers alone cannot
    distinguish a forced close from a perfect one."""
    exp = Decimal("168.00")
    forced = close_result(exp, exp, TOL)
    real = close_result(exp, exp, TOL)
    assert forced == real, "indistinguishable by arithmetic — hence counted_verified"
    assert forced["variance"] == Decimal("0.00") and forced["within_tolerance"] is True


# ── §7.3 · a drop is not petty cash ──────────────────────────────────────────────────────

def test_to_safe_is_not_an_expense():
    """Skimming CHF 1,000 to the safe when the box gets heavy moves money out of the drawer
    but not out of the business. Booked as petty cash it would overstate expenses by whatever
    the shop skims — next to milk and window cleaner in the Banana export."""
    assert "to_safe" in NON_EXPENSE_REASON_CODES
    assert "petty_cash" not in NON_EXPENSE_REASON_CODES


def test_every_non_expense_code_is_a_real_code():
    assert set(NON_EXPENSE_REASON_CODES) <= set(REASON_CODES)


def test_a_drop_still_reduces_the_expected_cash():
    """It is still money that left the drawer — the box must not expect it at reconcile.
    Only the ACCOUNTING treatment differs, not the arithmetic."""
    assert expected_cash("600.00", "400.00", 0, "1000.00", 0) == Decimal("0.00")
