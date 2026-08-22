# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short.** It hit **1,734 lines** on 2026-08-13, at which point it
> stopped being a list you can open and act on. The narrative moved to
> [`worklist-archive/`](worklist-archive/) — **nothing was deleted**, and the split was verified
> line-for-line. **Keep it under ~150 lines**: when an item is finished, move it to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread
> grows a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-08-22 (Sat evening).*

---

## ⬜ THE TABLET'S LTE — WORKS AT HOME, UNPROVEN IN LUZERN — 2026-08-22

Felix's ask: the till keeps selling when the shop Wi-Fi dies. The X1 Tablet's **Sierra EM7455** is
up on a Sunrise SIM and Angel ran Banco with Wi-Fi switched off. The blocker was that the modem
ships **FCC-locked** — one symlink into `/etc/ModemManager/fcc-unlock.d/`. Full runbook, traps and
the exact command sequence: [`onboarding/13-tablet-x1-debian.md`](onboarding/13-tablet-x1-debian.md)
(*LTE IS WORKING* section).

**Proved in Angel's flat on `Init7_1A34`, not on the counter.** The cold boot is now done (below); **four things left, all of them genuinely location-dependent:**

- [x] ~~**Cold boot**~~ — ✅ **PROVEN 2026-08-22 20:24, and it is machine-level, not location-level,
      so it does not need redoing in Luzern.** Full `poweroff` + mains unplugged, so the modem lost
      power and its FCC authorisation with it. On the way back up:
      `[fcc unlock dispatcher] singleton created` — it **found and ran** the symlinked script, where
      this afternoon the same line read *"file doesn't exist … no valid program found"*. Same boot:
      `cdc-wdm2 gsm connected shop-lte`, untouched. **The till survives a power cut with LTE intact.**
- [ ] Set `ipv4.route-metric 100` on the **shop** Wi-Fi profile — it is a different connection
- [ ] Measure signal where the till stands (29 % at home; concrete will be worse)
- [ ] Pull the Fritzbox WAN cable with the till open and ring a real sale
- [x] ~~Ask Felix what that SIM is~~ — ✅ **Sunrise, PURE DATA, CHF 5.50/month.** No voice, no
      surprise bill; cheap enough that leaving the modem registered all day costs nothing.
- [ ] 🔋 **A USB-C PD power bank — the tablet is meant to WALK the shop.** Earlier advice to
      "just keep it plugged in" assumed a fixed counter; it is not one, so 2 h matters.
      ⚠️ **It must be PD.** This tablet refuses 5 V, so a USB-A output does literally nothing —
      Angel's 10,000 mAh bank did exactly that. A PD bank negotiates 15–20 V, i.e. it *is* the
      adapter in a battery. Label must list multiple voltages (`9V/12V/20V`) and a wattage
      (30–65 W), output must be USB-C, cable must be **C-to-C**. Test:
      `cat /sys/class/power_supply/BAT*/status` → want `Charging`. A PD 20,000 mAh (~60 Wh
      usable) is ~1.5 charges of the 37 Wh battery. *Suspect the cable too — the same one
      failed to carry data or power through the dock.*
- [x] ~~🔋 **Battery**~~ — **measured 2026-08-22: nothing to buy.** `37.01 Wh` design,
      `34.67 Wh` now, **97 cycles → 93.7 % health.** The 2 h runtime is a 37 Wh battery driving a
      12" 2K screen (~17 W draw), i.e. the machine's *design*, not its decline — a new cell buys
      about eight minutes. Levers are brightness and radios, not capacity. **Note the LTE modem
      enabled today draws continuously; that is the price of the failover.** If the 4 h charge
      matters, check `charge_control_end_threshold` (a Lenovo 80 % cap) and use the real 45 W
      adapter — 9 W net charging says small charger, not tired battery.
- [x] ~~🔌 **A 45 W adapter**~~ — **RETRACTED, buy nothing. The adapter is 65 W, above the 45 W
      stock.** I read `power_now` = 8.45 W and extrapolated `37.01 Wh ÷ 8.45 W = 4.4 h`. **That
      reading was taken at 77 % and climbing** — Li-ion charges fast to ~80 % then tapers into
      constant-voltage, so 8.45 W describes the last stretch and nothing else. Same error as
      reading `sim-missing` off a powered-down modem, six hours apart. *If a real number is ever
      wanted, measure `power_now` at 30–50 %.* If charging genuinely is slow on 65 W, suspect the
      **cable** — one without PD support negotiates down to 5 V/15 W, and the cable is already
      under suspicion from the dock.

### ✅ FIXED — the Win 10 tablet's dead camera button

`4206246` showed the 📷 Webcam button wherever `getUserMedia` exists — which is *every* modern
browser, camera or not — so the old Win 10 tablet (touch, no camera) gained a button whose only
output was the alert *"No camera available"*. Now `enumerateDevices()` decides: presence is listed
with **no permission prompt**, and a `.banco-has-camera` class on `<html>` gates the buttons via
one CSS rule. A class rather than a reactive value because `x-show` is Alpine in three templates
and will not re-render when a module variable changes underneath it — and because it re-answers on
`devicechange`, so plugging the webcam in mid-shift works without a reload.

**Fails OPEN** if the browser cannot enumerate: hiding the button on the one machine that *has* a
camera is the worse error, and it is the one we just spent the evening fixing.

