"""Department keys — selling the ~30% of stock that has no barcode and never will.

See `onboarding/ai-coach/SPEC-department-keys.md` for the full spec and the measurements
behind it. The short version, because it is the part that gets forgotten:

    A department line is NOT a product. It never enters the catalog, never syncs to the
    master, never appears in Artemis, and is never enriched after the fact.

WHY THIS EXISTS. Roughly a third of Artemis stock has no usable EAN — glass, grinders, pipes,
grow supplies. Measured on prod 2026-08-07: **7% of the catalogue is scannable at all** (Bongs
0/178, Bong & Pipe Accessories 0/253, Grinders 8/200). The cashier cannot and will not identify
those at the counter. Angel, on what actually happens today:

    "figure pam is not going to try harder than a single scan and if nothing to scan she will
     create a whole new bong and never search it out in the catalog"

That on-the-fly create is the thing this replaces. It pollutes the catalogue with unidentifiable
stubs and makes a fresh duplicate every time the same bong sells again.

WHY THE BUTTONS ARE THE CATALOGUE'S OWN HEADINGS, not a new invented list. The first draft of the
spec invented nine German names; Angel killed it looking at the catalogue's own category dropdown:

    "maybe these are the title categories, the ones in bold ... and maybe it falls into those
     categories already. So then somebody can sort it out later if they want."

The payoff is that a SCANNED grinder and a BUCKETED grinder land in the same bucket, so
"Grinders did 2,400 this month" is one honest number instead of two halves. `product_group`
below is that link — it is the same string the catalogue already stores on every product.

WHY `receipt` IS NOT THE PROPER GERMAN NOUN. It is the word the girls write in the paper day
book, read off a month of photographed pages (`onboarding/19-what-actually-sells.md`). They write
`Grips`, so the button says `Grips`. A button reading `Grinder` is one she has to translate
mid-sale, and the whole design rests on there being nothing to translate.
"""
from __future__ import annotations

from typing import Optional

# `vat_class` is a real `product_class` from catalog_taxonomy.PRODUCT_CLASSES, NOT a rate. VAT is
# resolved through the SAME `vat_resolver.line_vat` path every catalog line uses, so a department
# line cannot drift from the rest of the till and a future rate change is still data, not code.
#
# ⚠️ `Getränke` is the one button with a different rate, via `cafe_food` (dine-in 8.1 / takeaway
# 2.6). SPEC §10.1 Q5 is open: nobody has confirmed the shop actually charges the reduced rate
# today. If Ralph says everything rings at 8.1, change this to "standard" — matching the shop
# beats being technically right.
DEPARTMENTS: list[dict] = [
    {"code": "GLAS", "receipt": "Glas",      "en": "Glass",
     "product_group": "Smoking Gear", "category": "Bongs",
     "vat_class": "standard",
     "covers": "Bongs, Glas, Bubbler, Bong-Ersatzteile"},

    {"code": "GRIP", "receipt": "Grips",     "en": "Grinders",
     "product_group": "Smoking Gear", "category": "Grinders",
     "vat_class": "standard",
     "covers": "Alle Grinder — Plastik, Metall, Holz"},

    {"code": "ZUBE", "receipt": "Zubehör",   "en": "Accessories",
     "product_group": "Smoking Gear", "category": None,
     "vat_class": "standard",
     "covers": "Pfeifen, Aschenbecher, Dosen, Waagen, Schnupf, Pressen"},

    {"code": "VAPE", "receipt": "Vape",      "en": "Vape",
     "product_group": "Vape", "category": None,
     "vat_class": "tobacco_nicotine",
     "covers": "E-Liquid, Pods, Elfbar, Einweg, Verdampfer"},

    {"code": "TABA", "receipt": "Tabak",     "en": "Tobacco",
     "product_group": "Tobacco & Shisha", "category": None,
     "vat_class": "tobacco_nicotine",
     "covers": "Blau, Shisha, Kohle, Schläuche, Zigi einzeln"},

    {"code": "CBD",  "receipt": "CBD",       "en": "CBD & hemp",
     "product_group": "CBD & Hemp", "category": None,
     "vat_class": "cbd_hemp",
     "covers": "Blow, Local Mary, Local Weed, Öle, Hasch"},

    {"code": "DEKO", "receipt": "Deko",      "en": "Lifestyle & gifts",
     "product_group": "Lifestyle & Gifts", "category": None,
     "vat_class": "standard",
     "covers": "Räucherstäbchen, Deko, Tüten, Textilien, Karten"},

    {"code": "GROW", "receipt": "Dünger",    "en": "Grow supplies",
     "product_group": "Grow & Lab", "category": None,
     "vat_class": "standard",
     "covers": "Dünger, Substrat, Drogentests"},

    {"code": "GETR", "receipt": "Getränke",  "en": "Drinks & snacks",
     "product_group": "Cafe & Food", "category": None,
     "vat_class": "cafe_food",
     "covers": "Kühlschrank, Snacks"},

    # ALWAYS LAST. SPEC §3.5: if the catch-all is the easiest key to reach, everything becomes
    # Diverses and the data is worthless. Order here drives the order on the till strip.
    {"code": "DIV",  "receipt": "Diverses",  "en": "Misc",
     "product_group": None, "category": None,
     "vat_class": "standard",
     "covers": "Alles andere"},
]

# Deliberately NOT departments — recorded so the decision is not silently redone (SPEC §3.3):
#   Papers & Rolling — 653 rows, 120 already scan, rank 1 in the day book. A button here would
#                      throw away the only good data the shop has.
#   Unsorted / System — a junk drawer, not a shelf. Nothing is "sold from Unsorted".

_BY_CODE = {d["code"]: d for d in DEPARTMENTS}

# SPEC §3.5. Ten used, and the cap is ten: adding an 11th means removing one, because every
# extra button is a decision at the till with a customer waiting.
MAX_DEPARTMENTS = 10


def all_departments() -> list[dict]:
    """The buttons, in strip order (Diverses last). Safe to hand straight to the till."""
    return [dict(d) for d in DEPARTMENTS]


def get_department(code: Optional[str]) -> Optional[dict]:
    """The department for a code, or None. Case-insensitive; whitespace tolerated."""
    if not code:
        return None
    return _BY_CODE.get(str(code).strip().upper())


def is_department(code: Optional[str]) -> bool:
    return get_department(code) is not None


def receipt_text(code: Optional[str]) -> str:
    """What the customer sees on the receipt, and what the day-close block is labelled with."""
    d = get_department(code)
    return d["receipt"] if d else (code or "")


def vat_class(code: Optional[str]) -> str:
    """The `product_class` this department's VAT resolves through.

    A department line has no product, so without this it would fall through to "standard" and
    every fridge drink would be taxed at the full rate. Returns "standard" for an unknown code —
    the legally-conservative default, never a crash at the till.
    """
    d = get_department(code)
    return d["vat_class"] if d else "standard"
