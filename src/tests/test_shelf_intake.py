"""Shelf intake — parsing a scanner gun's offline dump.

The gun types its cache out as KEYSTROKES, so this parser meets whatever the gun's terminator
setting and the browser between them produce. Every case below is a shape that can genuinely
arrive, not a hypothetical.

The rule under test throughout: **nothing is silently dropped.** A shelf that looks finished
and is not is the exact failure the whole workflow exists to prevent — so junk is reported,
repeats are counted, and a short upload raises a warning rather than passing quietly.
"""
import pytest

from src.services.shelf_intake import (
    ParsedDump, gtin_check_digit_ok, parse_dump, dump_warnings,
)


# ─── the terminator the gun happens to be set to ────────────────────────────────────────

@pytest.mark.parametrize("raw", [
    "7640183261763\n7611841001236\n4001636098115",       # LF  — the usual
    "7640183261763\r\n7611841001236\r\n4001636098115",   # CRLF
    "7640183261763\r7611841001236\r4001636098115",       # CR only
    "7640183261763\t7611841001236\t4001636098115",       # TAB suffix
    "7640183261763 7611841001236 4001636098115",         # space suffix — one run-on line
    "\n\n7640183261763\n\n\n7611841001236\n4001636098115\n\n",   # blank lines everywhere
])
def test_every_terminator_yields_the_same_three_codes(raw):
    parsed = parse_dump(raw)
    assert [c.code for c in parsed.codes] == [
        "7640183261763", "7611841001236", "4001636098115"]
    assert parsed.total_tokens == 3


def test_order_is_the_order_you_walked_the_shop():
    """Preserved on purpose: the work list then reads shelf by shelf, and the operator can
    recognise where they were standing."""
    parsed = parse_dump("7640183261763\n4001636098115\n7611841001236")
    assert [c.code for c in parsed.codes] == [
        "7640183261763", "4001636098115", "7611841001236"]


# ─── repeats, junk, counting ────────────────────────────────────────────────────────────

def test_the_same_product_scanned_twice_is_counted_not_dropped():
    """Two facings on a shelf is normal. It is one product and two scans, and both numbers
    matter — the count is how a short upload gets caught."""
    parsed = parse_dump("7640183261763\n7611841001236\n7640183261763\n")
    assert parsed.unique == 2
    assert parsed.total_tokens == 3
    assert parsed.repeats == 1
    assert parsed.codes[0].count == 2


def test_junk_is_reported_never_swallowed():
    parsed = parse_dump("7640183261763\nx\n??\n7611841001236\n")
    assert [c.code for c in parsed.codes] == ["7640183261763", "7611841001236"]
    assert parsed.junk == ["x", "??"]
    assert "not code-shaped" in " ".join(dump_warnings(parsed))


def test_non_ean_codes_survive():
    """Shops carry Code128 SKUs and our own printed labels — a parser that only accepted 13
    digits would quietly discard half a real shelf."""
    parsed = parse_dump("TAM-21796\nLZ-4a9f2c\n2000000217963\n")
    assert [c.code for c in parsed.codes] == ["TAM-21796", "LZ-4a9f2c", "2000000217963"]


def test_empty_dump_is_not_an_error():
    parsed = parse_dump("")
    assert parsed.codes == [] and parsed.total_tokens == 0
    assert dump_warnings(parsed) == []


# ─── the count check — the reason the workflow says to ask the gun first ─────────────────

def test_a_short_upload_warns_and_says_do_not_clear_the_cache():
    parsed = parse_dump("7640183261763\n7611841001236\n")
    warnings = dump_warnings(parsed, expected=412)
    assert warnings and "incomplete" in warnings[0]
    assert "Daten hochladen" in warnings[0]        # the actual recovery, named
    assert "Do NOT clear" in warnings[0]


def test_a_matching_count_says_nothing():
    parsed = parse_dump("7640183261763\n7611841001236\n")
    assert dump_warnings(parsed, expected=2) == []


def test_the_count_compares_TOKENS_not_unique_codes():
    """The gun counts scans, not products. Comparing its number against our de-duplicated
    total would flag every shelf with two facings as a short upload."""
    parsed = parse_dump("7640183261763\n7640183261763\n7611841001236\n")
    assert parsed.unique == 2 and parsed.total_tokens == 3
    assert dump_warnings(parsed, expected=3) == []


# ─── check digits ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("code", [
    "7640183261763",   # Blow Pure Diesel — a real EAN off a real packet
    "2000000217963",   # our own minted Curaprox code (still a valid EAN-13)
    "4001636098115",
])
def test_real_gtins_pass(code):
    assert gtin_check_digit_ok(code) is True


def test_a_transposed_digit_is_caught():
    assert gtin_check_digit_ok("7640183261736") is False


def test_a_non_gtin_returns_none_not_false():
    """None and False mean different things, and conflating them would paint every Code128
    SKU as a suspected misread."""
    assert gtin_check_digit_ok("TAM-21796") is None
    assert gtin_check_digit_ok("123456") is None          # 6 digits — no GTIN length
    for c in parse_dump("TAM-21796\n").codes:
        assert c.checksum_ok is None


def test_bad_check_digits_warn_but_are_still_in_the_work_list():
    """A bad check digit is USUALLY a misread and occasionally a genuinely odd code. It is
    the operator's call — so it is flagged, and it stays."""
    parsed = parse_dump("7640183261736\n7640183261763\n")
    assert len(parsed.codes) == 2
    assert "bad GTIN check digit" in " ".join(dump_warnings(parsed))


# ─── the in-store prefix ────────────────────────────────────────────────────────────────

def test_a_2_prefix_code_is_flagged_as_someones_in_store_code():
    """GS1 restricted distribution. Ours, most likely — the 07-07 import minted 5,105 of them
    (CATALOG-IDENTITY.md). A real code on our shelf that exists on no packet anywhere."""
    parsed = parse_dump("2000000217963\n7640183261763\n")
    assert parsed.codes[0].is_internal is True
    assert parsed.codes[1].is_internal is False


def test_a_short_or_alpha_code_is_not_called_internal():
    parsed = parse_dump("TAM-21796\n20000002\n")
    assert all(c.is_internal is False for c in parsed.codes)


# ─── the gun's invisible junk ───────────────────────────────────────────────────────────

def test_control_chars_do_not_create_ghost_codes():
    """BL-129 in another costume: a stray control char inside the stream must split cleanly,
    not produce a code that looks known-but-isn't."""
    parsed = parse_dump("7640183261763\x00\x027611841001236\n")
    assert [c.code for c in parsed.codes] == ["7640183261763", "7611841001236"]
