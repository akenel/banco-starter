# SPEC — Department Keys (non-catalog sales)

Status: draft for implementation
Scope: Banco POS, till + daily close + reporting
Owner: Angel

---

## 1. Problem

Roughly 30% or more of shop stock has no usable EAN and never will (glass, grinders,
grow supplies, samples, knick-knacks). The cashier cannot and will not identify these
at the till. Any flow that asks her to search, create a product, or look something up
mid-sale will be abandoned within a week.

Current fallback is an on-the-fly "lazy" product entry. That is wrong: it pollutes the
catalog with unidentifiable stubs and creates duplicates every time the same item sells
again.

## 2. Decision

Non-catalog items are sold against **department keys** — fixed accounting buckets with a
free-typed price. They are not products. They never enter the catalog, never sync to the
master, never appear in Artemis, and are never enriched after the fact.

A department line records: department, price, quantity, VAT rate, timestamp, and (if a
scan preceded it) the unresolved barcode.

## 3. The buttons

*Rewritten 2026-08-07. The first draft invented nine German names. Angel killed it — the shop
already HAS a category list, it is already on the catalogue screen, and Ralph and the girls
already use it. Inventing a second, parallel list would have been a second thing to learn.*

### 3.1 The idea, in one line

> **A button = one of the bold headings the catalogue already has.**

Nothing new to learn, nothing new to name. And the payoff is the part that matters:

- A **scanned** grinder and a **bucketed** grinder land in **the same bucket**. So "Grinders did
  2,400 this month" is one honest number, not two half-numbers that have to be added up.
- Someone can fix it later without a migration. Angel: *"no, I know that bong. That's the one you
  sold. It takes me fifteen minutes, but I'll find it and barcode it."* The sale already sits in
  Bongs; binding the EAN just makes the next one scan.
- Most of the time nobody will bother, **and that is fine.** *"You sell plastic grinders, metal
  grinders, whatever grinders. It's all grinders as far as I'm concerned."*

### 3.2 The buttons

Ten. `Diverses` is last. Receipt text is the word SHE writes in the day book, not the English
heading and not the correct German noun — she writes `Grips`, so the button says `Grips`.

| # | Button (her word) | English heading behind it | What goes in it | Things in it | Scan today | VAT |
|---|---|---|---|---|---|---|
| 1 | **Glas** | Smoking Gear → Bongs | Bongs, glass, bubblers, `Bong-Ersatz` | 178 | **0** | 8.1% |
| 2 | **Grips** | Smoking Gear → Grinders | Every grinder — plastic, metal, wood, all of them | 200 | 8 | 8.1% |
| 3 | **Zubehör** | Smoking Gear (the rest) | Pipes, ashtrays, `Dose`, scales, snuff, dab, presses | ~1,150 | 14 | 8.1% |
| 4 | **Vape** | Vape | E-liquid, pods, disposables, `Elfbar`, vaporizers | 1,885 | 6 | 8.1% |
| 5 | **Tabak** | Tobacco & Shisha | `Blau`, shisha, coal, hoses, **`Zigi einzeln`** | 424 | 53 | 8.1% |
| 6 | **CBD** | CBD & Hemp | `Blow`, `Local Mary`, `Local Weed`, oils, **`Hasch`** | 235 | 24 | 8.1% |
| 7 | **Deko** | Lifestyle & Gifts | `Räucherstäbchen`, decor, bags, textiles, `Karten` | 300 | **0** | 8.1% |
| 8 | **Dünger** | Grow & Lab | Fertiliser, substrate, drug tests | 61 | 21 | 8.1% |
| 9 | **Getränke** | Cafe & Food | Fridge drinks, snacks | 46 | 1 | **2.6%?** ⚠️ |
| 10 | **Diverses** | — | Everything else. **Last on the strip.** | — | — | 8.1% |

**Why `Glas` and `Grips` are split out of Smoking Gear:** a bong is ~100 francs, a grinder is ~15.
In one bucket you cannot tell a good bong month from a good grinder month, and bongs are where the
money is. Everything else in Smoking Gear stays together as `Zubehör` — she does not need to
decide between an ashtray and a stash tin mid-sale.

### 3.3 NOT buttons, on purpose

| Heading | Why not |
|---|---|
| **Papers & Rolling** (653 things, **120 scan**) | The best shelf in the shop and rank 1 in the day book. `Pape` and `Purize` already scan. A button here would throw away the only good data there is. |
| **Unsorted / System** (222 things) | A junk drawer, not a shelf. Nothing is "sold from Unsorted". |

