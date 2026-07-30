"""Cloning a product into its next variant (BLOW colours, nutrient sizes, paper formats).

The catalog's real volume problem isn't unique products — it's variants. One BLOW line is
orange/red/blue/white/silver; one nutrient is 250ml/1L/5L. Each is its own EAN and its own
row, but shares brand, category, 18+ and price with its siblings.
"""
import pytest

from src.routes.pos_router import ProductCloneRequest


def test_only_the_differing_fields_are_required():
    """A variant is a name plus, usually, a barcode. Everything else inherits."""
    r = ProductCloneRequest(name="Blow Joint WHITE Pure")
    assert r.name == "Blow Joint WHITE Pure"
    assert r.barcode is None
    assert r.price is None
    assert r.copy_image is True          # size variants share artwork


def test_colour_variants_can_refuse_the_parent_image():
    """A violet BLOW packet is not a grey one. A wrong photo is worse than none —
    it looks finished, so nobody goes back to fix it."""
    r = ProductCloneRequest(name="Blow Joint GREY Pure", copy_image=False)
    assert r.copy_image is False


def test_price_can_differ_for_size_variants():
    """'red 5 grams 50 and red 20gram 120' — same product, different price."""
    r = ProductCloneRequest(name="Canna Coco A 5L", price=120)
    assert float(r.price) == 120.0


def test_name_is_required_and_non_empty():
    with pytest.raises(Exception):
        ProductCloneRequest(name="")


def test_variant_carries_its_own_supplier_sku():
    """Each variant is a separate line on the supplier's order form."""
    r = ProductCloneRequest(name="RAW Classic King Size", supplier_sku="716165280293")
    assert r.supplier_sku == "716165280293"
