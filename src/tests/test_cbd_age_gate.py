"""CBD age-gating must not hinge on a product title's spelling.

FIELD FINDING 2026-07-29 (Artemis Lucerne). Four BLOW pre-rolled CBD joints sat in the live
catalog classed `standard` and sellable with NO 18+ check, because the classifier keyed on the
literal word "CBD" and the titles either omitted it or transposed it to "CDB". Meanwhile
"Blow Pre-built CBD Joint Pure" gated correctly — so whether a customer was asked for ID
depended on a typo.
"""
import pytest

from src.services.catalog_taxonomy import classify


@pytest.mark.parametrize("title", [
    'BLOW Joint GREY Pure',              # title never says CBD at all
    'BLOW CDB PRE JOINT GREEN Pure',     # CDB transposition
    'BLOW CDB PRE JOINT RED',
    'Blow Pre-built CBD Joint Pure "V1" 1 pc.',
    'Blow vorgebauter CBD Joint Pure "Strawberry"',
])
def test_cbd_prerolls_are_always_age_gated(title):
    _, cls, age = classify(title)
    assert cls == "cbd_hemp", f"{title!r} classed {cls!r} — would sell un-gated"
    assert age is True


@pytest.mark.parametrize("title", [
    'Nasty Juice Aroma Slow Blow 30ml',   # "Blow" is a vape FLAVOUR, not a CBD joint
    'Smoking Blue King Size',             # rolling papers
    'Canna Coco A 1L',                    # grow substrate
])
def test_innocent_titles_are_not_over_gated(title):
    """Over-gating is its own failure: staff learn to ignore prompts that fire wrongly."""
    _, cls, age = classify(title)
    assert cls != "cbd_hemp"
    assert age is False


@pytest.mark.parametrize("title,expect_age", [
    ('CBD Öl 10% 10ml', False),           # oils/tinctures are open — no ID needed
    ('CBD Samen Feminisiert', False),     # seeds are open
])
def test_open_cbd_forms_stay_open(title, expect_age):
    _, _, age = classify(title)
    assert age is expect_age


@pytest.mark.parametrize("title", [
    'Canna Coco A 1L', 'CANNA PK 13/14 250 ml', 'Plagron Pure Zym 1L',
    'GuanoKalong GK-Organics Florizon 1L', 'Metrop MR1 250ml',
    'Biobizz Fish-Mix 1L', 'Plagron Terra Grow 1L',
])
def test_grow_nutrient_brands_land_in_grow_supplies(title):
    """Angel hand-entered these 2026-07-30 and every one landed in 'Unsorted' — a fertiliser
    title is a brand plus a product code, so the brand is the only reliable handle."""
    cat, _, _ = classify(title)
    assert cat == "Grow Supplies", f"{title!r} -> {cat!r}"


# ── The title is not enough. Angel, after capturing stock by hand at the shop: ──
# "You can't go just off the title. These names, they could be funky gorilla names.
#  You'd have no idea. You have to go into the description to determine what it really is."

@pytest.mark.parametrize("title,description", [
    ("Gorilla Glue #4",    "Vorgebauter Joint mit 12% CBD, 1 Stück in der Tube."),
    ("Purple Haze Single", "CBD-Gehalt 14%. Pre-rolled joint, 1 pc in plastic tube."),
    ("Amnesia Single 1g",  "Pre-rolled CBD joint, 0.8g, in a plastic tube."),
])
def test_meaningless_strain_names_are_gated_from_the_description(title, description):
    _, cls, age = classify(title, description=description)
    assert cls == "cbd_hemp" and age is True


@pytest.mark.parametrize("title,description", [
    ("Smoking Blue King Size", "Perfect for your CBD flower and herbs. Thin papers."),
    ("RAW Classic King Size",  "Ideal zum Drehen von CBD Blüten."),
])
def test_an_incidental_cbd_mention_never_gates_papers(title, description):
    """The reason _CBD_STRONG is narrow. Papers advertise what you'd roll IN them, and if that
    gated them the shop would be asking for ID to sell a booklet of papers. Over-gating trains
    staff to wave prompts away — and then the real ones get waved through too."""
    _, cls, age = classify(title, description=description)
    assert cls != "cbd_hemp" and age is False


def test_a_cbd_joint_in_a_tube_is_still_gated():
    """_TOBACCO_ACCESSORY matches \\btube\\b, and these ship "one spliff in a plastic tube" —
    so vetoing on the description would have killed exactly the product we must gate."""
    _, cls, age = classify("Sour Diesel Single", description="Pre-rolled joint 12% CBD in tube")
    assert cls == "cbd_hemp" and age is True
