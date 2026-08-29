# ean-match — what is left, and in what order

*Measured against prod 2026-08-29. Rebuild these numbers with the queries at the bottom; do not
trust them after the next bulk import.*

**The whole job is 4,931 cards ≈ 14 hours of clicking** at the measured rate (8–13s per decision,
papers run 1). That is the number to plan against only if every category is worth doing, and
**it is not** — roughly 6 of those 14 hours are hardware that has no twin to find.

## The three tiers

| tier | what it is | cats | cards | hours |
|---|---|---|---|---|
| **A** | has controls, proven findable | 11 | 860 | **2.5** |
| **B** | no controls, feed has supply — unknown | 11 | 1,994 | 5.5 |
| **C** | hardware, house-brand — likely skip | 24 | 2,077 | 5.8 |

Tier A is the whole of the confident work and it fits in an afternoon.

## Per category

`deck` = active · minted · has a photograph (what select_run.py would build).
`ctrl` = rows already bound off a packet, which ride along and measure the run.
`known` = what fraction of those bound EANs is actually in the FourTwenty feed.
`feed` = feed rows in the matching `categorygroup_2`, i.e. how much supply exists to match against.

### Tier A — do these, in this order

| category | deck | ctrl | known | feed | hrs |
|---|---:|---:|---:|---:|---:|
| Filters & Tips | 225 | 39 | 69% | 308 | 0.6 |
| CBD Flower | 195 | 24 | 54% | 394 | 0.5 |
| Pipes | 116 | 12 | 50% | 231 | 0.3 |
| Tobacco | 109 | 55 | 44% | 107 | 0.3 |
| Rolling Papers *(46 left)* | 46 | 122 | 77% | 318 | 0.1 |
| Blunts & Wraps | 44 | 16 | 81% | 108 | 0.1 |
| Food & Snacks | 42 | 4 | 50% | 125 | 0.1 |
| Cones & Tubes | 39 | 1 | 100% | 81 | 0.1 |
| Rolling & Filling Machines | 22 | 1 | 100% | 81 | 0.1 |
| Other | 21 | 80 | 34% | — | 0.1 |
| Papers & Filters | 1 | 3 | 67% | 318 | 0.0 |

**Filters & Tips is the best next run**: 39 controls (second only to papers), 69% of them findable,
and 225 cards is a single sitting.

### Tier B — supply exists, nothing proves it works. Pilot before committing.

| category | deck | ctrl | feed | hrs | note |
|---|---:|---:|---:|---:|---|
| E-Liquids | 699 | 0 | **179** | 1.9 | ⚠ see below |
| Coils & Pods | 349 | 0 | 550 | 1.0 | |
| Vape Devices | 290 | 1 | 231 | 0.8 | |
| Prefilled & Disposables | 283 | 7 | 298 | 0.8 | 4/7 known found |
| Dab & Concentrate Gear | 157 | 0 | 299 | 0.4 | |
| Shisha Tobacco | 126 | 0 | 182 | 0.3 | |
| Snuff Accessories | 113 | 0 | 162 | 0.3 | |
| Drug Testing | 40 | 0 | 71 | 0.1 | |
| Shisha Coal | 25 | 0 | 182 | 0.1 | |
| Cigarette Tubes | 9 | 0 | 81 | 0.0 | |
| Nicotine Shots | 7 | 0 | 179 | 0.0 | |

⚠ **E-Liquids is the trap in this whole project.** It is the single largest block of work —
699 cards, 1.9 hours, 14% of everything left — and the feed holds about **179** rows that could
possibly be a liquid (`Vape Liquids` 150 + `Vape CBD` 29). Even a *perfect* matcher tops out at
26%, and there is not one control to say whether the real number is 26% or 2%. **Never open this
category without piloting it first.** Same caution, milder, for Coils & Pods and Vape Devices.

### Tier C — minted hardware. The minted code is probably the right answer.

Bongs · Grinders · Storage & Stash · Bong & Pipe Accessories · Vaporizers · Rolling Trays ·
Ashtrays · Lighters · Decor · Accessories (general) · Shisha Bowls/Hoses/Hookahs · Scales ·
Presses · Knives & Tools · Apparel · Entertainment & Games · Incense · Cosmetics · Gifts ·
Packaging & Bags · Rolling Accessories — **2,077 cards, 5.8 hours.**

12 minted bongs and grinders were ranked against the feed and **0 matched** (LESSONS,
2026-08-28). These are house-brand goods that exist in no other catalogue, and LESSON #9 says the
minted EAN is the correct answer for them, not a defect.

## Read the `known` column as a CEILING, not an estimate

Those percentages come from products Angel bound **by scanning a packet** — which means they are
the products branded enough to carry a printed barcode at all. The deck is the *complement* of
that set: what is still minted is disproportionately generic, house-brand, and unbarcoded.

This is why Bongs reads 75% in the table while 12 minted bongs matched **0**. Not a contradiction —
two different populations, and the deck is the harder one. Name the population in the same
sentence as the number (LESSON pattern #5).

## The pilot — 5 minutes buys a go/no-go

For any Tier B category, build the deck, work **30 cards**, and stop. At 10s a card that is five
minutes, and the confirm rate on those 30 tells you whether the remaining 600 are worth 1.7 hours.
Salt in decoys (rows whose EAN is in no feed) so the pilot measures gullibility and not just
recall — papers run 1 had none, and that gap is still open.

## Two things to fix before the next run

1. **`export-products.sql` re-presents decided cards.** It selects on `barcode_is_internal`, which
   `apply.py` deliberately never clears — so all 23 papers bound on Friday would appear again in a
   fresh papers deck. Needs `AND NOT EXISTS (SELECT 1 FROM product_barcodes WHERE product_id = p.id
   AND source = 'image-match')`. Until that lands, subtract the aliased count by hand.
2. **`sheet3.BOX = 3.0` is measured on papers and on nothing else.** Re-measure the price ratio per
   category (`prove-ean-box-price.py`) before trusting the box flag on liquids or tobacco.

## Rebuild these numbers

```sh
# deck / controls per category
./scripts/prod-query.sh -c "
SELECT p.category,
       COUNT(*) FILTER (WHERE p.barcode_is_internal AND i.id IS NOT NULL) AS deck,
       COUNT(*) FILTER (WHERE p.barcode_is_internal AND b.product_id IS NOT NULL) AS aliased,
       COUNT(*) FILTER (WHERE NOT p.barcode_is_internal) AS controls
FROM products p
LEFT JOIN LATERAL (SELECT id FROM product_images WHERE product_id=p.id LIMIT 1) i ON true
LEFT JOIN (SELECT DISTINCT product_id FROM product_barcodes WHERE source='image-match') b
       ON b.product_id = p.id
WHERE p.is_active GROUP BY p.category ORDER BY deck DESC;"

# feed supply per categorygroup_2
./scripts/prod-query.sh -c "
SELECT raw->>'categorygroup_1', raw->>'categorygroup_2', COUNT(*)
FROM reference_products
WHERE raw->>'gtin' IS NOT NULL
  AND coalesce(raw->>'mainimageurl', raw->>'imageurl_1') IS NOT NULL
GROUP BY 1,2 ORDER BY 3 DESC;"
```

The `known` column is `work/known_eans.csv` (exported by the query in git history) cross-referenced
against `work/poolfull.csv`, normalising the leading zero on both sides — a UPC-A and an EAN-13 are
one code (LESSON pattern #2).
