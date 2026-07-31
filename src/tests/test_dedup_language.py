"""Duplicate detection has to work across German and English.

FIELD FINDING 2026-07-30 (Artemis). Angel spent two hours re-creating BLOW CBD joints that
were already in the catalog. Two independent misses let it happen:

  1. He scanned the packet's REAL EAN; the imported row carried a MINTED 2xxxx code -> no
     barcode match.
  2. The name-dedup guard then compared his ENGLISH title against the GERMAN import and scored
     0.417, under the 0.5 threshold -> no "is it one of these?" warning either.

The packets are international English; the wholesale feed (Tamar, 420) is German.
"""
from src.routes.pos_router import _norm_name_for_match as norm


def test_the_pair_that_cost_two_hours_folds_identical():
    a = norm('Blow Pre-built CBD Joint Pure "V1" 1 pc. black')
    b = norm('Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz')
    assert a.split() == b.split(), f"{a!r} != {b!r}"


def test_colour_words_bridge_languages():
    for de, en in [("schwarz", "black"), ("weiss", "white"), ("grün", "green"),
                   ("blau", "blue"), ("grau", "grey"), ("gelb", "yellow"),
                   ("braun", "brown"), ("violett", "purple")]:
        assert norm(f"Blow Joint {de}").split() == norm(f"Blow Joint {en}").split(), de


def test_unit_words_bridge_languages():
    assert norm("Joint 1 Stk.").split() == norm("Joint 1 pc.").split()
    assert norm("Joint 1 Stück").split() == norm("Joint 1 piece").split()


def test_prerolled_wording_bridges_languages():
    assert norm("vorgebauter Joint").split() == norm("pre-built joint").split()
    assert norm("vorgebauter Joint").split() == norm("pre-rolled joint").split()


def test_punctuation_and_case_do_not_matter():
    assert norm('BLOW  JOINT  "GREY"  Pure!').split() == norm("blow joint grey pure").split()


def test_genuinely_different_products_stay_different():
    """Folding must not collapse distinct variants — that would hide real products behind a
    false 'you already have this'."""
    assert norm("Blow Joint black").split() != norm("Blow Joint white").split()
    assert norm("Canna Coco A 1L").split() != norm("Canna Coco B 1L").split()


# ─────────────────────────────────────────────────────────────────────────────────────────
# SPACING IS NOT MEANING — and it cost a match by nothing at all.
#
# Angel, testing on the tablet with the packet in his hand: the page title is "GIZEH Papers
# KingSize", the catalogue row is "Gizeh King Size" (TAM-21669). Same product — same price,
# same 34 leaves — and the screen said "nothing in the catalogue looks like that", one click
# from creating the duplicate this whole workflow exists to prevent.
#
#     'gizeh papers kingsize'  vs 'gizeh king size'   ->  0.500   and the guard is `> 0.5`
#     'gizeh papers king size' vs 'gizeh king size'   ->  0.682
#
# Measured on the live catalogue: 85 rows say "King Size", 2 say "KingSize", 1 says "KSS".
# ─────────────────────────────────────────────────────────────────────────────────────────
from src.routes.pos_router import _norm_name_for_match as _n


def test_kingsize_folds_to_two_words():
    assert _n("GIZEH Papers KingSize") == _n("GIZEH Papers King Size")


def test_the_hyphenated_form_folds_too():
    assert _n("Gizeh King-Size Slim") == _n("Gizeh King Size Slim")


def test_kss_is_the_same_thing_spelled_short():
    """One real row uses it: 'GIZEH All PINK Papers KSS + Aktivkohle Filter'."""
    assert "king size slim" in _n("GIZEH All PINK Papers KSS")


def test_it_does_not_invent_word_breaks_elsewhere():
    """A general split-any-compound rule would start cutting brand names in half."""
    assert _n("Kingpin Wraps") == "kingpin wraps"
    assert _n("Smoking Kingpin") == "smoking kingpin"


def test_ks_is_king_size_too():
    """Angel: "they use KS sometimes, or I have seen KSS for super KS." Every one of the 12 live
    rows using it means King Size — Eurocones KS, Raw KS slim, G-Rollz Pink KS Papers."""
    assert "king size" in _n("Raw KS slim Classic brown")
    assert "king size" in _n("Eurocones KS 800stk")


def test_kss_still_wins_over_ks():
    """Longer abbreviation first, or KSS would resolve as "king size" and lose the Slim."""
    assert "king size slim" in _n("GIZEH All PINK Papers KSS")
