"""Catalog taxonomy — the single source of truth for product CATEGORY and CLASS.

Two axes, two jobs (BL-96):
  * CATEGORY = merchandising. What the thing IS — for the wall + reports. A seeded skeleton
    that can grow freely (taste).
  * CLASS = behaviour. How the till TREATS it — age gate, VAT, compliance. A CONTROLLED set,
    because it drives money + law (a cashier can't invent a tax class).

`is_age_restricted` on a product is DERIVED from its class (set on save) so it can never drift
out of sync — but stays overridable via CRUD for an oddball.

This module also holds the rules-based classifier that maps the 7,272 FourTwenty reference items
onto the skeleton. It is re-runnable (scripts/reclassify_reference.py) — refine the rules here,
re-run, done.
"""
import html
import re

# --- CATEGORIES (merchandising skeleton — seeded, extensible) --------------------------------
CATEGORIES = [
    "CBD & Hemp", "Edibles", "Creams & Topicals", "Papers & Filters", "Grinders",
    "Lighters", "Pipes & Bongs", "Vaporizers", "E-Liquids", "Tobacco & Cigarettes",
    "Alcohol", "Grow Supplies", "Café", "Merch", "Accessories", "Other",
]

# --- CATEGORY EMOJI (display only — never behaviour) -----------------------------------------
# One server-owned place so every category ALWAYS shows a consistent emoji, including ones a
# shop types on the fly. Resolution order:
#   1. an explicit override (the future Category-CRUD will store a chosen emoji → pass it here)
#   2. a curated emoji for a known category (skeleton + common aliases) — looks "right"
#   3. a STABLE deterministic pick from the pool (same name → same emoji, forever; never blank)
# When the Category table + emoji-picker build lands, only step 1 changes — callers/UI stay put.
CATEGORY_EMOJI = {
    # skeleton (CATEGORIES above)
    "CBD & Hemp": "🌿", "Edibles": "🍬", "Creams & Topicals": "🧴", "Papers & Filters": "📄",
    "Grinders": "⚙️", "Lighters": "🔥", "Pipes & Bongs": "🌀", "Vaporizers": "💨",
    "E-Liquids": "🧪", "Tobacco & Cigarettes": "🚬", "Alcohol": "🍷", "Grow Supplies": "🌱", "Café": "☕",
    "Merch": "👕", "Accessories": "🎒", "Other": "🏷️",
    # common aliases / demo-seed names so existing data also looks right
    "CBD": "🌿", "Hemp": "🌿", "Cafe": "☕", "Coffee": "☕", "Bar": "🍺", "Beer": "🍺",
    "Wine": "🍷", "Drinks": "🥤", "Beverages": "🥤", "Food": "🍴", "Bakery": "🥐",
    "Snacks": "🍫", "Equipment": "⚙️", "Tobacco": "🚬", "Papers": "📄", "Vape": "💨",
}

# A pool of distinct, retail-neutral emojis for categories with no curated entry. Deterministic
# indexing means a typed-on-the-fly category gets a stable, intentional-looking icon every time.
_EMOJI_POOL = [
    "🛍️", "📦", "🎁", "🏷️", "🧺", "🧴", "🧪", "⚗️", "🔮", "💎", "🪙", "🔑", "🧰", "🛠️",
    "🔧", "🔩", "🧲", "🔋", "💡", "🕯️", "🔦", "📐", "📎", "✂️", "🖊️", "📒", "📕", "📗",
    "📘", "📙", "🗂️", "📌", "🧷", "🎒", "👜", "👛", "🧳", "👕", "👖", "🧢", "🧤", "🧣",
    "👟", "🕶️", "⌚", "💍", "🌿", "🍃", "🌱", "🌵", "🌴", "🌷", "🌹", "🌻", "🍀", "🍄",
    "🌰", "🫘", "🌶️", "🫚", "🧄", "🧅", "🥕", "🌽", "🥔", "🍅", "🍆", "🥑", "🍇", "🍈",
    "🍉", "🍊", "🍋", "🍌", "🍍", "🥭", "🍎", "🍐", "🍑", "🍒", "🍓", "🫐", "🥝", "🥥",
    "🍫", "🍬", "🍭", "🍯", "🍪", "🥐", "🥨", "🥯", "🧀", "🍵", "☕", "🧃", "🥤", "🧉",
    "🍶", "🍷", "🍸", "🍹", "🍺", "🥃", "🧊", "🍴", "🥢", "🧫", "🔬", "🧯", "🪔", "🎨",
    "🖌️", "🪕", "🎲", "🧩", "🎯", "🪀", "🪁", "🎏", "🎐", "🪴",
]


def category_emoji(category, override=None):
    """Display emoji for a category name. Never returns blank; stable for a given name.
    `override` (future Category-CRUD) wins so a shop can curate its own icon later."""
    if override:
        return override
    if not category:
        return "🏷️"
    name = str(category).strip()
    if name in CATEGORY_EMOJI:
        return CATEGORY_EMOJI[name]
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return _EMOJI_POOL[h % len(_EMOJI_POOL)]


# --- CLASSES (behaviour — controlled; each drives age / VAT / compliance) ---------------------
# vat: "standard" = 8.1% · "reduced" = 2.6% · "cafe_split" = dine-in 8.1% / takeaway 2.6% (asked at sale)
# promo_restricted: True = promotional discounts + loyalty-credit redemption are restricted.
#   * Tobacco / Nicotine — sales-promotion restrictions (Tabakproduktegesetz + cantonal rules).
#   * Alcohol — no below-cost / loss-leader / giveaway promos (Alkoholgesetz).
#   CBD / Hemp / standard / café are NOT promo-regulated — discount freely.
#   (Flag only — enforcement (warn-on-discount + block credit redemption) lands in Phase F.
#    Exact scope still needs Felix's Treuhänder/lawyer sign-off.)
PRODUCT_CLASSES = {
    "standard":         {"label": "Standard goods",      "age_restricted": False, "vat": "standard",   "compliance": None,         "promo_restricted": False},
    # Neutral 18+ bucket for on-the-fly quick-adds: the cashier's "18+?" toggle needs a class that
    # ACTUALLY drives the checkout age gate (which reads product_class, not the is_age_restricted
    # column) without wrongly restricting discounts (tobacco/alcohol) or triggering a THC report
    # (cbd_hemp). A manager can re-class it precisely later in the cleanup cockpit.
    "age_restricted":   {"label": "Age-restricted 18+",  "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": False},
    "tobacco_nicotine": {"label": "Tobacco / Nicotine",  "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": True},
    "alcohol":          {"label": "Alcohol",             "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": True},
    "cbd_hemp":         {"label": "CBD / Hemp — 18+ (flower·hash·vape·edibles)", "age_restricted": True,  "vat": "standard",   "compliance": "thc_report", "promo_restricted": False},
    "cbd_open":         {"label": "CBD / Hemp — open (oils·seeds·cosmetics)",     "age_restricted": False, "vat": "standard",   "compliance": "thc_report", "promo_restricted": False},
    "cafe_food":        {"label": "Café food & drink",   "age_restricted": False, "vat": "cafe_split", "compliance": None,         "promo_restricted": False},
}
DEFAULT_CLASS = "standard"


