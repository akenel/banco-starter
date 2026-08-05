# 19 · What actually sells at Artemis — read off the paper book

*Compiled 2026-08-05 from photographs of the shop's handwritten day book, **4 July – 5 August 2026**.
This is the only record of real demand that exists: Banco has 8 transactions of history, the paper
book has a month of them.*

> ### ⚠️ Read this before you trust a number
>
> **10 of 31 photographed pages were read**, spread across the whole date range. The ranking below
> was **stable from page to page** — the same names kept coming up in the same order — so the top of
> the list is solid. **The tail is a sample, not a census.**
>
> It is handwritten German shorthand in biro. Names that repeat constantly (`Pape`, `Blow`,
> `Purize`, `Grips`) are unambiguous. One-off entries are my best reading and some are guesses; a
> few I could not read at all and left out. **Treat this as a ranking, not an audit.**
>
> **Angel can check it in ten seconds** — he knows what sells. If the top five look wrong, the
> reading is wrong.

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

### Tier 1 — every day, several times a day

| | Written as | What it is | Typical |
|---|---|---|---|
| **1** | **Pape · Papes** | rolling papers | 2–12.– |
| **2** | **Blow · Blow PR** | CBD joints | 6.90–39.60 |
| **3** | **Purize** | activated-carbon filters | 4–39.90 |
| **4** | **Filter · Siebe · Tips** | filters, screens, tips | 0.90–10.– |
| **5** | **Grips** | grinders | 5–15.– |

> 🎯 **This is exactly the shelf Angel scanned on 5 August.** Papers, filters and tips were the right
> call by a wide margin — they are the shop's bread and butter and they now scan.
>
> ⚠️ **Except grinders.** Angel's read was *"you don't buy a grinder every day… I don't sell those
> very often."* **The book disagrees** — `Grips` shows up on most pages. Worth a shelf of its own.

### Tier 2 — most days

| Written as | What it is |
|---|---|
| **Clipper · Feuer · Brenner** | lighters and torches |
| **Local Mary** | CBD flower/brand |
| **Blau** | tobacco |
| **Medusa · Hash Medusa** | hash |
| **Getränke** | **drinks** |
| **Zigi · Zigi einzeln** | cigarettes, incl. **loose singles** |

### Tier 3 — regular but not daily

`Qualicann` · `Green Passion` · `Starbuds` · `Heimat` · `Parisienne` · `J-Hülle` (joint tubes) ·
`CBD Öl` · `Rolls` · `Räucherstäbchen` (incense) · `Farfalla` (essential oils) ·
pipes (`Glas-Pipe`, `HD-Pipe`, `Holzpfeife`) · vapes and e-liquid · `Cones` · `Dose`

### Seen once or twice — the long tail

`Schnitz-Set` · `Zigi-Maschine` (55.–) · `Waxy` · `Hanfsalbe` · `Bong-Ersatz` · `Red Bull` ·
`Lollies` · `Brownie Hasch` · `Local Weed` · `Osiris Öl` · `Sonnenberg` · `Red Leaf` ·
`Bubblegum Sticker` · `Karten` · `Warmer Coco` · `Cannalees`

---

## 🔎 Four things the book says that Banco does not know

**1. Grinders are not a slow mover.** See above. The assumption that shaped the scanning plan is
contradicted by a month of real sales.

**2. Drinks are being sold and are probably not in the catalogue.** `Getränke` at 1.10–6.– appears
repeatedly. `Cafe & Food` has 46 products; nobody has checked whether the drinks actually sold are
among them.

**3. Loose cigarettes.** `Zigi einzeln 1.–` — sold as singles out of a pack. That has **no barcode**
and cannot be scanned, so it needs a button or a PLU, not a bind. Worth deciding before go-live.

**4. The basket is small and fast.** Card totals run 1.10 to ~80.–, mostly 5–40.–, with occasional
150–380 outliers. Days total roughly **300–800 CHF on cards** plus cash. **This is a
many-small-transactions shop**, which is exactly the till speed doc 10 demands: *2 seconds, or it
is broken.*

---

## What to do with this

- **Next shelves to scan**, in order: **grinders**, then lighters (`Clipper`), then the CBD flower
  brands (`Local Mary`, `Green Passion`, `Qualicann`, `Starbuds`).
- **Check drinks** are in the catalogue at all.
- **Decide the loose-cigarette question** — it has no EAN by definition.
- **Retire this document** once Banco has a few weeks of real sales. `GET /reorder/suggestions`
  already ranks by what the till actually sold, and a query beats a photograph. Until then, this is
  the only demand data that exists.
