# The four rows that could not join the pool — 2026-08-22

Angel scanned 1 × Greengo King Size + 2 × Greengo King Size slim and the till
showed **CHF 6.00** where three plain papers should be **CHF 5.00**.

Nothing was wrong with the price. One checkbox was wrong: **"price is for the
whole pack"** was unticked, so the row stored `tier_mode = per_unit`.

`per_unit` means *"buy 3 of THIS product"*. `bundle` means *"3 packs for 5"* —
and only `bundle` rows pool with each other. A `per_unit` row is an island.

All four carry the identical broken shape:

    price 2.00 · per_unit · [{min_qty:1, 2.00}, {min_qty:3, 5.00}]

The `{min_qty:1, 2.00}` rung does nothing at all — it restates the base price.

## Why it looked fine

Three of the SAME slim pack alone does ring 5.00. The server spots a rung
priced above base, guesses it means a pack, and falls back to the pack ladder.
So the row passes every single-product test and only breaks when mixed.
**A row that is right alone and wrong in company will not be found by testing
it alone.**

## The fix — tick "price is for the whole pack", drop the 1-rung

| EAN | Product | Do |
|---|---|---|
| `2000000232225` | Elements Phantom King Size Slim | tick whole-pack |
| `2000000237800` | Elements Zushi King Size Slim | tick whole-pack |
| `85950672` | Greengo King Size slim | tick whole-pack |
| `84157089` | Smoking Gold Kingsize | **different** — see below |

Codes to paste into shelf intake: `per-unit-strays-codes.txt`
Rollback if the mode flip is ever done in SQL: `rollback-per-unit-four.sql`

## Smoking Gold is a separate decision, not a bug

Felix said Gold is a collector paper, costs 50 more, **no deal**. It was set to
2.50 with no tiers on 2026-08-21 — and it is back at 2.00 with a 3-for-5 rung.
Something in the round trip reverted it. Worth watching: if it reverts a second
time, the shelf-intake save is putting a price back, not the staff.

## Everything else is clean

85 active products carry a 3-pack rung correctly on `bundle`:
37 rolls + 33 papers (Rolling Papers), 10 rolls + 5 papers (Papers & Filters),
1 roll filed under "Other" (`Greengo Rolls King Size` — pools fine, the
category is just untidy). These four were the only strays.

---

# What the sweep found on its first run — live catalogue, 2026-08-22

`GET /catalog/price-check` over the live shop: **10 rows**, not the 4 I found by hand.

## Red — cannot pool (the original four)

| EAN | Product | Do |
|---|---|---|
| `2000000232225` | Elements Phantom King Size Slim | tick whole-pack |
| `2000000237800` | Elements Zushi King Size Slim | tick whole-pack |
| `85950672` | Greengo King Size slim | ✅ Angel fixed 2026-08-22 |
| `84157089` | Smoking Gold Kingsize | separate decision: 2.50, no deal |

## Amber — a `{min_qty: 1}` rung, and TWO of them are live money

A `min_qty: 1` rung silently replaces the shelf price. Confirmed against
`pricing.tier_unit_price()` itself, not by reading it:

| EAN | Product | Catalogue says | Till charges | Per unit |
|---|---|---|---|---|
| `4035687900004` | Tycoon Gas 250ml | 6.90 | **5.00** | **−1.90** |
| `85966789` | Greengo Wide Rolls | 4.00 | **3.50** | **−0.50** |

Neither is a deal — it is one unit. Whichever number is the intended one, the
shelf label and the drawer disagree today, and only Angel can say which is right.

The other six are harmless: the `min_qty: 1` rung restates the base price exactly,
so nothing changes at the till. They are flagged amber as dead weight, not as a
leak — four actiTube rows, two GIZEH rows.

**This is the point of the sweep.** Both leaks had been sitting in the catalogue,
on every screen, priced in indigo like a feature. Neither was findable by looking
at the row you happened to be working on.

---

# Category tidy — 2026-08-22

> Angel: *"can you fix them all so they are all 'Rolling Papers' … then they are all the same, so
> the Rolls with our bundle prices and the King Size Papers also have the 'Rolling Papers'
> category for consistency."*

**18 rows moved** — 17 from `Papers & Filters`, 1 from `Other`. Category only; price, tiers,
mode, class and age gate untouched. Rollback: `rollback-category-tidy.sql` (one statement per
EAN, restoring each row's own previous category).

The selector was the bundle ladder itself, not the category name — *"products carrying our two
deals"*. That matters: it caught every roll and paper and **no filters or tips**, which is the
line Angel drew himself (*"ks papers with filters get no bundle pricing"*). Picking rows by
category would have needed a judgement call per row; picking them by the deal they carry needed
none.

The live shop now reads as two clean groups and nothing else:

```
Rolling Papers · CHF 2.00 · 3 for  5.00 → 42 King Size papers
Rolling Papers · CHF 4.00 · 3 for 10.00 → 49 rolls
```

## One row does not match its 48 siblings — NOT changed

`2000000070070` **Greengo Rolls King Size** is `product_class = cbd_hemp` and **age-gated 18+**.
The other 48 rolls are `standard` with no gate. It is a rolling-paper roll; the class looks like
it was inferred from the brand name.

**Left alone on purpose.** Loosening an age gate is the one direction where a wrong bulk script
is a compliance failure, not a tidy-up. It needs Angel or Ralph to say "that is a plain paper",
and then it is a two-field edit.

It prices correctly either way — pooling keys on price and terms, not on class — so this is a
compliance-tidiness question, not a money one.
