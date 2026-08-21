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
    RESOLVABLE_SHOPS, _OG, _TITLE_PRICE_TAIL, looks_like_search_page, parse_shop_page,
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