### 3.4 The four holes this exercise found

*Recorded because each one is a real sale with nowhere to go.*

1. 🔴 **`Hasch` / `Medusa` / `GP Hasch` has no category anywhere in the system.** It sells most
   days. Parked under `CBD` above — **Ralph must confirm that is where he wants it**, because it
   is the one bucket with a legal dimension.
2. 🔴 **`Zigi einzeln 1.–`** — a single cigarette out of an opened pack. Can never have a barcode.
   Parked under `Tabak`.
3. 🔴 **Drinks.** Cafe & Food holds 46 things and **1** scans, yet `Getränke` / `Bio Bier` /
   `Red Bull` sell daily. They are probably not in the catalogue at all.
4. ⚠️ **Vape is 1,885 things — a third of the whole catalogue — and the day book barely sells
   any.** Either the book reading is wrong or a third of the catalogue is supplier data that has
   never sold in this shop. Worth knowing before anyone "cleans up the catalogue".

### 3.5 Hard rules

- Maximum 10, and 10 are used. **Adding an 11th means removing one**, because every extra button
  is a decision at the till.
- `Diverses` is **last** on the printed strip and last in the tap list. If the catch-all is the
  easiest key to reach, everything becomes `Diverses` and the data is worthless.
- VAT is a property of the button. It is never typed or chosen by the cashier.
- Codes are **Code128 alphanumeric**, not numeric, so a collision with a real EAN is impossible.
- **A button is a confession that we do not know what was sold.** Adding one is cheap; removing
  one after it has revenue against it is not.


## 4. Till flow

### 4.1 Normal path

1. Cashier scans product barcode.
2. EAN resolves → product line added. Nothing changes here.

### 4.2 Unresolved scan

1. Cashier scans product barcode.
2. EAN does not resolve.
3. POS shows a **non-blocking** notice: `Nicht gefunden — Abteilung wählen`.
   - No "create product?" prompt. No search box. No modal that must be dismissed.
   - The unresolved barcode is held in a pending slot for the next line only.
4. Cashier scans a department key from the till strip, or taps it on screen.
5. Price keypad opens with focus in the amount field.
6. Cashier types price, confirms. Line added.
7. The unresolved barcode is attached to that line (see §6) and the pending slot clears.

If the cashier does anything else instead (scans a different product, voids, tenders),
the pending barcode is discarded silently. No nagging.

### 4.3 No barcode at all

Steps 4–6 only. Department line with no attached barcode.

### 4.4 Input rules

- Department keys are both scannable (gun) and tappable (tablet). The gun is already in
  her hand; scanning must never require putting it down.
- Price: positive, non-zero, two decimals, ceiling 999.00.
- Prices at or above 200.00 require a second confirm tap (fat-finger guard).
- Quantity multiplier allowed on a department line (3 × 5.00), default 1.
- Cash rounding to 0.05 applies at tender as it does for catalog lines. Department lines
  are not individually rounded.
- Discounts on department lines: not supported. She adjusts the typed price instead.

## 5. What is explicitly not built

- No cleanup queue for department lines. If nobody knew what it was at the till, nobody
  knows at 20:00. The information is gone. Accept it permanently.
- No converting a department line into a product after the fact.
- No editing a department line after the sale closes. Corrections are a void plus re-ring,
  same as any other line.
- No department line ever reaches the master catalog or the Artemis storefront.

> ### ✅ What IS allowed — do not read the above as "never improve anything"
>
> Angel, 2026-08-07: *"no, I know that bong. That's the one you sold. It takes me fifteen minutes,
> but I'll figure it out and find it and barcode those bongs, because we want to track them."*
>
> **That is encouraged.** Go to the catalogue, find the bong, bind its barcode — and the NEXT one
> scans. What stays frozen is the line that already sold: it remains `Glas 95.00`, forever.
>
> The distinction is the whole discipline. **Improving the catalogue going forward: yes, always.
> Rewriting what a past sale was: never.** The moment a closed sale can be re-described, the
> journal stops being a record and the daily close stops being provable.

## 6. Miss log

Every unresolved barcode captured in §4.2 is written to a `catalog_miss` table:

```
barcode, first_seen, last_seen, hit_count, department_code, prices_seen[], resolved_ean
```