`prove-webcam-button-shows.js` is now 8 cases; the 4 new ones go red against the code that shipped
this evening. ⬜ **Still needs a human on the Win 10 tablet** — the button is gone by CSS, which is
a claim about a screen, and per LESSONS #7 those are not verified by reading a stylesheet.

---

### 🌙 DARK MODE — wanted, spec'd, NOT scheduled

Angel put the tablet in dark mode and Banco is still all white screens. **The power argument does
not hold** — the X1 Tablet is an **IPS LCD**, where the backlight burns the same whatever colour
the pixels are; dark mode saves power only on OLED. On an LCD the lever is *brightness*. So this is
a comfort feature — a bright white till in a dim shop is tiring over a shift, and an app that
ignores the OS setting looks broken. Fine reason to build it, different reason.

**Do NOT do it with Tailwind `dark:` variants.** Four classes alone account for **503 occurrences**
across the POS templates (`text-gray-900` ×204, `bg-white` ×148, `bg-gray-50` ×94, `bg-gray-100`
×57), before the rest of the palette — well over a thousand edits, on a live till, forever after
remembered by every new template.

**Do it in one place.** `base.html` already carries real CSS for `.btn-primary`, `.input-field` and
`.card`, and Tailwind's Play build emits its utilities as ordinary CSS, so one block repaints
everything:

```css
@media (prefers-color-scheme: dark) {
  .bg-white { background-color: #1c1c1e !important; }
  .text-gray-900 { color: #e8e8ea !important; }
  .bg-gray-50, .bg-gray-100 { background-color: #232326 !important; }
  /* ~30 more lines */
}
```

~40 lines, one file, follows the OS, reverts by deletion. **The cost is not the CSS — it is the
verification.** A blanket override will strand light text on newly-dark badges, and **the price
display is not cosmetic**: a cashier reads it fast, under pressure, with a customer waiting. Needs
a human on every screen — till, cart, checkout, catalogue, scan, receiving — the same afternoon the
18+ and price-warning passes each took. **Pick it up with an afternoon and fresh eyes, not at the
end of a long day.**

---

**🅿️ DOCKS ARE PARKED — buy nothing.** Two were tried and neither works: the **WiGig Dock W123**
reaches a machine only over a 60 GHz radio the Intel 8265 does not have (and Intel WiGig docking
has no Linux support), and the **Hybrid USB-C Dock DUD901** gave neither data nor charge.

**And a dock was never the point.** Angel: *"we have power cable for the tablet so that is
basically all we need."* Right. Its one real feature here is wired Ethernet — the gun is on
Bluetooth (no port) and the webcam has the USB-A — so a dock adds a box, a 135 W brick, a mains
socket and one more thing to knock off a counter, to buy one thing. If Ethernet is ever wanted it
is a **CHF 15 USB adapter**, not a dock.

> ⚠️ **And that "if" is unmeasured.** "Ethernet beats Wi-Fi for a fixed till" was my theory, not an
> observation — nobody has yet seen the shop Wi-Fi fail. **Run the till on Wi-Fi in Luzern with LTE
> behind it and watch.** Buy nothing until the failure is real.

**📸 Snap-find is DONE too — human-green 2026-08-22.** The webcam capture was running at the
browser default (~640×480), so the vision model could not read brand lettering and described
the object instead — an unbranded-but-specific read drops a perfect catalogue row from rank 1
to rank 16 of a list showing 6. Now asks 1920×1080; the server only downscales, so this had to
be fixed at the camera. Angel, close-up on a Champ High grinder: *"found the item in our
catalog right at the top — perfect hit."* Intake dimensions are now logged, so next time it is
measured, not guessed. **For an item genuinely not in the catalogue, paste the product page
(🔗 field on Add) — it returns a real EAN; a photo never can.**

**📷 The tablet camera is DONE — a USB webcam, human-green on the tablet 2026-08-22.** Re-measured 2026-08-22 on kernel `6.12.101`:
two sensors *are* fitted (OV2740 + OV5670) — the August "nothing attached" was wrong — but the
TPS68470 PMIC powering both has no board data for this model, so Linux cannot switch them on.
Kernel-patch territory; not going on a shop till. A USB webcam in the USB-A port *just worked* —
but Banco hid its own 📷 Webcam button on any touchscreen, so the tablet had **no live-camera
path at all**. Fixed and deployed (`4206246`, prod on `4206246`); Angel confirmed on the tablet:
*"the webcam button is there and it works"*. Still open: a small stand for the back office.
Ten-second re-check of the internal cameras after any kernel jump: `sudo dmesg | grep -i tps68470`.

---

## ✅ THE PRICE WARNING — BUILT, PROVED, HUMAN-GREEN — 2026-08-22 → [the day](worklist-archive/2026-08-22-pooling/)

Angel rang 1 Greengo King Size + 2 Greengo King Size slim and got **CHF 6.00** where three plain
papers are 5.00. The price was right; *"price is for the whole pack"* was unticked, so the row
stored `tier_mode: per_unit` — an island that can never pool. **Four live rows** had it.

They were never hidden. All three screens printed `3+ @ 5.00 ea` — literally true of per_unit,
absurd on its face (15.00 for three, while the till charged 5.00) — and nobody blinked, because
**a ladder printed in indigo reads as a deal however silly the number.** Being accurate was not
enough; it had to be loud, and it had to stop pricing a row it knows is wrong.

