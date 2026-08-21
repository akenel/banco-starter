# The six till reports of 2026-08-20 — BL-9 … BL-14

*Filed in-app under the `felix` login on the live shop (build `b349`). Investigated 2026-08-21 against the prod database and the templates. The short version lives at the top of [`WORKLIST.md`](../WORKLIST.md); this is the evidence.*

---

## 🔴 SIX REPORTS FROM THE TILL — 2026-08-20, filed in-app under `felix` (BL-9…BL-14)

**All six are tagged `annoying`. Not one is `blocking`.** Read that before reading Felix's
verdict — he told Angel the till is *"too complicated, too many buttons, the checkout will
have issues"*, and the reports filed from the shop's own machine say otherwise. The in-app
feedback widget worked perfectly: build `b349`, screen, referrer, viewport, console **and**
the failing network call, auto-attached, plus a screenshot on five of six.

### The number that explains all of it

```
5,446 products on the live till
4,998  carry a MINTED 2000000… barcode   (92%)
  414  can be found by scanning the real packet   (7.6%)
   29  of 107 sold catalogue lines had a real EAN  (27%)
```

**Three out of four things Felix rings up cannot be scanned off the pack.** He is not
complaining about buttons — he is complaining that the scanner does not work, and the
buttons he hates (department strip + "new item" form + the pending-code banner, all stacked
at once) **only appear because the scan missed.** Fewer buttons is the wrong fix. A scan
that hits is the fix. This is LESSONS.md 2026-07-30 still live in prod: the July Tamar
import minted 5,103 codes because Tamar publishes no EAN.

### ROOT CAUSE A — the till throws away the real EAN at the exact moment it has it

`scan.html:1385` · `createNoCodeItem()` always calls `genInternalBarcode()`, even when
`this.pendingBarcode` holds the code that just 404'd — the code the screen is **displaying**
in the amber banner three inches above the form. So:

> scan `4002450223400` → 404 → fill in name + price → saved as `2xxxxxxxxxxxx` →
> **that packet will never scan again.** Findable by name only. Forever.

That is **BL-9** (*"made on the fly but only searchable by name after"*), **BL-12** (*"create
mode not showing scanned results"*) and **BL-13** (*"when added via intake shelf left old
2000… ean"*) — one bug wearing three hats. The department line already attaches it
(`unresolvedBarcode`, scan.html:2071); the create path was never told. **Classic pattern 2 —
the downstream consumer that doesn't know about the field you added.**

Sibling, same shape: `catalog.html:1297` `_blankForm()` sets `barcode: ''` and never seeds it
from the search box — BL-10's screenshot shows `4260641140046` sitting in Search while the
Barcode field is empty and the hint invites *"leave it blank — a code is generated
automatically."* **That hint is the bug, written down as a feature.**

⚠️ This leaks. Every item created today adds another unscannable row.

### ROOT CAUSE B — the "read from this photo" panel shows the PREVIOUS product's photo

`catalog.html:1692` — `if (!this.snapPreview) { this.snapPreview = f.image; }`. `openCreate()`
clears `pendingImageUrl`, `gallery`, `_aiTail` — but **not** `snapPreview`, `snapName` or
`pageUrl`. So the second product of a sitting reads its page correctly, saves the right
photo, and shows the operator the *first* product's photo under the words "📷 read from this
photo", with the old URL beneath it.

BL-10 (*"papers stuck in image"*) and BL-11 (*"never brings in right info — cache maybe
stuck"*) are this. The panel exists precisely so the operator isn't proofing against a photo
they cannot see (Angel's grinder folder, "g08 or g09") — **showing the wrong one is worse
than showing none.**

### Still open

- **BL-14 · the cursor.** *"new sale cursor not at search by defaulted"* / *"cursor
  constantly reset to search bar input"* — the title and the body point opposite ways.
  `scan.html` refocuses `$refs.barcodeInput` after every scan, miss and department line
  (lines 1223/1236/1266/1777/2080), which is right for a gun and possibly wrong when he is
  editing a quantity in the cart. **Needs 30 seconds of Angel showing me which way it goes.**
- **Two unlabelled buttons in BL-14's screenshot** — the full-width green and purple buttons
  render as a bare 📊 and 📷 with no text, while every other `data-i18n` span on the same
  screen renders fine. The keys exist in all four languages (`pos-i18n.js:926`). Could be an
  html2canvas artifact. **Unverified — a screen is checked in a browser, not by reading the
  template.**
- **The tablet.** No Chrome by default, Firefox search "no good". Not reproduced, not
  specified. Ask what "no good" was.

### What fixes what

| Do | Fixes | Size |
|---|---|---|
| Bind `pendingBarcode` on create (scan) + seed from search (catalog) | stops the leak | small |
| Clear `snapPreview`/`snapName`/`pageUrl` in `openCreate()`; drop the `if (!snapPreview)` guard | BL-10, BL-11 | small |
| Kill the "a code is generated automatically" hint | the invitation | trivial |
| The 4,998 already in there | bind-on-scan is already built (BL-90) — 18 real aliases bound so far. No bulk source: **Tamar publishes no EAN.** | long haul |

---

