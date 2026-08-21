"""RESOLVABLE_SHOPS — the tier that asks a supplier's own shop for an EAN.

Network-free. The two things worth pinning are the two that were actually wrong or nearly
wrong when this was built, on 2026-08-21:

  1. THE PRICE MUST NEVER CROSS. Kings Castle is a wholesaler and puts the price in the page
     TITLE — "actiTube Aktivkohlefilter - Slim (50Stk.) kaufen, 99.00 CHF". That is the CASE
     price; the single is CHF 9.90 on the same page. Left in the title it would ride into the
     catalogue as part of the product NAME.
  2. A MISS MUST BE UNAMBIGUOUS. A search that finds nothing still returns HTTP 200 with a
     real page on it, and echoes the code back as the title. The hit signal is the REDIRECT to
     an article path, not the status code and not the body.
"""
import re

from src.services.web_product_lookup import (
    RESOLVABLE_SHOPS, _OG, _TITLE_PRICE_TAIL, _TITLE_CUT_VERB,
    looks_like_search_page, parse_shop_page,
)

KC = next(s for s in RESOLVABLE_SHOPS if s["key"] == "kingscastle")

# A real Kings Castle article page, trimmed to the tags the parser reads. The title is
# verbatim from https://www.kingscastle.ch/actiTube-ActiveFilter-7mm-10-x-50Stk — the CHF
# 99.00 is the TEN-PACK, while the single is CHF 9.90 on the same page.
HIT_HTML = (
    '<meta property="og:type" content="website">\n'
    '<meta property="og:title" content="actiTube Aktivkohlefilter - Slim (50Stk.) kaufen, 99.00 CHF">\n'
    '<meta property="og:description" content="Aktivkohlefilter zum Drehen">\n'
    '<meta property="og:image" content="https://www.kingscastle.ch/media/image/product/1/lg/a.jpg">\n'
)
HIT_URL = "https://www.kingscastle.ch/actiTube-ActiveFilter-7mm-10-x-50Stk"

# What a miss looks like: HTTP 200, a real page, still on the search URL, code echoed back.
MISS_HTML = '<meta property="og:title" content="42425700">\n'
MISS_URL = "https://www.kingscastle.ch/index.php?qs=42425700&search="


def test_every_shop_entry_is_usable():
    assert RESOLVABLE_SHOPS, "the tier is pointless with no shops in it"
    for shop in RESOLVABLE_SHOPS:
        for key in ("key", "label", "domain", "search", "why"):
            assert shop.get(key), (shop.get("key"), key)
        # {ean} is the whole contract — without it every lookup silently searches for nothing.
        assert "{ean}" in shop["search"], shop["key"]
        assert shop["search"].startswith("https://"), shop["key"]


def test_the_case_price_is_stripped_out_of_the_name():
    for raw, want in [
        ("actiTube Aktivkohlefilter - Slim (50Stk.) kaufen, 99.00 CHF",
         "actiTube Aktivkohlefilter - Slim (50Stk.)"),
        ("Purize Holzmundstück Xtra Slim mit Geschmack (5 Stk.) kaufen, 2.90 CHF",
         "Purize Holzmundstück Xtra Slim mit Geschmack (5 Stk.)"),
        ("Local Weed - Purple Kush Kit (40% CBD), 24.90 CHF",
         "Local Weed - Purple Kush Kit (40% CBD)"),
        ("Something Priced at 1'299.00 CHF", "Something Priced at"),
    ]:
        assert _TITLE_PRICE_TAIL.sub("", raw).strip() == want, raw


def test_a_name_that_merely_contains_a_number_survives():
    # The tail anchors at the END and needs a currency. A pack size must not be eaten.
    for name in ("GIZEH Active Filter 8mm 10 Stk", "Efest 18650 2600mah 40A",
                 "actiTube Konik 6mm 10pcs"):
        assert _TITLE_PRICE_TAIL.sub("", name).strip() == name, name


def test_og_tags_are_read_the_way_the_pages_publish_them():
    page = (
        '<meta property="og:type" content="website">\n'
        '<meta property="og:title" content="Purize Holzmundstück Xtra Slim (5 Stk.) kaufen, 2.90 CHF">\n'
        '<meta property="og:description" content="Mach deinen Joint zum Hingucker">\n'
        '<meta property="og:image" content="https://www.kingscastle.ch/media/image/product/11350/lg/x.jpg">\n'
    )
    assert _OG["title"].search(page).group(1).endswith("2.90 CHF")
    assert _OG["description"].search(page).group(1) == "Mach deinen Joint zum Hingucker"
    assert _OG["image"].search(page).group(1).endswith(".jpg")


