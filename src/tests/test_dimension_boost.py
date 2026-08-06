"""`62mm` is a size too — but only for RANKING, never for the dedup filter.

2026-08-06. Measured on the grinder shelf: **165 of 192 names carry a diameter in mm**
("Grinder Alu CNC 4teilig mit Sieb 62mm Rasta"). It is the best-covered spec on that shelf and the
first thing a customer asks — and `_query_size_regex` did not know `mm` at all, because it was built
for PACK sizes (g / ml / stk / er).

What that cost, proved on prod. Searching **"62 mm"** (with a space, as a person types it) matched
260 rows and the top four were a DynaVap condenser, a skateboard, and two **6mm** filters — not one
62mm grinder. With the boost the top four are all 62mm grinders.

⚠️ **The safety property these tests exist to protect.** `_SIZE_Q_RE` has TWO users:

  * `_query_size_regex` → an `ORDER BY`. Can reorder. **Cannot hide anything.**
  * `_product_size`     → the dedup guard, which FILTERS:
        `if same_size_only and want and not _same_size(want, _product_size(matched)): continue`
    and `_same_size` returns **False when either side is unknown**.

So teaching the SHARED regex about mm would make a query for "50mm" silently DROP the 27 grinders
whose names state no diameter. That is the 2026-07-31 bug exactly — *"a filter downstream of a fix
can quietly undo it"* (the pc./Stk. size table). Hence a separate `_DIM_Q_RE` used only by the
ranker. **Sort here, filter nowhere.**
"""
import pytest

from src.routes.pos_router import _product_size, _query_code_exact, _query_size_regex


@pytest.mark.parametrize("q,expect_num,expect_unit", [
    ("62mm", "62", "mm"),
    ("62 mm", "62", "mm"),           # ← the one that was broken: a space, as a person types it
    ("50mm", "50", "mm"),
    ("5.9mm", r"5\.9", "mm"),        # Purize mouthpieces are 5.9mm — decimal must survive
    ("5,9mm", r"5\.9", "mm"),        # German comma normalises to a dot
    ("12cm", "12", "cm"),            # cm too — bongs and pipes are sized in cm
    ("grinder 62mm", "62", "mm"),    # a real two-word till query
])
def test_a_dimension_is_recognised_for_ranking(q, expect_num, expect_unit):
    rx = _query_size_regex(q)
    assert rx is not None, f"{q!r} produced no size regex"
    assert expect_num in rx and expect_unit in rx, rx


@pytest.mark.parametrize("q,unit", [
    ("2g", "gr?"), ("10ml", "ml"), ("250er", "er"), ("34stk", "stk"),
])
def test_pack_sizes_are_untouched(q, unit):
    """Regression guard: adding dimensions must not disturb the pack-size path that already worked."""
    rx = _query_size_regex(q)
    assert rx is not None and unit in rx, rx


def test_pack_size_wins_when_a_query_has_both():
    """`_SIZE_Q_RE` is tried first on purpose. '50er 62mm' is a pack of 50, and the pack size is the
    stronger signal — it is what the dedup guard and the shelf both key on."""
    rx = _query_size_regex("50er 62mm")
    assert "er" in rx and "mm" not in rx, rx


# ---------------------------------------------------------------- the safety property

def test_DEDUP_is_still_blind_to_mm():
    """🔴 THE LOAD-BEARING TEST. `_product_size` feeds a FILTER whose `_same_size` treats unknown as
    a mismatch. If it learned mm, a search for "50mm" would drop every grinder that does not state a
    diameter — 27 of 192. It must keep returning '' for a diameter."""
    assert _product_size("Grinder Alu CNC 4teilig mit Sieb 62mm Rasta") == ""
    assert _product_size("Grinder Alu CNC 3teilig 62mm silber") == ""
    assert _product_size("Aktivkohlefilter actiTube Slim 6mm 50stk") == "50stk"   # pack size still read


def test_two_grinders_of_different_diameter_are_not_split_by_the_dedup_guard():
    """The consequence of the above, stated as behaviour: both sides come back '' — equal — so the
    guard does not filter either one out. Unknown is not treated as a value."""
    a = _product_size("Grinder Alu CNC 4teilig mit Sieb 62mm Rasta")
    b = _product_size("CNC Grinder Schwarz 4-Teilig Klein")
    assert a == b == ""


def test_the_code_ranker_does_not_claim_a_dimension():
    """Three rankers read the same raw query — code, size, name. A dimension must belong to exactly
    one of them, or the ORDER BY carries two competing CASEs over the same string."""
    for q in ("62mm", "62 mm", "5.9mm", "12cm"):
        assert _query_code_exact(q) is None, q
        assert _query_size_regex(q) is not None, q