This is the highest-value output of the whole feature. It is a self-prioritising catalog
backlog: an unknown barcode that has been scanned nine times is a real mover worth
enriching; one scanned once is noise. Back office works the list top-down by `hit_count`,
never at the till.

When a miss is later resolved into a real catalog product, set `resolved_ean` and stop
counting. Do not retroactively restate past sales — those lines stay as department revenue.

## 7. Journal, close and reporting

- Department lines are sales. Same append-only immutable journal, same sequence numbers,
  same daily close, same signed daily sheet. No special-casing.
- Daily close report shows department totals as a block, **laid out in the same order and
  wording as the shop's paper tally sheet**, so the parallel run can be reconciled line by
  line against Leandra's pen strokes.
- Daily close also shows: department revenue as a % of total revenue, and count of
  department lines vs catalog lines. This is the number that says whether the rollout is
  working. Target: catalog lines ≥ 80% of all lines, velocity-weighted.
- VAT split per rate must include department lines correctly.

## 8. Till strip (printed reference)

One A4 page, laminated, taped flat beside the till. Two copies printed — one gets sticky.

Per department, one row:

- Code128 barcode, large enough to scan at arm's length
- Department name in German, bold
- 3–4 example product photos, small, from the actual shop shelves
- One line of plain German saying what falls in it

Ordered by expected frequency, `Diverses` last.

## 9. Acceptance criteria

1. Unresolved scan → department line → tender completes in ≤ 3 cashier actions after the
   failed scan (department, price, confirm).
2. No modal at any point blocks the sale.
3. A cashier who has never seen the system can complete an unresolved-item sale using only
   the printed strip, with no verbal instruction.
4. Miss log correctly attributes the unresolved barcode to the department line that
   followed it, and does not attribute it when the cashier did something else instead.
5. Daily close department block matches a hand-tallied paper sheet for the same day.
6. VAT report totals reconcile including department lines at mixed rates.

## 10. Open items

*Split on purpose. A question only the shop can answer must not sit in a build queue waiting for
a developer, and a build decision must not sit waiting for Felix.*

### 10.1 🔴 Ralph (Rafi, the manager) and Felix — nobody else can answer these

*Ralph runs the floor and also appears as a cashier tab in the day book, so he is the one who
knows both what gets written down and what actually gets sold.*

| # | Question | Why it blocks |
|---|---|---|
| 1 | **Are the ten button words the words the girls actually use?** `Glas · Grips · Zubehör · Vape · Tabak · CBD · Deko · Dünger · Getränke · Diverses` | The whole design rests on her not having to translate mid-sale. If Leila or Leandra writes something else, her word wins. Check against the day-book photos — they are not in this repo. |
| 2 | **`Hasch` / `Medusa` — is `CBD` the right button for it?** | It has no category anywhere in the system today and it sells most days. It is also the one bucket with a legal dimension, so this is Ralph's call, not a developer's. |
| 3 | **Is `Hasch` / `Local Mary` weighed on a scale, or sold as pre-packed units?** | A weighed sale has no unit price to type. If it is weighed, that button needs a price-per-gram flow — a materially bigger build. |
| 4 | **`Blow` (CBD joints, rank 3 by volume) — sealed supplier packs with an EAN, or shop-packed?** | If sealed, it belongs in the catalogue and should be bound, not bucketed. Bucketing a top-3 seller would throw away real data. |
| 5 | **Is the reduced 2.6% rate actually charged on fridge drinks today, or is everything rung at 8.1%?** | VAT belongs to the button and is never chosen at the till. `Getränke` is the only button with a different rate. **Matching current shop practice beats being technically right** — if they charge 8.1% today, set it to 8.1%. |
| 6 | **Who may void a department line — cashier, or manager only?** | §5 says corrections are void + re-ring. A free-typed price with an easy void is the softest spot in this whole design for cash to walk. |
| 7 | **Vape is 1,885 things — a third of the catalogue — and the day book barely sells any.** Is that real? | Either the book reading is wrong, or a third of the catalogue is supplier data that has never sold in this shop. Worth knowing before anyone spends a week "cleaning up the catalogue". |
| 8 | **Should the customer receipt show the button name, or something plainer?** | A tourist reading `DIVERSES 45.00` may well ask what it was. |

### 10.2 🔧 Build decisions — Angel and the copilot, no shop input needed

