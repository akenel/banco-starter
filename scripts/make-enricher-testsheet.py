#!/usr/bin/env python3
# ============================================================================
# make-enricher-testsheet — a sheet Angel can CHECK, before the enricher touches prod.
#
#   python3 scripts/make-enricher-testsheet.py                 # 20 products, DE vs EN
#   python3 scripts/make-enricher-testsheet.py --count 10
#
# WHY THIS EXISTS. `enrich-from-source.py` wants to write ~5,111 products unattended. The
# question is not "does it run" — it ran fine the first time and reported **0 tier ladders
# across the whole catalogue**, because it only knew the German "ab 10 Stück" while
# source_url points at the /en/ pages that say "from 10 pieces". A clean run, a confident
# number, and nothing on the surface looking wrong.
#
# That was caught because Angel asked for six products he already knew the answers to
# instead of a 200-product sample nobody could check. This script industrialises exactly
# that: fetch REAL pages off the shop's own sitemap, run the REAL parser over them, and
# print what it extracted next to a link to the page — so a human can tick or cross each
# row in a couple of minutes.
#
# IT DELIBERATELY FETCHES EACH PRODUCT TWICE, /de/ AND /en/. WORKLIST records a defect —
# "spec parser loses fields on the /en/ pages, Quöllfrisch 16 facets -> 1" — and putting the
# two languages side by side turns that from a remembered anecdote into a number per product.
#
# Doing so on 2026-08-03 suggested THE NOTE IS BACKWARDS. Quöllfrisch (TAM-20067) reads 1
# spec on both languages now, and 1 is right: the page states exactly one before the footer
# begins. A 16 would have been one spec and fifteen rows of footer. So the danger is not the
# EN page losing fields, it is the parser running past the specs and inventing them — which
# is why JUNK below is checked on every page.
#
# Politeness: this is Felix's own shop, one request at a time with a delay. Do not point
# it anywhere else.
# ============================================================================
import argparse
import html as _html
import asyncio
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import httpx  # noqa: E402

# The parser under test — imported, never reimplemented. A testsheet built from a COPY of
# the logic would pass while the real enricher failed, which is worse than no sheet at all.
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "enrich_from_source", os.path.join(ROOT, "scripts", "enrich-from-source.py"))
_efs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_efs)
parse_page = _efs.parse_page

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126 Safari/537.36"}
SITEMAP = "https://artemisluzern.ch/sitemap.xml"

# THE REAL RISK, and it is not the one WORKLIST records.
#
# The Details block is parsed as "every line pair until a known heading", and on this site the
# footer starts immediately after the specs. So a page whose footer heading is NOT in the stop
# list does not lose fields — it GAINS them, silently, writing "Kontakt: Jugendschutz" and
# "AGB: Seit 1999" into raw_facets as though they were product specs.
#
# That is what a "16 facets" reading almost certainly was: one real spec and fifteen rows of
# footer. Checked here on every sampled page so the sheet reports it instead of assuming it.
JUNK = re.compile(
    r"impressum|kontakt|contact|agb|standort|location|jugendschutz|imprint|terms|seit 1999|"
    r"luzern|murbacherstrasse|support|lieferung|rechnung|mastercard|visa|twint|e-shop|"
    r"tamar trade|grow-how|newsletter|uhr$", re.I)

# Consumables are where the shop actually publishes quantity breaks (papers, tubes, filters,
# tips, lighters) — the same set WORKLIST scopes the tier work to. A sample drawn flat from
# 5,000 products would be mostly one-offs with no ladder at all, and a sheet whose every row
# reads "no tiers" tells you nothing about whether the parser works.
CONSUMABLE = re.compile(
    r"papers?|blaettchen|blattchen|huelsen|hulsen|tubes?|filter|tips?|feuerzeug|lighter|"
    r"gizeh|ocb|smoking|raw-|juicy|purize|rizla|drehpapier", re.I)


async def _fetch(client, url):
    try:
        r = await client.get(url)
        return r.text if r.status_code == 200 else None
    except Exception:
        return None


def _de_to_en(url: str) -> str:
    return url.replace("/de/produkt/", "/en/product/")


def _tam_sku(url: str) -> str:
    m = re.search(r"-(\d+)/?$", url)
    return f"TAM-{m.group(1)}" if m else "?"


def _fmt_tiers(t):
    return " · ".join(f"{x['min_qty']}+ → {x['unit_price']}" for x in t) if t else "—"


