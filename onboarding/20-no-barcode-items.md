# 20 · Products with no barcode — grinders, bongs, trays

*Opened 2026-08-05. **Grinders are the pilot; the workflow is meant to generalise.** Angel:
"if we nail down the workflow for that, it'll probably work for other things — trays, for example,
don't have barcodes and bongs typically don't either."*

---

## Why this is its own problem

Every catalogue tool in Banco assumes the packet carries an EAN. Shelf intake scans it, the till
resolves it, the alias table remembers it. **A grinder has no EAN at all** — no packet, often no box,
just a price sticker and a shape.

So the whole 2026-08-05 loop — *scan the shelf, bind what the gun read* — **does not apply to the
shelf the day book ranks 4th** ([`19`](19-what-actually-sells.md)).

**And it is the expensive end.** Per doc 19, the biggest single sales of the month were a `Mighty`
vaporizer at **398.–**, a bong-plus-kit at **307.–**, `Hanfsalbe` at 300.–. Consumables are the
volume; hardware is the value — and hardware is exactly what has no barcode.

---

## The rule that decides it: MINTING IS CORRECT HERE

The 2026-07-30 lesson is easy to misread:

> **Never invent an identifier that exists in the physical world.**

That was about **5,103 products whose real EAN existed** and was fabricated over — a catalogue that
could not be scanned because Banco had made up codes for things that already had them.

**A grinder has no EAN in the physical world.** Nothing is being overwritten, and no future scan will
ever contradict the minted code. **`barcode_is_internal = true` is exactly this case** — the flag
exists to say "this code is ours, not GS1's".

> **The rule is "don't invent one that EXISTS", not "never mint".**

---

## 🔧 The workflow (grinder pilot)

### 1 · Photograph every grinder
Angel's plan, and the only route in without an EAN. **One photo per SKU**, not per unit. Get the
price sticker in frame if there is one.

### 2 · Identify it
Most Artemis grinders come from **420** (the wholesaler), so the pictures should match against their
catalogue. **They rarely sell online** — Angel: *"people wanna feel it in their hand, that's why they
buy them in the store"* — which is why picture-matching beats a web search here.

⚠️ **A rarely-sold-online product is a thin-web product.** Expect the enricher's hit rate to be far
worse than it was for papers. Budget for typing the name by hand.

### 3 · A naming convention, decided ONCE and applied to all of them
This is the load-bearing step and the one that is cheap now and expensive later. Without it, a
cashier cannot find a grinder by typing, and picture-matching cannot dedupe.

Proposed: **`Grinder · <brand> · <material> · <parts> · <Ø mm>`**
e.g. `Grinder · Black Leaf · Alu · 4-teilig · 50mm`

The four things a customer actually asks for are **size, parts, material, brand**. Whatever shape is
chosen, **every grinder gets the same shape.**

### 4 · Mint a code and print a label
`barcode_is_internal = true`, then a label from the QL-820NWB (Bluetooth, working since
2026-08-04). **Without a label it still cannot be scanned**, and the cashier is back to typing a
name mid-sale — which breaks doc 10's *2 seconds, or it is broken*.

> ### 🏷️ The open question Angel raised: does the label FIT?
>
> *"I don't know if the small QR code label fits on most of the small grinders. And I don't know if
> they wanna stick on every single grinder."*
>
> Two real problems, and they need a physical test, not a decision on paper:
> - **Size.** The 18 mm QR (variant D) read as cleanly as 20 mm in the 2026-07-29 scan tests, so
>   there is already a genuinely small sticker available. **Test it on the smallest grinder in the
>   shop before committing.**
> - **Willingness.** A sticker on a CHF 40 object a customer is holding to judge is a retail
>   decision, not a technical one — **Felix's call.**
>
> **Fallbacks if a sticker on the product is refused:** a **shelf-edge label** the cashier scans
> instead of the product, or a **PLU/button** for the handful that sell most. Both keep the till fast
> without marking the goods.

### 5 · Prove it the only way that counts
Scan ten of them at the till with the objects in hand. **A rescan that resolves is not a rescan that
is right** — check the name and picture match the thing you are holding.

---

## What this pilot has to answer before it generalises

- [ ] Does picture-matching against 420 actually identify a grinder? (**hit rate on 10**)
- [ ] Does an 18 mm label physically fit the **smallest** grinder?
- [ ] Will Felix accept stickers on the goods — and if not, is shelf-edge acceptable?
- [ ] Does the naming convention survive a cashier typing two words under pressure?
- [ ] How long per item, really? (papers were **47 s**; this will be slower)

**Then apply the same five steps to trays, then bongs.**

---

## 📊 The other question: how many bongs do they actually sell?

Angel: *"they got a lot of those on the top shelves, they're hard to get at."*

**The day book cannot answer it precisely** — it records `Bong-Ersatz` and `Glas-Pipe` and
`Holzpfeife` as separate scribbles, and never says which bong. What it does show is that **one bong
sale carried a 307.– transaction**, so the value per sale is high even if the count is low.

⚠️ **Slow-moving + hard to reach + high value is the worst combination to leave uncatalogued**, and
also the least urgent to *scan* — nobody is waiting at the till while you find a bong. So:
**catalogue them for the price and the stock knowledge, not for till speed.**

**The real answer comes from Banco**, once a few weeks of sales exist —
`GET /reorder/suggestions` ranks by what actually sold. A month from now this question is a query.
