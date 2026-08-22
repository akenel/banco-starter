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
