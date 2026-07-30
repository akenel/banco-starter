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
