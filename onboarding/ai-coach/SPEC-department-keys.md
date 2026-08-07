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

## 3. Department list

*Rewritten 2026-08-07 from two things that already exist, rather than invented: the shop's own
handwriting in [`19-what-actually-sells.md`](../19-what-actually-sells.md) (25 of 31 photographed
day-book pages, 4 July – 5 August), and the measured scannability of every shelf on prod.*

> ⚠️ **The day-book photos are NOT in this repo** — only the transcription, and that document
> calls itself *"a ranking, not an audit"* with 6 pages too blurred to read. Angel must check
> this list against the photos he still holds before it is built. Names below are her words as
> transcribed; if she writes something else, her spelling wins.

### 3.1 The rule that decides what is a department

**Not "does it scan today" — "does a barcode exist in the physical world at all?"** That single
question splits the day book cleanly in two, and getting it wrong in either direction is expensive.

| | Pile A — **a real EAN exists, it is merely unbound** | Pile B — **no EAN exists, ever** |
|---|---|---|
| Examples | `Pape` · `Purize`/`Filter` · `Clipper` · `Blau` · `Zigi` packs · `Getränke` · `Elfbar` · `Mighty` · `CBD Öl` | `Glas`/bongs · `Pfeifen` · `Grips` · `Hasch`/`Local Mary` by weight · `Zigi einzeln` · `Dünger` · knick-knacks |
| Right answer | **Bind it once.** Finite work, and it is most of the volume. | **Department key.** No amount of work makes these scan. |
| Wrong answer | Making it a department — it cannibalises catalogue sales that would have worked, and destroys the velocity data permanently | Waiting for an EAN that is never coming |

> 🎯 **Rolling Papers is 55% scannable and is rank 1 in the book. `Pape` must NOT be a department.**
> Filters (rank 2) sit at 9%, but Purize packets carry real retail EANs — that is a *binding*
> backlog, not a department. Meanwhile **Bongs and Bong-Zubehör are 0% and 431 rows**, and Angel
> confirmed on 05-08: *"None of the grinders have EAN numbers."* That is Pile B, permanently.

### 3.2 The list

**Receipt text is HER word from the day book**, not the correct German noun. `Grips` is what she
writes for a grinder; a strip that says `Grinder` is a strip she has to translate mid-sale.

| Code | Receipt (her word) | Proper German | English | Covers — day-book terms | VAT |
|---|---|---|---|---|---|
| `DEPT-GLAS` | **Glas** | Glaswaren | Glass | Bongs, `Bong-Ersatz`, `Glas-Pipe`, bubblers, downstems, adapters | 8.1% |
| `DEPT-PFEI` | **Pfeife** | Pfeifen | Pipes | `HD-Pipe`, `Holzpfeife`, metal/one-hitters | 8.1% |
| `DEPT-GRIP` | **Grips** | Grinder | Grinders | `Grips`, `Grinder` — rank 4 in the book, 4% scannable | 8.1% |
| `DEPT-HASH` | **Hasch** | Hasch / Blüten | Hash & flower by weight | `Medusa`, `GP Hasch`, `Local Mary`, `Local Weed`, `Amnesia` | 8.1% |
| `DEPT-ZIGI` | **Zigi einzeln** | Einzelzigarette | Loose cigarette | `Zigi einzeln 1.–` — a single out of an opened pack | 8.1% |
| `DEPT-GETR` | **Getränke** | Getränke | Drinks | `Bio Bier`, `Red Bull`, fridge — ⚠️ see §10, VAT unconfirmed | 2.6%? |
| `DEPT-GROW` | **Dünger** | Growbedarf | Grow supplies | `Dünger`, substrate, `Root Juice`, `Wildkraut` | 8.1% |
| `DEPT-ZUBE` | **Zubehör** | Zubehör | Accessories | `Dose`, `J-Hülle`, `Ashtray`, `Löffel`, `Stahlwolle`, `Schnitz-Set`, `Karten` | 8.1% |
| `DEPT-DIV` | **Diverses** | Diverses | Misc | Everything else — **last on the strip** | 8.1% |

**Nine, not ten.** The tenth slot stays empty on purpose: the first thing the parallel run will
find is one bucket she keeps reaching for that is not here. Leave room for it.

### 3.3 Deliberately NOT departments — and why

*Each of these was a candidate and was rejected. Recorded so the decision is not silently redone.*