def test_the_miss_page_is_recognisable_without_fetching_anything():
    # What a miss actually returns: still on the search URL, title echoing the code back.
    # Both halves of the guard are asserted, because either alone has a hole — the URL test
    # alone would pass a soft-404, and the echo test alone would pass a product literally
    # named after its own EAN.
    miss_url = "https://www.kingscastle.ch/index.php?qs=42425700&search="
    hit_url = "https://www.kingscastle.ch/Purize-Holzmundstueck-6mm-1-x-5Stk"
    def looks_like_search(u):
        return "index.php" in u or "qs=" in u or "search" in u.rsplit("/", 1)[-1]
    assert looks_like_search(miss_url)
    assert not looks_like_search(hit_url)

    echoed = _OG["title"].search('<meta property="og:title" content="42425700">').group(1)
    assert _TITLE_PRICE_TAIL.sub("", echoed).strip() == "42425700"   # == the barcode -> rejected


def test_a_wholesaler_is_flagged_as_one():
    # Whether a source quotes cases is the operator-facing fact; losing the flag loses the
    # warning, and the warning is the only thing standing between a case price and the till.
    kc = next(s for s in RESOLVABLE_SHOPS if s["key"] == "kingscastle")
    assert kc["wholesale"] is True


# ---- the PARSER, exercised end to end without a network -----------------------------
#
# These exist because sabotaging the price strip on 2026-08-21 turned NOTHING red: the test
# above proves the regex works, and proving a regex works is not proving it is called. The
# parser was pulled out of the fetch loop so this file can reach it.

def test_a_hit_page_parses_and_the_case_price_never_reaches_the_name():
    out = parse_shop_page(HIT_HTML, HIT_URL, "4260641140046", KC)
    assert out is not None
    assert out["title"] == "actiTube Aktivkohlefilter - Slim (50Stk.)"
    # The load-bearing assertion: no currency anywhere in the product name.
    assert "CHF" not in out["title"] and "99.00" not in out["title"]
    assert out["source"] == "kingscastle"
    assert out["wholesale"] is True
    assert out["images"] == ["https://www.kingscastle.ch/media/image/product/1/lg/a.jpg"]
    assert out["lang_hint"] == "de"


def test_no_price_key_exists_at_all():
    # Not "the price is right" — the price must NOT BE THERE. Every source in this module
    # quotes somebody else's number and none of them is what this shop charges.
    out = parse_shop_page(HIT_HTML, HIT_URL, "4260641140046", KC)
    assert "price" not in out
    assert not any("price" in k for k in out), sorted(out)


def test_a_miss_parses_to_nothing():
    assert parse_shop_page(MISS_HTML, MISS_URL, "42425700", KC) is None


def test_a_product_page_whose_title_is_only_the_barcode_is_still_a_miss():
    # Belt and braces: if a shop ever serves a soft-404 on an article-looking URL, the echoed
    # title still has to be caught. Either guard alone has a hole.
    assert parse_shop_page('<meta property="og:title" content="42425700">',
                           HIT_URL, "42425700", KC) is None


def test_a_page_with_no_og_tags_is_a_miss_not_a_crash():
    assert parse_shop_page("<html><body>hello</body></html>", HIT_URL, "123", KC) is None
    assert parse_shop_page("", HIT_URL, "123", KC) is None


def test_the_url_signal_on_its_own():
    assert looks_like_search_page(MISS_URL)
    assert not looks_like_search_page(HIT_URL)


# ---- the source truncates its OWN title (2026-08-21) --------------------------------
#
# Kings Castle caps og:title at 80 chars. A long name arrives with "kaufen" chopped:
#   "…Xtra Slim 6mm im Glas - yellow (100 Stk.) kau, 19.90 CHF"
# The price strip is correct and STILL leaves "kau" welded to the product name. That went
# into the sandbox catalogue before Angel read it in the success message and said so.

TRUNC_HTML = (
    '<meta property="og:title" content="Purize Aktivkohlefilter Xtra Slim 6mm im Glas'
    ' - yellow (100 Stk.) kau, 19.90 CHF">\n'
)


def test_a_title_the_source_itself_truncated_does_not_keep_half_a_verb():
    out = parse_shop_page(TRUNC_HTML, HIT_URL, "4260748411544", KC)
    assert out["title"] == "Purize Aktivkohlefilter Xtra Slim 6mm im Glas - yellow (100 Stk.)"
    assert not out["title"].endswith("kau")
    assert "CHF" not in out["title"]


def test_every_partial_of_kaufen_is_cut():
    base = "Some Product 50Stk."
    for tail in ("kaufen", "kaufe", "kauf", "kau"):
        assert _TITLE_CUT_VERB.sub("", f"{base} {tail}").strip() == base, tail