def class_meta(cls: str | None) -> dict:
    return PRODUCT_CLASSES.get(cls or DEFAULT_CLASS, PRODUCT_CLASSES[DEFAULT_CLASS])


def class_is_age_restricted(cls: str | None) -> bool:
    """Single rule: a product is 18+ iff its class says so (the till + receiving read this)."""
    return class_meta(cls)["age_restricted"]


def class_promo_restricted(cls: str | None) -> bool:
    """True iff promotional discounts / loyalty-credit redemption are restricted (tobacco, alcohol)."""
    return class_meta(cls).get("promo_restricted", False)


def reconcile_age(product_class: str | None, is_age_restricted: bool | None) -> tuple[str, bool]:
    """Keep product_class (the source of truth) and the is_age_restricted flag consistent.

    The checkout age gate reads product_class, NOT the boolean column — so a bare "18+" toggle
    must land on a class that actually gates. If the caller flipped 18+ on an otherwise unclassed
    item (the on-the-fly quick-add, the cleanup cockpit), file it under the neutral "age_restricted"
    class; a manager can re-class it precisely (tobacco/cbd/…) later. Then always DERIVE the flag
    from the (possibly updated) class so the two can never drift.

    The toggle is BIDIRECTIONAL for the NEUTRAL bucket: flipping 18+ OFF on an "age_restricted"
    item demotes it back to standard (field 2026-07-08: editing 18+ off "saved" but stayed 18+,
    because the flag was re-derived from the unchanged class). It never un-gates a REAL substance
    class (tobacco/alcohol/cbd_hemp) via the toggle — those stay gated; reclass them explicitly.
    Returns (class, flag)."""
    cls = product_class or DEFAULT_CLASS
    if is_age_restricted and not class_is_age_restricted(cls):
        cls = "age_restricted"            # toggle ON a plain item → the neutral 18+ bucket
    elif is_age_restricted is False and cls == "age_restricted":
        cls = DEFAULT_CLASS               # toggle OFF the NEUTRAL bucket → standard (the fix)
    return cls, class_is_age_restricted(cls)


# --- CLASSIFIER: (title + FourTwenty category) -> (our_category, our_class, age_restricted) ---

# Negative guard so "tobacco-free" / "nikotinfrei" / "0mg" / herbal substitute never trip 18+.
# NOTE the \b0\s*mg\b boundary: without it, "20mg" (a NICOTINE e-cig) contains "0mg" and would be
# falsely cleared. "tabakersatz"/"kräutermischung" = herbal tobacco-substitute (no nicotine) = open.
_AGE_NEG = re.compile(r"tabakfrei|tobacco.?free|nikotinfrei|nicotine.?free|ohne\s+nikotin|\bno\s*nic\b|\b0\s*mg\b|null\s*nikotin|alkoholfrei|alcohol.?free|kräuter.?mischung|\bherbal\b|tabakersatz", re.I)
_TOBACCO = re.compile(r"tabak|tabacc|tobacco|zigar|sigaret|cigaret|nikotin|nicotin|\bsnus\b|nikotinbeutel|nicotine\s*pouch", re.I)
# Branded cigarettes + pack tokens the plain-tobacco regex misses. FourTwenty ships real cigarette
# packs titled "Marlboro Gold 10x20cig" / "Parisienne Jaune 8x25cig" — no "tabak"/"zigarette" in the
# title at all, so they leaked through as un-gated "standard" goods. Catch the brands + the NNxNNcig
# pack pattern + MYO/RYO loose-tobacco + HEETS/IQOS.
_CIG = re.compile(r"\bmarlboro\b|\bparisienne\b|\bcamel\b|\bwinston\b|gauloises|lucky\s*strike|\bchesterfield\b|american\s*spirit|\bpueblo\b|\bphilip\s*morris\b|\d+\s*x?\s*\d*\s*cig\b|\bcig\b|\bmyo\b|\bryo\b|\bheets\b|\biqos\b", re.I)
# Cigars / cigarillos — tobacco products the cigarette rules miss (field 2026-07-08:
# "Swisher Sweets" + "Smock Woods … Cigars" leaked as un-gated 'standard'). Brands (Swisher,
# Backwoods) + generic cigar/cigarillo terms. 0mg/herbal still veto via _AGE_NEG.
# ("blunt wrap" used to live here; it moved to _BLUNT below, which is wider AND has a veto.)
_CIGAR = re.compile(r"\bswisher\b|backwoods|cigarillo|zigarillo|\bcigars?\b|\bzigarre\b|\bzigarren\b|stumpen|\bcheroot\b|black\s*&?\s*mild|smock\s*woods", re.I)

# Blunts and wraps. FIELD FINDING 2026-08-27 (Artemis, counted from the live shop): **42
# blunts and wraps could be sold with no ID check**, while 35 near-identical products on the
# SAME SHELF were gated correctly. The split was arbitrary — "Blunt Wrap Platinum" gated,
# "Cyclones Blunt Hemp" did not — and the reason was pure word adjacency: the old pattern was
# `blunt\s*wraps?`, so it needed those two words TOUCHING. Every real title puts something
# between them ("Blunt HEMP Wraps", "Blunt CLEAR mit Filter", "Cone BLUNTS"), or drops one of
# them entirely ("Juicy Jays Blunts", "Hemp Wraps", "Super Wrap"). Angel checked the physical
# packet: it carries a cigarette-style tobacco health warning. The box settles it.
#
# So the WORD is the signal, not the pair. But "Blunt" is also a DESIGN name on hardware and a
# SHAPE name on glass, which is why this cannot be a bare \bblunts?\b. Measured over 11,009
# feed titles and 5,061 of our own products, a bare pattern newly gated 27 + 25 rows, and
# exactly 7 + 2 of those were hardware:
#
#     Lit Stick 2in1 Glas Blunt          a reusable GLASS PIPE shaped like a blunt
#     Tin Box - Blunt Orbit              a storage tin; "Blunt Orbit" is the printed artwork
#     Rolling Tray S Blunt Orbit         the same artwork on a tray
#     Fourtwenty Blunt Geko … Grinder    a grinder
#
# Nothing else. The veto is deliberately about the OBJECT (glass, tin, tray, grinder), never
# about a flavour or a brand, because a flavour word is exactly what an over-broad veto would
# use to let a real blunt through. LESSON #2.
_BLUNT = re.compile(r"\bblunts?\b|hemp\s*wraps?|super\s*wraps?", re.I)
_BLUNT_HARDWARE = re.compile(r"gla[sß]\s*blunt|glass\s*blunt|tin\s*box|blech-?dose|rolling\s*tray|\btray\b|grinder", re.I)
# 2026-08-21: the Swiss/German words were missing, so a bottle in FourTwenty's "Spirituosen"
# bucket classified `standard` — 17 of 44 spirits and ALL 5 of "Bier, Wein & Champagner"
# would have been imported un-gated. Substance words only, never brand names: "Bacardi" in a
# title is a rum, but "Bacardi" on a flavoured paper is not, and _FLAVOUR_PAPER already has
# to veto that. `alkoholfrei` stays vetoed by _AGE_NEG.
# Word-bounded where a spirit's name hides inside an ordinary word: the first cut gated
# **"Brandywine (Solanum lycopersicum)"** — a TOMATO variety in FourTwenty's Indoorgrowing
# bucket — as alcohol. One confident wrong answer in 10,082 is still a confident wrong answer.
_ALCOHOL = re.compile(r"alkohol|alcohol|vodka|wodka|\brum\b|whisky|whiskey|\bgin\b|liqueur|likör"
                      r"|absinth|\bbier\b|\bwein\b|spirituos|schnaps|\btequila\b|\bcognac\b|\bbrandy\b"
                      r"|\bgrappa\b|champagner|prosecco|\bsekt\b|aperitif|vermouth", re.I)
