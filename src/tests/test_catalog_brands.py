"""Brand awareness in duplicate matching.

Measured against the live catalog 2026-07-31: about half the 0.5-0.7 similarity proposals were
wrong, and wrong in a way no character-based score can see — `Canna` vs `Cocanna`, `Spritz` vs
`Spritze`. The fix is not a cleverer score; it is knowing they are different companies.
"""
import pytest

from src.services.catalog_brands import BRANDS, NOT_BRANDS, brand_of, brands_conflict


@pytest.mark.parametrize("a,b", [
    ("Canna Coco A 1L", "Beamer Candles Co Cocanna Banana"),   # canna != cocanna (substring!)
    ("Aperol Spritz", "Dosier Spritze 1ml"),                   # Spritz != Spritze
    ("Blow pure", "Local Weed vorgebauter CBD Joint Pure"),     # different CBD brands
    ("BLOW Joint GREY Pure", "Local Weed vorgebauter CBD Joint Pure"),
])
def test_real_false_positives_are_blocked(a, b):
    assert brands_conflict(a, b) is True


@pytest.mark.parametrize("a,b", [
    ('Blow Pre-built CBD Joint Pure "V1" 1 pc. black',
     'Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz'),   # the pair that cost 2 hours
    ("Raw Organic Rolls", "Raw Rolls Organic Hemp"),
    ("Smoking Red King Size", "Smoking King Size red thinnest"),
    ("Quöllfrisch Hell", "Bier Quöllfrisch Hell 5dl"),
    ("Greengo slim Rolls", "Greengo Rolls Slim"),
])
def test_real_duplicates_still_get_through(a, b):
    assert brands_conflict(a, b) is False


def test_unknown_brands_fall_back_to_plain_similarity():
    """An unrecognised brand must never suppress a match — the file is additive, not a gate."""
    assert brands_conflict("Some Unknown Thing 5g", "Another Unknown Thing 5g") is False


def test_brand_found_even_when_the_title_leads_with_a_category():
    assert brand_of("Aktivkohlefilter Purize 100stk") == "purize"
    assert brand_of("Bier Quöllfrisch Hell 5dl") == "quöllfrisch"


def test_category_nouns_are_never_treated_as_brands():
    """`grinder`, `bong`, `tabak` lead hundreds of unrelated titles. Treating one as a brand
    would suppress every genuine match in that category."""
    for word in ("grinder", "bong", "tabak", "vaporizer", "papers", "filter"):
        assert brand_of(f"{word} something 5g") is None


def test_the_two_lists_never_overlap():
    """A word in both would make brand_of() depend on iteration order."""
    assert BRANDS & NOT_BRANDS == set()
