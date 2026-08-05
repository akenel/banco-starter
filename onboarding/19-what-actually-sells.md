# 19 · What actually sells at Artemis — read off the paper book

*Compiled 2026-08-05 from photographs of the shop's handwritten day book, **4 July – 5 August 2026**.
This is the only record of real demand that exists: Banco has 8 transactions of history, the paper
book has a month of them.*

> ### ⚠️ Read this before you trust a number
>
> **25 of 31 photographed pages were read** across the whole date range; the remaining 6 are too
> blurred to transcribe honestly. The ranking was **stable from page to page** — the same names kept
> coming up in the same order — so the top is solid.
>
> It is handwritten German shorthand in biro. Names that repeat constantly (`Pape`, `Blow`,
> `Purize`, `Grips`, `Clipper`) are unambiguous. One-off entries are my best reading and some are
> guesses. **Treat this as a ranking, not an audit.**
>
> **Angel can check it in ten seconds** — he knows what sells. If the top five look wrong, the
> reading is wrong.
>
> **Day totals seen on the card pages:** 311 · 346 · 398 · 431 · 477 · 480 · 523 · 644 · 806 ·
> 1292 · 1325 CHF. Cash is a separate sheet on top of that.

---

## What the book actually is

Three things, and together they are the whole till on paper:

1. **Daily cash sheet** — every cash sale itemized by hand, with a full denomination count
   (`Noten 610.- / Münz 153.70 / Saldo 763.70`) and the opening float carried forward.
2. **Card pages** — every Händlerbeleg slip stapled in, items written beside each one, totalled as
   `Tagestotal Karte` (seen: 311.46 · 398.30 · 523.30 · 806.70).
3. **Cashier tabs** — `Leila` · `Raphi` · `Lele` — and a `Barentnahmen` (cash withdrawals) section.

That is itemized sales, a cash count and a shift report. **It is more complete than expected**, and
it is the thing Banco replaces.

---

## 🏆 The ranking

### Tier 1 — on almost every page, often more than once

| | Written as | What it is | Typical |
|---|---|---|---|
| **1** | **Pape · Papes** | rolling papers | 2–12.– |
| **2** | **Purize · A-Filter · Filter · Siebe · Tips** | activated-carbon filters, screens, tips | 0.90–39.90 |
| **3** | **Blow · Blow PR** | CBD joints | 6.90–39.60 |
| **4** | **Grips · Grinder** | **grinders** | 5–35.– |
| **5** | **Clipper · Feuer · Brenner** | lighters and torches | 1–20.– |

> 🎯 **Ranks 1–3 are exactly the shelf Angel scanned on 5 August.** Papers and filters are the shop's
> bread and butter by a wide margin, and they now scan.
>
> 🔴 **Rank 4 contradicts the plan.** Angel's read was *"you don't buy a grinder every day… I don't
> sell those very often."* **The book disagrees flatly.** `Grips` or `Grinder` appears on nearly
> every page read, **twice on some** — 5.50 · 7.– · 9.– · 10.– · 15.– · 35.– · 38.50. It is a tier-1
> line, not a slow mover. **Next shelf.**

### Tier 2 — most days

| Written as | What it is |
|---|---|
| **Local Mary** | CBD flower — the most-named single brand |
| **Blau** | tobacco |
| **Medusa · Hash · GP Hasch** | hash |
| **Rolls · Rips** | paper rolls |
| **Getränke · Bio Bier · Red Bull** | **drinks** |
| **Zigi · Zigi einzeln** | cigarettes, incl. **loose singles at 1.–** |
| **Puesto · Puebla** | (recurring, product unclear) |

### Tier 3 — regular but not daily

`Qualicann` · `Green Passion` · `Starbuds` · `Heimat` · `Parisienne` · `Elfbar` · `CBD Vape` ·
`E-Liquid` · `J-Hülle` (joint tubes) · `CBD Öl` (69–138.–) · `Räucherstäbchen` · `Farfalla` ·
`Gizeh` · `OCB` · `Elements` · `Smoking` · pipes (`Glas-Pipe`, `HD-Pipe`, `Holzpfeife`) · `Dose` ·
`Tabakersatz` · `Local Weed` · `Cannabees`

### 💰 Big-ticket, seen once or twice — but they matter to the takings

`Mighty` **398.–** (Storz & Bickel vaporizer) · `Amnesia` 100.– · `CBD Öl` 127–138.– ·
`Zigi-Maschine` 55.– · `Rips-Box` 49.– · `Raffco T.2` 89.– · `Farfalla` 57.– · `Vaporizer` 30–44.– ·
`Hanfsalbe` 300.– · `Bong-Ersatz` · `Storz+Bickel Netzadapter`

### The long tail

`Schnitz-Set` · `Waxy` · `Lolly` · `Brownie Hasch` · `Osiris Öl` · `Sonnenberg` · `Red Leaf` ·
`Bubblegum Sticker` · `Karten` · `Warmer Coco` · `Swiss Polar` · `Wildkraut` · `Dünger` ·
`Akku Pen` · `Rollmaschine` · `Stahlwolle` · `Winston` · `Löffel` · `Ashtray`

---

## 🔎 Four things the book says that Banco does not know

**1. Grinders are not a slow mover.** See above. The assumption that shaped the scanning plan is
contradicted by a month of real sales.

