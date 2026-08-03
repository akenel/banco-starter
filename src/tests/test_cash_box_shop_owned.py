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
import re
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


# ── the till screen must handle what the API can return ──────────────────────────────────

def test_the_open_screen_handles_every_rejection_the_api_can_return():
    """THE ONE THAT NEARLY SHIPPED A SHOP-STOPPER.

    Opening the box used to be a plain 200-or-error call. It now has two rejections that are
    STEPS IN THE FLOW, not failures: the §6 guard (409 off_baseline) and the morning reveal
    (400 opening_variance). The screen only set `this.error = <string>` — so a morning that
    differed from last night by more than the tolerance would have shown a red line with no
    note field and NO WAY FORWARD. The shop could not have opened its till.

    Caught by reading the template before deploying, not by any test. So: every structured
    code the endpoint can raise must be named in the screen that calls it."""
    import io
    router = io.open("src/routes/pos_router.py", encoding="utf-8").read()
    screen = io.open("src/templates/pos/shift.html", encoding="utf-8").read()

    start = router.index("async def open_cash_shift(")
    end = router.index("async def shift_paid_in_out(")
    open_endpoint = router[start:end]

    codes = set(re.findall(r'"code":\s*"([a-z_]+)"', open_endpoint))
    assert codes, "no structured codes found — did the endpoint change shape?"
    for code in codes:
        assert code in screen, (
            f"POST /shift/open can return code '{code}' and shift.html never mentions it — "
            f"the cashier would get a dead end")


def test_the_open_screen_can_actually_satisfy_both_rejections():
    """Naming the code is not enough: the retry has to send what the server asked for."""
    import io
    screen = io.open("src/templates/pos/shift.html", encoding="utf-8").read()
    assert "confirm_off_baseline" in screen, "no way to answer the guard"
    assert "openNote" in screen, "no way to supply the morning note"


def test_the_open_screen_never_shows_the_expected_figure_before_the_count():
    """The blind count is the control, and a helpful UI is exactly how it gets lost. The open
    panel must not render an expected/last-night figure anywhere — the reveal comes back in
    the RESPONSE, after a count exists."""
    import io
    screen = io.open("src/templates/pos/shift.html", encoding="utf-8").read()
    panel = screen[screen.index('id="open-drawer"'):screen.index("ACTIVE SHIFT (open)")]
    for leak in ("shift.expected_cash", "openReveal.expected", "last_expected"):
        assert leak not in panel, f"the open panel leaks the expected figure via {leak}"


def test_an_unverified_figure_must_not_be_quoted_as_fact():
    """§5, one link further down the chain. A forced close sets counted = expected, so the
    SLOPE can carry a number nobody ever counted. The next morning the reveal would say "last
    night's reconcile said CHF 168.00" as though somebody had looked — and the cashier would
    hunt for a discrepancy that may well be in that figure, not in the box.

    Found on prod, 2026-08-03: pam's box was force-closed at 168.00, making it the slope.

    The comparison still happens. What changes is that it is not presented as fact."""
    import io
    router = io.open("src/routes/pos_router.py", encoding="utf-8").read()
    start = router.index("async def open_cash_shift(")
    end = router.index("async def shift_paid_in_out(")
    endpoint = router[start:end]
    assert "expected_verified" in endpoint
    assert "prev.counted_verified" in endpoint, "the slope must inherit the previous verification"
    assert "NEVER PHYSICALLY" in endpoint, "an unverified expectation must say so to the cashier"


def test_day_one_baseline_is_also_not_a_count():
    """The configured baseline is a setting somebody typed, not a drawer anybody counted, so
    the very first open must not present it as an observation either."""
    import io
    router = io.open("src/routes/pos_router.py", encoding="utf-8").read()
    start = router.index("async def open_cash_shift(")
    seg = router[start:router.index("async def shift_paid_in_out(")]
    baseline_branch = seg[seg.index("day one: the baseline seeds it"):]
    assert "expected_verified = False" in baseline_branch[:200]


def test_the_forced_close_note_is_for_a_person_not_for_the_audit():
    """Angel, reading the first version on the shift report: "this has my name in there, this
    seems really confusing to me". He was right, twice over.

    Everything structural — forced, never counted, by whom, when — is ALREADY in columns and in
    audit_log. Repeating it in prose produced a wall of text nobody can parse at the moment they
    need it, which is the opposite of what §5 was for. And a developer's name means nothing to
    an auditor or to Leandra: attribution belongs in reconciled_by, not in a sentence.

    So the note stays short, in shop language, and carries only what a human typed."""
    import io
    router = io.open("src/routes/pos_router.py", encoding="utf-8").read()
    start = router.index("async def force_close_cash_box(")
    end = router.index("def _shift_report(")
    note = router[start:end]
    assert "Never counted" in note
    assert "{username}" not in note.split("variance_note")[1][:400], \
        "no names in the note — attribution is a column, not prose"
    assert "counted_verified = False" in note or "counted_verified" in note


def test_the_report_shows_a_badge_from_the_COLUMN_not_the_prose():
    """A forced close shows counted == expected and variance 0.00 — which reads as 'the drawer
    balanced'. The badge that stops that must key off counted_verified, so it still works when
    somebody writes a short or empty note."""
    import io
    screen = io.open("src/templates/pos/shift.html", encoding="utf-8").read()
    assert "report.counted_verified === false" in screen, \
        "the not-counted badge must read the column, not search the note text"


