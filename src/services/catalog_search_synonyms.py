"""Bilingual + brand search-term expansion for the till (BL-101 durable layer).

The Artemis catalog is stored in GERMAN — categories ("Feuerzeuge", "Waagen") and
names ("Feuerzeug BIC mini"). Staff and tourists search in ENGLISH ("lighter", "scale")
or by BRAND ("bic", "raw"). A plain trigram/ILIKE match cannot bridge "lighter" ->
"Feuerzeug": the two strings share no letters, so word-similarity scores ~0.

This module maps how people ASK to how the catalog is STORED. `expand_search_terms`
returns the German/variant terms of any concept the query hits; the till search
(`search_products_fast`) then also matches AND boosts products whose category or name
contains one of them — so "lighter" reaches every item in category "Feuerzeuge".

Curated ON PURPOSE (not ML): the concept list is built from the shop's REAL active
categories (pulled from prod 2026-07-14). To add a concept, append a list of equivalent
lowercase terms. Keep the GERMAN catalog word (the one that actually appears in
`products.category` / name) in the list, or an English query will expand to nothing that
exists in the data. This is the honest ceiling of a text layer: it makes an item
FINDABLE; brand + type is what makes it FAST (see the search-hint tooltip).
"""
import re

# Each inner list = ONE concept: every way people say it (DE + EN + variants), lowercase.
# The German catalog term MUST be present so an English ask expands to a stored string.
SYNONYM_CONCEPTS: list[list[str]] = [
    ["lighter", "lighters", "feuerzeug", "feuerzeuge"],
    ["grinder", "grinders", "mühle", "muehle", "crusher"],
    ["scale", "scales", "waage", "waagen", "digitalwaage"],
    ["bong", "bongs", "waterpipe", "wasserpfeife", "bong pfeifenzubehoer"],
    ["pipe", "pipes", "pfeife", "pfeifen"],
    ["tobacco", "tabak", "drehtabak", "rolling tobacco"],
    ["shisha tobacco", "shishatabak", "shisha tabak", "molasse"],
    ["shisha", "shishas", "hookah"],
    ["paper", "papers", "rolling paper", "rolling papers", "blättchen", "blaettchen", "drehpapier"],
    ["filter", "filters", "tips", "filter tips"],
    ["ashtray", "ashtrays", "aschenbecher"],
    ["storage", "stash", "aufbewahrung"],
    ["stash box", "stashbox", "hidden safe", "verstecktresor", "verstecktresore", "tresor"],
    ["tray", "trays", "rolling tray", "schalen", "schalen trays"],
    ["coal", "charcoal", "kohle"],
    ["snuff", "schnupftabak", "schnupfutensilien"],
    ["knife", "knives", "messer"],
    ["press", "pollen press", "presse", "pressen"],
    ["rolling machine", "drehmaschine", "drehmaschinen", "stopfmaschine", "stopfmaschinen"],
    ["cone", "cones", "hülsen", "huelsen", "joint huelsen cones"],
    ["blunt", "blunts", "blunt wrap"],
    ["vaporizer", "vaporiser", "verdampfer"],
    ["liquid", "liquids", "e-liquid", "eliquid", "juice"],
    ["pod", "pods", "coil", "coils", "pods coils"],
    ["drug test", "drug tests", "drogentest", "drogentests"],
    ["cream", "balm", "salbe", "creme", "kosmetik", "cosmetic", "topical"],
    ["seeds", "samen", "hanfsamen"],
    ["decoration", "dekoration", "deko"],
    ["cbd", "hemp", "hanf"],
    # brand aliases where the ASK differs from the STORED spelling (most brands are already
    # a substring of the name, so only the awkward ones earn a row here).
    ["storz", "storz & bickel", "storz bickel", "storz und bickel"],
]


def _build_index(concepts: list[list[str]]) -> dict[str, frozenset]:
    """term -> the full set of terms in its concept (so any alias reaches the German word)."""
    idx: dict[str, set] = {}
    for group in concepts:
        members = set(group)
        for term in group:
            idx.setdefault(term, set()).update(members)
    return {k: frozenset(v) for k, v in idx.items()}


