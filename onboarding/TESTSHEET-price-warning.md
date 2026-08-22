# Test sheet — the price warning (prod)

**Shop:** https://banco.wolfhold.app · log in as a **manager** (the editor steps need it)
**Build:** `275768b` · deployed 2026-08-22
**Time:** about 13 minutes

> ⛔ **Never press Checkout.** Every cart step ends with 🗑️ **Clear**.
> A completed transaction is a line in the Kassenbuch.

Mark each line **PASS** or **FAIL**. A FAIL is not a disaster — write down what you
actually saw, that is the useful part.

---

## A · The sweep — 2 min

| # | Do this | Expect | ✓ |
|---|---|---|---|
| A1 | Open **Catalog**, let the list load | | |
| A2 | Look under the four stat boxes | An amber-edged panel: **⚠️ Pricing to check (8)** | ☐ |
| A3 | Tap the panel to open it | It expands into a list | ☐ |
| A4 | Read the top two | **Elements Phantom King Size Slim** and **Elements Zushi King Size Slim**, in RED, "3+ costs MORE than one" | ☐ |
| A5 | Read the rest | Six in AMBER — 4 × actiTube, 2 × GIZEH — about a "1+" break | ☐ |
| A6 | Look under each red one | A line telling you to tick "price is for the whole pack" | ☐ |

If the count is not 8, write the number down — it is not necessarily wrong,
it means something changed in the catalogue since this sheet was written.

---

## B · The badge on the row — 3 min

| # | Do this | Expect | ✓ |
|---|---|---|---|
| B1 | Catalogue search: `Elements Phantom King Size Slim` | | |
| B2 | Look at the row | A RED warning chip, and **no** 🏷️ deal chip | ☐ |
| B3 | Search: `Smoking Red Kingsize` | | |
| B4 | Look at the row | 🏷️ **3 for 5.00**, and **no** warning | ☐ |

> **B4 is the most important line on this sheet.** If a correct row gets flagged,
> stop and tell me. A warning that cries wolf gets switched off within a week,
> and then it protects nothing.

| # | Do this | Expect | ✓ |
|---|---|---|---|
| B5 | **Shelf intake** → paste both codes below → **Triage the shelf →** | | |
| B6 | The Elements Phantom row | Red warning + the "tick whole pack" line | ☐ |
| B7 | The Smoking Red row | **3 for 5.00**, no warning | ☐ |

```
2000000232225
84157065
```

---

## C · Caught as you type, fixed in one tap — 3 min

**The catalogue editor**

| # | Do this | Expect | ✓ |
|---|---|---|---|
| C1 | Catalog → **Smoking Red Kingsize** → ✏️ Edit → scroll to **Quantity price breaks** | Type is **N for X total** | |
| C2 | Click the other radio, **price EACH** | A red box appears at once: "Check this price — 3+ costs MORE than one" | ☐ |
| C3 | Look inside the red box | A blue **N for X total** button | ☐ |
| C4 | Tap the blue button | Red box gone, **N for X total** selected again | ☐ |
| C5 | **Cancel** — do not save | | |

**The till editor** (the one you used this morning)

| # | Do this | Expect | ✓ |
|---|---|---|---|
| C6 | Scan → `84157065` → tap the cart line → **Manager price fix** | | |
| C7 | Untick **price is for the whole pack** | "⚠️ That is a price RISE, not a deal" | ☐ |
| C8 | Look under it | A blue **Yes — price is for the whole pack** button | ☐ |
| C9 | Tap it | The box ticks itself, the warning clears | ☐ |
| C10 | **Cancel**, then 🗑️ **Clear** the cart | | |

---

## D · The money still works — 4 min

> ⛔ 🗑️ **Clear** after each basket. Never Checkout.

**D-i · Mix and match (this morning's bug)**

| # | Scan | Expect | ✓ |
|---|---|---|---|
| D1 | `84157065` Smoking Red ×1 | | |
| D2 | `84190369` Smoking Green ×1 | | |
| D3 | `85950672` Greengo King Size slim ×1 | Total **CHF 5.00** — not 6.00 | ☐ |
| D4 | `716165177814` Elements King Size ×1 | Total **CHF 7.00** (3 for 5, then start again) | ☐ |
| D5 | 🗑️ Clear | | |

**D-ii · Greengo Wide Rolls — the leak you closed**

| # | Scan | Expect | ✓ |
|---|---|---|---|
| D6 | `85966789` Greengo Wide Rolls ×1 | Line **CHF 4.00** (it rang **3.50** before your fix) | ☐ |
| D7 | `716165280293` Raw Rolls Classic KS ×1 | | |
| D8 | `8414775013707` Smoking Brown Rolls ×1 | Total **CHF 10.00** — the Wide Roll joins the roll deal | ☐ |
| D9 | 🗑️ Clear | | |

**D-iii · Tycoon Gas — the other leak**

| # | Scan | Expect | ✓ |
|---|---|---|---|
| D10 | `4035687900004` Tycoon Gas 250ml ×1 | Line **CHF 6.90** (it rang **5.00** before your fix) | ☐ |
| D11 | 🗑️ Clear | | |

---

## E · The bench card — 1 min

| # | Do this | Expect | ✓ |
|---|---|---|---|
| E1 | Open the link below | The Elements Phantom bench card shows the RED warning, not a deal chip | ☐ |

https://banco.wolfhold.app/pos/cleanup?mode=bench&pid=cedc2897-abeb-4751-82a6-1df8b218d4dc

---

## Verdict

- [ ] **GO** — every line passed, prod is good
- [ ] **NO GO** — write which line, and what you saw instead

### Still open after this sheet (not part of the test)

- `2000000232225` **Elements Phantom KS Slim** and `2000000237800` **Elements Zushi KS Slim**
  are still on the wrong mode. They are the *subject* of section A/B — fix them **after**
  the sheet, or A4 stops matching.
- `84157089` **Smoking Gold** now reads 2.00 with a 3-for-5. Felix said Gold is a collector
  paper at 2.50 with **no** deal. Someone's call, not a bug.