**Angel ran the 25-check sheet on prod: `25 pass · 0 fail · GO`.** Prod on `73e9cff`.

| Shipped | Where it came from |
|---|---|
| `tierWarning()` — one rule, three screens + both editors | the CHF 6.00 basket |
| `GET /catalog/price-check` — the whole catalogue at once | a badge only helps whoever scrolls past |
| The EAN above the price on every row | *"i see no EAN here … a quick glance"* |
| A sticky Save on the edit modal | two saves that never reached the server |
| The equal `1 →` rung goes silent | `+ Add break` creates it, by design |
| `✓ Pricing checked — nothing to fix` | twenty minutes proving a working feature worked |

**Money found and closed:** Tycoon Gas labelled 6.90, ringing **5.00** (−1.90 a can). Greengo
Wide Rolls labelled 4.00, ringing **3.50**. Both were a `min_qty: 1` rung silently replacing the
shelf price — *one unit is not a deal*. Neither was findable by looking at the row you happened
to be working on; the sweep found both on its first run.

**Angel cleared all ten flagged rows himself.** The live shop now carries 92 quantity ladders and
**0** that cannot mean what they say.

**Proof:** `prove-bad-price-is-visible.js`, 34 assertions — 6 of them guard-breaks that must stay
SILENT. Reverting each of the four features turns 5 red. Plus 5 sibling provers (77 total) and 53
pricing unit tests.

### ✅ The till now EXPLAINS the deal — 2026-08-22 · **17/17 GO**, retest **10/10 GO**

Twice in one day Angel sent a screenshot of a cart asking *"is this my pricing issue?"* Both times
the arithmetic was right and the screen showed only numbers. **Numbers cannot say why.** He could
send a screenshot; Layla and Mark cannot.

Every cart line that carries a ladder now says one of four things, and the checkout screen repeats
it as the last word before the drawer opens:

| | |
|---|---|
| `🏷️ 3 for CHF 5.00 — 3 in this deal` | pooled, and how many are in it |
| `🏷️ 3 for CHF 5.00 — not reached yet` + `+1 more → save CHF 1.00` | how far off, and what it is worth |
| `⚠️ not in the deal — this pack is priced per unit` | **the one that cost the day** |
| *(nothing)* | a plain product, most of the basket |

Plus **Deals in this basket** above the totals, naming the members of each group — the only thing
that answers *"why did these three not pool?"* without opening a product.

Every figure comes from the same `_bundleTotal()` the drawer uses, so the explanation cannot drift
from the charge. `prove-till-explains-the-deal.js`, 39 assertions, four of them guard-breaks that
must stay SILENT — a till that comments on every line is a till nobody reads. Neutering
`dealInfo()` turns 7 red.

**Two older bugs fell out of it, both found in Angel's pasted screen text, not by a test:**

1. **`pack ✓` on a line charged in full.** Two papers pool but two is below the three-rung, so the
   pool saved nothing — and a pool that saved nothing was still marking the line volume-priced.
   On the server that set `tier_final`, which takes a line out of `eligible_subtotal`, so **a
   manager's discount silently skipped two full-price papers.**
2. **The cart quoted a discount the drawer would not give.** The server discounts the eligible
   portion only; `checkout.html` mirrored it; the cart panel did not. Three deal papers + a
   lighter at 10% showed **CHF 8.91** in the cart and **CHF 9.41** at checkout and in the drawer.
   `isPromoRestricted()` and `cartEligibleSubtotal()` now live in `base.html` — one copy.

`prove-cart-agrees-with-till` was green through all of it: it compares line totals and **never
builds a discounted basket**. A shape the harness cannot make, not a gap in it.

**UAT:** `onboarding/testsheets/TEMPLATE.html` — steps as data, PASS/ISSUE/FAIL, per-step notes,
timing, a copy-out report, and a training mode that hides the expected result until asked. Two
sheets built on it. See `onboarding/testsheets/README.md`.

**Closed 2026-08-22 — Smoking Gold is not special.** Angel: *"GOLD is same as the others, nothing
special — sounds special but it's the same as Deluxe `84195937`. These are the King Size Papers,
no filter no tips."* Felix's "collector, 2.50, no deal" was a misread of the name. Verified: Gold
and Deluxe are byte-identical on everything that prices them — 2.00, `bundle`, 3-for-5, standard
class, no age gate. **The 3-for-5 it already carries is correct.**

*(Cosmetic only: Gold sits in `Papers & Filters`, Deluxe in `Rolling Papers`. Pooling keys on
price + terms, not category, so the till is unaffected — but they are the same kind of thing.)*

---

## ✅ BUNDLE PRICING — BUILT, PROVED, LIVE — 2026-08-21 evening → [the day](worklist-archive/2026-08-21-price-consistency/)

A customer buys a Smoking, a Raw and an OCB — not three of one. Until tonight that rang **6.00**
where three of one paper rang 5.00. It now rings **5.00**, and the rule that made it simple was
Angel's own: *"if the paper has tier pricing then they can mix."* **The deal IS the group** — no
roll table, no paper table, nothing to maintain. Two lines pool on identical bundle terms + the
same base price, which sorts the live shop into exactly two groups with no configuration:

```
49 products · CHF 4.00 · 3 for 10.00     rolls
38 products · CHF 2.00 · 3 for  5.00     King Size papers
```

