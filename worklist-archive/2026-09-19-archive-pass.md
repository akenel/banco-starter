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

---

## `L6` — the shift never closes · CLOSED 2026-09-19

### ~~`L6` · The shift never closes~~ — **FIXED 2026-09-19** `2c735a4` `bae9a0b` `72a86c3`
⚠️ **AND I HAD THE WORD WRONG.** "Shift" here is **attendance**, not the cash box. Two tables:
`cash_shifts` is the **drawer** (float · count · variance) and is closed **by a person, with a
count**; `shift_sessions` is **who logged in**, and `shift/end` is documented *"normal logout"*.
Angel: *"a logout does not mean close the shift … Layla leaves it open and does not do a count
before she leaves and felix ends the day and he is the person counting."* **The drawer already
works that way** — his own data: `pam` opened 2 Sep, **`layla` reconciled** it on the 5th.
📌 Felix's drawer has been **open since 2026-09-10 16:11, float CHF 1'216.00**. Not a bug.
**What was actually broken:** there is no End Shift button — `shift/end` fires *inside*
`logout()`, fire-and-forget, `.catch(()=>{})`, with whatever token is in hand. The access token
lives **5 minutes**, so the one logout that matters — the one caused *by* the session dying —
posted a dead token and swallowed the 401. Now: renew, then close, then clear (1.5s bounds).
Plus **My Day's before-midnight fallback had no date bound**, so it prefilled a start time from
a row days old. Bounded at 16h; 15h still works, 17h excluded.
Plus **prod had no application log at all** — a level set with no handler, so everything under
WARNING was binned. 90 lines on prod now where there were 0. Keycloak idle 60→600 min, max
600→840 min (Angel's call, trade-off recorded in `kc-set-session-timeouts.py`).
**Proof:** `prove-the-shift-row-closes.js` 11/0, red verified by reverting — and it took **four
harness faults**, every one a false PASS on the bug it exists to catch. Read its header.
**STILL OPEN, and they are small:**
- ⚠️ **The four stale rows are untouched** — Angel's call, he or Felix set them by hand.
- 🔓 `update_activity()` exists in the model and **nothing calls it**, so `last_activity` is
  frozen at login. That is why no honest end time could be recovered for the four.
- 🔓 `shift_sessions.transaction_count` is **never incremented** — read in 3 places, written in 0.
  (`cash_shifts.transaction_count` is computed properly; only the attendance one is dead.)


---

## `L1` — the cover image · CLOSED 2026-09-19

### ~~`L1` · The cover image~~ — **FIXED 2026-09-19** `e9543c1` + the postcard sibling
Tickets 48, 49, 50, 51 — and Layla's own words were the diagnosis: *"no cover miamges but they
have pictures."* `products.image_url` is the **cover** and drifts from the gallery two ways:
**cover NULL** (a gallery photo only promotes when none is set) and **cover DANGLES** (replacing
a photo leaves it aimed at a deleted id — the 32 × `404 /images/…` in one day's log). The
catalogue reads the gallery, the cart read the cover: same product, two screens, two answers.
**The cure was already written** — `hasImg()`/`thumbSrc()`/`onImgError()` in `scan.html` have read
`fallback_image_url` since BL-043, and the cart line already calls them. **Only the SEARCH
endpoint ever sent it**; scan and detail — the two that fill the cart — returned the bare row.
Fixed on both, plus `_product_display_image()` (postcard · postcard sheet · label batch) which
handled NULL and returned a dangling cover blindly. Standing rule 9, twice.
**`prove-the-cart-shows-the-photo.js` 14/0, red verified** — the fixture uploads a REAL jpeg,
because with no bytes the `<img>` 404s anyway and a byte-less fixture would report the bug as
never fixed. Regression `prove-bad-price-is-visible.js` 34/0.
✅ **No prod data change needed** — the code now copes with all 10 broken rows as they stand.
🔎 **The drift itself is NOT fixed** (new ones will still appear, now harmless). Unproven
hypothesis: the catalog edit form carries `form.image_url` and the PUT applies it with
`exclude_unset=True`, so a stale value in a reopened form can overwrite a corrected cover.
⚠️ **Human-green owed: Layla scans one of her three and sees the picture.**



### `L1` human-green — the run that closed it

Angel, on the live shop, 2026-09-19 11:13, build `3cebdee`, 3m55s:

```
  0.1  PASS      A1   PASS      B1   PASS      C1   PASS
  0.2  PASS      A2   PASS      B2   PASS      D1   PASS

8 pass · 0 issue · 0 fail · 0 not run          VERDICT: GO
```

**B1 is the one that counts** — `3661075228804`, the Jetflame, whose cover pointed at a photo
that had been deleted. That is the path that 404'd 32 times in one day's log, and the only step
on the sheet that a broken build could not have passed.

⚠️ `DEVICE STATE NOT RECORDED` — the three rig selectors were left unset. **Angel confirmed
afterwards: the run was on his Android phone.** So the T1 tablet, which is the actual till, has
machine-green only (the cart line was driven at 1280×800) and no human on it for this fix. That
is acceptable here — the change is a server field plus a shared template, and the phone exercises
the same code — but it is the honest shape of the evidence and not the same as a till PASS.
It does not invalidate this run, because this sheet's `needs` deliberately said *"a tablet OR an
Android phone — either is fine"* and the cart line was measured at both 390×844 and 1280×800 before the sheet was
written. On a sheet where the device IS the subject, it would invalidate it. See the 2026-09-04
runs that had to be thrown out.

**A first partial run was correctly refused.** The first paste came back `2 pass · 6 not run ·
VERDICT: INCOMPLETE`, with only C1 and D1 marked — and those two are precisely the steps that
cannot discriminate: C1 (a product with genuinely no photo shows 📦) passes on the BROKEN build
too, because the bug was photos not showing, never boxes appearing. Banking that as evidence
would have been a green summary over an unchecked box (LESSON #12).

---

## `6x` — the discounted sale that did not reconcile · CLOSED 2026-09-19

6x. 🔴 **NEW 2026-09-17 — A DISCOUNTED SALE DOES NOT RECONCILE, and this is the tax-man one.**
   `transactions.tax_amount` is the VAT on what was actually charged (**correct**).
   `line_items.vat_amount` is the **pre-discount** per-line figure (**stale**). So on the live shop
   **6 of 60 sales do not tie out** — gaps of 0.01, 0.02, 0.06, 0.39, 0.56 and **0.80** — and every
   one of the six carries a discount, in exact proportion to it. Undiscounted sales tie out exactly.
   ⚠️ **`pos_router.py:7587` sums `LineItemModel.vat_amount` for a report**, so a report can state
   MORE VAT than the books declare. Two numbers in one system that disagree on a discounted sale is
   precisely what makes an inspector open every transaction. Fix is the write path: store the
   prorated VAT on the line (the same `factor = total/subtotal` `split_vat` already uses) — or
   prorate at every read. **Not started; not a midnight job.**

---

## Item 10 — the tablet camera · settled, moved out 2026-09-19

10. 📷 **THE TABLET CAMERA — diagnosed 2026-09-10, and it is NOT broken hardware.** `ov2740` sensor
   bound · `ipu3` loaded · libcamera 0.4.0 · pipewire up — and **`cam --list` returns zero cameras.**
   Every `/dev/video*` belongs to `ipu3-imgu` (processing, not capture). An Intel **IPU3 MIPI** sensor
   never presents a plain V4L2 node. **Banco's side is correct — do not touch `posShowWebcam()`.**
   ❌ **CORRECTION 2026-09-17 — I had the failing step wrong.** This said the sensor was *bound* and
   that libcamera's IPU3 pipeline handler was the gap, i.e. a userspace fix. Re-measured on kernel
   `6.12.107`: `/sys/bus/i2c/drivers/ov2740/` has **no bound device** at all — only bind/unbind/
   module/uevent. libcamera has nothing to build a pipeline *from*. `13-tablet-x1-debian.md` had it
   right all along: the TPS68470 PMIC has no board data, and it is a kernel patch. **Do not debug
   it.** An afternoon on the pipeline handler would have found nothing. **Untried cheap unblock: a powered USB hub (~CHF 20)** — the tablet
   has one port and the gun owns it. (LESSON #3: the 2026-08-05 "nothing attached" verdict was wrong
   too — ACPI declares two fitted sensors. Angel's instinct has now been right twice.)



---

## ~~`L1` · The cover image~~ · full text moved out 2026-09-19

### ~~`L1` · The cover image~~ — **FIXED 2026-09-19** `e9543c1` + the postcard sibling
Tickets 48–51, and Layla named it: *"no cover miamges but they have pictures."* The cart read
`products.image_url` (the **cover**), the catalogue read the gallery — so one product, two
screens, two answers. **The cure was already written** (`hasImg`/`thumbSrc`/`onImgError` have
read `fallback_image_url` since BL-043); only the SEARCH endpoint ever sent it, and scan +
detail are the two that fill the cart. Fixed there and in `_product_display_image()`
(postcard · label batch), which returned a dangling cover blindly. Standing rule 9, twice.
**`prove-the-cart-shows-the-photo.js` 14/0, red verified.** ✅ **No prod data change needed.**
🔎 The **drift itself is not fixed** — new ones appear, now harmless. Unproven: the catalog edit
form carries `form.image_url` and the PUT applies it `exclude_unset=True`, so a stale value in a
reopened form could overwrite a corrected cover.
✅ **HUMAN-GREEN 2026-09-19 11:13 · 8 pass · 0 fail · GO**, 3m55s, live shop, **on Angel's Android phone** — incl. B1, the Jetflame with the dead cover. Tablet viewport machine-checked only. → [`sheet`](onboarding/testsheets/2026-09-19-the-picture-in-the-cart.html)
→ [`the full record`](worklist-archive/2026-09-19-archive-pass.md)


---

## ~~`L6` · The shift never closes~~ · full text moved out 2026-09-19

### ~~`L6` · The shift never closes~~ — **FIXED 2026-09-19** `2c735a4` `bae9a0b` `72a86c3`
⚠️ **"Shift" means ATTENDANCE, not the cash box** — two tables, and the drawer (`cash_shifts`)
already hands over between people and is closed by whoever counts it, exactly as Angel
described. What broke: `shift/end` fires inside `logout()` with a 5-minute-old token, so the
one logout caused *by* the session dying posted a dead token and swallowed the 401. Fixed, plus
My Day's unbounded fallback, plus **prod had no application log at all** (90 lines now, was 0),
plus Keycloak idle 60→600 / max 600→840. `prove-the-shift-row-closes.js` **11/0, red verified**.
📌 Felix's drawer has been **open since 2026-09-10, float CHF 1'216.00**. Not a bug — practice.
**Still open, small:** the 4 stale rows are Angel's to set by hand · `update_activity()` is never
called so `last_activity` is frozen at login · `shift_sessions.transaction_count` never
increments (read in 3 places, written in 0). → [`the full record`](worklist-archive/2026-09-19-archive-pass.md)

### 💵 `R1` · Cash rounding direction is now a SETTING — **SHIPPED 2026-09-19 `34b1f31`**
Felix wants up, Layla wants down, Angel agreed with Layla. `store_settings.cash_rounding_mode`
= **`nearest` (default, UNCHANGED)** | `down`. Admin-only, sealed server-side, behind the VAT
modal. 58 tests pass with **every existing one untouched** — the proof no takings moved.
⚠️ **I nearly overwrote Angel's own 2026-08-03 decision** because I advised before reading
`total_rounding.py`, which already held it: *Felix does not discount, he gives a treat — so
rounding down silently implements the policy he rejected. "Rounding is physics. Treats are
pricing."* Docstring **amended, not rewritten**; the old argument stands above it.
❓ **Ask Felix what "round up" means** — *nearest* (what he has always had, and what he saw at
5.13→5.15) or *always up*? Only the latter is a third mode, and the only one a customer could
object to.

### 🔓 `R2` · **VAT was the ONLY guarded setting.** Found while doing `R1`.
Everything else on `/pos/settings` saves in silence, including: **`currency`** (every price in
the shop) · `cashier_max_discount` · `manager_max_discount` · both **welcome discounts** (money
given away automatically) · `cash_tolerance` (whether a drawer counts as balanced) ·
`default_markup_pct`. Rounding now has a guard; these seven do not.
▶️ **The fix is to generalise, not to add an eighth bespoke modal** — `_confirmVatChange` →
`_confirmMoneyChange(rows)`, one snapshot on load, one diff on save, money fields ONLY. If it
fires on a phone number it becomes wallpaper and protects nothing on the day it matters.
📌 Good news: `store_settings` changes are **already audit-logged by a DB trigger** (17 rows on
prod), so *who and when* is answered at a layer nobody can bypass.
❓ **Small, pre-existing, Angel's call:** in that modal the buttons stack **Cancel on top, "Yes"
at the bottom** — and the bottom is what a thumb reaches. The code comment says the intent was
the opposite. Angel human-greened this modal on 2026-09-17, so it is a question, not a bug.

