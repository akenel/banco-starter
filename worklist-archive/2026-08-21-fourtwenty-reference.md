# The FourTwenty lookup was never loaded — 2026-08-21

*Angel's theory, tested. He was right, and the reason is worse and simpler than he feared.*

> *"Seems to me that FourTwenty has the items, we just don't get matches and our 420 lookup is
> failing when it should be working… I have the feeling that they are the proper numbers. So I'm
> kind of back at the beginning again here. I don't know what we're doing wrong."*

He was doing nothing wrong.

---

## What was measured

| | |
|---|---|
| `reference_products` on **Felix's shop** (159.69.198.85) | **0 rows** |
| `reference_products` on the **sandbox** | **0 rows** |
| `reference_products` on **lapiazza** (helixnet, the ancestor) | **0 rows** |
| `reference_products` on **wolfhold** (freehold) | table does not exist |
| `scripts/import_reference_catalog.py` — the importer the model's own docstring names | **does not exist, and never has** (`git log --all` finds nothing) |

So every FourTwenty code path in the app has been querying an empty table on every machine, for
its whole life. `/reference/search`, `reference_matches` in snap-find, `/catalog/match-candidates`,
`_reference_best_match`, `POST /reference/{id}/adopt` — all live, all correct, all reading nothing.

**CLAUDE.md pattern 1 at its purest: green on every layer a test can reach, and on no screen.**

## The data exists. It is in the monster repo.

```
/home/angel/repos/helixnet/debllm/feeds/fourtwenty/products_latest.csv   3.5 MB, 2025-11-30
  10,082 rows · 9,977 with a real numeric GTIN (99.8%) · 11 minted-looking
  columns: sku;gtin;producttitle_de;brandname;categorygroup_1..3;productcategory;
           weight_g;mainimageurl;imageurl_1..4;salespriceinclvat;vatratepercentage;shipping
  + specifications_latest.csv (5.9 MB) and stock_latest.csv (375 KB)
```

`_reference_best_match`'s own docstring says *"We hold 10,284 FourTwenty rows — 99% with images,
100% with prices"*. That was measured on Angel's bench against a database that no longer exists.
**The number was true; the table it described was never shipped anywhere.**

## Two of his three failed scans are in the feed, with everything

| his scan | in the feed? | what the feed has |
|---|---|---|
| `4002450223400` (BL-12) | ✅ | Pueblo Classic Tabak Dose 100g · CHF 26.50 · 2 photos · Drehtabak |
| `7666563986873` (BL-13) | ✅ | Sasso Tabaccos Brazil Hash BIO · CHF 6.90 · photo |
| `4260641140046` (BL-10, actiTube) | ❌ | genuinely absent — his workaround was correct for that one |

BL-13 is the whole thesis in one row: he scanned the Sasso packet, got a 404, and his catalogue
already holds *"Tabak Beutel Sasso Tobaccos Hash 25gr."* under the minted `2000000202365`.
The real code was sitting in a CSV in another repo the entire time.

## Why loading the CSV is necessary but NOT sufficient

`catalog_shelf_intake_triage`'s docstring says, in Angel's own reasoning:

> *"It is tempting to also propose catalogue matches for the unknowns, but **a bare EAN carries no
> name, so there is nothing to match ON.** The match needs a title, and a title only exists once
> the operator has looked the code up (`POST /catalog/page-facts`)."*

**That was true only because the reference table was empty.** With 9,977 GTIN→title rows loaded,
a bare EAN *does* carry a name. The comment is a fossil of the empty table, and it is what sends
him to a web search nine times out of ten.

Same shape in `_find_catalog_matches` (pos_router.py:1546): it searches `reference_products` by
**title trigram only** — never by barcode — even though the table has a barcode column with its
own index. `/reference/search` (2132) and `_reference_best_match` (3210) *do* match on barcode.
The path he actually walks is the one that doesn't.

## And the web lookup he thinks is "the FourTwenty search" isn't

`services/web_product_lookup.py` hits **UPCitemdb** then **OpenFoodFacts / OpenProductsFacts**,
then hands back a Google URL. It never touches 420.ch. Those databases are food and mass-market
heavy, which is exactly why a Swiss headshop EAN misses. There has never been a live FourTwenty
search to fail.

## How much of the catalogue this rescues — an ESTIMATE, and a floor

Crude normalised title match, my script not the server's trigram:

```
4,995 minted live rows  vs  9,977 feed rows with a real GTIN
  129 exact normalised title match   (2.6%)
  249 close match >= 0.88            (5.0%)
  ---
  378 minimum (7.6%)
```

**Treat 378 as a floor, not the answer.** Tamar and FourTwenty name the same product differently
("Tabak Beutel Sasso Tobaccos Hash 25gr." vs "Sasso Tabaccos Brazil Hash BIO") and my matcher
cannot see through that. The real number is higher and unknown. It is also the wrong lever:

**The lever is scan-time, not bulk.** Load the table, make the EAN miss consult the reference BY
BARCODE, and every packet Angel picks up hands him the real name, price and photo — for the 9,977
items FourTwenty carries. He confirms, it binds, that packet scans forever. The catalogue heals
at the speed of the shelf instead of at the speed of a fuzzy-match script that would bind
siblings. Lesson 8: a wrong bind looks exactly like a right one.

## What to build, in order

1. **`scripts/import_reference_catalog.py`** — upsert the CSV into `reference_products` on
   `(supplier, ref_key)`. Idempotent, re-runnable when a fresh dump arrives. `supplier='420'`.
2. **Make the EAN miss consult the reference by barcode** — the scan miss and shelf-intake
   triage. The endpoint already exists; the flow does not use it.
3. **Then** reverse-lookup: feed title → trigram against the live catalogue → *"is this your
   'Tabak Beutel Sasso…'?"* → bind, human confirming. This is what rescues the Tamar rows.
4. Copy the feed OUT of `helixnet` — Banco cannot depend on the monster repo it left.
   (`[[banco-left-the-monster-repo]]` — that IS the thesis.)

⚠️ Nothing here has been built. This file is the measurement, not the fix.
