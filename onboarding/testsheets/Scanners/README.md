# Scanner guns — setup and the keyboard-layout trap

## The trap, first

**A scanner gun is a keyboard.** It doesn't send text — it presses the *key* that produces a character
on **its own** configured layout, and the OS reads that key through the layout **the session** uses.
Mismatch them and punctuation silently mutates.

Seen for real on 2026-07-29, both guns, both machines:

```
page showed:   QR-LOGO-15
gun typed:     QR'LOGO'15
```

Gun on **US**, session on **Swiss German (`ch`)**. US puts `-` right of `0`; Swiss German reads that key
as `'`.

**Why it hides for weeks:** EAN-13 is pure digits, and digits are identical across these layouts. Till
scanning looks perfect. But **every SKU has a hyphen** (`TAM-21796`), so the first Code128 SKU label
scanned finds nothing.

| Layout | key right of `0` | key right of `.` |
|---|---|---|
| US | `-` | `/` |
| UK / GB | `-` | `/` |
| **Swiss German** | `'` | `-` |
| **German** | `ß` | `-` |

German and Swiss German agree on `-`. That matters below.

> It is also **per-user**: `gsettings` layout is per session, so the bug can appear for one user and not
> another on the same machine — nasty when the kiosk auto-logs-in as one user and staff switch to another.
> Check both: `localectl status; gsettings get org.gnome.desktop.input-sources sources`

---

## Inateck BCST-35 (the CHF 36 one)

2D imager — reads QR, Data Matrix, PDF417, Aztec as well as all the usual 1D. Confirmed reading our QR
labels down to **10 mm**.

**Configuration is by scanning barcodes out of the manual** (`Inateck_BCST-35_..._User_Manual-V1.2.pdf`,
in this folder). The barcodes are images, so text-searching the PDF finds nothing — open it and look.

**There is no Swiss German option.** Available: US *(factory default)*, German, French, Italian, Spanish,
UK, Canadian, Japanese, Swedish, Dutch, Danish, Norwegian, Portuguese, Polish.

**Use German.** It puts `-` on the same key as Swiss German, and both are QWERTZ, so letters, digits and
hyphens all come through correctly on a `ch` machine.

### Setting it — manual page 4, "Keyboard Setting"

Scan these three in order. You can scan straight off the screen.

1. **`Enter Setup`** — wide barcode at the **top** of the page
2. **`German Keyboard`**
3. **`Save and Exit`** — wide barcode at the **bottom** of the page

The manual's own rule: *[Enter Setup] – [Specific Function Setting] – [Exit and Save]*. Blue LED stays lit
while in setup mode. A `(*)` next to a barcode means factory default.

### Then verify — do not assume

Open `../SCANNER-GUN-TEST.html`, click the capture box, scan a few codes:

```
QR-LOGO-15   ✅ gun and session agree
QR'LOGO'15   ❌ still mismatched
```

Every code on that page names its own size, so the log also tells you the smallest one your gun manages.

---

## Netum NS L8 (the CHF 55 one)

Also a 2D imager, and the better scanner of the two — faster and more forgiving on awkward angles.

**Its config codes live on the web, not in the box.** The booklet exists but is thin; the full set is at:

**<https://doc1.netum.net/L8/en/keyboard>**

Open that page and scan the layout you want **straight off the screen**. Same three-step pattern as any gun:
enter setup → pick the setting → save.

Set to **German** for the same reason as the Inateck — Swiss German isn't usually offered, and German puts `-`
on the same physical key.

> Bookmark that URL, or save the page. A gun whose config lives on a vendor website is one domain change away
> from being unconfigurable — which is exactly the sort of thing that bites three years later when a shop
> replaces a till.

---

## Both guns, as configured 2026-07-29

| | Inateck BCST-35 | Netum NS L8 |
|---|---|---|
| Price | ~CHF 36 | ~CHF 55 |
| 2D (QR) | ✅ | ✅ |
| Config via | PDF in this folder, page 4 | <https://doc1.netum.net/L8/en/keyboard> |
| Layout set to | German | German |
| Verified | `-` comes through correctly, QR to 10 mm | `-` correct, QR reads |

Both passed `../SCANNER-GUN-TEST.html` after the change: hyphens arrive as `-`, not `'`.

---

## Other guns

Config barcodes are **vendor and model specific** — never scan one gun's codes into another. Find the model
number on the underside or in the battery compartment, then get that manufacturer's manual.

If a gun's layout list doesn't include anything workable, look for **"ALT + keypad"** / **"Unicode output"**
mode: it types by numeric code rather than key position, so it is layout-independent.

---

## Banco covers this anyway

`_find_product_by_any_barcode` (`src/routes/pos_router.py`) retries layout-corrected candidates when a
scanned code matches nothing — so `TAM'21796` still resolves to `TAM-21796`. It is a **fallback, never a
rewrite**: only tried after the raw code found nothing, so a real apostrophe can't be corrupted. A hit logs
a warning naming the correction, so a mis-set gun surfaces rather than hiding.

Fix the gun anyway. The fallback is a safety net for shops running hardware we didn't choose.