# Shisha bucket is MIXED: molasses tobacco (18+) sits beside hoses/charcoal/foil/adapters (open).
# These markers make a shisha line the actual 18+ substance — the brands are ALWAYS molasses
# tobacco, so they gate off the title alone even when the supplier category is a generic dump.
_SHISHA_TOBACCO = re.compile(r"shisha\s*tabak|shishatabak|\btabak\b|molasse|al\s*fakher|\badalya\b|\bnakhla\b|serbetli|\bstarbuzz\b|\bfumari\b", re.I)
# Nicotine e-cigarettes: a vape context + a NON-ZERO nicotine strength ("20mg"). The (?!0) keeps
# "0mg" / nicotine-free out; the mg is 1–2 digits so CBD's 100/500/1000mg never trips it. Vape
# context (device words or the vape category) scopes it so a "CBD 20mg" edible isn't caught.
_ECIG_CONTEXT = re.compile(r"disposable|\bpod\b|\bvape\b|e-?zigar|\bpuff\b|elf\s*bar|elfbar|\bvozol\b|\bhoke\b|lost\s*mary|maryliq|geek\s*bar|\belux\b|\bwaka\b|\baisu\b|nic\s*salt|\bnicsalt\b|vaporiz|e-?liquid|\bliquids?\b|\b\d{1,3}\s*ml\b", re.I)
_NIC_MG = re.compile(r"\b(?!0\b)\d{1,2}\s*mg\b", re.I)
# Disposable-vape brands: their consumables (refill / prefilled pod / nachfüllbehälter) are nicotine
# by default — Artemis names them "…Refill Blueberry Ice" / "…Nachfüllbehälter …20mg" (no "disposable"
# word), which the FourTwenty-tuned rules missed. A "refill" ONLY counts as nicotine next to one of
# these brands, so a lighter's "gas refill" is never caught. 0mg / OHNE NIKOTIN still veto (via _AGE_NEG).
_VAPE_BRAND = re.compile(r"elf\s*bar|elfbar|lost\s*mary|maryliq|\bvozol\b|geek\s*bar|\belux\b|\bwaka\b|\bhoke\b|\baisu\b", re.I)
_VAPE_REFILL = re.compile(r"\brefill\b|nachf(?:ü|ue)ll", re.I)
# The FORM carries nicotine by default: a "disposable" or a "prefilled pod" ships with e-liquid,
# and in CH/EU that's nicotine unless the title explicitly says "No Nic" / "0mg" (caught by _AGE_NEG).
# This catches the pods/disposables that carry no "NNmg" token in the title at all. Empty hardware
# (refillable / replacement / bare "…Ohm" pods, kits with no liquid) has neither word → stays open.
_ECIG_FORM = re.compile(r"\bdisposable\b|prefilled\s*pod", re.I)
# Inside the tobacco/cigarette category group, these titles are ACCESSORIES/herbal, not the substance
# (filling machines, filter tubes, papers). They must NOT inherit the group's 18+ flag.
_TOBACCO_ACCESSORY = re.compile(r"filling|filter|stopf|maschine|machine|hülse|\btube\b|papier|\bpaper|\btips?\b|\bkulu\b", re.I)
# Looks like tobacco/alcohol but is an ACCESSORY (a bag / holder / case), not the 18+ substance —
# so it never gets the age gate. (Kavatza Tabaktasche, Zigarettenhalter, Tabakbefeuchter…)
_SUBSTANCE_ACCESSORY = re.compile(
    r"tasche|portemonnaie|portmonnaie|halter|befeuchter|\betui\b|humidor|aufbewahr|löffel|\bspoon\b"
    # Storage that HOLDS the substance is not the substance. UAT dry run 2026-07-30 wanted to
    # age-gate "Joint-Pack für 4 Joints" and "Joint-Pack Smellproof Metal Tube" — a case and a
    # tube. Gating a container teaches staff the prompt is noise.
    r"|smell[- ]?proof|joint[- ]?pack|\bcase\b|geruchsdicht", re.I)
# Rum / whisky etc. as a FLAVOUR on papers/wraps/blunts — not alcohol. (Juicy Jay's Rum papers…)
_FLAVOUR_PAPER = re.compile(r"paper|\bwrap|blunt|blättchen|\bcone|juicy\s*jay", re.I)
# CBD in a NON-smokable, non-recreational form (oil / tincture / drops / seeds / cosmetics) — NOT
# age-gated (Angel: "the oils are not"). Everything else CBD (flower, hash, vape, edibles) stays 18+.
# Conservative on purpose: only CLEAR open forms land here, because this is the one no-ID class.
# CBD detection, deliberately wider than the literal word.
#
# FIELD FINDING 2026-07-29 (Artemis, Angel capturing stock): four BLOW pre-rolled CBD joints
# were classed `standard` and sellable with NO 18+ gate, because the classifier keyed on the
# literal "CBD" and the titles either omitted it ("BLOW Joint GREY Pure") or TRANSPOSED it
# ("BLOW CDB PRE JOINT RED"). Meanwhile "Blow Pre-built CBD Joint Pure" gated correctly — so
# whether a customer got asked for ID depended on a typo in a product title.
#
# So: accept the CDB transposition, and treat a handful of pre-roll BRANDS as CBD in their
# own right. A brand name is a far more reliable signal than a keyword the packaging may
# never print. Age-gating must not hinge on spelling.
# A CBD signal strong enough to trust from the DESCRIPTION rather than the title.
#
# WHY THE DESCRIPTION AT ALL. Angel: "You can't go just off the title. These names, they could
# be funky gorilla names. You'd have no idea." Exactly — strain and brand names say nothing
# about what a thing legally IS, and the titles are typed by hand at a counter (the live "CDB"
# was a typo made while copying off a package).
#
# WHY NOT JUST GREP THE DESCRIPTION FOR "CBD". Because rolling papers say "perfect for your CBD
# flower" and would start demanding ID — and over-gating trains staff to wave prompts away,
# which is worse than the leak. So the description must carry something an ACCESSORY never
# does: a CBD content figure, or an explicit pre-rolled form.
#
# The accessory guards can't help here either: a CBD joint ships "in a plastic tube", and
# _TOBACCO_ACCESSORY matches \btube\b — so vetoing on the description would kill the very
# product we need to gate.
_CBD_STRONG = re.compile(
    r"\d{1,2}\s*(?:[.,]\d+)?\s*%\s*(?:cbd|cdb)"            # "12% CBD"
    r"|(?:cbd|cdb)[\s-]*(?:gehalt|content|anteil|value)"       # "CBD-Gehalt", "CBD content"
    r"|vorgebaute?r?\s+(?:cbd\s+)?joint|pre[-\s]?rolled?\s+(?:cbd\s+)?joint", re.I)
