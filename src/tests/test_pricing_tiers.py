"""BL-26 tier pricing — unit tests for the break-selection + validation helpers."""
from decimal import Decimal

import pytest

from src.services.pricing import tier_unit_price, tier_line_total, validate_price_tiers

# The real GIZEH tubes ladder from artemisluzern.ch.
GIZEH = [
    {"min_qty": 1, "unit_price": "4.90"},
    {"min_qty": 10, "unit_price": "4.50"},
    {"min_qty": 50, "unit_price": "4.30"},
    {"min_qty": 100, "unit_price": "3.90"},
]


@pytest.mark.parametrize("qty,price,brk", [
    (1, "4.90", False),    # base tier — not a volume break
    (5, "4.90", False),    # still base, below the 10 break
    (9, "4.90", False),
    (10, "4.50", True),    # first real break
    (49, "4.50", True),
    (50, "4.30", True),
    (99, "4.30", True),
    (100, "3.90", True),
    (500, "3.90", True),   # above the top tier → top price holds
])
def test_gizeh_ladder(qty, price, brk):
    up, volume_break = tier_unit_price(GIZEH, Decimal("4.90"), qty)
    assert up == Decimal(price)
    assert volume_break is brk


def test_no_tiers_falls_back_to_base():
    assert tier_unit_price(None, Decimal("2.50"), 100) == (Decimal("2.50"), False)
    assert tier_unit_price([], Decimal("2.50"), 100) == (Decimal("2.50"), False)


def test_base_price_quantized():
    up, brk = tier_unit_price([], Decimal("2.5"), 1)
    assert up == Decimal("2.50")


def test_malformed_tiers_ignored_not_crash():
    bad = [{"min_qty": None, "unit_price": "1.00"}, {"min_qty": 10}, {"nope": 1}]
    up, brk = tier_unit_price(bad, Decimal("4.90"), 20)
    assert up == Decimal("4.90") and brk is False


def test_validate_normalizes_and_sorts():
    out = validate_price_tiers([
        {"min_qty": 100, "unit_price": "3.9"},
        {"min_qty": 1, "unit_price": 4.9},
        {"min_qty": 10, "unit_price": "4.50"},
    ])
    assert [r["min_qty"] for r in out] == [1, 10, 100]
    assert out[0]["unit_price"] == "4.90"      # quantized to cents, stored as string
    assert out[2]["unit_price"] == "3.90"


def test_validate_empty_clears():
    assert validate_price_tiers(None) == []
    assert validate_price_tiers([]) == []


def test_validate_requires_first_tier_min_qty_1():
    with pytest.raises(ValueError):
        validate_price_tiers([{"min_qty": 10, "unit_price": "4.50"}])
    # per_unit is the default → same rule when passed explicitly
    with pytest.raises(ValueError):
        validate_price_tiers([{"min_qty": 3, "unit_price": "4.00"}], mode="per_unit")


def test_validate_bundle_allows_first_break_at_qty_2_plus():
    # Felix's real case: a bundle "3 for 8.00, 10 for 25.00" has NO qty-1 row (base = product price).
    # The old code rejected this ("first must be min_qty 1") — the editor-save bug. Now it's valid.
    out = validate_price_tiers(
        [{"min_qty": 3, "unit_price": "8.00"}, {"min_qty": 10, "unit_price": "25.00"}],
        mode="bundle",
    )
    assert [r["min_qty"] for r in out] == [3, 10]
    assert out[0]["unit_price"] == "8.00"


def test_validate_bundle_drops_qty_1_row():
    # BL-31: a qty-1 "bundle" is just the base price — FOLD it away, don't dead-end the save.
    # A lone qty-1 row → tiers clear (flat price).
    assert validate_price_tiers([{"min_qty": 1, "unit_price": "1.40"}], mode="bundle") == []
    # Mixed: the real pack survives, the qty-1 base row is dropped.
    out = validate_price_tiers(
        [{"min_qty": 1, "unit_price": "1.40"}, {"min_qty": 3, "unit_price": "4.00"}], mode="bundle")
    assert [r["min_qty"] for r in out] == [3]
    assert out[0]["unit_price"] == "4.00"


def test_validate_rejects_duplicate_and_negative():
    with pytest.raises(ValueError):
        validate_price_tiers([{"min_qty": 1, "unit_price": "1.00"}, {"min_qty": 1, "unit_price": "2.00"}])
    with pytest.raises(ValueError):
        validate_price_tiers([{"min_qty": 1, "unit_price": "-1.00"}])


