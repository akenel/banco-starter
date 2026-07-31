"""BL-128 #2 — size-token boost regex (rank the exact size to the top of till search).

The query "lemon haze 2g" must float the 2g variant above the 10g. This locks the query→regex
extraction (digit-boundary safe: 2g never matches 12g/20g/2mg/2ml). The ORDER BY behaviour itself
was proven read-only on prod (Local Weed Lemon Haze 2g floats; 2ml/25gr do not).
"""
from src.routes.pos_router import _query_size_regex, _product_size


def test_product_size_normalized():
    # BL-128 #3 — the dedup guard only treats SAME-size items as duplicates.
    assert _product_size("Local Weed Lemon Haze 2g") == "2g"
    assert _product_size("Lemon Haze 2gr") == "2g"          # gr → g
    assert _product_size("Wonderhaze CBD 10g") == "10g"
    assert _product_size("CBD Oil 10ml") == "10ml"
    assert _product_size("Blunt Wraps 34 Stk") == "34stk"   # Stück family
    assert _product_size("Rolling Papers 250er") == "250er"


def test_product_size_none_when_absent():
    assert _product_size("BIC Feuerzeug mini") == ""
    assert _product_size("King Size Grinder") == ""
    assert _product_size("") == ""


def test_two_g_is_not_ten_g():
    # the exact reason the guard exists: 2g must never equal 10g
    assert _product_size("Lemon Haze 2g") != _product_size("Lemon Haze 10g")


def test_size_extracted_from_query():
    assert _query_size_regex("lemon haze 2g") == r"\y2\s?gr?\y"
    assert _query_size_regex("lemon haze 10g") == r"\y10\s?gr?\y"
    assert _query_size_regex("cbd oil 10ml") == r"\y10\s?ml\y"
    assert _query_size_regex("nicotine 20mg") == r"\y20\s?mg\y"


def test_no_size_no_boost():
    for q in ("grinder", "king size", "bic lighter", "", "lemon haze"):
        assert _query_size_regex(q) is None


def test_decimal_dot_escaped():
    # 0.5g → the decimal dot is escaped so the PG regex is literal, not any-char
    assert _query_size_regex("hash 0.5g") == r"\y0\.5\s?gr?\y"


# ─────────────────────────────────────────────────────────────────────────────────────────
# 2026-07-31 — the count unit is LANGUAGE-SPECIFIC, and forgetting that undid a fix.
#
# The packet says "1 pc.", the wholesale row says "1 Stk." — one quantity, two languages.
# The table knew `pcs` but not the singular `pc`, so the English name produced NO size token
# while the German produced `1stk`. The dedup guard's same-size rule then discarded the pair
# AFTER the DE<->EN folding had correctly scored it 0.857.
#
# Found by running the live endpoint against the exact pair it exists to catch and getting
# an empty list back. A filter downstream of a fix can quietly undo it.
# ─────────────────────────────────────────────────────────────────────────────────────────

def test_pc_and_stk_are_the_same_size():
    """The pair that cost Angel two hours of re-creating products that already existed."""
    en = _product_size('Blow Pre-built CBD Joint Pure "V1" 1 pc. black')
    de = _product_size('Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz')
    assert en == de == "1stk"


def test_every_way_of_saying_a_piece_collapses_to_one_token():
    for text in ("3 pc", "3 pc.", "3 pcs", "3 pcs.", "3 Stk", "3 Stk.",
                 "3 Stück", "3 Stueck", "3 pieces", "3 piece"):
        assert _product_size(f"Some Product {text} black") == "3stk", text


def test_the_trailing_dot_does_not_hide_a_size():
    """'1 Stk.' and '1 pc.' both end in a period — a regex anchored on \\b alone reads the dot
    as the boundary only by luck, so it is pinned here."""
    assert _product_size("Papers 50 Blatt.") == "50blatt"
    assert _product_size("Tips 100 pcs.") == "100stk"


def test_piece_units_still_do_not_collide_with_other_units():
    """`pc` must not start matching inside unrelated words or swallow real units."""
    assert _product_size("Grinder 4pc") == "4stk"
    assert _product_size("CBD Oil 10ml") == "10ml"
    assert _product_size("Lemon Haze 2g") == "2g"
    assert _product_size("Preroll pcs") == ""          # a unit with no number is not a size


def test_the_query_boost_regex_treats_pc_and_stk_as_one_family():
    """The same fix must reach till SEARCH ranking, not only the dedup guard — a customer
    typing '100 pc' should float the '100 Stk.' row exactly as '100 pcs' already did."""
    rx = _query_size_regex("tips 100 pc")
    assert rx is not None
    for unit in ("stk", "stück", "pcs", "pc"):
        assert unit in rx


# ─────────────────────────────────────────────────────────────────────────────────────────
# German counts a pack two ways, and an English packet a third. "200er Hülsen", "200 Stk."
# and "200 pcs" are the same 200 things — but the matcher compared the tokens literally and
# discarded the right row. Found 2026-07-31 while wiring alias search: the catalogue's
# "Zigaretten-Hülsen 200er Gizeh Air Plus" was invisible to "Gizeh Air Plus Cigarette Tubes
# 200 pcs", its own recorded English name.
#
# Narrow on purpose: only within the COUNT family. 2g must never equal 2ml.
# ─────────────────────────────────────────────────────────────────────────────────────────
from src.routes.pos_router import _same_size


def test_er_and_stk_are_the_same_count():
    assert _same_size("200er", "200stk") is True
    assert _same_size("34stk", "34er") is True


def test_the_same_token_is_obviously_the_same():
    assert _same_size("2g", "2g") is True


def test_different_numbers_are_never_the_same():
    assert _same_size("200er", "100stk") is False
    assert _same_size("34stk", "50stk") is False


def test_it_never_crosses_unit_families():
    """The whole reason the size rule exists: 2g is not 2ml and never becomes it."""
    assert _same_size("2g", "2ml") is False
    assert _same_size("250er", "250g") is False
    assert _same_size("10ml", "10stk") is False


def test_an_unknown_side_is_not_a_match():
    assert _same_size("200er", "") is False
    assert _same_size("", "200er") is False
