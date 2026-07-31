"""Scraped page text must arrive DECODED, because encoded text silently breaks matching.

Found live 2026-07-31. Angel enriched Gizeh King Size papers from a page whose title was served
as `GIZEH&#x20;Papers&#x20;KingSize`. Nothing unescaped it, so that string was stored as the
product name — and then the duplicate matcher normalised it to `gizeh x20 papers x20 kingsize`
and scored it against the catalogue's own `Gizeh King Size Slim` (TAM-16301):

        encoded  ->  0.429     under the 0.5 threshold, so: "nothing looks like that"
        decoded  ->  1.000     a perfect match

Banco told him the most fundamental product in a headshop was not in the catalogue, while it sat
there under a minted barcode. The matcher was fine. Its input was corrupted one step earlier.

His words: "if we don't find the Gizeh papers, we're in trouble."
"""
import html


def _unescape_facts(out: dict) -> dict:
    """Mirror of the decode step at the end of _page_product_facts."""
    return {k: (html.unescape(v) if k != "_html" and isinstance(v, str) else v)
            for k, v in out.items()}


def test_the_gizeh_case_that_broke_matching():
    facts = _unescape_facts({"name": "GIZEH&#x20;Papers&#x20;KingSize"})
    assert facts["name"] == "GIZEH Papers KingSize"
    assert "&#x20;" not in facts["name"]


def test_quotes_survive_decoding_intact():
    """This shop's real titles carry quotes — Blow ... "V1" ... — so &quot; is not exotic here."""
    facts = _unescape_facts(
        {"name": 'Blow vorgebauter CBD Joint Pure &quot;V1&quot; 1 Stk. schwarz'})
    assert facts["name"] == 'Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz'


def test_ampersands_in_brand_names():
    assert _unescape_facts({"name": "Bull &amp; Bear Papers"})["name"] == "Bull & Bear Papers"


def test_apostrophes_in_both_forms():
    assert _unescape_facts({"name": "Rizla&#39;s Green"})["name"] == "Rizla's Green"
    assert _unescape_facts({"name": "Rizla&apos;s Green"})["name"] == "Rizla's Green"


def test_image_urls_are_decoded_too():
    """An og:image query string arrives with &amp;, which makes the URL 404 — a product with a
    broken picture looks like a product nobody set up."""
    out = _unescape_facts({"image": "https://cdn.example.com/p.jpg?w=800&amp;h=600&amp;fit=crop"})
    assert out["image"] == "https://cdn.example.com/p.jpg?w=800&h=600&fit=crop"


def test_non_strings_are_left_alone():
    out = _unescape_facts({"price": 2.0, "found": True, "name": "Plain", "currency": None})
    assert out["price"] == 2.0 and out["found"] is True and out["currency"] is None


def test_decoded_text_is_idempotent():
    """Running it twice must not eat a literal ampersand a product legitimately contains."""
    once = _unescape_facts({"name": "Bull &amp; Bear"})["name"]
    assert _unescape_facts({"name": once})["name"] == "Bull & Bear"


# ─────────────────────────────────────────────────────────────────────────────────────────
# EAN printed in the body copy, with no structured data behind it.
#
# fourtwenty.ch does this: "EAN 42422884" is in the visible text, its JSON-LD carries no gtin.
# So a shop that genuinely publishes EANs looked to Banco like one that doesn't — and Angel
# spent a day concluding no source existed. Verified live 2026-07-31.
#
# Reading a bare number out of prose is exactly the sort of thing that goes wrong quietly, so
# it is fenced twice: the digits must be LABELLED, and must pass the GTIN check digit.
# ─────────────────────────────────────────────────────────────────────────────────────────
import re
from src.services.shelf_intake import gtin_check_digit_ok

# The gap between label and digits is often MARKUP or an ENTITY — `EAN">4242…` in a Magento
# data-th cell, or `EAN&nbsp;4242…`. Entities contain letters and digits, so a plain
# [^0-9A-Za-z] run stops dead at `&nbsp;` and finds nothing. Allow entities explicitly.
_GAP = r"(?:&[a-z]+;|&#\d+;|[^0-9A-Za-z]){0,20}"
_LABELLED = re.compile(
    r"(?:EAN|GTIN|Barcode|Artikelnummer|Artikelnr\.?)" + _GAP + r"(\d{8,14})", re.I)


def _scrape(html_text):
    for m in _LABELLED.finditer(html_text):
        if gtin_check_digit_ok(m.group(1)):
            return m.group(1)
    return None


def test_the_fourtwenty_case():
    html_text = "Papers beträgt 11 x 3.1 x 0.5 cm, EAN 42422884 Länge 107mm Breite 44mm"
    assert _scrape(html_text) == "42422884"


def test_labels_in_either_language_and_with_punctuation():
    for text in ("EAN: 42422884", "EAN&nbsp;42422884", "GTIN 42422884",
                 "Artikelnummer 42422884", 'data-th="EAN">42422884</td>',
                 "Barcode&#58;&nbsp;42422884"):
        assert _scrape(text) == "42422884", text


def test_an_unlabelled_number_is_ignored():
    """A bare 8-digit run in prose is a dimension, an order number or a date — not an identity."""
    assert _scrape("Length 107mm, ref 42422884 in our system") is None


def test_a_labelled_number_that_fails_its_checksum_is_rejected():
    """A misread or an internal article number wearing the EAN label. Better none than wrong —
    a bad barcode binds the wrong product and hides the right one."""
    assert _scrape("EAN 42422885") is None


def test_dimensions_next_to_the_label_do_not_hijack_it():
    """'11 x 3.1 x 0.5 cm' sits right before the label on the real page."""
    assert _scrape("Papers beträgt 11 x 3.1 x 0.5 cm, EAN 42422884") == "42422884"


def test_the_first_VALID_labelled_code_wins_not_the_first_labelled_one():
    assert _scrape("EAN 99999999 and also EAN 42422884") == "42422884"