**Four money bugs found and fixed today, three of them by Angel noticing a number looked odd:**

| what rang | should have | how it was found |
|---|---|---|
| 19 Gizeh Rolls Slim Pink → **5.89** | 55.10 | auditing every tiered row with the till's own function |
| 4 packs → **13.33** | 14.00 | Angel asked **Ralph**, who serves the counter |
| cart showed **15.00**, drawer 5.00 | 5.00 | Angel testing the mix at the till |
| same deal **7.00** and **6.67** in one cart | 7.00 | Angel testing again |

**Ralph's rule** (whole packs, then the deal starts again) is now the semantics everywhere,
including the above-base rescue, which had been left on the old pro-rata behaviour.

**Provers** — `prove-mix-and-match.js` rings REAL sales (localhost + `BANCO_ALLOW_FAKE_SALES=1`),
`prove-cart-agrees-with-till.js` compares 320 quantities and 9 mixed baskets line by line across
BOTH tier modes. Every one was watched go red before being trusted. 53 pricing unit tests.

### ▶️ Tomorrow — Angel's hands

- [ ] **Test a spread of packs.** The maths is proved; the shop floor is not.
- [ ] `30058569` **OCB Premium Slim black** — tick *"price is for the whole pack"*. Plain paper,
      belongs in the deal; stored `per_unit` so it cannot pool.
- [ ] `30104891` **OCB Virgin Slim + Filters** — has filters, so by Angel's rule **no deal at
      all**. Remove its tiers, do not convert them.
- [ ] 8 King Size papers still to decide · 6 Rips to price · Old School's box price.

### 🔜 The piece that is missing

**The till does not EXPLAIN the deal.** The money is right; nothing says "3 for 5 applied", nothing
prompts *"add one more and save CHF 1"*, and nothing says **why a line did not join the pool** —
Angel had to ask. A cashier sees `pack ✓` on one line and not the one beside it with no way to
know one is a filtered paper and the other is misconfigured. Layla and Mark will have to trust a
number they cannot check. That is the next real build.

---

## ✅ PROD IS LIVE ON TODAY'S CODE AND THE REFERENCE IS LOADED — 2026-08-21

Deployed `7559fa1`, **all readiness checks green** (incl. silent token refresh and the
append-only 18+ trigger), then imported the FourTwenty reference **from the live feed**.

```
reference_products        11,035 rows · 10,980 with a barcode · 10,384 distinct codes
                          11,024 photos · 11,035 prices · 981 gated 18+
alcohol rows              57 — and ZERO of them un-gated
live products             5,446 — UNCHANGED. 4,998 minted — UNCHANGED.
age_check_event           untouched
```

**The deploy had to come first, and that was the whole point.** A dry run on the old build
classified **959** rows as 18+ against today's **981** — the 22-row gap was the alcohol fix, and
importing without it would have loaded Absinthe, Agwa, the Arehucas rums and the Sulzer
sparkling wine marked *not 18+*, which `/reference/{id}/adopt` copies onto a live product.
That would have left prod **worse** than it was, because hand-creating an "Absinthe Mansinthe"
already gated on the title. Verified on the box before importing: prod's `classify()` now
returns `alcohol/True` for Spirituosen and still leaves *Brandywine (Solanum lycopersicum)* —
a tomato — alone.

Proven on the live box, by asking the database and the lookup rather than the script:

```
4002450223400 -> Pueblo Classic Tabak Dose 100g   CHF 26.50  18+  amb=1
7666563986873 -> Sasso Tabaccos Brazil Hash BIO   CHF  7.50  18+  amb=1
8718403231311 -> BioBizz Fish Mix 500ml           CHF  8.00       amb=1
7640181330065 -> BudBouncy's V1 Indoor 3g         CHF 15.00  18+  amb=1
9999999999994 -> no reference          (GS1 coupon-range filler, correctly refused)
8412766066114 -> Clipper 1 Horn 654    CHF 3.00  amb=9  ← says "9 products share this code"
```

*Sasso is CHF 7.50 now, not the 6.90 in the nine-month-old copy — staleness cost prices too,
not just coverage.* **Refresh with `--fetch --apply --prune` whenever the range moves.**

---

## 🔴 THE FOURTWENTY LOOKUP WAS NEVER LOADED — 2026-08-21 → [the measurement](worklist-archive/2026-08-21-fourtwenty-reference.md)

Angel: *"FourTwenty has the items, we just don't get matches… I have the feeling that they are
the proper numbers."* **Both halves are right, and he was doing nothing wrong.**

```
reference_products   Felix's shop 0 rows · sandbox 0 · lapiazza 0 · wolfhold: no table
scripts/import_reference_catalog.py — the only writer, per the model's own docstring
                     DOES NOT EXIST, and never has (git log --all finds nothing)
```

Every FourTwenty path in the app — `/reference/search`, `reference_matches`, `adopt`,
`_reference_best_match` — has queried an **empty table on every machine, for its whole life.**
Pattern 1 at its purest. And `web_product_lookup.py` (the thing he thinks is the FourTwenty
search) hits UPCitemdb and OpenFoodFacts — **it never touches 420.ch.**

**The data is real and it is in the monster repo:**
`helixnet/debllm/feeds/fourtwenty/products_latest.csv` — 10,082 rows, **9,977 with a real GTIN
(99.8%)**, prices and photos. Two of his three failed scans yesterday are in it with everything
(`4002450223400` Pueblo · `7666563986873` Sasso Hash); the actiTube genuinely is not.

