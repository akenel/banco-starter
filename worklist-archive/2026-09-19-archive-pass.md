# Archive pass — 2026-09-19

*Triggered by `scripts/worklist-check.py` (516 lines, limit 500) while recording Layla's eight
tickets from the shop test of 2026-09-18. **Verbatim, nothing deleted.** Two closed threads moved
out of `WORKLIST.md`, and two orphan fragments removed — both left behind by the 2026-09-17
archive pass, and both of them WRONG where they sat.*

---

## Moved out: item 1 — the age gate (CLOSED `9c292b8`)

A three-row remainder stayed live in `WORKLIST.md`; the closed narrative is here.

```
1. ~~🔞 **The age gate misses siblings.**~~ **CLOSED `9c292b8` · 14 live rows applied, gated 1157→1171.**
   5 hashish were sellable with no ID. Ratchet proof, 5,436 swept, 0 un-gated. Split clusters 15→2.
   ⚠️ **3 rows need Angel's EYE, not a regex** — titles carrying only a brand: `Cannabees Purple Fuel
   4g`, `Qualicann Habanero Kush`, and `ELFBAR 4in1 Pod Cherry ICE` (no strength on the label).
```

---

## Moved out: item 2 — the placeholder price sentinel (CLOSED 2026-09-17)

The live remainder — 84 products still unpriced, the 999.00 hole, the `SEPARATOR` rows, and the
un-chipped `till_priced` — stayed in `WORKLIST.md`. The closed narrative is here.

```
2. ⚠️ **The placeholder guard is still two values wide.** ▶️ **2026-09-17 — the list is now REACHABLE:**
   `/pos/cleanup` → The Bench → **🚫 Can't be sold**. The server had `_bench_gap_expr("price")`
   (`price IN (99.00, 999.99)`) and was returning `gap_counts["price"]` on every page load, with
   **no chip on the screen** — LESSON #1 again, the same shape as `allow_nonstandard`. **84 live
   products** on the shop: 34 at 99.00 (ALL created 07.07.26, all big-ticket — 12 bongs at exactly
   99.00 is not a coincidence) and 50 at 999.99.
   ✅ **Angel judged that batch: all 34 were placeholders.** *"i was wrong to do 99 and should of
   made the place holder 999.99 which is an obvious place holder."* `UPDATE 34` on the shop;
   **zero rows at 99.00 anywhere**, 84 at 999.99, all still refused at the till. None had ever
   sold — the guard held, so no receipt carries that number.
   ✅ **CLOSED 2026-09-17 — `UNVERIFIED_PRICES = (Decimal("999.99"),)`.** One sentinel. A bong at
   **CHF 99.00 now sells**; before tonight the till refused a real price, which is a worse fault
   than the one the sentinel caught. Safe because it was MEASURED, not assumed: of 5,347 live
   prices **not one ends in .99** (.90 × 2,818 · .00 × 1,846 · .50 × 561 · then round tens). Not
   safe for being large — the shop holds a rosin press at CHF 1'199.00. Angel had the principle
   right and the number slightly off: the house style is .90, not .95.
   Both screens that paint a row red (`cleanup`, `shelf_intake`) were changed in the same commit,
   or the bench would list rows the till would happily sell (LESSON #13). `scan.html` needed
   nothing — its JS reads the list from the server. 37 tests, and the till asked with its own
   predicate: `[999.99]` · refuses 999.99 · sells 99.00, 99.90, 1199.00.
   🔎 **Also unreachable and worth a second chip:** `till_priced` — a price a cashier guessed
   mid-sale, on something that has actually sold. Counted, returned, no button. Felix's margin list.
    `UNVERIFIED_PRICES = (99.00, 999.99)`. The
   six live rows at 999.00 were moved to 999.99 on 2026-09-10 (Angel likes the guard: *"it basically
   forced the user to put the right price in"*), **but type 999.00 tomorrow and it walks through.**
   The four rows at 0.00 are his `SEPARATOR-001…004` shelf markers — an intake aid for testing without
   selling. **Deliberate. Leave them.**
```

---

## Removed: two orphan fragments from the 2026-09-17 pass

When threads 2 and 6 were cut down last night, two tails were left attached to the wrong bodies.
Both read as live statements and **both contradicted the line above them.** Recorded here because
nothing is deleted — but do not carry either one forward; they are superseded.

**1 · Under item `6x`**, immediately after *"Not started; not a midnight job."*:

```
 The books are right
   (`tax_amount` == sum of line VAT); the cart's estimate is the odd one out. Predates 5 August.
```

This is the tail of the OLD item 6 (the cart-vs-receipt rappen, closed `11da57b`). Sitting under
`6x` it says the books tie out — which is the exact opposite of what `6x` measured: 6 of 60
discounted sales do NOT tie out.

**2 · Inside item 2**, after the sentinel was narrowed to one value:

```
    `UNVERIFIED_PRICES = (99.00, 999.99)`. The
```

The set became `(Decimal("999.99"),)` last night. Left in place, it tells a future reader the
guard is still two values wide — the very thing the commit removed, and the reason a CHF 99.00
bong could not be sold.

*Lesson: a splice that cuts a paragraph in half leaves the other half somewhere. After an archive
pass, read the seams.*
