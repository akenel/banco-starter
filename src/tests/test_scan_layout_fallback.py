"""Keyboard-layout fallback on the scan path (BL: guns type '-' as ''')."""
import re

import pytest

from src.routes.pos_router import _layout_variants


def test_the_bug_we_actually_hit():
    """Gun on US, session on Swiss German: TAM-21796 arrives as TAM'21796."""
    assert "TAM-21796" in _layout_variants("TAM'21796")


def test_ean13_is_never_touched():
    """Digits are identical across these layouts — no variant, no risk."""
    assert _layout_variants("2000000217963") == []


def test_a_clean_sku_needs_no_correction_to_be_found_first():
    """Variants exist for the reverse case, but the raw code is tried first
    in _find_product_by_any_barcode, so a correct scan never reaches here."""
    assert "TAM-21796" not in _layout_variants("TAM-21796")


def test_plain_alphanumeric_yields_nothing():
    assert _layout_variants("PLAIN123") == []


def test_bounded():
    """Never explode into a huge candidate set — this runs on every scan miss."""
    assert len(_layout_variants("A'B/C-DßE+F")) <= 8


def test_qwertz_is_a_real_swap_not_a_one_way_replace():
    """Y and Z TRADE places on QWERTZ. A replace() maps one onto the other and
    destroys the original — only translate() actually swaps."""
    assert "ZYX" in _layout_variants("YZX")
    assert "YZX" in _layout_variants("ZYX")


def test_no_variant_ever_equals_the_input():
    for c in ["TAM'21796", "YZ-ABC", "2000000217963", "A/B", "PLAIN"]:
        assert c not in _layout_variants(c)