_INDEX = _build_index(SYNONYM_CONCEPTS)
# phrase concept-keys ("rolling paper", "storz & bickel") that a word-token split misses.
_MULTIWORD_KEYS = tuple(k for k in _INDEX if " " in k or "&" in k)
_TOKEN = re.compile(r"[a-zäöüß0-9]+", re.I)
_MAX_Q = 60

# --- German compounds (2026-08-07) -------------------------------------------------
# Token matching is EXACT, so "Aktivkohlefilter" — one word, as German writes it — expanded
# to NOTHING, while "Aktiv Kohle Filter" expanded to seven terms. Same concept, same shop,
# and filters are rank 2 in the day book. German compounds are head-FINAL: the last element
# is the type ("…filter", "…papier", "…waage"), which is exactly the word the concept index
# holds. So a suffix match on a long token recovers the concept.
#
# Deliberately conservative, because a bad expansion is worse than none — it would boost a
# whole unrelated shelf:
#   • suffix only (head-final), never an interior substring
#   • the token must be a real compound (>= 8 chars) with >= 3 chars left in front of the head
#   • FALSE FRIENDS are listed explicitly, measured against the live catalogue vocabulary
#     rather than imagined: "silicone" ends in "cone" but is not a joint tube.
_COMPOUND_MIN_TOKEN = 8
_COMPOUND_MIN_HEAD = 4
_COMPOUND_MIN_STEM = 3
# Found by running this expander over all 1,401 catalogue words of 8+ letters and READING the
# output — not by imagining what might go wrong. 70 words expand; these are the ones that were
# wrong, and "Durchmesser" is the dangerous one: diameter appears in half the bong and grinder
# names in this shop, and it would have boosted the entire knife shelf on a size query.
_FALSE_FRIENDS = frozenset((
    "durchmesser",   # DIAMETER — ends "messer" (knife). Everywhere in this catalogue.
    "rootjuice",     # BioBizz plant food — ends "juice" (e-liquid)
    "silicone",      # ends "cone" — a material, not a joint tube
    "silikon",
    "vaporizer",     # ends in its own key; harmless but skip the extra pass
))
_COMPOUND_HEADS = tuple(sorted(
    (k for k in _INDEX if " " not in k and "&" not in k and len(k) >= _COMPOUND_MIN_HEAD),
    key=len, reverse=True))          # longest head first: "digitalwaage" before "waage"


def _compound_concepts(token: str) -> frozenset:
    """Concept terms for a German compound noun, via its head. Empty when it isn't one."""
    if len(token) < _COMPOUND_MIN_TOKEN or token in _FALSE_FRIENDS:
        return frozenset()
    for head in _COMPOUND_HEADS:
        if token.endswith(head) and len(token) - len(head) >= _COMPOUND_MIN_STEM:
            return _INDEX[head]
    return frozenset()


def expand_search_terms(q: str) -> list[str]:
    """Extra German/variant terms to also match+boost for a raw query.

    Matches the WHOLE query and each word token against the concept index (so both
    "lighter" and "bic lighter" expand to the "feuerzeug…" concept), plus any multi-word
    concept key contained in the query ("digital scale", "rolling paper"). Returns a
    de-duped, sorted list — INCLUDING the query's own concept terms (the caller matches
    these against category, which the base query never checks). Empty when nothing is
    recognised: the caller then runs the plain search entirely unchanged.
    """
    q = (q or "").strip().lower()
    if not q or len(q) > _MAX_Q:
        return []
    candidates = set(_TOKEN.findall(q))
    candidates.add(q)
    hits: set[str] = set()
    for c in candidates:
        if c in _INDEX:
            hits |= _INDEX[c]
        else:
            # not a known term on its own — it may be a German compound whose HEAD is one
            hits |= _compound_concepts(c)
    for key in _MULTIWORD_KEYS:
        if key in q:
            hits |= _INDEX[key]
    return sorted(hits)