def test_a_real_name_ending_in_a_short_word_survives():
    # Only 3+ characters are cut, so these must come through untouched. A rule that eats
    # " K" or " Ka" would quietly rename real products.
    for name in ("Vape Pod 2ml K", "Grinder Ka", "Blunt Wrap OK", "Papers Kb"):
        assert _TITLE_CUT_VERB.sub("", name).strip() == name, name


# ---- the FAMILY page (2026-08-21) ---------------------------------------------------
#
# Angel, holding a Vaal pod: "this is peach ice, not the blueberry." 6941908339899 redirects
# correctly to /Vaal-VapePod-20mg-EPack-1-Stk — and that page is a PARENT with a flavour
# selector. It says "Peach ICE" and "Blueberry ICE" five times each, and the scanned code
# appears on it ZERO times. The redirect was right, the page was right, and the name
# "Vaal E-Pack Pods (20mg)" is missing the one word that identifies the packet.
#
# The discriminator: does the page PRINT the code we searched for? Measured across six real
# lookups — the four exact hits all print it, both family pages print no EAN at all.

FAMILY_HTML = (
    '<meta property="og:title" content="Vaal E-Pack Pods (20mg) kaufen, 18.90 CHF">\n'
    '<div>Peach ICE</div><div>Blueberry ICE</div>\n'      # the range, on one page
)
EXACT_HTML = (
    '<meta property="og:title" content="Purize Aktivkohlefilter 6mm - green (50 Stk.) kaufen, 8.90 CHF">\n'
    '<span class="ean">4260748412268</span>\n'            # the shop names THIS variant's code
)


def test_a_family_page_is_flagged_not_discarded():
    out = parse_shop_page(FAMILY_HTML, HIT_URL, "6941908339899", KC)
    # Still a hit — a family name plus a photo beats a bare number.
    assert out is not None
    assert out["title"] == "Vaal E-Pack Pods (20mg)"
    # …but it must NOT claim to be this exact item.
    assert out["exact"] is False


def test_a_page_carrying_the_code_is_exact():
    out = parse_shop_page(EXACT_HTML, HIT_URL, "4260748412268", KC)
    assert out["exact"] is True
    assert "green (50 Stk.)" in out["title"]


def test_exactness_is_about_THIS_code_not_any_code():
    # A neighbouring variant's code on the page must not make our code "exact" — that is how a
    # peach pod would inherit the blueberry's confidence.
    out = parse_shop_page(EXACT_HTML, HIT_URL, "6941908339899", KC)
    assert out["exact"] is False


# ---- a barcode DATABASE is not a shop (2026-08-21) ----------------------------------
#
# Angel scanned 6943498644650. Kings Castle did not have it, so the chain fell through to
# UPCitemdb, which answered:
#
#     "2 Renova Zero & A Kanger U-boat With Pods Three Devices-one Bid"
#
# — an eBay auction title, "one Bid" and all. The CODE is right; the words are somebody's
# advert. These databases aggregate marketplace listings, which is exactly why they can answer
# codes no shop carries and exactly why their wording must never be presented as a supplier's.
#
# It also caught a hole in the `exact` flag added an hour earlier: only the shop tier computed
# it, so every generic-database hit inherited False and would have been labelled "this is the
# product RANGE" — which is not true and not the problem. Different failures need different
# words, or the operator learns to ignore both.

def test_the_two_warnings_are_different_states():
    kc = next(s for s in RESOLVABLE_SHOPS if s["key"] == "kingscastle")
    # A shop page that carries the code: exact, and nobody's advert.
    exact = parse_shop_page(EXACT_HTML, HIT_URL, "4260748412268", kc)
    assert exact["exact"] is True
    assert exact.get("crowd_sourced", False) is False

    # A shop FAMILY page: not exact — but still a shop, so not crowd-sourced either.
    family = parse_shop_page(FAMILY_HTML, HIT_URL, "6941908339899", kc)
    assert family["exact"] is False
    assert family.get("crowd_sourced", False) is False
    # The two states must be distinguishable, or one warning has to cover both and says
    # the wrong thing about at least one of them.
    assert (exact["exact"], exact.get("crowd_sourced", False)) != \
           (family["exact"], family.get("crowd_sourced", False))


def test_a_shop_hit_never_claims_to_be_crowd_sourced():
    # `crowd_sourced` is set only by the generic-database branches of lookup_product. The shop
    # parser must not set it at all, or a supplier's own page would carry a warning telling the
    # operator to distrust it.
    kc = next(s for s in RESOLVABLE_SHOPS if s["key"] == "kingscastle")
    for html, code in ((EXACT_HTML, "4260748412268"), (FAMILY_HTML, "6941908339899")):
        assert parse_shop_page(html, HIT_URL, code, kc).get("crowd_sourced", False) is False