| # | Question | Notes |
|---|---|---|
| 9 | **Where does the button live on the line?** | `line_items.product_id` is **already nullable** (its own comment: *"name lives in notes, price is sent by the till"*) and the report path already renders such lines from `notes`. So this is additive, not a rewrite. A real `department_code` column is still worth it — reporting off a free-text note is the mistake this spec exists to prevent. |
| 10 | **Does the button map to `product_group`, or to its own list?** | Mapping to the existing `product_group` is the entire point of §3 — it is what makes a scanned grinder and a bucketed grinder add up to one number. `Glas` and `Grips` are the two exceptions: they map to a *sub*category (Bongs, Grinders) rather than the heading. |
| 11 | **Does the till strip print from Banco, or is it a one-off Angel designs once?** | Code128 + the Bluetooth QL-820NWB already works. A shop that clones Banco needs to print its own strip, so this should be a route — not a PDF that exists on one laptop. |
| 12 | **Interaction with the till guard + first-price panel (shipped 08-07).** | A *catalogued* product with a `999.99` placeholder still needs the price panel. The risk is that Pam rings a known product as `Glas` because it is two taps faster. §7's catalog-line percentage is the detector — so it has to be **on a screen**, not merely computed. |
| 13 | **§7's "catalog lines ≥ 80%" is a guess.** | Measured 2026-08-07: the catalogue is **7% scannable** overall (Papers 55%, Filters 9%, Grinders 4%, Bongs 0%). Department lines may be well over 20% at first. Track the trend; do not read a missed target as failure. |
| 14 | **§6's miss log cannot see the items that motivated this spec.** | It fires only when a barcode is scanned *and fails*. Bongs and grinders have no barcode to scan, so nothing is logged. It will do real work on drinks, cigarettes and new stock. For glass, the button total is the only signal there will ever be. |

---

## 11. Making the buttons configurable — phase 2, deliberately not phase 1

*Angel, 2026-08-07: "these departments are all hard coded should we have them as part of the
config settings so the admin can add or remove some button labels?"*

**Yes, eventually.** Banco is meant to be cloned, and a bakery's buttons are not a headshop's.
Hard-coding ten German-Swiss smoking-shop buckets into a product other people are supposed to
stand up is a temporary state, not a design.

### 11.1 Why it waits for the shadow day

**We do not yet know whether these ten are the right ten.** §3.2 reserves the tenth slot on
purpose — *"the first thing the parallel run will find is a bucket she keeps reaching for that
nobody predicted"* — and the shadow-day tally
([`testsheets/SHADOW-DAY-TALLY.html`](../testsheets/SHADOW-DAY-TALLY.html)) exists to produce
exactly that answer, in one day, on paper, for free.

Building a settings screen first means building the tool for changing an answer before knowing
what the answer is. Run the day, read the Key column, then decide whether config is *how you fix
a wrong list* or merely *a nicety for the next shop*.

### 11.2 The four guardrails — cheap to write now, expensive to retrofit

*Recorded so whoever builds it does not have to rediscover them.*

1. 🔴 **A department with revenue against it can never be deleted — only retired.** Past sales
   reference the code, and §5 forbids rewriting a closed sale. Retiring hides it from the strip
   and keeps it in the reports. **The day-close block already handles this** — an unknown code
   that took money still appears, flagged `retired`, so the block reconciles to the till rather
   than to today's configuration.
2. 🔴 **`vat_class` is a tax decision, not a UI preference.** It must be a fixed picklist of real
   `PRODUCT_CLASSES` values, admin-only, with the consequence spelled out on screen. Free text
   here misfiles a whole shelf's VAT silently and in the shop's favour — the kind an auditor
   finds, not a test.
3. ⚠️ **The shipped ten are translated into four languages; a custom one will not be.** Config
   labels override the built-in `dept.*` strings, and a shop-added button shows the same word in
   every language. That is acceptable — it is the shop's own word, which is the whole point —
   but it must be a stated behaviour, not a surprise.
4. ⚠️ **The cap of ten and `Diverses` last must be enforced BY the config screen**, not left to
   convention. Both exist for reasons that are invisible from a settings page: every extra button
   is a decision at the till with a customer waiting, and a catch-all that is easy to reach eats
   everything (§3.5).

### 11.3 What it is not

Not a per-cashier preference, and not a way to reorganise the shop's reporting after the fact.
Changing the buttons changes what tomorrow's sales are filed under; it never re-files yesterday's.
