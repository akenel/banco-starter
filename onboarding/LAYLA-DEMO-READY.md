# What is left before Layla runs a shift

*Written 2026-09-04, after Layla ran her first testsheet on the shop tablet
(`2026-09-04-classes-that-did-nothing.html` — 9 pass · 2 issue · GO WITH ISSUES).
Ranked by **"will she hit this at the counter in one shift"**, not by how interesting it is.*

The decided plan has not changed: **Layla first, not Felix. One shift, 11:00–16:00, alongside
paper.** Go-live 1 Oct. This is the list that stands between here and that shift.

---

## 1 · MUST — she will hit these, and they cost her time or credibility

| | what | where it bites |
|---|---|---|
| **1.1** | **The Total and Checkout row is clipped by the bottom tab bar** once the cart has two lines | Every multi-line sale. `TOTAL: CHF 10.9…` cut through the middle. This is the **money row** and it is the worst thing on the list. |
| **1.2** | **Date filters render `mm/dd/yyyy`** on Transactions, Product Sales and Audit — six native pickers | Layla found it herself. Transaction History is where a cashier goes to find a receipt for a customer standing there. The same screen prints `Showing 04.09.2026` one line below the filter that says `09/04/2026`. |
| **1.3** | **The on-screen keyboard buries the search results** | Typing `cbd` shows *"Showing 20 of 366 matches"* and one and a half rows. She has to dismiss the pad to see what she searched for — on every search. |
| **1.4** | **Checkout's discount chips do not reflect a discount already applied**, and *"Your max discount: 100%"* is developer copy | Target Total sets 15.25% and the chips show nothing selected. A cashier cannot tell what the customer is being charged. |
| **1.5** | **The left-hand product list cuts its last row in half** | Every pack looks like it is missing something. Small, constant, undermines trust in the screen. |

## 2 · SHOULD — visible, survivable, but she will ask about them

| | what |
|---|---|
| **2.1** | The header shows **Keycloak role names** — `layla \| default-roles-kc-pos-realm-dev-1, pos-cashier, pos-manager`. On her screen right now. Reads as something broken. |
| **2.2** | The green **"Login successful!"** toast lands on top of the user chip it sits next to. |
| **2.3** | **Cleanup Queue truncates mid-word** — *"Finish setting up quick-added prod…"*, *"5395 products to finis"*. |
| **2.4** | **Order Book's suggestion list stays open** after you pick an item, covering "✓ linked to catalog" and the Qty label. |
| **2.5** | **An invalid time shows nothing beside the box** — the only signal is the green button greying out further down the page. |
| **2.6** | **`/pos/kb-approvals` is reachable from no screen.** Layla asked where the KB is; the honest answer is that there is no door. A whole page with no entry point. |

## 3 · CAN WAIT — real, but not in her way

- **Settings' 55 typed inputs have no keypad.** Deferred by Angel, with a good reason: it is
  one-time admin work and should be done with a proper keyboard. Not a cashier screen.
- Settings' intro line is wrong about what a manager may change.
- `scripts/keypad-inventory.py` still recommends the setting that was proved broken on 09-04.
- `isotto/`, `camper/` and `backlog/` carry their own `type="date"` fields and their own
  `base.html` cascade — none of them is the till.
- `[i18n] missing key: reorder.by`.
- `_price_kiosk_lines` prices each line alone and never pools ACROSS lines the way the till does.
  Logged, unproven either way.

## 4 · NOT A BUG — decisions, and they are not mine

- **The kiosk `source` / welcome-percentage mislabel.** Moves money. Needs Felix.
- **Should validate-on-press screens grey their button as well?** Catalog deliberately keeps Save
  live and puts the reason in a red box beside it — the pattern chosen in August after a toast went
  unread. Felix flagged it; it is a judgement call, not a defect.
- **The login background.** Done as the shop's own star at `.30`; `--login-mark-opacity` is the one
  number if it ever wants to be softer.

---

## What "ready" means

**Section 1 clear, section 2 at least looked at.** Nothing in section 3 stops a cashier ringing a
sale, and section 4 is not ours to close.

One more thing that is not on any list: **everything this week was proved in the flat.** The shop's
network, the shop's lighting and the shop's counter have not been in the loop since the tablet was
set up. LESSON #1 has bitten on exactly that before. An hour at that counter before the shift is
worth more than another day of fixes.
