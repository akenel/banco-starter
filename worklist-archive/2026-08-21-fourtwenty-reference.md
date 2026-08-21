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

---

# Later the same day — the feed was stale, and a second source measured

## The feed was nine months old, and that was most of my "35%"

`fourtwenty-sync.py` (helixnet, KB-038) names three public URLs that still work:
`fourtwenty.ch/Dropship/Data/dropship_{product feed_v2,specificationfeed_v1,stockfeed_v1}.csv`.

| | rows | distinct real GTINs | matches Felix's 432 real-EAN packets |
|---|---|---|---|
| the copy in helixnet, 2025-11-30 | 10,082 | 9,425 | 153 (35%) |
| downloaded today | 11,035 | 10,404 | **174 (40%)** |

`--fetch` now does the download from inside banco-starter, so a refresh no longer needs the
monster repo. `--prune` removes rows a later feed dropped (188 on the first refresh) and
refuses when the feed is under half the loaded size — a truncated download must never be able
to empty the shop's lookup table.

## Their EANs are NOT different from the packet

Angel: *"why would fourtwenty.ch have different EANs than what is on the actual package —
something is just fundamentally wrong."*

Nothing is. Where FourTwenty carries a product their code is the manufacturer's code:
174 exact matches, and on Gizeh alone **9 of 16 match digit-for-digit including the 8-digit
EAN-8s** — so there is no truncation or padding problem either. 13 feed-misses were searched
on fourtwenty.ch by hand and **the site agreed with the feed 13 times out of 13**. The
dropship feed is not a subset of the webshop; it is the webshop.

The 60% that miss is COVERAGE. FourTwenty is one wholesaler.

## Kings Castle — measured, and genuinely complementary

`kingscastle.ch` is JTL-Shop and answers an EAN search at `?qs=<ean>`. Ten codes FourTwenty
does **not** have:

| EAN | Kings Castle |
|---|---|
| 4260641140046 | ✅ actiTube ActiveFilter 7mm — the BL-10 code nobody else had |
| 4260748411032 | ✅ Purize Holzmundstück 6mm |
| 798190264677 | ✅ LocalWeed VapeKit 40% CBD Purple Kush |
| 42425700 · 42239512 · 42061199 (Gizeh) | ❌ |
| 716165202400 · 716165174516 (Raw, Cyclones) | ❌ |
| 3086126789880 (BIC) · 7630021913565 (American Spirit) | ❌ |
| 7640244720505 (Blow CBD) | ❌ |

**3 of 11 — and all three are ones FourTwenty lacks.** Estimated combined reach ≈ 40% + 16%
≈ **56%**. Nothing else we have covers Purize, actiTube variants or LocalWeed.

⚠️ **Take the name, the photo and the EAN — NEVER the price.** Kings Castle is a wholesaler
and lists cases: EAN `4260641140046` returned *"actiTube ActiveFilter 7mm (10 x 50Stk) —
CHF 99.00"* while the single sits on the same page at CHF 9.90. Auto-filling that price would
be wrong by 10×, and it is the multipack-shares-a-GTIN trap again, from a new direction.

**No feed needed for this one:** `/catalog/page-facts` already reads a product page for name,
price, photo and EAN. The missing piece is only *search Kings Castle by EAN* as a tier below
the reference.

## Tamar: closed, not deferred

`helixnet/src/services/supplier_search/tamar.py:104` returns `barcode=None`, hardcoded. Tamar
publishes no EAN and never will through that adapter. And
`b2b.fourtwenty.ch/b2b_de/uber-uns/downloads.html` carries only safety sheets, lab analyses,
manuals and press kits — no product feed.

## ⛔ THE PROD IMPORT IS BLOCKED, AND ON PURPOSE

Dry-run on Felix's box, 2026-08-21:

```
prod (999800d)    18+ by our classifier :  959
sandbox (today)   18+ by our classifier :  982
```

The 23-row gap **is the alcohol fix**. Prod's `classify()` still has no layer-2 alcohol branch,
so importing there today would load ~22 bottles — Absinthe, Agwa, the Arehucas rums, the Sulzer
sparkling wine — into `reference_products` marked **not 18+**, and `/reference/{id}/adopt`
copies `age_restricted` straight onto the live product (pos_router.py:2287).

**It would leave prod worse than it is now.** Today, hand-creating "Absinthe Mansinthe" gets
gated on the title. Adopting it from an un-fixed reference would not.

**So: deploy today's code to prod first, then import.** Not the other way round.