⚠️ **Loading it is necessary, not sufficient.** Shelf-intake triage refuses to match unknowns
because *"a bare EAN carries no name"* — true only while the table was empty. And
`_find_catalog_matches` searches the reference **by title only, never by barcode**, though the
column is indexed and two other endpoints do use it.

**① THE IMPORTER IS BUILT AND PROVEN** — `scripts/import_reference_catalog.py` (`a9dda04`).
Sandbox: 0 → **10,082 rows**, idempotent on a second run, and `_reference_best_match` now
answers `4002450223400 → Pueblo Classic Tabak Dose 100g CHF 26.50 how=barcode`. Dry run unless
`--apply`. ✅ **RUN ON PROD 2026-08-21 06:32 UTC — measured 2026-08-22 evening, not remembered.**
`reference_products` on Felix's box: **11,035 rows · 10,980 with a real EAN · 981 age-gated**,
all stamped `2026-08-21 06:32`. `--fetch` pulled a fresher feed than the 10,082-row CSV, hence
the higher count. Spot-check live tonight: `4002450223400 → Pueblo Classic Tabak Dose 100g
CHF 26.50`. This item sat marked "Angel's call" for a day AFTER it was done — pattern 3, a
remembered state with no expiry condition on it.

Three things its first dry run caught, each of which would have shipped:
- **FourTwenty's 18+ flag is their checkout policy, not the product** — they mark a USB wall
  plug `mindestalter: 18`. Importing it would have gated 2,220 rows, and `adopt` copies
  `age_restricted` straight onto the live product. **A till that IDs a phone charger teaches
  the cashier to click through the age gate.** Our classifier decides (829); theirs is kept in
  `raw` and printed as a disagreement.
- **`classify()` was already written for this table and had no caller** — its docstring says
  *"Map a REFERENCE ITEM to (our_category, our_class, age_restricted)"*.
- **Layer 2 had no alcohol branch.** A bottle's title is a brand, so 17 of 44 "Spirituosen"
  and **all 5** of "Bier, Wein & Champagner" would have loaded **un-gated**. Fixed; measured
  across all 10,082 rows: **22 newly gated, 0 un-gated.** 4 new tests.

**② AN EAN MISS NOW ASKS THE REFERENCE — BY BARCODE** (`e66acb3`). Neither half needed a new
endpoint; both were already built around an empty table.
- **The till:** a miss that the supplier knows opens the find-and-bind panel **with the real
  title already in the search box** — which is what lets her find the Tamar row under a minted
  code and bind THIS code to it. A miss nobody knows still gets 2026-08-07's quiet department
  strip. No modal for nothing.
- **Shelf intake:** unknown rows now carry title, price, photo, category and 18+.
  **Exact barcode only — never a name guess.** *"It says, well, of course, it doesn't find
  it… so then I have to do basically a web search."* Now it answers first.