# NOT included, and this is the whole point of the pattern being narrow: a bare mention of
# "CBD flower" / "CBD Blüten". Rolling papers say "ideal zum Drehen von CBD Blüten" and would
# start demanding ID — verified, it over-gated Smoking and RAW on the first run. A real CBD
# flower product states it in its TITLE, which the layer-3 title path already catches.

_CBD_TOKEN = re.compile(
    r"\bcbd\b|\bcdb\b|cannabidiol"                 # incl. the common CDB transposition
    r"|\bblow\b.{0,24}\bjoint\b|\bjoint\b.{0,24}\bblow\b"   # BLOW pre-rolls
    r"|vorgebaute?r?\s+joint", re.I)
# NOT a bare "pre-roll": G-Rollz Prerolled cones are EMPTY flavoured papers, and gating them
# would ask a customer for ID to buy a booklet of cones. Pre-roll only counts in _CBD_STRONG,
# where it must be followed by "joint".

_CBD_OPEN = re.compile(r"\böl\b|\boil\b|\boel\b|tinktur|tincture|\bdrops?\b|tropfen|\bseed\b|\bseeds\b|\bsamen\b|kosmetik|cosmetic|creme|cream|salbe|\bbalm\b|lotion|serum", re.I)

# Ordered keyword -> category; first match wins. CBD checked before creams so "CBD oil" lands in CBD.
_CATEGORY_RULES = [
    (re.compile(r"grinder|mühle|mill\b", re.I),                                   "Grinders"),
    (re.compile(r"clipper|feuerzeug|lighter|sturmfeuer|\bbic\b|jet\s?flame", re.I), "Lighters"),
    (re.compile(r"bong|beaker|glaskopf|\bglas\b|pfeife|\bpipe|bubbler|chillum|\bdab|nektar|recycler", re.I), "Pipes & Bongs"),
    (re.compile(r"vapo|vaporiz|crafty|mighty|\bpax\b|dynavap|volcano", re.I),     "Vaporizers"),
    (re.compile(r"e-?liquid|\bliquid\b|\bbase\b|aroma|shake.?&.?vape", re.I),     "E-Liquids"),
    (re.compile(r"paper|blättchen|king\s?size|\bfilter|\btips?\b|\bcone|roach|rolling|drehmaschine|rolls?\b", re.I), "Papers & Filters"),
    # Grow nutrients by BRAND. Angel entered these by hand 2026-07-30 and every one landed in
    # "Unsorted" — the classifier knew Metrop but not the rest of the shelf. A fertiliser
    # bottle's title is the brand plus a product code ("CANNA PK 13/14", "Plagron Pure Zym"),
    # so brand is the only reliable handle.
    (re.compile(r"\bcanna\b|\bbio ?canna\b|plagron|biobizz|bio-?bizz|guanokalong|guano kalong"
                r"|\bmetrop\b|advanced nutrients|hesi|atami|\bterra ?(grow|bloom)\b"
                r"|rhizotonic|cannazym|\bboost\b.{0,12}\bml\b", re.I),            "Grow Supplies"),
    (re.compile(r"cbd|cdb|cannabidiol|\bhanf|\bhemp", re.I),                          "CBD & Hemp"),
    (re.compile(r"creme|cream|salbe|\bbalm|lotion|topical|massage", re.I),        "Creams & Topicals"),
    (re.compile(r"edible|gummi|schoko|chocolate|cookie|keks|\btee\b|\btea\b|honig|honey|lutsch|sirup", re.I), "Edibles"),
    (re.compile(r"\bgrow|dünger|substrat|\berde\b|\bseed|\bsamen|\bzelt|grow.?lamp|nährstoff", re.I), "Grow Supplies"),
    (re.compile(r"shirt|hoodie|\bcap\b|mütze|sticker|poster|patch|\bpin\b", re.I),     "Merch"),
    (re.compile(r"tray|ashtray|aschenbecher|storage|\bbox\b|\betui|stash|waage|scale|brush|reinig|tasche|portemonnaie|\bhalter\b|befeuchter|humidor", re.I), "Accessories"),
    # Alcohol LAST — same _ALCOHOL marker as the 18+ class, so a real bottle (vodka/bier/gin…) files
    # under Alcohol AND flags 18+ together. Placed last so a flavoured PAPER/EDIBLE/E-LIQUID ("Rum
    # Flavour Papers") is caught by its own product rule first and never mislabelled Alcohol.
    (_ALCOHOL,                                                                   "Alcohol"),
]

# FourTwenty's own clean buckets we trust as-is (only "Accessories"/"Themed"/"Promotions" are the dump).
_REF_CATEGORY_MAP = {
    "CBD": "CBD & Hemp",
    "Vaporizers": "Vaporizers",
    "E-Liquids": "E-Liquids",
}


def _reftags(raw, ref_category) -> str:
    """The supplier's OWN taxonomy, html-unescaped + lowercased into one searchable string.

    The title alone can't tell a Marlboro pack from a lighter, but FourTwenty files it under
    "Tabak, ... Zigaretten"; a CBD flower under "CBD Blüten"; a nicotine e-cig under "Disposable
    Einweg E-Zigaretten". The importer stows every feed column in `raw`, so we read the structured
    category groups straight from there — the strong, non-guessy signal. Empty for feeds without
    these columns, in which case classify() just leans on the title (unchanged behaviour)."""
    parts = []
    if isinstance(raw, dict):
        parts = [raw.get(k) for k in
                 ("categorygroup_1", "categorygroup_2", "categorygroup_3", "productcategory")]
    if ref_category:
        parts.append(ref_category)
    return html.unescape(" | ".join(p for p in parts if p)).lower()


