"""Tier-2 product identification from the WEB — free, keyless (Felix's "search the web" idea).

Resolve an unknown product by its BARCODE against free barcode databases, so the till/receiving can
auto-fill title + brand + category + description + images and the human just confirms. NEVER raises —
degrades to a manual Google link. Careful, per Angel's brief:
  • QUOTA-AWARE — UPCitemdb's free trial is ~100/day; we surface exactly how many are left so the
    operator uses them wisely, and stop hitting it at 0.
  • GRACEFUL FALLBACK — over quota / not found → Open Products Facts (unlimited) → the Google URL.
  • RICH — return ALL images (the operator may want a different one) + brand/category/description.
  • LANGUAGE-CAREFUL — web data comes in many languages (OPF gave Dutch for a BIC); we flag the
    likely language so the caller can offer a translate, never silently trust it.

Cost note: a barcode is looked up ONCE ever (learn-back → cataloged forever), so free tiers suffice.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger("helix.web_product_lookup")

# ---------------------------------------------------------------------------------------
# TIER 1 — SHOPS THAT ANSWER AN EAN SEARCH DIRECTLY.
#
# Tried BEFORE the generic barcode databases, because for a Swiss headshop they hit far more
# often. UPCitemdb and Open*Facts are food- and mass-market-heavy; a Purize mouthpiece or a
# LocalWeed vape kit is not in either of them, and is on the shelf of a shop that sells them.
#
# Measured 2026-08-21 on ten EANs from Felix's catalogue that FourTwenty does NOT carry:
# Kings Castle answered 3 — actiTube ActiveFilter, Purize Holzmundstück, LocalWeed VapeKit —
# and all three were codes nothing else we had could resolve.
#
# `search` must be a URL that, on an EXACT code match, REDIRECTS to the product page. That
# redirect is the hit signal: a miss stays on the search URL. Both were verified by hand.
#
# ⚠️ `wholesale: True` means the price on that page is a CASE price, not a shelf price. EAN
# 4260641140046 returns "actiTube Aktivkohlefilter - Slim (50Stk.)" — the right NAME — at
# CHF 99.00, while the single sits on the same page at CHF 9.90. That is why this function
# has never returned a price and must not start: name, photo and description only.
#
# A shop cloning Banco edits this list. Adding an entry is one dict and no code.
RESOLVABLE_SHOPS = [
    {
        "key": "kingscastle",
        "label": "Kings Castle",
        "domain": "kingscastle.ch",
        "search": "https://www.kingscastle.ch/index.php?qs={ean}&search=",
        "why": "JTL-Shop; an exact EAN redirects to the article. Carries Purize, actiTube and "
               "Swiss CBD lines that FourTwenty does not.",
        "wholesale": True,
        "lang": "de",
    },
]

# og: tags are what these pages publish; JTL ships them on every article and there is no
# JSON-LD to read instead (checked). Kept deliberately dumb — one regex, no HTML parser
# dependency, and anything unexpected simply yields None.
_OG = {
    "title": re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)', re.I),
    "description": re.compile(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)', re.I),
    "image": re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']*)', re.I),
}
# JTL appends the price to the page title — "… kaufen, 2.90 CHF" / "…, 24.90 CHF". Strip it:
# it is the CASE price on a wholesaler and putting it in the product NAME would carry the wrong
# number into the catalogue by the back door.
_TITLE_PRICE_TAIL = re.compile(r"[,\s]*(?:kaufen[,\s]*)?[\d'’.,]+\s*(?:CHF|EUR)\s*$", re.I)

# …AND THE VERB THE SOURCE ITSELF CHOPPED IN HALF.
#
# Kings Castle caps og:title at 80 characters, so a long name arrives as
#   "Purize Aktivkohlefilter Xtra Slim 6mm im Glas - yellow (100 Stk.) kau, 19.90 CHF"
# The price strip above is correct and still leaves "kau" welded to the product name — which
# is what went into the sandbox catalogue on 2026-08-21 before Angel spotted it in the success
# message. Stripping the price is not enough when the SOURCE is truncated.
#
# Only 3+ characters, so a real name ending in " Ka" or " K" survives untouched.
_TITLE_CUT_VERB = re.compile(r"\s+(?:kaufen|kaufe|kauf|kau)$", re.I)


def looks_like_search_page(url: str) -> bool:
    """A miss stays on the search URL; a hit lands on an article path.

    Split out of the fetch so it can be tested without the network — and it is the whole hit
    signal, so an untested version of it is an untested tier."""
    return "index.php" in url or "qs=" in url or "search" in url.rsplit("/", 1)[-1]


def parse_shop_page(html: str, final_url: str, barcode: str, shop: dict) -> dict | None:
    """A fetched page -> the lookup dict, or None if this was a miss. PURE — no network.

    Pure on purpose. The first version of this lived inside the fetch loop, and when the price
    strip was sabotaged to prove the tests could catch it, NOTHING went red: the unit test
    exercised the regex directly and the browser test could not reach the parser at all. A
    parser you can only reach through somebody else's webserver is a parser you cannot test.
    """
    if looks_like_search_page(final_url):
        return None
    m = _OG["title"].search(html or "")
    # STRIP THE PRICE OUT OF THE NAME. JTL puts it in the page title — "… kaufen, 99.00 CHF" —
    # and on a wholesaler that is the CASE price. Left in, it rides into the catalogue as part
    # of the product's name and no later screen would ever question it.
    title = _TITLE_PRICE_TAIL.sub("", (m.group(1) if m else "")).strip()
    title = _TITLE_CUT_VERB.sub("", title).strip()
    if not title or title == barcode:
        return None        # the echo case: a miss page titles itself with the code
    desc = _OG["description"].search(html or "")
    img = _OG["image"].search(html or "")

    # 🎯 IS THIS PAGE ABOUT THE THING WE SCANNED, OR ABOUT ITS FAMILY?
    #
    # Angel, 2026-08-21, holding a Vaal pod: "this is peach ice, not the blueberry."
    # `6941908339899` redirected correctly to /Vaal-VapePod-20mg-EPack-1-Stk — and that page is
    # a PARENT with a flavour selector. It says "Peach ICE" and "Blueberry ICE" five times each,
    # and the scanned code appears on it ZERO times. So the redirect was right, the page was
    # right, and the NAME we would have handed back — "Vaal E-Pack Pods (20mg)" — is missing the
    # one word that identifies what he is holding.
    #
    # Same disease as the pack-size trap, one level down: a variant, not a quantity. And it is
    # the worst kind, because the answer looks complete.
    #
    # The discriminator is simple and general: DOES THE PAGE PRINT THE CODE WE SEARCHED FOR?
    # Measured across six lookups — the four exact hits all print it (…yellow (100 Stk.),
    # …green (50 Stk.), Purple Kush Kit, actiTube Slim (50Stk.)); both family pages print no
    # EAN at all. A shop that lists a variant's code on the page is telling us which variant
    # this is; one that does not has only shown us the range.
    #
    # NOT a reason to discard the hit — the family name plus a photo is still a big head start
    # over a bare number. It is a reason to SAY SO, so nobody creates "Vaal E-Pack Pods (20mg)"
    # and discovers next month that three flavours share it.
    exact = bool(barcode) and barcode in (html or "")

    return {
        "found": True,
        # True  → the page carries this exact code; the title names the item.
        # False → the code resolved to a FAMILY page; the title is the range, and the variant
        #         (flavour / size / colour) is NOT identified. The packet is the authority.
        "exact": exact,
        "source": shop["key"],
        "source_label": shop["label"],
        "source_url": final_url,
        # The caution the operator needs BEFORE they trust the number they can see on that
        # page in the other tab. No price crosses this boundary, ever.
        "wholesale": bool(shop.get("wholesale")),
        "title": title,
        "brand": None,
        "category": None,
        "description": (desc.group(1).strip() if desc else None) or None,
        "images": [img.group(1)] if img else [],
        "lang_hint": shop.get("lang"),
    }


async def _shop_lookup(client, barcode: str) -> dict | None:
    """Ask each RESOLVABLE_SHOP for this exact code. First hit wins; None if nobody knows it.

    One request per shop, sequential, stopping at the first answer — so the common case is a
    single GET. These are suppliers' own sites, not ours: never loop, never retry, never bulk.
    """
    for shop in RESOLVABLE_SHOPS:
        try:
            r = await client.get(shop["search"].format(ean=barcode), follow_redirects=True)
            if r.status_code != 200:
                continue
            # THE HIT SIGNAL IS THE REDIRECT. An exact match lands on the article path; a miss
            # stays on the search URL and echoes the code back as the page title. Testing the
            # URL rather than the body is what makes a miss unambiguous — the search page for
            # "3086126789880" is a perfectly valid 200 with content on it.
            final = str(r.url)
            hit = parse_shop_page(r.text, final, barcode, shop)
            if hit:
                return hit
        except (httpx.HTTPError, ValueError, KeyError) as e:
            # A supplier's site being slow or down must never break a scan. NARROW on purpose:
            # a bare `except Exception` here swallowed a NameError (`_og` for `_OG`) and the
            # whole tier silently returned None while every part of it worked in isolation —
            # found only by running the body without the guard. An except that can hide a typo
            # is not error handling, it is a blindfold.
            logger.debug("shop lookup failed for %s at %s: %s", barcode, shop["key"], e)
            continue
    return None


_UPCITEMDB_TRIAL = "https://api.upcitemdb.com/prod/trial/lookup"
# The "Open * Facts" family — free, keyless, unlimited. FOOD is the big one (3M+ products: drinks,
# snacks, gummies…), then non-food PRODUCTS. A shop sells both, so try food first (more common),
# then products. Same API shape for all of them.
_OFACTS_HOSTS = ("world.openfoodfacts.org", "world.openproductsfacts.org")
_OFACTS = "https://{}/api/v0/product/{}.json"
_TIMEOUT = 12


def _google_url(barcode: str, name: str) -> str | None:
    q = " ".join(x for x in (barcode, name) if x).strip()
    return "https://www.google.com/search?q=" + quote_plus(q) if q else None


async def _reachable_images(client, urls: list[str]) -> list[str]:
    """Keep only images that ACTUALLY load — retailer CDNs (onbuy…) hotlink-block, so a raw URL
    from UPCitemdb often 403s/unresolves and shows a broken icon. Return the ones that resolve to
    a real image, so 'no pic' is clean (→ snap a photo) instead of broken. Short parallel HEADs."""
    import asyncio as _a

    async def ok(u):
        try:
            r = await client.head(u, timeout=4, follow_redirects=True)
            if r.status_code == 405:   # host rejects HEAD → tiny ranged GET
                r = await client.get(u, timeout=4, follow_redirects=True, headers={"Range": "bytes=0-0"})
            return u if (r.status_code < 400 and "image" in r.headers.get("content-type", "")) else None
        except Exception:
            return None

    if not urls:
        return []
    res = await _a.gather(*[ok(u) for u in urls])
    return [u for u in res if u]


async def lookup_product(barcode: str | None, name: str | None = None) -> dict:
    """Barcode (primary) → a UI-ready product dict. Keyless + free. Never raises.

    Returns: {found, source, title, brand, category, description, images[], lang_hint,
              quota:{remaining,limit,reset,source}|None, google_url, note}.
    `note`: 'no_barcode' | 'quota_exhausted' | 'not_found' | None.
    """
    barcode = (barcode or "").strip()
    name = (name or "").strip()
    out: dict = {
        "found": False, "source": None, "source_label": None, "source_url": None,
        "wholesale": False,
        # See parse_shop_page: False means "we landed on the family, not the item".
        "exact": False,
        "title": None, "brand": None, "category": None,
        "description": None, "images": [], "lang_hint": None, "quota": None,
        "google_url": _google_url(barcode, name), "note": None,
    }
    # NOTE THE ABSENCE OF A PRICE, AND KEEP IT. Every source here quotes somebody else's
    # price — a wholesaler's case price, a foreign retailer's shelf price — and none of them
    # is what this shop charges. The operator types the price. That has always been true of
    # this function; RESOLVABLE_SHOPS makes it load-bearing.
    if not barcode:
        out["note"] = "no_barcode"      # nothing to auto-resolve — hand back the Google (name) link
        return out

    async with httpx.AsyncClient(timeout=_TIMEOUT, headers={"User-Agent": "Banco/1.0"}) as c:
        # 0) SHOPS THAT ANSWER AN EAN — first, because for this trade they hit far more often
        #    than the generic databases below (see RESOLVABLE_SHOPS). Costs one GET.
        shop_hit = await _shop_lookup(c, barcode)
        if shop_hit:
            out.update(shop_hit)
            out["images"] = await _reachable_images(c, out["images"])
            return out

        # 1) UPCitemdb trial — rich + rate-limited. Read the quota straight off the headers.
        try:
            r = await c.get(_UPCITEMDB_TRIAL, params={"upc": barcode})
            rem = r.headers.get("x-ratelimit-remaining")
            if rem is not None:
                out["quota"] = {
                    "remaining": int(rem),
                    "limit": int(r.headers.get("x-ratelimit-limit") or 0),
                    "reset": int(r.headers.get("x-ratelimit-reset") or 0),
                    "source": "upcitemdb",
                }
            if r.status_code == 200:
                items = (r.json() or {}).get("items") or []
                if items:
                    it = items[0]
                    raw_imgs = [u for u in (it.get("images") or []) if u][:6]
                    out.update(
                        found=True, source="upcitemdb",
                        title=it.get("title") or None, brand=it.get("brand") or None,
                        category=it.get("category") or None,
                        description=it.get("description") or None,
                        images=await _reachable_images(c, raw_imgs),
                    )
                    return out
            elif r.status_code == 429:
                out["note"] = "quota_exhausted"     # over the free daily limit → fall through to OPF
        except Exception:
            pass

        # 2) Open Food/Products Facts — free + unlimited; coverage + LANGUAGE vary (flag, don't trust).
        for host in _OFACTS_HOSTS:
            try:
                r2 = await c.get(_OFACTS.format(host, barcode))
                d2 = r2.json() or {}
                if d2.get("status") == 1:
                    p = d2.get("product") or {}
                    imgs = [p.get("image_url")] if p.get("image_url") else []
                    out.update(
                        found=True, source=host.split(".")[1],   # 'openfoodfacts' | 'openproductsfacts'
                        title=out["title"] or p.get("product_name") or None,
                        brand=out["brand"] or p.get("brands") or None,
                        category=out["category"] or p.get("categories") or None,
                        description=out["description"] or p.get("generic_name") or None,
                        images=out["images"] or await _reachable_images(c, [u for u in imgs if u]),
                    )
                    langs = p.get("languages_hierarchy") or []
                    if langs:
                        out["lang_hint"] = str(langs[0]).replace("en:", "")   # e.g. 'nl' → Dutch
                    return out
            except Exception:
                continue

    if out["note"] is None:
        out["note"] = "not_found"
    return out
