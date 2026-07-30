"""Known brand names — the taxonomy that stops `Canna` matching `Cocanna`.

WHY THIS FILE EXISTS. Duplicate detection compares product names, and character-based
similarity has no idea what a brand is. Measured against the live catalog 2026-07-31:

    Canna Coco A 1L               <-> Beamer Candles Cocanna Banana    0.50
    Aperol Spritz                 <-> Dosier Spritze 1ml               0.43
    Juicy Jays Raspberry Incense  <-> Juicy Jays Rolls Raspberry       0.50
    Blow pure                     <-> Local Weed vorgebauter Joint     0.70

Every one is obvious to a human in a quarter of a second, and invisible to trigram
similarity. The fix is not a cleverer score — it is knowing that `Canna` and `Cocanna` are
different companies.

Angel's framing: *"we have suppliers, but they're wholesalers. They have product lines. But we
need names like Gizeh or RIPS or Biobizz so we know these are brand names... a file we set up
once, and then add to it as new companies come along."*

HOW TO EXTEND IT. Add the brand, lowercase, to the right bucket. That is the whole procedure.
An unknown brand is not an error — the matcher simply falls back to plain similarity for that
pair, exactly as it behaved before. **Never add a category noun** (grinder, bong, tabak,
vaporizer): those appear in hundreds of unrelated products and would suppress real matches.

Seeded from the live Artemis catalog (most common leading tokens, hand-filtered) plus the
brands Angel named at the shelf.
"""
from __future__ import annotations

import re

# Grouped only for human readability — the matcher treats it as one flat set.
BRANDS: set[str] = {
    # ── papers, tips, rolls ──
    "raw", "gizeh", "smoking", "rips", "greengo", "juicy", "elements", "ocb",
    "blaze", "purize", "actitube", "cone", "cones", "g-rollz", "grollz", "moon",
    "jass", "swan", "rizla", "mascotte", "bob", "kavatza",
    # ── CBD / hemp ──
    "blow", "cannatonic", "harlequin", "heimat", "botanicals", "swisscbd",
    "localweed", "local",
    # ── grow nutrients & substrate ──
    "canna", "biobizz", "plagron", "guanokalong", "metrop", "hesi", "atami",
    "advanced", "aptus", "ecolizer", "greenhouse", "terra",
    # ── vape hardware ──
    "elfbar", "geekvape", "vaporesso", "innokin", "uwell", "voopoo", "eleaf",
    "joyetech", "vozol", "smok", "aspire", "lostmary", "wolkenkraft", "storz",
    "davinci", "arizer", "puffco", "dynavap", "xmax", "flowermate",
    # ── e-liquid ──
    "capella", "fruizee", "aisu", "curieux", "nasty", "riot", "dinner",
    "twelve", "bad", "pod", "salt",
    # ── shisha ──
    "adalya", "aeon", "alfakher", "hookain", "darkside", "musthave", "oduman",
    # ── lighters, accessories, misc ──
    "zippo", "clipper", "bic", "beamer", "storm", "jetflame", "tresor",
    # ── drinks & snacks ──
    "quöllfrisch", "quollfrisch", "feldschlösschen", "feldschlosschen",
    "aperol", "redbull", "coca", "rivella", "curaprox",
}

# Words that LOOK like a leading brand but are categories. Listed so nobody adds them by
# accident when extending from a token-frequency dump — every one of these appears in the
# catalog's top-45 leading tokens and would wreck matching.
NOT_BRANDS: set[str] = {
    "grinder", "bong", "tabak", "vaporizer", "shisha", "liquid", "adapter",
    "aschenbecher", "filterpapier", "aktivkohlefilter", "schnupftabak",
    "rolling", "joint-pack", "blech-dose", "glas-steckkopf", "metallpfeife",
    "zigaretten", "grip", "black", "big", "double", "just", "lost", "pipe",
    "dose", "papers", "filter", "tips", "rolls", "kit", "set", "box",
}

_TOKEN = re.compile(r"[a-zA-ZäöüÄÖÜßé0-9+-]+")


def brand_of(name: str | None) -> str | None:
    """The brand a product name belongs to, or None if we don't recognise one.

    Looks at the first few tokens rather than only the first: real titles lead with the brand
    ("Gizeh King Size") but plenty lead with a category ("Aktivkohlefilter Purize"), and both
    should resolve to the same brand.
    """
    if not name:
        return None
    for tok in _TOKEN.findall(name.lower())[:4]:
        if tok in NOT_BRANDS:
            continue
        if tok in BRANDS:
            return tok
    return None


def _tokens(name: str | None) -> set[str]:
    return set(_TOKEN.findall((name or "").lower()))


def brands_conflict(a: str | None, b: str | None) -> bool:
    """True when two names cannot be the same product because a brand is missing or differs.

    The rule is stronger than "both sides name a brand and they differ", which was too weak in
    practice — it let `Aperol Spritz` match `Dosier Spritze 1ml`, because `Dosier` is a category
    word and resolves to no brand at all.

    So: **if either side names a brand we know, that brand must appear as a whole token on the
    other side.** Whole token matters — it is what separates `canna` from `cocanna`, which is a
    substring and a different company.

    Still conservative in the direction that counts. If NEITHER side names a known brand we
    return False and the caller falls back to plain similarity, exactly as before. This can only
    ever suppress a proposed match, never create one — and a suppressed match costs a few
    seconds of typing, whereas a wrong one silently corrupts the catalog.
    """
    ba, bb = brand_of(a), brand_of(b)
    if not ba and not bb:
        return False
    ta, tb = _tokens(a), _tokens(b)
    if ba and ba not in tb:
        return True
    if bb and bb not in ta:
        return True
    return False
