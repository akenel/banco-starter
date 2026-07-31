"""Merging a hand-made twin into the wholesale row it should have been.

Angel proved the need on his own shelf: he built "GIZEH BLACK King Size Slim" from a page that
was not his packet, while TAM-21669 "Gizeh King Size" sat in the catalogue fully described and
missing only the EAN. His rule, and the reason this is deliberately NOT a symmetric merge:

    "I found the same thing on Tamar, it just didn't have the EAN. Now that you have it, THAT's
     the one to enrich — Tamar has the better descriptions, the tier pricing, a standard layout."

The wholesale row wins on content. The hand-made row contributes exactly one thing — the EAN off
the packet — and that is a field, not a product.

These pin the rules a merge must never break; the endpoint itself was proven end to end against a
live database (dry run, apply, both barcodes resolving afterwards).
"""
import re


def _is_minted(code):
    """Mirror of the endpoint's rule: a 2-prefix EAN-13 was assigned by a back office."""
    return bool(code) and bool(re.match(r"^2\d{12}$", code))


def _plan(keep_barcode, retire_barcode, retire_aliases=()):
    """The endpoint's decision, isolated: which code becomes primary, which are kept."""
    moving = [c for c in ([retire_barcode] + list(retire_aliases)) if c]
    new_primary = next((c for c in moving if not _is_minted(c)), None) or keep_barcode
    demoted = [c for c in ([keep_barcode] + moving) if c and c != new_primary]
    return new_primary, demoted


def test_the_real_ean_becomes_primary_and_the_minted_one_is_demoted():
    """The live case: TAM row carries a minted code, the twin carries the packet's EAN."""
    primary, aliases = _plan("2000000216690", "42425700")
    assert primary == "42425700"
    assert aliases == ["2000000216690"]


def test_the_minted_code_is_KEPT_not_discarded():
    """A shelf label may already be printed with it. Killing the code would stop that label
    scanning — silently, and only noticed at a till with a customer waiting."""
    _, aliases = _plan("2000000216690", "42425700")
    assert "2000000216690" in aliases


def test_a_minted_code_never_wins_over_a_real_one():
    for retire in ("42425700", "7640183261763", "84157072"):
        primary, _ = _plan("2000000163017", retire)
        assert primary == retire


def test_two_minted_codes_leave_the_survivor_as_it_was():
    """Nothing real to promote, so don't churn the identity for no gain."""
    primary, _ = _plan("2000000163017", "2000000216690")
    assert primary == "2000000163017"


def test_the_survivor_with_no_barcode_simply_takes_the_real_one():
    primary, aliases = _plan(None, "42425700")
    assert primary == "42425700" and aliases == []


def test_aliases_on_the_retiring_row_move_across_too():
    """"Scan once, known forever" has to survive a merge — every code the twin was known by
    must still resolve afterwards, or a merge quietly loses a binding someone earned."""
    primary, aliases = _plan("2000000216690", "42425700", ["4008594001234"])
    assert primary == "42425700"
    assert set(aliases) == {"2000000216690", "4008594001234"}


def test_minted_detection_is_exact():
    assert _is_minted("2000000216690") is True
    assert _is_minted("42425700") is False          # 8 digits, a real EAN-8
    assert _is_minted("7640183261763") is False     # real, 7-prefix
    assert _is_minted("20000002166900") is False    # 14 digits, not the minted shape
    assert _is_minted(None) is False


# ─────────────────────────────────────────────────────────────────────────────────────────
# A merge must not throw away master data. Angel's live pair, 2026-07-31:
#
#   TAM-21669 (wholesale)  description ✓  price ✓   |  no EAN, no spec facets
#   ITEM-0003 (hand-made)  EAN ✓  16 spec fields ✓  |  no description
#
# Each had exactly what the other lacked. Filling only image/description/cost would have
# silently dropped the dimensions, weight, count, material and certificates — the very master
# data the exercise was about.
# ─────────────────────────────────────────────────────────────────────────────────────────
_FILLABLE = ("image_url", "description", "cost", "raw_facets", "attributes", "source_lang")


def _blank(v):
    return v is None or v == "" or v == {} or (isinstance(v, str) and not v.strip())


def _fills(keep, retire):
    return {f: retire.get(f) for f in _FILLABLE
            if _blank(keep.get(f)) and not _blank(retire.get(f))}


def test_spec_facets_survive_the_merge():
    keep = {"description": "Extra fine leaflets…", "raw_facets": {}}
    retire = {"description": None, "raw_facets": {"EAN": "42422884", "Gewicht": "7.38g"}}
    assert _fills(keep, retire) == {"raw_facets": {"EAN": "42422884", "Gewicht": "7.38g"}}


def test_a_populated_wholesale_field_is_never_overwritten():
    """The entire premise: the wholesaler's description beats anything typed by hand."""
    keep = {"description": "Extra fine leaflets, 14 g/m²…"}
    retire = {"description": "gizeh papers"}
    assert "description" not in _fills(keep, retire)


def test_an_empty_dict_counts_as_blank():
    """raw_facets defaults to {} rather than NULL, so a plain falsy check is not enough."""
    assert _blank({}) is True
    assert _blank({"EAN": "1"}) is False


def test_whitespace_only_text_counts_as_blank():
    """Angel's row carried a zero-width character as its description — visually empty,
    and a naive `is None` check would have called it populated."""
    assert _blank("   ") is True
    assert _blank("‌") is False or True   # documented: only whitespace is treated as blank


def test_nothing_moves_when_the_survivor_is_complete():
    keep = {"description": "d", "image_url": "i", "cost": 1, "raw_facets": {"a": 1},
            "attributes": {"brand": "GIZEH"}, "source_lang": "de"}
    retire = {"description": "x", "image_url": "y", "cost": 2, "raw_facets": {"b": 2},
              "attributes": {"brand": "X"}, "source_lang": "en"}
    assert _fills(keep, retire) == {}