**2. Drinks are being sold and are probably not in the catalogue.** `Getränke` at 1.10–6.– appears
repeatedly. `Cafe & Food` has 46 products; nobody has checked whether the drinks actually sold are
among them.

**3. Loose cigarettes.** `Zigi einzeln 1.–` — sold as singles out of a pack. That has **no barcode**
and cannot be scanned, so it needs a button or a PLU, not a bind. Worth deciding before go-live.

**4. The basket is small and fast.** Card transactions run 1.10 to ~80.–, mostly **5–40.–**, with
occasional 100–400 outliers. Card days total 311–1325 CHF, plus a separate cash sheet. **This is a
many-small-transactions shop**, which is exactly the till speed doc 10 demands: *2 seconds, or it
is broken.*

**5. The treat bowl is real and in use.** `Lolly` appears in the book at 1.–, alongside full-price
items. Felix's *hold the price, give a treat* policy is not theory — it is running, on paper, today.
`line_item.is_giveaway` already models it.

---

## What to do with this

- **Next shelves to scan**, in order: **grinders** (the finding), then **lighters** (`Clipper` is
  everywhere), then the CBD flower brands (`Local Mary` first — it is the most-named single brand in
  the book), then `Green Passion` · `Qualicann` · `Starbuds`.
- **Check drinks** are in the catalogue at all.
- **Decide the loose-cigarette question** — no EAN by definition.
- **The big-ticket lines are worth binding even though they sell rarely** — a `Mighty` at 398.– is
  worth more than a hundred packets of papers, and getting it wrong at the till is a much bigger
  mistake.
- **Retire this document** once Banco has a few weeks of real sales. `GET /reorder/suggestions`
  already ranks by what the till actually sold, and a query beats a photograph. Until then, this is
  the only demand data that exists.

---

## 💥 Where the big days come from — and it is NOT the consumables

The card day totals swing from **311 to 1325 CHF**. Reading what sat on the big days, the spikes are
consistently **hardware and CBD oil/flower**, never papers:

| Single transaction | What it was |
|---|---|
| **398.–** | **`Mighty`** — a Storz & Bickel vaporizer |
| **378.–** | `Zigi Pap` — bulk, reads like a trade sale |
| **307.–** | `Bong-Ersatz` + `Filter` + `Dochte` + `Brenner` — a bong and its kit |
| **300.–** | `Hanfsalbe` |
| **158.40** | `Purize` + `Waxy` + `Filter` + `Grips` |
| 138.– · 127.– | `QC Öl` · `CBD Öl` |
| **100.–** | `Amnesia` |
| 110.– · 104.– · 102.50 | (unread detail) |

> ### 🎯 The shape of the business, in one line
>
> **Consumables are the VOLUME. Hardware and flower are the VALUE.**
>
> Papers at 2–12.– appear on every page and make the day tick over. A single `Mighty` at **398.–** is
> worth roughly **eighty packets of papers**. Both matter, and they need opposite treatment:
> consumables need a **fast till**, hardware needs the **price and the product to be exactly right**.
>
> ⚠️ **And the high-value end is precisely the end with no barcodes** — vaporizers, bongs, grinders,
> trays. The stuff that is hardest to get into Banco is the stuff where a mistake costs the most.

---

## 📅 What sold on 5 August (the day Angel was there)

Both sheets for the day were photographed — the cash page and the card page.

**Cash:** opening float **763.70** (Noten 610.– · Münz 153.70). Around **28 line items**, the
largest being `UD-Tips` **81.–**, `Zigi-Maschine` **55.–**, `Purize` **39.90 ×2**, `Blau` 33.30,
`Starbuds` 22.90, `Borghi` 19.50, `Brenner` 19.–. The rest are 1.50–15.– consumables.

**Card:** ~21 transactions, 1.– to 50.–. `Zigi Case` 50.– · `Local Mary` 49.80 · `Clippers` 42.– ·
`HD-Pipe` 38.– · `B-Pro` 32.20 · `Local Weed` 31.70 · `GP Grill` 30.–.

**On the day: `Pape` ~8 times · `Clipper` 3 · `Grips` 3 · `Local Mary` 2 · `Purize` 3.** One
`Zigi einzeln` at **1.–** — the loose-cigarette case, live.

**A completely ordinary day**, which is what makes it useful: papers, filters, lighters and grinders
tick over all day, and one or two 40–80.– items carry the takings.

---

## ⚠️ Grinders and bongs need a different approach

*Angel, 2026-08-05: "The bongs are gonna be hard, and the grinders are gonna be hard stuff too, get
EAN numbers. **None of the grinders have EAN numbers.** They have prices on them, and they have
pictures."*

So the shelf-intake loop — scan the packet, bind the real EAN — **does not apply to the shelf the
book says is rank 4.** Options, none of them decided:

- **Mint an internal barcode and print a label.** That is what `barcode_is_internal` is for, and the
  labeller already works over Bluetooth. It makes them scannable at the till, which is the whole
  point. ⚠️ But it is the 2026-07-30 lesson's neighbour — *never invent an identifier that exists in
  the physical world.* A grinder with genuinely no EAN is the case where minting is **correct**,
  because nothing real is being overwritten. **The rule is "don't invent one that exists", not
  "never mint".**
- **Sell by name/search**, no barcode. Works, but breaks the 2-second till.
- **A PLU button** for the handful that sell most.

Same question covers **loose cigarettes**, which can never have a barcode either. Worth deciding
once, for all three.