Two hazards found by scanning a **made-up** control code and getting a confident answer:
- **GS1 980–999 (coupons) and 20–29 (someone else's in-store code) are not packet codes** —
  the feed uses them as filler. Refused. 9,977 → 9,953. **977–979 KEPT**: those are ISBNs and
  the shop really sells the books.
- **145 codes sit on more than one product** — a Clipper 4-pack at CHF 75 and its singles at
  CHF 7.50 share a GTIN. The screen now says *"the supplier lists N under this code"* instead
  of naming one confidently.

`scripts/prove-barcode-binding.js` — **29 checks, 29/29**, real browser. Sabotaged both halves
→ 7 red. Skips **loudly** when the reference is empty, because a silent skip is the exact
shape that hid this for the project's whole life.

**③ KINGS CASTLE IS TIER 3** (`cbc158d`). Order on a miss: live catalogue → our reference
(local, instant) → a shop that answers an EAN. Measured on ten codes FourTwenty lacks, Kings
Castle answered **3** — actiTube, Purize, LocalWeed — all of them codes nothing else could
resolve. **Reach ~40% → ~56%.**
- **Generalised, not hardcoded:** `RESOLVABLE_SHOPS` is a list of dicts; a shop cloning Banco
  adds an entry with no code. The scoped-search buttons derive from the same list.
- **The offer never takes over.** The department strip appears immediately; the lookup runs
  unawaited and an offer appears *beside* it. 2026-08-07's decision stands.
- ⚠️ **No price crosses, and it is load-bearing now.** Kings Castle is a wholesaler: EAN
  `4260641140046` lands on *"actiTube Aktivkohlefilter - Slim (50Stk.)"* — the right name,
  Angel's own BL-10 product — at **CHF 99.00**, while the single is CHF 9.90 on the same page.

**Still to do:** ④ measure how often *"Is it already in my catalogue?"* actually binds to an
existing minted row — the button exists, the hit rate does not. ⑤ ~~deploy tier 3 to prod~~
✅ **already there** — `a9dda04`, `e66acb3`, `cbc158d` are all ancestors of prod's `9abc082`
(`git merge-base --is-ancestor`, checked 2026-08-22). ⑥ a SECOND wholesale feed is still the
big lever; neardark needs creds.

### ⚠️ THE REFERENCE DOES NOT FIX THE 4,979 MINTED CODES — measured on prod 2026-08-22

Asked directly: *"is that going to replace the existing tamar 2000000 EANs … and fix those bad
internal dummy eans — is that the idea?"* **No.** Worth writing down, because it is the natural
reading and it is wrong.

The importer writes **one table** via one `UPSERT` — `reference_products` — and never touches
`products`. It is a clipboard beside the catalogue, not a migration.

And a bulk title-match cannot do it either. Measured on Felix's box tonight, 4,979 minted rows
against all 11,035 reference titles (`pg_trgm`):

```
300-row sample, best similarity vs the WHOLE reference table
  < 0.5   212 rows  (71%)   ← no usable match at all
  ≥ 0.7    36 rows  (12%)
  = 1.00    9 rows   (3%)
full 4,979 with an EXACT title match to a ref row carrying a real EAN:  140  (2.8%)
```

So the ceiling on auto-binding is **140 of 4,979**, and even those are not safe: **145 reference
codes sit on more than one product** (the Clipper 4-pack at CHF 75 and its singles at CHF 7.50
share a GTIN), so an exact title match can bind the code of the wrong pack size — and per
LESSONS #8 a wrong bind looks exactly like a right one from inside the database. Only the packet
tells them apart.

**What actually converts a minted row is one scan** — bind-on-scan (BL-90), at the counter, with
the packet in a hand. The reference's job is to make that scan *land*: a miss the supplier knows
now opens find-and-bind with the real title already in the box. 18 aliases bound so far.
**The open number is still ④ — the hit rate — and it is measurable at the till, not here.**

### ④ THE HIT RATE — MEASURED 2026-08-22. It cannot be answered yet, and here is why.

**113 minted codes HAVE been converted.** The bind promotes correctly: a real EAN off a packet
takes the primary slot and the minted `2xxxxxxxxxxxx` is demoted to an alias, never discarded
(`pos_router.py:2329`). So a rescued row is `product_barcodes.barcode ~ '^2\d{12}$'` with a real
`products.barcode` — **113 on prod**, out of 4,979. **2.3% in three and a half weeks.**

```
day      rescues   sales that day
07-31       16
08-05       50            ← hand-binding sessions, not till traffic
08-06       27
08-20       13          2
08-21       12          1     ← reference went live 06:32 UTC this morning
08-22        1          0
```

**None of them came from the till.** The box has rung **50 transactions in its entire life**
(45 completed + 5 refunded, since 2026-07-25) and **4 in the last nine days.** Twelve binds on
08-21 spread from 07:24 to 17:28 against **one sale** — that is a human at the catalogue screen
working through a list, not a cashier scanning a packet. *(Inference from timing: the endpoint is
the same either way, so the DB cannot distinguish them. It is a strong inference, not a fact.)*

**So the reference's effect is unmeasurable, and would have been whatever we found.** 13 binds
the day before it loaded, 12 the day after. With one sale between them there is no denominator.
**The blocker on ④ is not instrumentation — it is that the shop is in acceptance, not trading.**

### 🔴 AND THE MISS RATE IS NOT BEING RECORDED AT ALL

`catalog_miss` — SPEC §6's "self-prioritising enrichment backlog" — holds **1 row, ever.**
`_record_catalog_miss` is called from two places (`pos_router.py:5850`, `:6464`) and both are
gated `if ln.department_code and ln.unresolved_barcode`. **Only a miss rung through the
department strip is counted.** A miss the cashier handles by creating the item — now the good
path, since `createNoCodeItem()` binds the real code — carries no `unresolved_barcode` on a
department line, so it is never counted. Defensible as design (it *was* resolved), but the
consequence is that **"three of four scans miss" has no live measurement behind it.** That
figure came from counting minted rows in the catalogue, which is a stock, not a rate.

**What this actually says:** hand-binding works and is the only thing converting rows. At 113 per
three weeks, 4,979 rows is years. The reference does not change that rate — it changes what a
human sees when they get there. **The lever is a shelf pass with the gun, not a till feature**,
which puts this behind the inventory-mode dump in `▶️ NOW`.

*Bulk name-matching stays weak and measured: "Tabak Beutel Sasso Tobaccos Hash 25gr." does not
reach "Sasso Tabaccos Brazil Hash BIO" at the 0.5 threshold. **Scan-time beats bulk.***

---

## 🔴 SIX REPORTS FROM THE TILL — 2026-08-20 (BL-9…BL-14) → [the evidence](worklist-archive/2026-08-20-till-reports.md)

**All six tagged `annoying`. Not one `blocking`.** Read that before reading Felix's verdict.

```
5,446 products live · 4,998 carry a MINTED 2000000… barcode (92%)
  414 findable by scanning the real packet (7.6%)
   29 of 107 sold catalogue lines had a real EAN (27%)
```

**Three of every four things Felix rings up cannot be scanned off the pack.** The buttons he
hates — department strip + "new item" form + pending-code banner, stacked at once — *only
appear because the scan missed.* Fewer buttons is the wrong fix; a scan that hits is the fix.

1. **🩸 THE LEAK — `scan.html:1385`.** `createNoCodeItem()` always mints, even when
   `pendingBarcode` holds the code that just 404'd and the screen is *displaying* it. Every
   item created today adds another unscannable row. = BL-9, BL-12, BL-13.
   Sibling: `catalog.html:1297` never seeds Barcode from the search box, and its hint
   *"leave it blank — a code is generated automatically"* is the bug written down as a feature.
2. **📷 `catalog.html:1692`** — `if (!this.snapPreview)` plus an `openCreate()` that never
   clears `snapPreview`/`snapName`/`pageUrl` ⇒ the panel shows the **previous** product's photo
   under the words "read from this photo". = BL-10, BL-11.
3. **BL-14 · the cursor** — title and body point opposite ways; needs 30 seconds of Angel
   showing me. Plus two unlabelled buttons in his screenshot — **unverified**, could be an
   html2canvas artifact, and a screen is checked in a browser.
4. **The tablet** — no Chrome by default, Firefox search "no good". Not specified yet.

The 4,998 already in there: bind-on-scan is built (BL-90); 18 real aliases bound so far.
Tamar publishes no EAN — but **FourTwenty does**, and that feed was never loaded. See the item
above; it is the same problem seen from the other end.

---

## 🔴 The silent-refresh bug — CLOSED 2026-08-13 → [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md)

Fixed in `9f34f85`; now pattern 6 in `CLAUDE.md` and a lesson in `LESSONS.md`.

---

## 🔍 OPEN, NOT REPRODUCED — the till felt slow in Angel's browser

`[Violation] 'click' handler took 1144–2077ms`, seven times between 13:05 and 13:14 on
2026-08-13. **Measured here and could not reproduce it:** Add-to-cart, quantity, payment
select all run **80–100 ms**, and Checkout 500 ms (a page navigation), with zero
violations — in headless *and* in a fully rendered browser under Xvfb. One "Add" click
fires **no** network at all.

Two theories ruled out by checking rather than guessing: no rebuild was running during
that window (the app container last started 12:52, his violations begin 13:05), and the
i18n MutationObserver is already scoped to `childList`+`subtree` on *added* nodes only,
with a comment naming this exact hazard.

**What is left, and it is testable in 30 seconds:** his screenshot shows **DevTools open**
with the Elements panel live, plus several browser extensions. Alpine mutates the DOM on
every keystroke and every cart change, and a live Elements panel re-renders on each one.
→ Close DevTools, ring the same cart, and see whether it still lags. If it does,
`scratchpad/click-probe.js` names the offending handler in his own browser.

*Not a defect until it reproduces without DevTools — but not closed either.*

---

## ✅ PROD IS LIVE ON TODAY'S CODE — 2026-08-14, ALL GREEN

Felix's shop is deployed and every readiness check passes:

```
✅ silent token refresh works — a session survives past the 5-min access token
✅ 18+ evidence is append-only (trg_ace_append_only installed)
✅ ALL GREEN.        banco.wolfhold.app 200 · banco-auth.wolfhold.app 200
```

**The 18+ evidence is now genuinely permanent on prod** — that trigger had never been
installed there, and until this deploy the table any screen called "append-only" could have
been rewritten by a single UPDATE. 13 compliance rules seeded, 0 active by design.
Felix rang a sale immediately afterwards; the audit cockpit caught it.

**Two things went wrong on the way, both mine, both now guarded:**

1. **The deploy silently did not run the first time.** `deploy-prod.sh` was typed without
   `./scripts/`, and the *command not found* scrolled past under 37 files of successful pull.
2. **I crash-looped Keycloak** — `You can not set both 'hostname' and 'hostname-url' options`.
   My own preflight, written that morning, **passed the broken config**, because it validated
   each value alone and never the pair. The app served 200 throughout, so **the shop looked
   alive while nobody could log in** — the nastier failure shape. Fixed, and the preflight now
   refuses the combination (proven by restoring the exact broken file).

⚠️ **The box is on `999800d`.** The two commits since — `250053f`, `b0cf512` — are compose and
script changes only, no app code. A `git pull` picks them up; **nothing needs redeploying.**

**Left over from the B2 detour:** the storage cap is lifted (31 GB, no cap, ~13¢/month). Still
worth doing when convenient — a lifecycle rule on `wolfhold-banco-backups` (229 dumps since
20 July, "keep all versions", nothing ages out), and a look at
`wolfhold-freehold-backups` (35 files, **30.7 GB** — that was what blew the cap, not Banco).

---

## ▶️ NOW — needs Angel's hands

1. **⛔ The two bulk catalogue scripts are blocked on WHERE they run, not on code.**
   Local dev has **6 products**; the 5,111 live on the prod/UAT box, and `deploy-prod.sh` is
   written to run *on* that server. Decide: a shell on prod, or a dump pulled down here. Then
   `enrich-from-source.py --apply` (~90 min) and `adopt-images.py --apply` (~137 min).
   → detail in [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md)

2. ~~**🔫 The gun's inventory-mode dump is unproven**~~ — ✅ **CLOSED 2026-08-22, human-green.**
   Angel: *"the gun has been tested and it works fine, there are no issues."* The burst survives
   the browser textarea. **The last unknown in shelf intake is gone and the 10× path is open** —
   which matters more tonight than it did this morning, because the 08-22 measurement says
   hand-binding at a screen is the ONLY thing converting minted rows (113 in 3½ weeks) and a
   shelf pass with the gun is the only thing that goes faster. Runbook:
   [`onboarding/09-shelf-intake.md`](onboarding/09-shelf-intake.md); triage is read-only
   (`pos_router.py:1002` — *"Nothing is written"*), so it is safe to point at the live shop.
   ⬜ *One doc question left, and it is a DOC question, not a re-test:* the scanner README cites
   **Inateck** BCST-35 §4.6 p.20 for Inventurmodus, this list said **Netum**. Whichever gun Angel
   used is the right one — fix the loser so the next shop's runbook is not wrong.

---

## ✅ The 18+ evidence work — DONE, human-green 2026-08-13 → [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md)

Angel ran it and called it: *"it's working fine."* **Do not reopen it for another pass.**
`scripts/prove-till-18plus.js` (45 checks, rings as `ralph`) still runs before a promote.

---

## 🔜 NEXT

3. **🔐 Go-live hardening** — DNS preflight + a default-secret gate in `deploy-prod.sh`; and the DR
   restore (Move B), still **blocked on read-only B2 credentials**. The backup has never been
   restored, so it is a belief, not a capability.

4. **🌱 Seeded realm users are published — DEFERRED ON PURPOSE 2026-08-14, not forgotten.**
   `keycloak/import/realm-export.json` carries **six users with plaintext, non-hashed
   passwords**, and `github.com/akenel/banco-starter` is **public** (HTTP 200 unauthenticated):
   `felix` (`pos-admin`), `ralph` (`pos-manager`), `michael`, `pam`, `pos-developer`,
   `pos-auditor`. Both `compose.yml:39` and `compose.prod.yml:35` boot Keycloak with
   `--import-realm` from that same file — prod and dev seed from one export.
   **Angel's call, 2026-08-14: leave them.** The usernames aren't the secret, these are seeded
   demo accounts, and **he rotated `felix`'s password on the live box**, so the published one is
   dead for the account that actually has privilege. Reasonable.
   ⚠️ **The one mechanism that could quietly undo that:** Keycloak's `--import-realm` only seeds
   when the realm doesn't already exist. So today's rotation holds — *until the Keycloak DB
   volume is ever recreated* (`down -v`, a fresh box, a restore drill onto a clean box). Then the
   export re-imports and **`felix`'s password silently reverts to the published one**. The
   DR restore in item 3 is exactly that scenario. Whoever drills it: check `felix` afterwards.
   When it comes up the list: strip the six users from the export (freehold did this in
   `a202c32` — `kc-prd` ships `"users": []` and the first admin is made by hand), and treat all
   six published passwords as burned regardless. The other five still have live published
   passwords today.

---

## 🧹 NEEDS TRIAGE — read before trusting

[`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) holds ~1,000
lines of catalogue, till and shelf-intake items written between 07-30 and 08-07. **Their status was
not re-verified when they were archived**, and at least one was already wrong:

> the shared cash box was filed as *"design agreed 2026-08-03, not built"* — it shipped in
> `fd035dd`, and the `cashier_id == user_id` filter it describes is gone from the code.

**So: check the code before acting on anything in there.** Promoting the still-live ones up to NOW
is a 20-minute job worth doing once, not a thing to re-derive every session.

---

## ⏲️ A decision the logs raised — how long may a till sit idle?

Angel's 15:46 logout was **correct**: 152 minutes idle against a 60-minute
`ssoSessionIdleTimeout`. Not the refresh bug returning — refresh verified 200 at the time
of writing. But it is worth deciding deliberately for the shop rather than inheriting it:
**60 minutes of a backgrounded tab and the cashier is logged out.** In the foreground the
till polls and the session stays warm; a tablet asleep over lunch does not. Overnight
logout is *desirable*; a quiet Tuesday afternoon one is not.

---

## 📌 Standing facts worth not re-learning

- **The app image bakes `src/` in — there is no bind mount.** `docker compose restart app` restarts
  the **old** code and says nothing. Any change under `src/` needs `./scripts/rebuild.sh`.
- **Prod authenticates against the DEMO realm** (`kc-pos-realm-dev`, users felix/pam/ralph),
  imported from a file **in a public GitHub repo**. Still the go-live blocker.
- **Banco is zero-perpetual.** `stock_quantity = 1` is the *design*, not missing data. Never set
  `min_stock` / `max_stock` / reorder points — `/reorder/suggestions` ranks by what the till sold.
- **`age_check_event` is append-only** (a PL/pgSQL trigger, not `REVOKE` — which is a no-op against
  a table owner). Nothing can tidy a row away, including a mis-tap.

---

## 🧪 How to prove it before claiming it

| what | command |
|---|---|
| stand up | `./scripts/rebuild.sh` → `./scripts/standup.sh` |
| server-side 18+ evidence | `BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py` |
| **the actual screens** | `BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-till-18plus.js` |

⚠️ Both scripts **ring real completed sales** and refund them afterwards; a completed transaction is
a line in the Kassenbuch. `BANCO_ALLOW_FAKE_SALES=1` exists so it cannot happen by accident.
Playwright is **borrowed via `NODE_PATH`, not vendored** — this repo has no node build, on purpose.

---

## 📚 The archive

| file | what's in it |
|---|---|
| [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md) | Gate Zero, and the whole 18+ evidence thread 08-10 → 08-13 |
| [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) | catalogue, shelf intake, till and search, through 08-07 — **status unverified** |
| [`worklist-archive/backlog.md`](worklist-archive/backlog.md) | not yet scheduled — offline kit, monitoring, labels, exports |
| [`worklist-archive/done.md`](worklist-archive/done.md) | shipped, most recent first, with commit hashes |
