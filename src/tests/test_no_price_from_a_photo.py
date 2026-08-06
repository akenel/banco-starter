"""A photograph must never set a price. Not a guess, not a sticker it can read.

2026-08-06, found by Angel running five shelf photos through snap-find. He photographed three
wooden grinders with a hand-written `10.-` sticker in frame and marked it FAIL twice:

    "Did it read the 10.- sticker as a price?"                         FAIL
    "Mark FAIL if a price appeared anywhere it could be saved"         FAIL

The `product` vision domain was asking for it outright —

    '"price_estimate" a number in CHF if you can guess from the type, else null'

— and four screens auto-filled the answer into a saveable field the instant that field was blank:

    scan.html      -> lazyPrice   (the TILL)
    catalog.html   -> form.price  (new product)
    receiving.html -> newPrice    (goods-in, then applyTradeDiscount())
    kiosk.html     -> cPrice

The catalogue rows for those grinders are CHF 39.00 and CHF 12.90. Nothing errored, nothing
looked wrong, and a number invented by a language model was one Save away from being what a
customer pays.

`read_product_page`, 140 lines further down the SAME file, has refused to return a price since
the day it shipped, with the reason written in its docstring: *"a wrong price overcharges a
customer."* Two paths in one file, opposite rules. This is the 2026-08-03 shape again — the fix
existed, on the other side of the module.

These tests pin BOTH halves, because either one alone leaves the hole open:
  * the prompt/coerce must not produce a price even if a model volunteers one, and
  * no template may assign a snap/suggestion field into a price input.
"""
import pathlib
import re

import pytest

from src.services.vision import PRODUCT, _coerce_product

SRC = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = SRC / "templates" / "pos"

# Every screen that can take an AI product read. If a new one appears, add it here.
SNAP_SCREENS = ["scan.html", "catalog.html", "receiving.html", "kiosk.html"]


def test_the_prompt_never_asks_for_a_price():
    p = PRODUCT.prompt.lower()
    assert "price_estimate" not in p, "the product prompt is asking for a price again"
    for word in ("guess", "estimate"):
        assert f'"{word}' not in p, p
    # and it must say so out loud, so a future edit has to delete an explicit instruction
    assert "do not return a price" in p, "the prompt must forbid a price explicitly"


@pytest.mark.parametrize("volunteered", [
    {"name": "Holz Grinder", "price_estimate": 10},
    {"name": "Holz Grinder", "price_estimate": "10.00"},
    {"name": "Holz Grinder", "price": 10},
    {"name": "Holz Grinder", "price_chf": 10, "sticker_price": "10.-"},
])
def test_coerce_drops_a_price_the_model_volunteered(volunteered):
    """The model can still SEE the sticker. The coerce is what makes that harmless.

    A cached or hand-rolled prompt elsewhere could still return a price; dropping it at the
    boundary means no caller ever has one to auto-fill."""
    out = _coerce_product(volunteered)
    assert out["name"] == "Holz Grinder"
    leaked = [k for k in out if "price" in k.lower()]
    assert not leaked, f"price leaked through coerce: {leaked} -> {out}"


def test_no_screen_autofills_a_price_from_an_ai_read():
    """The half that actually moved money: an assignment INTO a price field.

    Matches `<anything>price... = <suggestion-ish>`, e.g.
        this.lazyPrice = s.price_estimate
        this.form.price = s.price_estimate
    Reading a price from a real catalog row (`m.price`, `p.price`) is fine and must stay —
    that is the shop's own number, not the model's."""
    offenders = []
    # left side is a price field; right side comes off the AI suggestion object (s./d.suggestion)
    pat = re.compile(
        r"^(?P<line>.*?\b(?:this\.)?[A-Za-z_.]*[Pp]rice\b\s*=\s*"
        r"(?:String\()?\s*(?:s|sug|suggestion|d\.suggestion)\.[A-Za-z_]+.*)$",
        re.M)
    for fname in SNAP_SCREENS:
        f = TEMPLATES / fname
        assert f.exists(), f"{fname} moved — update SNAP_SCREENS"
        for m in pat.finditer(f.read_text(encoding="utf-8")):
            offenders.append(f"{fname}: {m.group('line').strip()}")
    assert not offenders, (
        "a screen is auto-filling a price from an AI read again:\n  "
        + "\n  ".join(offenders))


def test_page_reader_and_photo_reader_now_agree():
    """The two AI paths must hold the same rule — that mismatch was the whole bug."""
    from src.services import vision
    # the page prompt is assembled from _PAGE_PROMPT_HEAD + _PAGE_PROMPT_TAIL — join every part
    parts = [getattr(vision, n) for n in dir(vision)
             if n.startswith("_PAGE_PROMPT") and isinstance(getattr(vision, n), str)]
    assert parts, "no _PAGE_PROMPT* found — did the page reader get renamed?"
    page_prompt = "\n".join(parts).lower()
    assert "not return a price" in page_prompt, "the page reader stopped forbidding prices"
    assert "do not return a price" in PRODUCT.prompt.lower()