# --- BUNDLE mode ("N for X total") — Felix's real case: Gizeh 1.40, "3 for 4.00, 10 for 12.00" -----
BUNDLE = [
    {"min_qty": 1, "unit_price": "1.40"},
    {"min_qty": 3, "unit_price": "4.00"},
    {"min_qty": 10, "unit_price": "12.00"},
]


@pytest.mark.parametrize("qty,line,brk", [
    (1, "1.40", False),    # base
    (2, "2.80", False),    # still base tier (1)
    (3, "4.00", True),     # the "3 for 4.00" pack — line is EXACTLY 4.00 (line-level rounding)
    (4, "5.33", True),     # 4 × (4.00/3)=5.333 → 5.33
    (5, "6.67", True),     # 5 × 1.333 → 6.67
    (9, "12.00", True),    # 9 × 1.333 → 12.00
    (10, "12.00", True),   # the "10 for 12.00" pack — exact
    (20, "24.00", True),   # 20 × (12/10)=1.20 → 24.00
])
def test_bundle_line_totals(qty, line, brk):
    assert tier_line_total(BUNDLE, Decimal("1.40"), qty, mode="bundle") == Decimal(line)
    _, volume_break = tier_unit_price(BUNDLE, Decimal("1.40"), qty, mode="bundle")
    assert volume_break is brk


def test_bundle_vs_per_unit_differ_on_same_data():
    # Same rows, different meaning: bundle "3 for 4.00" = 4.00 total.
    #
    # UPDATED 2026-07-31. This test used to assert that per_unit on the SAME data charged
    # 12.00 — "a price hike… exactly the bug Felix hit" — i.e. it documented the hazard as
    # expected behaviour instead of preventing it. Then TAM-21669 turned up live with exactly
    # that data and tier_mode NULL, one sale away from charging CHF 12.00 for three packs of
    # papers that cost CHF 4.20 flat.
    #
    # A quantity break can never cost more than buying singles, so mis-flagged data is now
    # re-read as a pack total rather than rung up. Setting tier_mode is still the correct fix;
    # this is the net beneath it.
    assert tier_line_total(BUNDLE, Decimal("1.40"), 3, mode="bundle") == Decimal("4.00")
    assert tier_line_total(BUNDLE, Decimal("1.40"), 3, mode="per_unit") == Decimal("4.00")
    # …and never worse than the flat price, whichever way it is read.
    assert tier_line_total(BUNDLE, Decimal("1.40"), 3, mode="per_unit") <= Decimal("4.20")


def test_per_unit_default_unchanged():
    # No mode arg → per_unit (back-compat): GIZEH ladder still per-unit each.
    assert tier_line_total(GIZEH, Decimal("4.90"), 10) == Decimal("45.00")   # 10 × 4.50
    assert tier_unit_price(GIZEH, Decimal("4.90"), 10)[0] == Decimal("4.50")


# ═════════════════════════════════════════════════════════════════════════════════════════
# A QUANTITY BREAK CAN NEVER COST MORE THAN BUYING ONE.
#
# Found live 2026-07-31 on TAM-21669 "Gizeh King Size" — a product Angel was about to sell:
#
#     base CHF 1.40 · tiers [{3: 4.00}, {10: 12.00}] · tier_mode NULL
#
# The till falls back to per_unit when tier_mode is unset, so three packs would have rung up
# at 3 × 4.00 = CHF 12.00 against a flat price of CHF 4.20, and ten at CHF 120.00 against
# 14.00. A 3x overcharge on a live product in a live shop.
#
# The data is plainly bundle-shaped and simply never had its mode recorded. Rather than guess
# intent, enforce the invariant every quantity break in the world obeys: buying more must not
# raise the unit price. Both recovery branches move money toward the CUSTOMER, which is the
# only safe direction for a guess about price.
# ═════════════════════════════════════════════════════════════════════════════════════════
from decimal import Decimal
from src.services.pricing import tier_unit_price, tier_line_total

_GIZEH = [{"min_qty": 1, "unit_price": "1.40"},
          {"min_qty": 3, "unit_price": "4.00"},
          {"min_qty": 10, "unit_price": "12.00"}]


def test_the_live_overcharge_is_gone():
    """Three packs must not cost CHF 12.00 when one costs CHF 1.40."""
    assert tier_line_total(_GIZEH, "1.40", 3, "per_unit") == Decimal("4.00")
    assert tier_line_total(_GIZEH, "1.40", 10, "per_unit") == Decimal("12.00")


