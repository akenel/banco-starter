"""The barcode-format objection, and the way past it.

2026-08-28, from the counter. The pack of **JaJa Noir King Size XXL Black Zigarettenpapier**
carries `2024VL099B` — letters and all, a real printed code, no EAN stripe anywhere on it.
`_barcode_objection` refused it on create, on update AND on alias-add, and the documented way
past (`allow_nonstandard=true`) was a QUERY PARAMETER that appeared in zero templates. So from
every screen a cashier can reach, that product was unsaveable. Angel spent over an hour on it.

The guard's own comment had predicted exactly this: *"a guard with no way past it is a trap —
the operator would just put the code in the name field instead, where nothing can ever scan it."*
Written, and then not wired to a button.

The objection is RIGHT most of the time (a lot number scanned instead of the EAN), so it stays.
Only the dead end goes. These tests pin the two halves the screen depends on:

  1. the refusal still fires on the things it should, and
  2. it is machine-IDENTIFIABLE, so the "use it anyway" button attaches to THIS 422 and to no
     other — the same endpoints also 422 for a missing price, where an override is nonsense.
"""
import pytest

from src.routes.pos_router import (_barcode_objection, _barcode_objection_detail,
                                   _barcode_is_a_url, _barcode_url_refusal_detail)


# ---- the guard still guards -------------------------------------------------

def test_a_lot_number_is_still_objected_to():
    # the case the guard exists for: letters scanned from the batch code beside the barcode
    assert _barcode_objection("2024VL099B") is not None
    assert _barcode_objection("LOT-88213") is not None


def test_odd_lengths_and_bad_check_digits_are_still_objected_to():
    assert _barcode_objection("12345") is not None            # not 8/12/13/14
    assert _barcode_objection("7612400036196") is not None     # real code, last digit bumped


def test_real_codes_pass_clean():
    for code in ("7612400036195", "42425700", "0716165177777", "2000000264066"):
        assert _barcode_objection(code) is None, code


def test_blank_is_not_an_objection():
    # leaving the barcode empty is a legitimate choice — bind it on the first scan (LESSON #9)
    assert _barcode_objection("") is None
    assert _barcode_objection(None) is None


# ---- and it can be told apart from every other 422 --------------------------

def test_the_detail_is_structured_so_a_screen_can_find_it():
    d = _barcode_objection_detail(_barcode_objection("2024VL099B"))
    assert d["conflict"] == "barcode_format"      # what catalog.html tests on
    assert d["override"] == "allow_nonstandard"   # names its own way out
    assert isinstance(d["message"], str) and d["message"]


def test_the_message_survives_for_a_human_to_read():
    # the API helper prefers detail.message, so a cashier sees the sentence and never the JSON
    d = _barcode_objection_detail(_barcode_objection("2024VL099B"))
    assert "2024VL099B" in d["message"]
    assert "letters" in d["message"].lower()


def test_the_marker_is_not_something_another_422_could_claim():
    # a price refusal on the same endpoint is a plain string; only this one carries `conflict`,
    # which is why the override button cannot attach itself to the wrong refusal
    d = _barcode_objection_detail("anything")
    assert set(d) == {"conflict", "message", "override"}


# ---- and a QR code is not a barcode at all ----------------------------------
# 2026-09-17, from the counter. A packet with NO stripe anywhere on it, only a QR.
# Angel scanned the QR "like a silly cashier might do" and Banco bound
# https://vqr.vc/BiWfnR9bv to AlpenBreeze. It got in because _barcode_objection saw
# letters and said LOT NUMBER — the wrong reason — and offered the override, which
# a cashier staring at a packet with no other code will quite reasonably press.

def test_a_scanned_qr_url_is_refused():
    for code in ("https://vqr.vc/BiWfnR9bv", "http://x.co/a", "www.jaja.ch",
                 "HTTPS://VQR.VC/X", "mailto:shop@example.ch", "tel:0791234567",
                 "BEGIN:VCARD"):
        assert _barcode_is_a_url(code) is not None, code


def test_the_jaja_packet_still_saves():
    # THE WHOLE POINT OF KEEPING THESE TWO GUARDS SEPARATE. 2024VL099B is a real code
    # printed on a real packet, it has letters, and it must stay saveable via the
    # override. A URL must not. One hour was lost to this packet in August.
    assert _barcode_is_a_url("2024VL099B") is None
    for code in ("7612400036195", "2000000264066", "ITEM-0300", "LOT-88213", "42425700"):
        assert _barcode_is_a_url(code) is None, code


def test_blank_is_not_a_url():
    assert _barcode_is_a_url("") is None
    assert _barcode_is_a_url(None) is None


def test_the_url_refusal_names_NO_way_past_it():
    # A shop may genuinely need an odd code; no shop has ever needed https:// as one.
    # The screen attaches "use it anyway" to a detail carrying `override`. This one
    # must not carry it, so no button appears.
    d = _barcode_url_refusal_detail(_barcode_is_a_url("https://vqr.vc/BiWfnR9bv"))
    assert d["conflict"] == "barcode_is_a_url"
    assert "override" not in d
    assert "WEB LINK" in d["message"]
    assert "blank" in d["message"].lower()      # tells the cashier what to do instead


def test_the_message_does_not_dump_a_giant_url_at_a_cashier():
    long_url = "https://example.com/" + "x" * 200
    msg = _barcode_is_a_url(long_url)
    assert "…" in msg and len(msg) < 400
