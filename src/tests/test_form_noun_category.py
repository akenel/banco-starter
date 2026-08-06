"""When the two AI reads disagree about what the thing IS, say so.

2026-08-06. snap-find reads a photo twice on white-label shelves: a BRAND read (what is printed on
it) and a FORM read (what shape it is). The brand read decides the category — and it drifts.

The case that forced this. Angel photographed a vacuum storage tin:

    run 1  brand → "Tightvac Vacuum Storage Container"  category "Storage & Stash"   ✅
    run 2  brand → "Egatvec Grinder"                    category "Grinders"          ❌

On run 2 the FORM read answered **"Dose Silikon 2teilig 35mm"** — a *tin*, not a grinder. It
described what it actually saw and contradicted stage 1, **and nothing noticed**: the operator got a
confident list of grinders for a storage container.

A disagreement is the system knowing something is off. Swallowing it is the same silent-failure
shape as the morning's AI-that-never-ran returning 200 OK, and the opposite of the honest match
score this endpoint was designed around — *never a confident wrong answer*.

`_form_noun_category` is the detector. These tests pin the two things that matter: it recognises the
nouns that actually appear, and — more importantly — **it stays quiet when it does not know**, so an
unfamiliar noun can never raise a false alarm on a shopkeeper's screen.
"""
import pytest

from src.routes.pos_router import (
    _FORM_NOUN_CATEGORY,
    _WHITE_LABEL_CATEGORIES,
    _form_noun_category,
)


@pytest.mark.parametrize("form_name,expected", [
    # the exact string from the run that exposed this
    ("Dose Silikon 2teilig 35mm", "Storage & Stash"),
    # the ordinary case — form read agrees with a grinder
    ("Grinder Alu CNC 4teilig mit Sieb 50mm", "Grinders"),
    ("Grinder Metall/Acryl 4teilig mit Sieb 50mm", "Grinders"),   # slash-separated materials
    ("Mühle Alu 2teilig 40mm", "Grinders"),                       # German for grinder
    ("Schale Metall 27cm", "Rolling Trays"),
    ("Aschenbecher Glas 10cm", "Ashtrays"),
    ("Waage digital 0.01g", "Scales"),
    ("Glaspfeife 12cm", "Pipes"),
    ("Bong Acryl 30cm", "Bongs"),
    ("Feuerzeug Metall", "Lighters"),
])
def test_recognises_the_noun_that_opens_a_form_read(form_name, expected):
    assert _form_noun_category(form_name) == expected


@pytest.mark.parametrize("form_name", [
    "",                                   # nothing
    "   ",
    "Zubehör Kunststoff 5cm",             # a real word, not one we map
    "Ersatzteil 3teilig",
    "Alu CNC 4teilig 50mm",               # material first, NO noun at all
    "50mm silber",                        # just attributes
    "Widget Deluxe",                      # invented
])
def test_stays_QUIET_when_the_noun_is_unknown(form_name):
    """🔴 The load-bearing one. An unrecognised noun must return None, never a guess — otherwise the
    screen cries wolf at a shopkeeper and the warning stops meaning anything. Silence is the safe
    default; only a noun we positively know may contradict stage 1."""
    assert _form_noun_category(form_name) is None


def test_none_is_also_safe_for_a_missing_read():
    assert _form_noun_category(None) is None


def test_the_noun_may_appear_after_the_first_word():
    """Models do not always lead with the noun. 'Alu Grinder 4teilig' must still resolve."""
    assert _form_noun_category("Alu Grinder 4teilig 50mm") == "Grinders"


def test_punctuation_does_not_hide_the_noun():
    assert _form_noun_category("Dose, Silikon, 35mm") == "Storage & Stash"
    assert _form_noun_category("Grinder-Alu 4teilig") == "Grinders"


def test_every_white_label_shelf_has_at_least_one_noun_that_maps_to_it():
    """Stage 2 only runs on `_WHITE_LABEL_CATEGORIES`. If one of those shelves had no noun mapping
    to it, a disagreement on that shelf could never be detected — the check would be dead for it,
    silently. Pin the two lists together."""
    mapped = set(_FORM_NOUN_CATEGORY.values())
    missing = _WHITE_LABEL_CATEGORIES - mapped
    assert not missing, f"white-label shelves with no detectable noun: {missing}"


def test_a_matching_noun_is_not_a_conflict():
    """Sanity on the caller's contract: same category → nothing to warn about. The endpoint only
    raises `category_conflict` when implied != cat."""
    assert _form_noun_category("Grinder Alu 4teilig 50mm") == "Grinders"   # == stage-1 'Grinders'