def test_it_never_charges_more_than_the_flat_price():
    """The invariant, stated directly: no quantity is worse off than buying singles."""
    for qty in range(1, 15):
        line = tier_line_total(_GIZEH, "1.40", qty, "per_unit")
        assert line <= Decimal("1.40") * qty, f"qty {qty} charged {line}"


def test_an_explicit_bundle_still_behaves_exactly_as_before():
    assert tier_line_total(_GIZEH, "1.40", 3, "bundle") == Decimal("4.00")
    assert tier_line_total(_GIZEH, "1.40", 10, "bundle") == Decimal("12.00")


def test_a_genuine_per_unit_discount_is_untouched():
    """The guard must not disturb correct data: descending per-unit tiers are the normal case."""
    tiers = [{"min_qty": 1, "unit_price": "3.90"},
             {"min_qty": 10, "unit_price": "3.70"},
             {"min_qty": 50, "unit_price": "3.50"}]
    assert tier_unit_price(tiers, "3.90", 10, "per_unit")[0] == Decimal("3.70")
    assert tier_unit_price(tiers, "3.90", 50, "per_unit")[0] == Decimal("3.50")
    assert tier_line_total(tiers, "3.90", 50, "per_unit") == Decimal("175.00")


def test_nonsense_in_either_reading_falls_back_to_the_flat_price():
    """A tier that is worse than base however you read it is bad data, not a price."""
    tiers = [{"min_qty": 2, "unit_price": "99.00"}]
    unit, brk = tier_unit_price(tiers, "1.40", 2, "per_unit")
    assert unit == Decimal("1.40") and brk is False
    assert tier_line_total(tiers, "1.40", 2, "per_unit") == Decimal("2.80")


def test_below_the_first_break_nothing_changes():
    assert tier_line_total(_GIZEH, "1.40", 1, "per_unit") == Decimal("1.40")
    assert tier_line_total(_GIZEH, "1.40", 2, "per_unit") == Decimal("2.80")


# ── A GUESS MAY ONLY GO SO FAR ───────────────────────────────────────────────────────────
#
# 2026-08-21, found on the live shop while auditing every tiered product with the till's own
# pricing function. `Gizeh Rolls Slim Pink` — base CHF 2.90, tier {min_qty 10, "3.10"},
# tier_mode per_unit. 3.10 is above base, so the bundle-rescue re-read it as "10 for 3.10"
# and charged CHF 0.31 each. Ten packs rang up at 3.10; nineteen at 5.89.
#
# The rescue exists for good reason and stays. What was wrong was the claim in its comment
# that moving money toward the customer is "the only safe direction for a guess" — without a
# bound it is simply the other loss.

def test_a_slightly_high_per_unit_tier_is_not_read_as_a_giveaway():
    """The live bug: base 2.90 with a 3.10 tier must NOT become 0.31 each."""
    tiers = [{"min_qty": 1, "unit_price": "3.50"}, {"min_qty": 10, "unit_price": "3.10"},
             {"min_qty": 20, "unit_price": "2.50"}, {"min_qty": 60, "unit_price": "2.40"}]
    base = Decimal("2.90")
    assert tier_line_total(tiers, base, 10, mode="per_unit") == Decimal("29.00")
    assert tier_line_total(tiers, base, 19, mode="per_unit") == Decimal("55.10")
    # and buying more must still never cost less in total than buying fewer at that rung
    assert tier_line_total(tiers, base, 10, mode="per_unit") > \
           tier_line_total(tiers, base, 9, mode="per_unit")


def test_the_believable_guess_still_happens():
    """"3 for 5.00" written as per_unit against a base of 2.00 is a real deal — keep rescuing it."""
    tiers = [{"min_qty": 1, "unit_price": "2.00"}, {"min_qty": 3, "unit_price": "5.00"}]
    assert tier_line_total(tiers, Decimal("2.00"), 3, mode="per_unit") == Decimal("5.00")
    assert tier_line_total(tiers, Decimal("2.00"), 6, mode="per_unit") == Decimal("10.00")


def test_a_genuine_deep_discount_is_untouched():
    """Tiers at or below base never reach the guess, however deep they go."""
    tiers = [{"min_qty": 1, "unit_price": "1.50"}, {"min_qty": 500, "unit_price": "0.60"}]
    assert tier_line_total(tiers, Decimal("1.50"), 500, mode="per_unit") == Decimal("300.00")


def test_an_explicit_bundle_is_never_second_guessed():
    """tier_mode='bundle' means what it says, however cheap — the operator was explicit."""
    tiers = [{"min_qty": 10, "unit_price": "3.10"}]
    assert tier_line_total(tiers, Decimal("2.90"), 10, mode="bundle") == Decimal("3.10")
