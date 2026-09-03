# Contact sheet — shot list, 2026-09-03

*Angel drives the real tablet; the copilot looks at the pictures. This exists because
every real bug this week was found by a HUMAN LOOKING AT A PICTURE — the 4px supplier
picker, the 790px Qty box, the modal 135px off the top, the refusal 322px below the
fold. Five DOM probes said the picker was fine. Only the screenshot disagreed.*

**Why this and not a headless render:** the proofs run at 1280×800. The tablet is
**2160×1440** with `force-device-scale-factor=1`. Every geometry number in
`prove-keypad` sections J/K/L describes a screen that does not exist. Until a real
screenshot sets the scale, the harness is measuring fiction.

## Rules — read once

1. **This is the SHOP'S LIVE DATA.** Never complete a sale. Adding to a cart writes
   nothing; pressing the final Checkout/Pay button writes a line into the Kassenbücher.
   Stop before that, every time.
2. **Do not save an edited product.** Open the edit modal, look, press Escape/Cancel.
3. If you must create anything, name it **ZZTEST**.
4. **Landscape**, the way it sits on the counter, unless a step says otherwise.
5. **Take them IN ORDER and take nothing else in between** — the copilot maps shots to
   steps by timestamp.
6. PrtScr = whole screen, straight to `~/Pictures/Screenshots`. No selection box.
7. Reload the tablet TWICE first (service worker) so you are on build `50a89aa`.

## The shots

### The six that matter most — if you stop early, stop after these

| # | screen | get into this state | what the copilot is looking for |
|---|---|---|---|
| 1 | **New Sale** | fresh load, nothing scanned | where the caret lands, how much empty space, is the fold in the right place |
| 2 | **New Sale** | 3 items in the cart, one of them a 3-for-10 pack | does the pack price read clearly, is the total where the eye goes |
| 3 | **New Sale** | keypad open on **Discount %** | what the pad covers, whether the number you are typing is visible |
| 4 | **Order Book** | landing, scrolled to the "To order" list | the row I just fixed: `Qty [64px] [supplier] [Ordered]` on ONE line |
| 5 | **Manage Catalog** | edit modal open on a real product, **do not save** | modal top, Save bar, whether the form is reachable |
| 6 | **Manage Catalog** | same modal, keypad open on a price field | the whole point of last night — is the focused box above the pad |

### The rest, same rules

| # | screen | state |
|---|---|---|
| 7 | New Sale | the on-the-fly **new item** form open, keypad on Item name |
| 8 | Checkout | basket loaded, before pressing anything final |
| 9 | Checkout | keypad open on **Amount received** |
| 10 | Order Book | supplier dropdown **open**, options showing |
| 11 | Manage Catalog | landing — where the caret lands in search |
| 12 | Manage Catalog | edit modal with **two** price-break rows added |
| 13 | Receiving | the create form open, showing "Bought a box? Paid CHF __ for __ units" |
| 14 | Shelf Intake | landing |
| 15 | My Day / Closeout | landing |
| 16 | Kiosk | landing, then one with an item added |

## When done

Say so. The copilot pulls the whole batch with `scp` and looks at every one.

**Nothing gets fixed from this list until the pictures have been looked at** — the point
is to find what neither of us has thought to look for, not to confirm what we already
believe.