| Day-book term | Why not a department |
|---|---|
| `Pape` / `Papes` | **55% already scannable, rank 1 by volume.** A department here would delete the shop's best data. |
| `Purize` / `Filter` / `Tips` | Real retail EANs exist (9% bound). This is a **binding backlog**, and it is rank 2 — worth the work. |
| `Clipper` / `Feuer` | Branded lighters carry EANs. Binding work, not a bucket. |
| `Blau` / `Zigi` packs | Tobacco packs carry EANs (32% bound). Also the shelf with the tightest legal traceability. |
| `Mighty` / `Vaporizer` / `Elfbar` / `E-Liquid` | **`Mighty` is 398.– — one is worth eighty packets of papers.** The book's own conclusion: *hardware needs the price and the product to be exactly right.* Never bucket the expensive end. |
| `CBD Öl` (69–138.–) · `Hanfsalbe` (300.–) | Same reason. High value, real packaging, real EANs. |
| `Blow` (CBD joints, rank 3) | ⚠️ **Undecided — Felix question.** If they are shop-packed with no barcode it belongs in `DEPT-HASH`; if they come sealed from a supplier with an EAN it is Pile A. See §10. |

### 3.4 Hard rules

- Maximum 10. Every extra one is a decision at the till. Nine used, one held in reserve.
- `DEPT-DIV` is **last** on the printed strip and last in the tap list. If the catch-all
  is the easiest key to reach, everything becomes `DIV` and the data is worthless.
- VAT rate is a property of the department. It is never typed or chosen by the cashier.
- Codes are **Code128 alphanumeric**, not numeric. This makes barcode collision with a
  real EAN structurally impossible.
- **A department is a confession that identity is gone.** Adding one is cheap; removing one after
  it has revenue against it is not. When unsure, use `DEPT-DIV` and read the miss log.

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

*Split on purpose: a question only Felix or the shop can answer must not sit in a build queue
waiting for a developer, and vice versa. §3 is now derived and no longer blocks.*

### 10.1 🔴 Felix / the shop — nobody else can answer these

| # | Question | Why it blocks |
|---|---|---|
| 1 | **Is the 2.6% reduced rate actually charged on fridge drinks today?** Or is everything rung at 8.1%? | VAT is a property of the department and is never chosen at the till. Getting it wrong misfiles every drink sale, and it is the one department with a different rate. Drop `DEPT-GETR` to 8.1% if that matches current practice — matching the shop beats being technically right. |
| 2 | **`Blow` (CBD joints) — sealed supplier packaging with an EAN, or shop-packed?** | Decides whether rank 3 by volume is Pile A (bind it) or Pile B (`DEPT-HASH`). Getting this wrong either deletes the velocity data for a top-3 line, or leaves the cashier searching for something that cannot be found. |
| 3 | **Does `Hasch` / `Local Mary` sell by weight off a scale, or as pre-packed units?** | A weighed sale has no unit price to type. If it is weighed, `DEPT-HASH` needs a price-per-gram flow, which is a materially different build. |
| 4 | **Should department revenue be broken out on the customer receipt, or shown only as the line name?** | Receipt layout + what the customer sees. A tourist reading `DIVERSES 45.00` may query it. |
| 5 | **Confirm the nine names against the day-book photos.** Angel holds them; they are not in this repo. | §3 is derived from a transcription that calls itself *"a ranking, not an audit"*, with 6 of 31 pages unreadable. If she writes a bucket that is not here, it is missing from the strip. |
| 6 | **Who is allowed to void a department line?** Cashier, or manager only? | §5 says corrections are void + re-ring. A free-typed price with an easy void is the softest spot in the whole design for cash to leak. |

### 10.2 🔧 Build decisions — Angel and the copilot, no shop input needed

| # | Question | Notes |
|---|---|---|
| 7 | **Where does `department_code` live on the line?** | `line_items.product_id` is **already nullable** (comment: *"name lives in notes, price is sent by the till"*) and the report path already renders those lines from `notes`. A real `department_code` column is still worth it — reporting on a free-text note is the mistake this spec exists to avoid. |
| 8 | **Does the till strip print from Banco, or is it a one-off design?** | Code128 + the Bluetooth QL-820NWB already works. A shop that clones Banco needs to print its own strip, so this should be a route, not a PDF Angel made once. |
| 9 | **Interaction with the till guard + first-price panel (shipped 08-07).** | A *catalogued* product with a `999.99` placeholder still needs the price panel. Risk: Pam rings a known product as `DEPT-GLAS` because it is two taps faster. §7's catalog-line percentage is the detector — make sure it is on a screen, not just computed. |
| 10 | **§7's "catalog lines ≥ 80%" target is a guess.** | Measured 2026-08-07: the catalogue is **7% scannable** overall (Papers 55%, Filters 9%, Grinders 4%, Bongs 0%). Department lines may be well over 20% at first. Track the trend, do not treat a missed target as failure. |
| 11 | **§6's miss log is blind to Pile B.** | It fires only when a barcode is scanned *and fails*. Bongs and grinders have no barcode to scan, so nothing is logged. The miss log will do real work on drinks, cigarettes and new stock; for glass the department total is the only signal there will ever be. Consistent with §5 — but do not expect it to solve the problem that motivated the spec. |
