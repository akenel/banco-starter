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