def classify(title: str | None, ref_category: str | None = None, raw=None,
             description: str | None = None) -> tuple[str, str, bool]:
    """Map a reference item to (our_category, our_class, age_restricted). Pure + deterministic.

    CLASS is decided in three layers, most-certain first: (1) the TITLE says it outright (real
    tobacco / cigarette brand / alcohol); (2) the SUPPLIER CATEGORY says it (the reliable signal
    the title hides — nicotine e-cigs, shisha tobacco, CBD flower/pollen); (3) a TITLE-CBD
    fallback. The negative guards (0mg / nikotinfrei / herbal / tabakersatz) and the
    accessory guards veto at every layer, so a filling machine or a 0mg pod never gets gated."""
    t = title or ""
    tags = _reftags(raw, ref_category)
    neg = _AGE_NEG.search(t)

    # CLASS first (it drives the age flag).
    cls = DEFAULT_CLASS
    is_cbd = bool(_CBD_TOKEN.search(t))
    # (1) TITLE is decisive: named tobacco/cigarette, shisha molasses, or a nicotine e-cig — unless
    #     it's an accessory/herbal. Shisha brands + the mg-in-vape signal gate off the title alone,
    #     so they hold up even when the supplier category is a coarse dump ("Accessories"/"Vaporizers").
    # …and a CBD blunt is CBD, not tobacco. Without this veto "Legendary Premium CBD Blunt 2g"
    # moved cbd_hemp -> tobacco_nicotine: still 18+, so the age gate never noticed, but it
    # quietly dropped the `thc_report` compliance obligation that rides on cbd_hemp. Caught by
    # sweeping the whole feed for CLASS changes and not only for gate changes (LESSON #2).
    is_blunt = bool(_BLUNT.search(t)) and not _BLUNT_HARDWARE.search(t) and not is_cbd
    if (_TOBACCO.search(t) or _CIG.search(t) or _CIGAR.search(t) or _SHISHA_TOBACCO.search(t)
            or is_blunt) and not neg and not _SUBSTANCE_ACCESSORY.search(t):
        cls = "tobacco_nicotine"
    elif (_NIC_MG.search(t) or _ECIG_FORM.search(t)
          or (_VAPE_BRAND.search(t) and _VAPE_REFILL.search(t))) \
            and not is_cbd and not neg and not _SUBSTANCE_ACCESSORY.search(t):
        # A non-CBD NNmg nicotine strength gates ON ITS OWN — no ecig-context word required.
        # (field 2026-07-09: "VAAL E-Pack 20mg" / "Instaflow O Pro Starterkit … 20mg" had no
        # disposable/pod/vape token → leaked as un-gated standard.) CBD (100/500/1000mg = 3-digit,
        # excluded by _NIC_MG's 1-2 digit cap + the is_cbd guard) and 0mg / no-nic still veto.
        cls = "tobacco_nicotine"                   # nicotine strength, a liquid-bearing form, or a brand refill
    elif _ALCOHOL.search(t) and not neg and not _SUBSTANCE_ACCESSORY.search(t) and not _FLAVOUR_PAPER.search(t):
        cls = "alcohol"
    # (2) SUPPLIER CATEGORY closes the leaks the title can't see. A tobacco GROUP still can't
    #     override the accessory guards: a pouch/holder/case (_SUBSTANCE_ACCESSORY) or a
    #     machine/filter/paper (_TOBACCO_ACCESSORY) stays open even under "Tabak…Zigaretten".
    elif tags:
        tobacco_ok = not neg and not _SUBSTANCE_ACCESSORY.search(t) and not _TOBACCO_ACCESSORY.search(t)
        if ("cbd blüten" in tags or "cbd pollen" in tags or "blüten" in tags) and not _CBD_OPEN.search(t):
            cls = "cbd_hemp"                       # flower / trim / pollen (hash) = 18+
        elif "cbd samen" in tags:
            cls = "cbd_open"                       # seeds = open (no ID)
        elif "disposable" in tags and "zigaret" in tags and tobacco_ok:
            cls = "tobacco_nicotine"               # nicotine disposables (0mg vetoed above)
        elif ("zigaretten" in tags or "tabak," in tags or tags.startswith("tabak")) and tobacco_ok:
            cls = "tobacco_nicotine"               # the tobacco/cigarette group, minus machines/filters
        elif "shisha" in tags and _SHISHA_TOBACCO.search(t) and tobacco_ok:
            cls = "tobacco_nicotine"               # shisha molasses tobacco only (not hoses/charcoal)
        elif _ALCOHOL.search(tags) and not neg and not _SUBSTANCE_ACCESSORY.search(t) \
                and not _FLAVOUR_PAPER.search(t):
            # The leak layer 2 exists to close, and it had no alcohol branch at all. A bottle's
            # title is usually a BRAND ("Bacardi Carta Blanca 70cl") and says nothing about what
            # it is; the supplier's bucket ("Spirituosen", "Bier, Wein & Champagner") says it
            # outright. Same guards as the title path — a rum-flavoured paper is still a paper.
            cls = "alcohol"
        elif ref_category == "CBD" or _CBD_TOKEN.search(t):
            cls = "cbd_open" if _CBD_OPEN.search(t) else "cbd_hemp"
    # (3) TITLE-CBD fallback (no supplier tags) — the path EVERY hand-captured product takes,
    #     and therefore the one that has to be widest. A cashier standing at the shelf has no
    #     supplier tags to lean on; the title is all there is. This is exactly where the BLOW
    #     pre-rolls leaked (2026-07-29): created by hand, no tags, title never said "CBD".
    elif _CBD_TOKEN.search(t):
        cls = "cbd_open" if _CBD_OPEN.search(t) else "cbd_hemp"
    #     …and when the TITLE is a meaningless strain/brand name, fall through to what the
    #     product says about ITSELF. Only a strong signal counts (see _CBD_STRONG) — an
    #     incidental "great with CBD flower" in a papers blurb must never gate papers.
    #     …and the accessory guards apply here too. An accessory's blurb DESCRIBES the thing it
    #     is for ("holds 4 pre-rolled joints", "for your CBD flower"), so without this veto the
    #     description path gates filters, cones and storage tubes. Caught by the UAT dry run
    #     before it touched a row — 12 of its 16 proposed changes were accessories.
    elif (description and _CBD_STRONG.search(description) and not _CBD_OPEN.search(t)
          and not _TOBACCO_ACCESSORY.search(t) and not _SUBSTANCE_ACCESSORY.search(t)):
        cls = "cbd_hemp"

    # CATEGORY: honour FourTwenty's clean buckets, else keyword-classify the dump.
    cat = _REF_CATEGORY_MAP.get(ref_category or "")
    if cat is None:
        for rx, c in _CATEGORY_RULES:
            if rx.search(t):
                cat = c
                break
    if cat is None:
        cat = "Accessories" if ref_category == "Accessories" else "Other"

    # A real cigarette/tobacco product belongs in its own category, not "Papers"/"Other".
    # Any tobacco_nicotine line qualifies now (branded packs like "Marlboro 10x20cig", disposable
    # nicotine e-cigs, and shisha tobacco all lack a "tabak"/"zigarette" token in the title).
    if cls == "tobacco_nicotine":
        cat = "Tobacco & Cigarettes"

    return cat, cls, class_meta(cls)["age_restricted"]


