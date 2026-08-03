"""What the "fill it from the page" button is allowed to overwrite — and what it is not.

Angel, on Felix's grinder (2026-08-03): "you could go and edit the product, give it a proper
name, a description, do everything manually. But you don't wanna really do that."

So the bench card reads the product's own page and fills the boxes. Every one of those fill
rules is a POLICY decision, not plumbing, and each has a way of being quietly wrong:

  * a scraped price silently replacing what the shop actually charges
  * a foreign-currency figure sitting in an editable box at 11pm
  * a web page switching OFF an 18+ gate
  * a page's own category regrowing the German-slug mess the taxonomy was cleaned of

The rules live in `fillFromPage()` inside cleanup.html, so this test EXTRACTS that function and
runs it in node against a stub API. Testing a copy of the logic would be worse than no test:
this repo's most expensive bug shape is a client mirror that drifts while every unit test stays
green (the `pc.`/`Stk.` size table, dead for weeks). Sabotage-checked — flip any rule and a test
here fails.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

_CLEANUP = Path(__file__).resolve().parents[2] / "src/templates/pos/cleanup.html"
needs_node = pytest.mark.skipif(not shutil.which("node"), reason="node not installed")


def _extract(fn: str) -> str:
    """Pull one method (name through its closing brace) out of the Alpine data object."""
    src = _CLEANUP.read_text(encoding="utf-8")
    m = re.search(rf"^            (?:async )?{re.escape(fn)}\(.*?^            \}},", src, re.S | re.M)
    assert m, f"{fn}() not found in {_CLEANUP.name} — did the template change shape?"
    return m.group(0).rstrip(",")


def run_fill(facts, row, currency="CHF"):
    """Execute the REAL fillFromPage() against stubbed page-facts, return the row after."""
    script = f"""
const FACTS = {json.dumps(facts)};
const ROW = Object.assign({{
  _name: '', _description: '', _category: '', _barcode: '', _price: '',
  _imgUrl: '', _age: false, _factsUrl: 'https://shop.example/p/1',
  _filling: false, _fillErr: '', _filled: '', _preFill: null, image_url: '',
}}, {json.dumps(row)});

global.API = {{ post: async () => FACTS }};
global._cfg = (k) => (k === 'currency' ? {json.dumps(currency)} : null);
const page = {{
  {_extract("fillFromPage")},
  {_extract("undoFill")}
}};
(async () => {{
  await page.fillFromPage(ROW);
  console.log(JSON.stringify(ROW));
}})();
"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


GOOD = {
    "found": True,
    "name": "Champ High White Leaf Grinder 4-part 50mm",
    "description": "Four-part aluminium grinder, 50 mm, with pollen catcher.",
    "suggested_category": "Grinders",
    "suggested_age_restricted": False,
    "barcode": "3661075283438",
    "price": 12.90,
    "currency": "CHF",
    "image": "https://shop.example/img/grinder.jpg",
}


# ── the name: the whole point ────────────────────────────────────────────────────────────

@needs_node
def test_the_name_is_always_replaced():
    """"grinder" is exactly what we came to fix. If the fill politely preserved it, the button
    would do nothing useful on the one row that needed it most."""
    r = run_fill(GOOD, {"_name": "grinder"})
    assert r["_name"] == "Champ High White Leaf Grinder 4-part 50mm"


@needs_node
def test_a_rename_is_shown_in_full_before_and_after():
    """Angel accepted "…Grinder [40506209] - Jelly-Joker" over a good name he had typed himself,
    because the summary said only "name" — true, and useless. A name prints on a shelf label and
    a receipt; it does not get to change behind one word in a list."""
    r = run_fill(GOOD, {"_name": "grinder"})
    assert r["_renamed"] == "grinder", "the old name must be kept for the before/after"


@needs_node
def test_no_before_and_after_when_the_name_did_not_change():
    """Otherwise every fill shouts about a rename that never happened, and the warning stops
    meaning anything."""
    r = run_fill(GOOD, {"_name": GOOD["name"]})
    assert r["_renamed"] == ""


@needs_node
def test_a_name_taken_from_a_page_title_is_flagged():
    """Structured data is the shop naming its product; a page title is decoration we trimmed and
    might not have trimmed perfectly. The operator should know which one they are reading."""
    from_title = run_fill({**GOOD, "name_source": "page_title"}, {"_name": "grinder"})
    structured = run_fill({**GOOD, "name_source": "structured"}, {"_name": "grinder"})
    assert from_title["_nameFromTitle"] is True
    assert structured["_nameFromTitle"] is False


