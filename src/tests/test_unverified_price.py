"""The placeholder-price flag — Catalog Health's only MONEY check.

2026-08-05. Angel ran a shelf-intake session, did not know the shelf price for a run of products,
and typed **99.00** deliberately: a number wrong enough that a cashier would query it at the till.
Sound reasoning. What failed is that **nothing in Banco knew it was a sentinel** — 74 products sat
at 99.00, all scannable, and every gap detector stayed silent because they all ask *"what is
MISSING?"* and a placeholder is not missing.

It is the 0.00 doctrine wearing a plausible number, and worse: 0.00 gets noticed, 99.00 does not.

These tests pin the two things that are easy to get wrong later:
  1. the sentinel set is EXACTLY {99.00, 999.99} — not "anything suspicious", which would guess
  2. `price` is filterable but is **NOT** part of `_bench_gap_clause()`, the four-gap completeness
     definition. Folding a money flag into the completeness bar would silently move every counter
     the shop is already working against.
"""
from decimal import Decimal

from src.routes.pos_router import (
    UNVERIFIED_PRICES,
    _BENCH_GAP_KINDS,
    _bench_gap_clause,
    _bench_gap_expr,
)


def test_sentinels_are_exactly_the_two_documented_values():
    """99.00 because the shop already has 74 of them; 999.99 because it is the better flag."""
    assert set(UNVERIFIED_PRICES) == {Decimal("99.00"), Decimal("999.99")}


def test_sentinels_are_decimal_not_float():
    """Money is Decimal everywhere in this codebase. A float 99.0 would not compare equal to a
    NUMERIC(10,2) column reliably, and the check would quietly match nothing."""
    assert all(isinstance(p, Decimal) for p in UNVERIFIED_PRICES)


def test_price_is_a_filterable_gap_kind():
    """It must be in _BENCH_GAP_KINDS or `/pos/cleanup?mode=bench&gap=price` falls back to the
    full four-gap bench — the card would link somewhere that does not answer the question."""
    assert "price" in _BENCH_GAP_KINDS


def test_price_expr_is_not_the_fallback():
    """An unknown kind falls back to the whole bench clause. If `price` ever stopped being
    recognised, the count would silently become "every unfinished product" — a number that looks
    plausible and is wrong. Pin that it is its own expression."""
    assert str(_bench_gap_expr("price")) != str(_bench_gap_clause())


def test_price_expr_mentions_both_sentinels():
    compiled = str(_bench_gap_expr("price").compile(compile_kwargs={"literal_binds": True}))
    assert "99.00" in compiled
    assert "999.99" in compiled


def test_price_is_NOT_part_of_the_completeness_bench():
    """The load-bearing one. `_bench_gap_clause()` defines "unfinished" for the bench, the
    shelf-intake stub list and the workbook export. A placeholder price is a MONEY bug, not a
    master-data completeness gap — adding it here would move counters the shop is mid-way through
    working against, and would relabel a priced-but-unverified row as "incomplete"."""
    clause = str(_bench_gap_clause().compile(compile_kwargs={"literal_binds": True}))
    assert "99.00" not in clause
    assert "999.99" not in clause


def test_unknown_kind_still_falls_back_to_the_bench():
    """Regression guard on the existing contract — adding `price` must not have broken it."""
    assert str(_bench_gap_expr("nonsense")) == str(_bench_gap_clause())
    assert str(_bench_gap_expr(None)) == str(_bench_gap_clause())


def test_the_original_four_gaps_still_resolve_to_themselves():
    """Standing rule 6 — when you touch one thing, check its siblings."""
    for kind in ("photo", "description", "category", "cost"):
        assert str(_bench_gap_expr(kind)) != str(_bench_gap_clause()), kind