# ============================================================================
# THE HONEST "NO COST" — a closed vocabulary, kept here and not in the router.
#
# A filled-in COST is the shop's done-flag for a catalogue row, and it is the right one: it is
# the only field on the cleanup form a machine cannot honestly supply. A name, a description, a
# photo, a category, even the EAN can all come from a supplier feed or a model, and a row that
# was auto-filled LOOKS finished. Cost can only come from a person holding an invoice.
#
# But a flag with no honest "no" is a flag people clear with a lie. A gift, a sample, consignment
# or old stock with a lost invoice had no way off the bench except typing a number that was not
# true — and a fabricated cost is WORSE than a missing one, because nobody can later tell a
# made-up 1.00 from a real one and it poisons every margin figure quietly. Same disease as the
# minted EANs, and this catalogue still carries 4,998 rows of what that costs.
#
# Lives in this module so it can be TESTED: importing pos_router needs a live database, which is
# why thirty test files error without one. A vocabulary nobody can import is a rule nobody can
# check. (Pure data — no DB, no network.)
NO_COST_REASONS = {
    "gift":        "a gift / freebie — nothing was paid",
    "sample":      "a supplier sample",
    "consignment": "on consignment — paid only when it sells",
    "unknown":     "cost genuinely not known (old stock, invoice gone)",
}


def resolve_class_on_create(name: str | None, product_class: str | None,
                            is_age_restricted: bool | None,
                            description: str | None = None) -> tuple[str, bool]:
    """The on-the-fly / quick-create rule (compliance safety net).

    Honour the operator's explicit choice first (a picked class or the 18+ toggle, via
    reconcile_age). THEN, if the item is still plain 'standard', run the title classifier —
    and if the NAME is an age-restricted substance (tobacco/nicotine, alcohol, CBD flower),
    upgrade to that class so it can NEVER be sold un-gated (field 2026-07-08: a cashier who
    forgot the 18+ toggle on "Swisher Sweets" was ringing it with no ID gate). The net only
    ever makes an item MORE restrictive — it never un-gates an operator's choice. A manager
    can re-class precisely later in the cleanup cockpit. Returns (class, flag)."""
    cls, flag = reconcile_age(product_class, is_age_restricted)
    if cls == DEFAULT_CLASS:
        _, suggested, _ = classify(name or "", description=description)
        if suggested in ("tobacco_nicotine", "alcohol", "cbd_hemp"):
            return suggested, True
    return cls, flag