@needs_node
def test_a_page_with_no_product_on_it_changes_nothing():
    """artemisluzern.ch returns 200 with boilerplate and no name. Reporting that as a fill
    would invite saving a shop's marketing blurb as a product description."""
    r = run_fill({"found": False, "why": "That page didn't state a product name"},
                 {"_name": "grinder", "_price": "15.00"})
    assert r["_name"] == "grinder" and r["_price"] == "15.00"
    assert r["_filled"] == "" and "didn't state" in r["_fillErr"]
    assert r["_preFill"] is None          # nothing touched, so nothing to undo


# ── money: the rule with real consequences ───────────────────────────────────────────────

@needs_node
def test_a_price_the_shop_already_charges_is_never_overwritten():
    """Pam sold it at 15.00. The page says 12.90. 15.00 is what the till actually took, and a
    scraped figure must not quietly replace it."""
    r = run_fill(GOOD, {"_name": "grinder", "_price": "15.00"})
    assert r["_price"] == "15.00"
    assert "price" not in r["_filled"]


@needs_node
def test_a_blank_price_is_filled_only_from_our_own_currency():
    r = run_fill(GOOD, {"_name": "grinder", "_price": ""}, currency="CHF")
    assert r["_price"] == 12.90 and "price" in r["_filled"]


@needs_node
def test_a_foreign_price_is_refused_and_SAYS_SO():
    """Silence would leave the operator to notice the currency themselves, which is precisely
    what nobody does at the end of a long evening."""
    eur = {**GOOD, "currency": "EUR", "price": 9.90}
    r = run_fill(eur, {"_name": "grinder", "_price": ""}, currency="CHF")
    assert r["_price"] == ""
    assert "EUR" in r["_filled"] and "CHF" in r["_filled"]
    assert "NOT filled" in r["_filled"]


# ── the age gate: one direction only ─────────────────────────────────────────────────────

@needs_node
def test_a_page_can_turn_an_age_gate_ON():
    r = run_fill({**GOOD, "suggested_age_restricted": True}, {"_name": "x", "_age": False})
    assert r["_age"] is True and "18+" in r["_filled"]


@needs_node
def test_a_page_can_NEVER_turn_an_age_gate_OFF():
    """Loosening an age gate is the one direction where being wrong is a compliance failure —
    the same rule `reclass-age-gate.py` runs under. A web page does not get that authority."""
    r = run_fill({**GOOD, "suggested_age_restricted": False}, {"_name": "x", "_age": True})
    assert r["_age"] is True
    assert "18+" not in r["_filled"]


# ── the fields that defer to a human ─────────────────────────────────────────────────────

@needs_node
def test_a_description_someone_wrote_wins_over_a_scraped_one():
    r = run_fill(GOOD, {"_name": "x", "_description": "Felix's own words about this grinder."})
    assert r["_description"] == "Felix's own words about this grinder."
    assert "description" not in r["_filled"]


@needs_node
def test_the_scanned_barcode_outranks_the_page():
    """The packet is in your hand; the page is a claim about a packet. If they disagree, the
    thing you are holding wins — and a barcode swap is invisible after the fact."""
    r = run_fill({**GOOD, "barcode": "9999999999999"}, {"_name": "x", "_barcode": "3661075283438"})
    assert r["_barcode"] == "3661075283438"


@needs_node
def test_a_blank_barcode_is_filled_from_the_page():
    """Worth having: 2 scans in 10 never read, and the page still carries the GTIN."""
    r = run_fill(GOOD, {"_name": "x", "_barcode": ""})
    assert r["_barcode"] == "3661075283438" and "barcode" in r["_filled"]


@needs_node
def test_a_real_category_is_kept_and_a_gap_is_filled():
    kept = run_fill(GOOD, {"_name": "x", "_category": "Grinders & Storage"})
    assert kept["_category"] == "Grinders & Storage"
    filled = run_fill(GOOD, {"_name": "x", "_category": ""})
    assert filled["_category"] == "Grinders"      # OUR taxonomy, not the source's


@needs_node
def test_the_photo_is_offered_not_fetched():
    """`/images/from-url` writes immediately. Nothing here may write before a human has looked,
    so the link is loaded into the box and the operator presses Get it."""
    r = run_fill(GOOD, {"_name": "x"})
    assert r["_imgUrl"] == "https://shop.example/img/grinder.jpg"
    assert "Get it" in r["_filled"]


@needs_node
def test_an_existing_photo_is_not_replaced():
    r = run_fill(GOOD, {"_name": "x", "image_url": "https://cdn.banco/own.jpg"})
    assert r["_imgUrl"] == ""


# ── the way back ─────────────────────────────────────────────────────────────────────────

