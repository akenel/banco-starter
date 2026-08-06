"""Typing an ARTICLE NUMBER at the till must land on that exact product.

2026-08-06. Angel, looking for a way to sell products that have **no barcode** — grinders, bongs,
trays — without sticking anything on the goods, because Felix refused that:

    "Every grinder already has a 4-5 digit number unique in the system…
     if you type 1002 well then good luck."

Both halves were right, and both were measured on prod before this was written:

  * the FULL 5 digits returned **exactly one product, 300 times out of 300**
  * a bare **4-digit** type hit **15 products** at worst, and was unique only **30%** of the time

So typing the number is a genuinely fast route to a no-barcode sale — but the search ranked numeric
hits by `relevance`, which is a name+description trigram, and **a number never matches a name**. The
order was noise. On real prod data, searching `1166` put the exact `TAM-1166` (*Messingsieb rund
20mm*) **last of four**, under `TAM-11666`, `TAM-24116` and `TAM-21166`.

These tests pin the *detector*. The ranking itself is SQL and was proved against prod:
`TAM-1166` moved from 4th to 1st.
"""
import pytest

from src.routes.pos_router import _query_code_exact, _query_size_regex


@pytest.mark.parametrize("q,expected", [
    ("12815", "12815"),                  # the bare number a cashier types
    ("TAM-12815", "12815"),              # the whole SKU off a shelf label
    ("tam-12815", "12815"),              # lowercase — a cashier is not careful
    ("tam12815", "12815"),               # no separator
    ("SKU_12345", "12345"),              # underscore separator
    ("  10027  ", "10027"),              # padded — trailing space from a scanner or a thumb
    ("1002", "1002"),                    # 4-digit: still a code, still ranked exact-first
    ("LZ-3661075283438", "3661075283438"),   # a long non-TAM SKU
    ("123", "123"),                      # the 3-digit floor, inclusive
])
def test_recognises_an_article_number(q, expected):
    assert _query_code_exact(q) == expected


@pytest.mark.parametrize("q", [
    "62",            # ⚠️ a SIZE, not a code — 62mm grinders exist and 2-digit codes barely do
    "50",            # same
    "2g", "62mm", "10ml",          # sizes with units
    "grinder", "Grinder 50mm",     # words, and a word + size
    "", "   ", None,               # nothing
    "TAM-", "abc",                 # a prefix with no number
    "12 815",                      # a space INSIDE the digits is not one number
])
def test_ignores_everything_that_is_not_an_article_number(q):
    assert _query_code_exact(q) is None


def test_the_two_digit_floor_is_deliberate():
    """A 2-digit query is far more likely a size ('62' for a 62mm grinder) than a code, and only
    5 of the 5,099 TAM SKUs carry fewer than 3 digits. The floor costs almost nothing and stops
    the code ranking fighting the SIZE ranking over the same string."""
    assert _query_code_exact("62") is None
    assert _query_code_exact("623") == "623"


def test_it_does_not_steal_queries_the_size_ranker_wants():
    """Both rankers read the raw query, so a size must never be claimed as a code — otherwise a
    '2g' search would sort by a nonexistent article instead of floating 2g products."""
    for q in ("2g", "10ml", "34stk"):
        assert _query_code_exact(q) is None, q
        assert _query_size_regex(q) is not None, q


def test_mm_is_not_a_pack_size_and_that_is_fine_here():
    """Noted while writing these: `_query_size_regex` handles PACK sizes (g / ml / stk) and does
    NOT treat `mm` as one — so '62mm' gets no size boost. That is a gap for GRINDERS specifically,
    where the diameter in mm is the size a customer asks for ('Grinder … 62mm Rasta').

    It is filed rather than fixed here, because it belongs to the size ranker, not the code
    ranker. What matters for THIS change is only that the two never fight over the same string:
    '62mm' is claimed by neither, so nothing regresses."""
    assert _query_size_regex("62mm") is None
    assert _query_code_exact("62mm") is None


def test_a_pure_number_is_not_treated_as_a_size():
    """The mirror of the above — '12815' has no unit, so the size ranker leaves it alone and the
    code ranker takes it. If both claimed it the ORDER BY would carry two competing CASEs."""
    assert _query_size_regex("12815") is None
    assert _query_code_exact("12815") == "12815"