# ============================================================================
# BL-CAT — CANONICAL CATEGORY FUNNEL (generated from banco-category-taxonomy-draft.json 2026-07-16)
# The single chokepoint that keeps the 2-level tree from regrowing into the 61-German-slug mess.
# Category = MERCHANDISING axis only; product_class/age/VAT stay a SEPARATE locked axis.
# ============================================================================
CANONICAL_LABEL_GROUP = {
    "Accessories (general)": "Unsorted / System",
    "Alcohol": "Bar & Alcohol",
    "Apparel & Textiles": "Lifestyle & Gifts",
    "Ashtrays": "Smoking Gear",
    "Blunts & Wraps": "Papers & Rolling",
    "Bong & Pipe Accessories": "Smoking Gear",
    "Bongs": "Smoking Gear",
    "CBD Flower": "CBD & Hemp",
    "Cafe": "Cafe & Food",
    "Cigarette Tubes": "Papers & Rolling",
    "Coils & Pods": "Vape",
    "Cones & Tubes": "Papers & Rolling",
    "Cosmetics": "CBD & Hemp",
    "Creams & Topicals": "CBD & Hemp",
    "Dab & Concentrate Gear": "Smoking Gear",
    "Decor": "Lifestyle & Gifts",
    "Drug Testing": "Grow & Lab",
    "E-Liquids": "Vape",
    "Edibles": "CBD & Hemp",
    "Entertainment & Games": "Lifestyle & Gifts",
    "Extracts & Oils": "CBD & Hemp",
    "Filters & Tips": "Papers & Rolling",
    "Food & Snacks": "Cafe & Food",
    "Gifts & Gadgets": "Lifestyle & Gifts",
    "Grinders": "Smoking Gear",
    "Grow Supplies": "Grow & Lab",
    "Incense & Smudge": "Lifestyle & Gifts",
    "Knives & Tools": "Lifestyle & Gifts",
    "Lighters": "Smoking Gear",
    "Nicotine Shots": "Vape",
    "Other": "Unsorted / System",
    "Packaging & Bags": "Lifestyle & Gifts",
    "Pipes": "Smoking Gear",
    "Prefilled & Disposables": "Vape",
    "Presses": "Smoking Gear",
    "Rolling & Filling Machines": "Papers & Rolling",
    "Rolling Accessories": "Papers & Rolling",
    "Rolling Papers": "Papers & Rolling",
    "Rolling Trays": "Papers & Rolling",
    "Scales": "Smoking Gear",
    "Shisha Bowls": "Tobacco & Shisha",
    "Shisha Coal": "Tobacco & Shisha",
    "Shisha Hoses": "Tobacco & Shisha",
    "Shisha Tobacco": "Tobacco & Shisha",
    "Shishas & Hookahs": "Tobacco & Shisha",
    "Snuff Accessories": "Smoking Gear",
    "Storage & Stash": "Smoking Gear",
    "Tobacco": "Tobacco & Shisha",
    "Unsorted": "Unsorted / System",
    "Vape Accessories": "Vape",
    "Vape Devices": "Vape",
    "Vaporizers": "Vape",
}
CATEGORY_SYNONYMS = {
    "Accessories": "Accessories (general)",
    "Accessories (general)": "Accessories (general)",
    # Alcohol (its own 18+ merchandising line) + the common ways it's written / imported.
    "Alcohol": "Alcohol",
    "Alkohol": "Alcohol",
    "Beer": "Alcohol",
    "Bier": "Alcohol",
    "Wine": "Alcohol",
    "Wein": "Alcohol",
    "Spirits": "Alcohol",
    "Spirituosen": "Alcohol",
    "Liquor": "Alcohol",
    "Apparel & Textiles": "Apparel & Textiles",
    "Aschenbecher": "Ashtrays",
    "Ashtrays": "Ashtrays",
    "Aufbewahrung": "Storage & Stash",
    "Blunts": "Blunts & Wraps",
    "Blunts & Wraps": "Blunts & Wraps",
    "Bong & Pipe Accessories": "Bong & Pipe Accessories",
    "Bong Pfeifenzubehoer": "Bong & Pipe Accessories",
    "Bongs": "Bongs",
    "CBD & Hemp": "CBD Flower",
    "CBD Flower": "CBD Flower",
    "Cafe": "Cafe",
    "Café": "Cafe",
    "Cigarette Tubes": "Cigarette Tubes",
    "Coils & Pods": "Coils & Pods",
    "Cones & Tubes": "Cones & Tubes",
    "Cosmetics": "Cosmetics",
    "Creams & Topicals": "Creams & Topicals",
    "Dab & Concentrate Gear": "Dab & Concentrate Gear",
    "Decor": "Decor",
    "Dekoration": "Decor",
    "Diverses": "Other",
    "Drehhilfen": "Rolling Accessories",
    "Drehmaschinen": "Rolling & Filling Machines",
    "Drehpapier": "Rolling Papers",
    "Drogentests": "Drug Testing",
    "Drug Testing": "Drug Testing",
    "E Zigis": "Vape Devices",
    "E-Liquids": "E-Liquids",
    "Edibles": "Edibles",
    "Entertainment & Games": "Entertainment & Games",
    "Extracts & Oils": "Extracts & Oils",
    "Extrakte": "Extracts & Oils",
    "Feuerzeuge": "Lighters",
    "Filter": "Filters & Tips",
    "Filters & Tips": "Filters & Tips",
    "Food": "Food & Snacks",
    "Food & Snacks": "Food & Snacks",
    "Geschenke Gadgets": "Gifts & Gadgets",
    "Gifts & Gadgets": "Gifts & Gadgets",
    "Grinder": "Grinders",
    "Grinders": "Grinders",
    "Grow Supplies": "Grow Supplies",
    "Headshop": "Unsorted",
    "Incense & Smudge": "Incense & Smudge",
    "Joint Huelsen Cones": "Cones & Tubes",
    "Knives & Tools": "Knives & Tools",
    "Kohle": "Shisha Coal",
    "Kosmetik": "Cosmetics",
    "Lighters": "Lighters",
    "Liquids": "E-Liquids",
    "Marijuana": "CBD Flower",
    "Messer": "Knives & Tools",
    "Nicotine Shots": "Nicotine Shots",
    "Nikotinshots": "Nicotine Shots",
    "Oel Dabbing": "Dab & Concentrate Gear",
    "On the fly": "Unsorted",
    "Other": "Other",
    "Packaging & Bags": "Packaging & Bags",
    "Papers & Filters": "Rolling Papers",
    "Pfeifen": "Pipes",
    "Pipes": "Pipes",
    "Pods Coils": "Coils & Pods",
    "Prefilled": "Prefilled & Disposables",
    "Prefilled & Disposables": "Prefilled & Disposables",
    "Pressen": "Presses",
    "Presses": "Presses",
    "Raeucherartikel": "Incense & Smudge",
    "Raw Produkte": "Cones & Tubes",
    "Rolling & Filling Machines": "Rolling & Filling Machines",
    "Rolling Accessories": "Rolling Accessories",
    "Rolling Papers": "Rolling Papers",
    "Rolling Trays": "Rolling Trays",
    "Scales": "Scales",
    "Schalen Trays": "Rolling Trays",
    "Schlaeuche": "Shisha Hoses",
    "Schnupfutensilien": "Snuff Accessories",
    "Shisha Bowls": "Shisha Bowls",
    "Shisha Coal": "Shisha Coal",
    "Shisha Hoses": "Shisha Hoses",
    "Shisha Tobacco": "Shisha Tobacco",
    "Shishas": "Shishas & Hookahs",
    "Shishas & Hookahs": "Shishas & Hookahs",
    "Shishatabak": "Shisha Tobacco",
    "Snuff Accessories": "Snuff Accessories",
    "Stopfmaschinen": "Rolling & Filling Machines",
    "Storage & Stash": "Storage & Stash",
    "Tabak": "Tobacco",
    "Tabakkoepfe": "Shisha Bowls",
    "Textilien": "Apparel & Textiles",
    "Tobacco": "Tobacco",
    "Treats": "Other",
    "Unsorted": "Unsorted",
    "Unterhaltung": "Entertainment & Games",
    "Vape Accessories": "Vape Accessories",
    "Vape Co": "Prefilled & Disposables",
    "Vape Devices": "Vape Devices",
    "Vaporizer": "Vaporizers",
    "Vaporizers": "Vaporizers",
    "Verpackung": "Packaging & Bags",
    "Verstecktresore": "Storage & Stash",
    "Waagen": "Scales",
    "Zigaretten Huelsen": "Cigarette Tubes",
    "Zubehoer": "Accessories (general)",
}
# Enrichment-recipe vocabulary (catalog_enrichment._ALLOWED_*) -> canonical, so a BULK re-enrich /
# Artemis re-import also lands on the clean tree instead of seeding a 4th competing vocabulary.
CATEGORY_SYNONYMS.update({
    "Rolling Machines": "Rolling & Filling Machines",
    "Cones": "Cones & Tubes",
    "Pre-rolled": "Cones & Tubes",
    "Storage": "Storage & Stash",
    "Bong Heads & Bowls": "Bong & Pipe Accessories",
    "Storage & Safes": "Storage & Stash",
    "Glass Accessories": "Bong & Pipe Accessories",
    "CBD Hash": "CBD Flower",
    "CBD Flowers": "CBD Flower",
    "CBD Extracts": "Extracts & Oils",
    "CBD Cosmetics": "Cosmetics",
    "CBD Other": "CBD Flower",
    "Vape Kits": "Vape Devices",
    "Vape Pods": "Coils & Pods",
    "Disposables": "Prefilled & Disposables",
    "Shisha Pipes": "Shishas & Hookahs",
    "Coals & Heat": "Shisha Coal",
    "Shisha Accessories": "Accessories (general)",
    "Apparel": "Apparel & Textiles",
    "Posters & Stickers": "Decor",
    "Gifts": "Gifts & Gadgets",
    "Lifestyle Accessories": "Gifts & Gadgets",
    "Grow Lights": "Grow Supplies",
    "Nutrients & Soil": "Grow Supplies",
    "Tents & Climate": "Grow Supplies",
    "Grow Accessories": "Grow Supplies",
})