@needs_node
def test_undo_restores_every_box_exactly():
    """Nothing is saved until Save & done — but a box rewritten under your cursor is still a
    surprise, and a half-undo is worse than none."""
    before = {"_name": "grinder", "_description": "", "_category": "", "_barcode": "",
              "_price": "", "_imgUrl": "", "_age": False}
    script = f"""
const FACTS = {json.dumps(GOOD)};
const ROW = Object.assign({{_factsUrl: 'https://shop.example/p/1', _filling: false,
  _fillErr: '', _filled: '', _preFill: null, image_url: ''}}, {json.dumps(before)});
global.API = {{ post: async () => FACTS }};
global._cfg = () => 'CHF';
const page = {{ {_extract("fillFromPage")}, {_extract("undoFill")} }};
(async () => {{
  await page.fillFromPage(ROW);
  const changed = ROW._name;
  page.undoFill(ROW);
  console.log(JSON.stringify({{changed, after: ROW}}));
}})();
"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    r = json.loads(out.stdout)
    assert r["changed"] != "grinder", "the fill did not actually change anything to undo"
    for k, v in before.items():
        assert r["after"][k] == v, f"{k} was not restored ({r['after'][k]!r} != {v!r})"
    assert r["after"]["_filled"] == "" and r["after"]["_preFill"] is None


@needs_node
def test_undo_on_a_row_that_was_never_filled_is_a_no_op():
    script = f"""
const ROW = {{_name: 'grinder', _preFill: null, _filled: '', _fillErr: ''}};
const page = {{ {_extract("undoFill")} }};
page.undoFill(ROW);
console.log(JSON.stringify(ROW));
"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout)["_name"] == "grinder"


# ── the page-title cleaner ───────────────────────────────────────────────────────────────
#
# Server side, so plain Python. This is the half that stops a competitor's name reaching the
# catalogue in the first place; the before/after above is the half that catches what slips past.

from src.routes.pos_router import _clean_page_title      # noqa: E402


def test_the_exact_string_that_reached_angels_catalogue():
    """Live, on prod, 2026-08-03: jelly-joker.de's og:title, saved whole onto his grinder —
    another shop's name and their article number, one click from a printed shelf label."""
    got = _clean_page_title(
        "Ø50mm - 4-teiliger Champ High White Leaf Grinder [40506209] - Jelly-Joker",
        "https://www.jelly-joker.de/grinder/champ-high-white-leaf")
    assert got == "Ø50mm - 4-teiliger Champ High White Leaf Grinder"
    assert "Jelly-Joker" not in got and "40506209" not in got


def test_the_shop_name_goes_from_either_end():
    for title, expected in [
        ("Champ High Grinder | Jelly-Joker", "Champ High Grinder"),
        ("Jelly-Joker – Champ High Grinder", "Champ High Grinder"),
        ("Jelly-Joker | Champ High Grinder | Jelly-Joker", "Champ High Grinder"),
    ]:
        assert _clean_page_title(title, "https://jelly-joker.de/x") == expected


def test_a_shop_name_in_the_MIDDLE_is_left_alone():
    """Only decoration lives at the ends. In the middle it is part of what the thing is called,
    and this cleaner must never edit the product itself."""
    t = "Grinder - Jelly-Joker Edition - 50mm"
    assert _clean_page_title(t, "https://jelly-joker.de/x") == t


def test_only_the_sites_OWN_name_is_stripped():
    """A trailing word is not automatically noise. "Champ High Grinder - Blue" must survive, and
    so must a brand that happens to sit last."""
    t = "Champ High Grinder - Blue"
    assert _clean_page_title(t, "https://jelly-joker.de/x") == t
    assert _clean_page_title("Grinder - Gizeh", "https://jelly-joker.de/x") == "Grinder - Gizeh"


def test_article_numbers_go_but_real_bracketed_detail_stays():
    """4+ digits in brackets is a SKU. Sizes and counts are product facts and must survive."""
    assert _clean_page_title("Grinder [40506209]", "") == "Grinder"
    assert _clean_page_title("Grinder (123456)", "") == "Grinder"
    assert _clean_page_title("Papers (2 pcs)", "") == "Papers (2 pcs)"
    assert _clean_page_title("Grinder [50mm]", "") == "Grinder [50mm]"
    assert _clean_page_title("Rolls (100)", "") == "Rolls (100)"       # 3 digits — a count


def test_it_never_returns_an_empty_name():
    """A blank name is worse than a decorated one: it fails the save and loses the lookup."""
    assert _clean_page_title("Jelly-Joker", "https://jelly-joker.de/x") == "Jelly-Joker"
    assert _clean_page_title("[40506209]", "") == "[40506209]"
    assert _clean_page_title("   ", "") == ""


def test_it_survives_junk_input_without_raising():
    """It runs on whatever a shop published, and page-facts must never 500."""
    for title, url in [("", ""), ("x", "not-a-url"), ("a - b", None), ("Grinder", "http://[::1]")]:
        _clean_page_title(title, url or "")


def test_a_plain_title_with_no_decoration_is_untouched():
    assert _clean_page_title("Champ High White Leaf Grinder 4-part 50mm",
                             "https://jelly-joker.de/x") == "Champ High White Leaf Grinder 4-part 50mm"
