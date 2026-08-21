# Scan tiers — the live half-hour test

**Where:** https://banco.wolfhold.app/pos → Scan → Barcode
**Built 2026-08-21.** Every code below was checked against the **live shop and the live
lookups** that morning — the "should happen" column is measured, not predicted.

**Nothing here rings a sale.** Tier 1 drops an item in the cart — empty the cart when you're
done. The only thing that writes to the catalogue is if *you* press bind or create.

---

## Part A — ten codes, one per behaviour

Type each into the barcode box, press Enter, and tick it.

### 1 · Already bound → straight into the cart

No banner, no strip, no panel. It just lands.

| # | Code | Should land as | ✅ |
|---|---|---|---|
| A1 | `716165202486` | RAW 5 Stage Cone Set / 5 Cones | |
| A2 | `3661075283438` | Grinder Champ High White Leaf — 4-teilig | |
| A3 | `7612400041724` | Parisienne Jaune MYO 230g | |

### 2 · Our reference knows it → the panel opens **already named**

"Not on file — find it first", and the search box is **pre-filled with the real name.**
Nothing to type.

| # | Code | The name that should appear | ✅ |
|---|---|---|---|
| A4 | `0810132918988` | Hemper Glass Filter Tips 6mm 5pcs | |
| A5 | `6901811290533` | RP SOS Pump Plus 5000l/h | |
| A6 | `9008122312248` | Grinder Crystal Blue Zinc 4er | |
| A7 | `4260748411537` | PURIZE Xtra-Slim ø 5,9mm 100er Glas Pink | |

*(A4 and A7 also check that a **leading zero** and an **ø** survive the round trip.)*

### 3 · Only Kings Castle knows it → strip first, then an offer

The amber banner and department strip appear **immediately**. A second or two later a **blue
box** slides in underneath: 📚 *from Kings Castle*, a photo, and an orange wholesaler warning.
**Watch that nothing already on screen moves.**

| # | Code | The offer that should appear | ✅ |
|---|---|---|---|
| A8 | `4260748411544` | Purize Aktivkohlefilter Xtra Slim 6mm im Glas — Yellow | |
| A9 | `4260748412268` | Purize Aktivkohlefilter Xtra Slim 6mm — green | |

### 4 · Nobody knows it

| # | Code | Should happen | ✅ |
|---|---|---|---|
| A10 | `7640000000001` | Banner + department strip. **No offer, ever.** | |

---

## Part B — the two new escapes

| # | Do this | Should happen | ✅ |
|---|---|---|---|
| B1 | On A8's offer, press **Use it** | Panel opens, code held, name pre-filled | |
| B2 | In that panel, press **⏭️ Not now — just sell it from a department** | Panel closes, you're back on the strip, **the code is still in the amber banner** | |
| B3 | Now tap **Misc**, type `5.00`, add to cart | Line added. The code rode along with it. | |
| B4 | Finish that sale, then open **🔎 What the till couldn't find** from the dashboard | `4260748411544` is on the list, ×1, department Diverses, last rung CHF 5.00 | |
| B5 | Press **What is it?** on it | Kings Castle names it, with the photo | |

**B4 is the one I most want confirmed.** It's the only step that proves the promise on that
button — *"the code is kept"* — is true end to end on the live shop. Everything before it I
tested; that chain I've only tested on the sandbox.

---

## Part C — ten real packets off the shelf

The part I can't do. **Pick them at random** — whatever's nearest, not the ones you remember
fighting with.

```
1  IN THE CART             already bound
2  PANEL, WITH A NAME      our reference knew it
3  BLUE OFFER              Kings Castle knew it
4  STRIP ONLY              nobody knows it
```

| # | Packet | 1 / 2 / 3 / 4 |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |
| 8 | | |
| 9 | | |
| 10 | | |

**Bring back four numbers.** My estimate is ~40% for 1+2 and ~56% including 3, from a sample I
already told you was biased. Yours isn't.

---

## What to shout about

- **A wrong name offered confidently.** Kings Castle sells cases — the name can be right while
  the *thing* is a 10-pack. If an offer names something that isn't in your hand, tell me. That's
  the one failure class this shop keeps paying for.
- **The offer arriving after you've already tapped a department.** It shouldn't move anything.
  If it feels like it does, that's a design call and I want to hear it.