def test_a_forced_close_never_shows_a_GREEN_BALANCED_VERDICT():
    """Angel's screenshot, mid-testsheet: pam's uncounted box rendered

        ✅ Balanced within tolerance
        +CHF 0.00

    in green, directly above the note saying nobody had counted it. The banner keyed off
    `within_tolerance`, and a forced close sets counted == expected, so within_tolerance is
    True — truthfully, and misleadingly.

    No count means there is nothing to have a verdict ABOUT. counted_verified is checked FIRST
    and the green path is not reachable when it is false."""
    import io
    screen = io.open("src/templates/pos/shift.html", encoding="utf-8").read()
    verdict = screen[screen.index("rounded-lg p-4 mb-4 text-center"):]
    verdict = verdict[:verdict.index("<table")]
    assert "counted_verified === false" in verdict, "the verdict must consult the column first"
    green = verdict.index("shift.balanced")
    guard = verdict.index("counted_verified === false")
    assert guard < green, "the not-counted branch must come BEFORE the balanced branch"
    assert "bg-green-100" in verdict and "bg-amber-100" in verdict
    # and the green class must be inside the branch that only runs when it IS verified
    assert verdict.index("bg-amber-100") < verdict.index("bg-green-100")


def test_a_setting_nobody_can_set_is_not_a_setting():
    """Angel, running the testsheet: "could not find this setting maybe not needed now?"

    cash_box_float existed in the model, the migration, and the API schema — and on no screen.
    So the §6 guard could only ever be configured by curl, which means in practice never, which
    means the guard was dead on arrival for a real shop.

    Every cash-box setting the API accepts must appear on the settings screen, and the screen
    must both load and send it."""
    import io
    schema = io.open("src/schemas/pos_schema.py", encoding="utf-8").read()
    screen = io.open("src/templates/pos/settings.html", encoding="utf-8").read()
    upd = schema[schema.index("class StoreSettingsUpdate"):schema.index("class StoreSettingsRead")]
    fields = [f for f in re.findall(r"^\s{4}(cash_\w+):", upd, re.M)]
    assert fields, "no cash_* settings found — did the schema move?"
    for f in fields:
        assert f"form.{f}" in screen, f"{f} is accepted by the API but has no field on the screen"
        assert f"{f}:" in screen, f"{f} is never sent in the save payload"


def test_a_blank_baseline_means_unconfigured_not_zero():
    """An empty box must leave the guard SILENT, not assert that the cash box should hold
    nothing — which would make every count 'wildly off' and question every morning."""
    import io
    screen = io.open("src/templates/pos/settings.html", encoding="utf-8").read()
    assert "cash_box_float === '' || F.cash_box_float == null ? null" in screen
    assert baseline_check("600.00", None)["off_baseline"] is False


def test_an_expected_flow_step_does_not_shout_in_the_console():
    """Angel, mid-testsheet, seeing a red `API call failed: Error {"code":"opening_variance"…}`:
    "think it broken got a error in webconsole tigs ... this seems super complicated now".

    Nothing was broken — that was the morning reveal working exactly as designed. But the
    morning count is SUPPOSED to come back "add a note" or "is that right?", and a red console
    line reads as a bug no matter what the page does next.

    Anything carrying a structured `code` is expected and handled by its caller."""
    import io
    base = io.open("src/templates/pos/base.html", encoding="utf-8").read()
    handler = base[base.index("} catch (error) {"):]
    handler = handler[:handler.index("},")]
    assert "error.detail && error.detail.code" in handler
    assert "console.info" in handler and "console.error" in handler, \
        "handled codes log quietly; everything else must still shout"


def test_the_shift_log_shows_EVERYONE_like_the_summary_above_it():
    """Standing rule 6, failed by me and caught by Angel in minutes.

    The shift report read "Transactions 2" (both cashiers, correct) while the itemised Daily
    Sales Log underneath listed 1 — because `shift_transactions` still carried
    `cashier_id == shift.user_id`, the exact twin of the filter I had removed from
    `_shift_sales`. I fixed one query and never went looking for the other."""
    import io
    router = io.open("src/routes/pos_router.py", encoding="utf-8").read()
    start = router.index("async def shift_transactions(")
    seg = router[start:start + 2500]
    assert "cashier_id == shift.user_id" not in seg, \
        "the itemised log must sum everyone, like the summary it sits under"


def test_a_named_reason_is_enough_on_its_own():
    """The skim Angel recorded never existed: he picked the movement, typed the amount, pressed
    Record — and a 400 for a blank free-text reason landed in a banner at the top of a page he
    had scrolled past. Nothing saved, nothing looked wrong.

    A named code IS a reason. Only 'other' (or no code at all) still needs words."""
    import io
    router = io.open("src/routes/pos_router.py", encoding="utf-8").read()
    start = router.index("async def shift_paid_in_out(")
    seg = router[start:router.index("async def current_cash_shift(")]
    assert "_LABELS" in seg and "to the safe" in seg
    # the blank-reason refusal must be reachable ONLY when the code cannot speak for itself
    assert 'if code in _LABELS:' in seg


def test_the_paid_outcome_is_shown_where_the_button_is():
    """A page-top banner is invisible to somebody who has scrolled down to press Record."""
    import io
    screen = io.open("src/templates/pos/shift.html", encoding="utf-8").read()
    assert "paidMsg" in screen and "paidOk" in screen