# BL-130 — the SHELF-PHOTO reader's vocabulary (the 5th writer into the funnel).
# Reading the shop's shelves from photos (47 shots -> 256-product draft, 2026-07-16) invented its own
# plain-English category names. They're sensible but they are NOT our canonical labels, so half the
# seeded batch fell into "Unsorted". Map them here — at the ONE chokepoint — so every future photo-read
# batch lands on the clean tree instead of needing a patch script. Same doctrine as the German-slug mess:
# fix the funnel, not the rows.
CATEGORY_SYNONYMS.update({
    "Pre-Rolled Cones": "Cones & Tubes",
    "Rolling Trays & Mats": "Rolling Trays",
    "Blunt Wraps & Cigarillos": "Blunts & Wraps",
    "Bongs & Water Pipes": "Bongs",
    "Bong Accessories & Cleaning": "Bong & Pipe Accessories",
    "Vapes & E-Liquids": "E-Liquids",          # mixed bucket; refined per-item by name (see _refine_vape)
    "CBD & Hemp": "CBD Flower",                 # group name used as a category; flower is the default lane
    "Tobacco Substitutes": "Tobacco",
    "Incense": "Incense & Smudge",
    "Smudge & Ritual": "Incense & Smudge",
    "Aromatherapy & Room Spray": "Gifts & Gadgets",
    "Cosmetics & Body Care": "Cosmetics",
    "Humidity Control": "Storage & Stash",      # Boveda packs live with storage
    "Growing Supplies": "Grow Supplies",
    "Books & Media": "Entertainment & Games",
    "Games": "Entertainment & Games",
    "Jewelry & Decor": "Decor",
    "Detox & Test Kits": "Drug Testing",
    "Accessories": "Accessories (general)",
})

# BL-134 — the FOURTWENTY supplier catalog's own headings (10,284 reference rows in prod, the biggest
# single source we have). Three of its fourteen stranded in Unsorted and one was silently WRONG, which
# is worse: "Papers & Filters" sent every FILTER into Rolling Papers. Mixed headings are split by name
# via _MIXED_REFINE above — a supplier lumping two lanes together is not a reason to mis-file half of them.
CATEGORY_SYNONYMS.update({
    "Papers & Filters": "Rolling Papers",        # → Filters & Tips when the NAME says filter/tip
    "Pipes & Bongs": "Pipes",                    # → Bongs / Bong & Pipe Accessories by name
    "Tobacco & Cigarettes": "Tobacco",
    "Merch": "Gifts & Gadgets",
    "Papers": "Rolling Papers",
    "CBD": "CBD Flower",
    "Gas": "Accessories (general)",              # lighter gas refills
    "Equipment": "Accessories (general)",
    "Bar": "Cafe",
    "books": "Entertainment & Games",
})

CANONICAL_CATEGORIES = sorted(CANONICAL_LABEL_GROUP.keys())
_CATEGORY_SYNONYMS_LOWER = {k.lower(): v for k, v in CATEGORY_SYNONYMS.items()}


# BL-130 — split the one MIXED vape bucket by what the product's name says it is. A source that files
# disposables, nic-salt liquids and pods all under one "Vapes & E-Liquids" heading would otherwise dump
# them into a single lane; the name is a reliable tell. Only consulted for that ambiguous label.
_VAPE_REFINE = (
    ("Prefilled & Disposables", ("disposable", "puff", "elf bar", "elfbar", "lost mary", "vozol", "einweg")),
    ("Coils & Pods",            ("pod", "coil", "cartridge", "elfa")),
    ("Nicotine Shots",          ("nic shot", "nikotin shot", "nicotine shot")),
    ("Vape Devices",            ("kit", "device", "mod", "akku", "battery")),
)

# A supplier's own headings lump two real lanes under one name. Splitting them by NAME is the only
# honest option — otherwise a whole side of the bucket is silently mis-filed (FourTwenty's
# "Papers & Filters" was sending every FILTER into Rolling Papers: 772 reference rows).
_MIXED_REFINE = {
    "Rolling Papers": (          # from "Papers & Filters"
        ("Filters & Tips", ("filter", "tip", "aktivkohle", "activated carbon", "spitzen", "purize",
                            "slim size", "6mm", "carbon")),
    ),
    "Accessories (general)": (   # the catch-all bucket hides whole real sections inside itself
        # Angel, spot-checking the bench: "section for dabbers?? put in accessories for now, but still??"
        # There IS a section — "Dab & Concentrate Gear" — nothing just ever routed to it, so every
        # dabber, dab mat and banger sank into the catch-all. A category that exists but is unreachable
        # is the same as no category.
        ("Dab & Concentrate Gear", ("dabber", "dab mat", "dabmat", "banger", "carb cap", "carbcap",
                                    "dab rig", "dab tool", "enail", "e-nail", "quartz nail",
                                    "concentrate", "wax ", "shatter")),
        ("Scales",                 ("waage", "scale ", "feinwaage", "pocket scale")),
        ("Lighters",               ("feuerzeug", "lighter", "torch", "benzin", "flint", "stein ")),
        ("Grinders",               ("grinder", "mühle", "muehle")),
        ("Storage & Stash",        ("stash", "tabaktasche", "pouch", "tin box", "dose ", "tresor")),
    ),
    "Pipes": (                   # from "Pipes & Bongs"
        ("Bongs", ("bong", "waterpipe", "wasserpfeife", "percolator", "beaker", "acryl bong")),
        ("Bong & Pipe Accessories", ("adapter", "diffusor", "diffuser", "kupplung", "coupling",
                                     "downstem", "vorkühler", "steckkopf", "ersatz")),
    ),
}


def _refine_vape(name: str):
    n = (name or "").lower()
    for label, tells in _VAPE_REFINE:
        if any(t in n for t in tells):
            return label
    return None


def _refine_mixed(label: str, name: str):
    n = (name or "").lower()
    for alt, tells in _MIXED_REFINE.get(label, ()):
        if any(t in n for t in tells):
            return alt
    return None


def canonicalize_category(raw, name: str = None):
    """Funnel any free-text category string -> (canonical_category_label, group_label).

    Exact synonym (English canonical, German slug, or legacy string) wins; a case-insensitive
    retry catches minor casing drift; anything unknown or blank lands in ('Unsorted',
    'Unsorted / System') so a NEW item is never a fresh non-canonical category. This is BL-CAT's
    anti-regrowth backstop — every product create/adopt runs its category through here.

    `name` is OPTIONAL (BL-130): when the source category is a known MIXED bucket, the product name
    disambiguates it (a "Elf Bar 600 Disposable" filed under "Vapes & E-Liquids" is a disposable, not
    an e-liquid). Callers that don't pass a name behave exactly as before.
    """
    s = (raw or "").strip()
    if not s:
        return ("Unsorted", "Unsorted / System")
    lbl = CATEGORY_SYNONYMS.get(s) or _CATEGORY_SYNONYMS_LOWER.get(s.lower())
    if not lbl:
        return ("Unsorted", "Unsorted / System")
    if lbl == "E-Liquids" and name:
        lbl = _refine_vape(name) or lbl
    if name:
        lbl = _refine_mixed(lbl, name) or lbl
    return (lbl, CANONICAL_LABEL_GROUP.get(lbl, "Unsorted / System"))