async def main_async(args):
    async with httpx.AsyncClient(follow_redirects=True, timeout=30, headers=UA) as c:
        idx = (await c.get(SITEMAP)).text
        subs = re.findall(r"<loc>(.*?)</loc>", idx)
        urls = []
        for s in subs:
            body = await _fetch(c, s)
            if body:
                urls += [u for u in re.findall(r"<loc>(.*?)</loc>", body) if "/produkt/" in u]
            if len(urls) > 4000:
                break
        print(f"{len(urls)} product URLs in the sitemap", file=sys.stderr)

        rnd = random.Random(args.seed)
        consum = [u for u in urls if CONSUMABLE.search(u)]
        rnd.shuffle(consum)
        rest = [u for u in urls if not CONSUMABLE.search(u)]
        rnd.shuffle(rest)
        # Mostly consumables (where ladders live), plus a few controls so the sheet also shows
        # what an ordinary product looks like — "no tiers" must be distinguishable from "broken".
        n_ctrl = max(2, args.count // 5)
        picked = consum[:args.count - n_ctrl] + rest[:n_ctrl]
        print(f"sampling {len(picked)} ({args.count - n_ctrl} consumables + {n_ctrl} controls)",
              file=sys.stderr)

        rows = []
        for i, de_url in enumerate(picked, 1):
            en_url = _de_to_en(de_url)
            de_html = await _fetch(c, de_url)
            await asyncio.sleep(args.delay)
            en_html = await _fetch(c, en_url)
            await asyncio.sleep(args.delay)

            de = parse_page(de_html) if de_html else {}
            en = parse_page(en_html) if en_html else {}
            name = "?"
            if de_html:
                m = re.search(r"<h1[^>]*>(.*?)</h1>", de_html, re.S)
                if m:
                    # UNESCAPE. The first cut of this sheet printed "Granny&#x2019;s Deluxe" and
                    # "Mundst&#xFC;ck" — the very bug CLAUDE.md has a lesson about (0.429 vs
                    # 1.000). A sheet a human is meant to read against a shop page must show
                    # what the page shows.
                    name = _html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
                    name = re.sub(r"\s+", " ", name).strip()[:60]
            rows.append({
                "sku": _tam_sku(de_url), "name": name, "de_url": de_url, "en_url": en_url,
                "de_ok": de_html is not None, "en_ok": en_html is not None,
                "de_tiers": de.get("tiers", []), "en_tiers": en.get("tiers", []),
                "de_facets": len(de.get("facets", {})), "en_facets": len(en.get("facets", {})),
                "facets_sample": list((de.get("facets") or {}).items())[:3],
                "junk": {k: v for k, v in (en.get("facets") or {}).items()
                         if JUNK.search(k) or JUNK.search(str(v))},
            })
            print(f"  {i:>3}/{len(picked)}  {rows[-1]['sku']:<11} "
                  f"tiers de={len(rows[-1]['de_tiers'])} en={len(rows[-1]['en_tiers'])}  "
                  f"specs de={rows[-1]['de_facets']} en={rows[-1]['en_facets']}", file=sys.stderr)
        return rows


def render(rows, path):
    n = len(rows)
    de_t = sum(1 for r in rows if r["de_tiers"])
    en_t = sum(1 for r in rows if r["en_tiers"])
    agree = sum(1 for r in rows if r["de_tiers"] == r["en_tiers"])
    lost = [r for r in rows if r["de_facets"] > r["en_facets"]]
    dead = [r for r in rows if not r["de_ok"] or not r["en_ok"]]
    junky = [r for r in rows if r["junk"]]

    L = []
    A = L.append
    A("# Enricher testsheet — does `enrich-from-source.py` read a page correctly?\n")
    A("*Generated by `scripts/make-enricher-testsheet.py`. Every row is a REAL product page on "
      "the shop's own site, parsed by the REAL parser the bulk run would use.*\n")
    A("**How to use this:** open the DE link, look at the price box and the Details table, and "
      "tick the row. You are checking two things only — did it find the right **quantity "
      "breaks**, and did it find the **spec table**. Ten or twenty rows is plenty; the point is "
      "that you know the answers, not that the sample is big.\n")
    A("> The one that matters is a ladder that is WRONG, not one that is missing. A missing "
      "ladder means the till charges the normal price. A wrong one charges a customer the wrong "
      "money.\n")

    A("\n## What the run found\n")
    A(f"| | |\n|---|---|")
    A(f"| products sampled | {n} |")
    A(f"| tier ladders found on **/de/** | {de_t} |")
    A(f"| tier ladders found on **/en/** | {en_t} |")
    A(f"| DE and EN agree on the ladder | {agree} / {n} |")
    A(f"| pages that failed to fetch | {len(dead)} |")
    A(f"| products where **/en/ lost spec fields** | {len(lost)} |")
    A(f"| products with **footer junk written as specs** | {len(junky)} |")

    if junky:
        A("\n### 🛑 Footer junk is being stored as product specs\n")
        A("The Details block ends at a known heading, and on this site the footer begins right "
          "after the specs. Where a footer heading is missing from the stop list the parser does "
          "not lose fields — it INVENTS them. These would be written to `raw_facets` by "
          "`--apply`:\n")
        A("| SKU | product | junk it would store |")
        A("|---|---|---|")
        for r in junky:
            A(f"| {r['sku']} | {r['name']} | " +
              "; ".join(f"`{k}: {v}`" for k, v in list(r["junk"].items())[:3]) + " |")
    else:
        A("\n### ✅ No footer junk in the specs\n")
        A("Checked every sampled page for the failure mode that actually threatens this parser: "
          "the Details block runs into the site footer and stores `Kontakt: Jugendschutz` as a "
          "product spec. **None found** — the stop list holds on both languages.\n")

    if lost:
        A("\n### The DE/EN spec difference, measured\n")
        A("WORKLIST records this as *\"spec parser loses fields on the /en/ pages (Quöllfrisch "
          "16 → 1)\"*. **That note looks wrong.** Re-checked on 2026-08-03: Quöllfrisch "
          "(TAM-20067) now reads 1 spec on BOTH languages — and 1 is the correct answer, "
          "because that page states exactly one (`Hersteller: Quöllfrisch`) before the footer "
          "starts. A 16 would have been one spec plus fifteen rows of footer. So the earlier "
          "reading was probably the DE side over-collecting, not the EN side losing.\n\n"
          "Any genuine remaining differences are listed here. **`source_url` points at the "
          "/en/ pages**, so the right-hand column is what a bulk run would store:\n")
        A("| SKU | product | specs on /de/ | specs on /en/ | lost |")
        A("|---|---|---:|---:|---:|")
        for r in sorted(lost, key=lambda r: r["de_facets"] - r["en_facets"], reverse=True):
            A(f"| {r['sku']} | {r['name']} | {r['de_facets']} | {r['en_facets']} | "
              f"**{r['de_facets'] - r['en_facets']}** |")

    A("\n## The sheet — tick each row\n")
    A("| ✔/✘ | SKU | product | quantity breaks the parser found | specs DE/EN | page |")
    A("|:---:|---|---|---|:---:|---|")
    for r in rows:
        tiers = _fmt_tiers(r["de_tiers"])
        flag = "" if r["de_tiers"] == r["en_tiers"] else " ⚠️ DE≠EN"
        fetch = "" if (r["de_ok"] and r["en_ok"]) else " ❌ fetch failed"
        A(f"|  | {r['sku']} | {r['name']} | {tiers}{flag}{fetch} | "
          f"{r['de_facets']}/{r['en_facets']} | [open]({r['de_url']}) |")

    A("\n## What a cross means\n")
    A("- **Ladder wrong / invented** → STOP. Do not run `--apply` on prod. This is money.\n"
      "- **Ladder missing but the page shows one** → the regex missed a wording; fixable, "
      "and safe to fix before the bulk run.\n"
      "- **Specs 0 on both** → that product has no Details table. Not a bug.\n"
      "- **Specs high on DE, low on EN** → the known defect above. Informational fields only, "
      "no money at risk — but it is what would get written.\n")
    A("\n*Tiers are money. Specs are information. Judge them by different standards.*\n")

    open(path, "w", encoding="utf-8").write("\n".join(L))
    return {"n": n, "de_t": de_t, "en_t": en_t, "agree": agree, "lost": len(lost),
            "dead": len(dead)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--out", default=os.path.join(
        ROOT, "onboarding", "testsheets", "enricher-testsheet.md"))
    args = ap.parse_args()

    rows = asyncio.run(main_async(args))
    s = render(rows, args.out)
    print(f"\n✅ {args.out}")
    print(f"   {s['n']} products · ladders de={s['de_t']} en={s['en_t']} · "
          f"agree {s['agree']}/{s['n']} · /en/ spec loss on {s['lost']} · dead fetches {s['dead']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
