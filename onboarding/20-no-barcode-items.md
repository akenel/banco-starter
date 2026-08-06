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

### 2 · Identify it — ✅ THE TOOL ALREADY EXISTS

**`POST /products/snap-find`** (`pos_router.py:1438`), exposed on **`/pos/catalog`**
(`catalog.html:1259`). Its own docstring describes this exact job:

> *"Snap a photo → the AI reads the item → **SEARCH the real catalog** for it (find-first)… so the
> cashier can pick the item that **ALREADY exists** (in `products` or the **FourTwenty reference**).
> …Honest confidence is the match score, not the model's self-rating — **the grinder can't return a
> confident wrong answer**, because a low `best_match_score` means 'not found → search or create'."*

It searches **both** the catalogue and the **420** reference — which is exactly where Angel says the
grinders come from. Nothing to build to get started.

> ### 🔎 Where the button actually is — found the hard way 2026-08-06
>
> **`/pos/catalog` → `+ New product` → the indigo box at the top of the modal → ✨ snap-fill.**
>
> ⚠️ **There are two photo controls on that screen and the obvious one is wrong.** The file picker in
> the **scan** overlay is the *barcode reader's* no-camera fallback — it tries to decode a **barcode**
> out of the photo, and on a grinder it correctly fails with
> `No MultiFormat Readers were able to detect the code`. That reads exactly like the AI broke. It did
> not; it was never called.
>
> The AI button is gated `x-show="!editing"` — **create mode only** — so you have to open "new
> product" before the tool that tells you whether the product already exists will run. Backwards, and
> filed in `WORKLIST.md`. Until it moves, **go through `+ New product` even when you expect a match.**

⚠️ **A rarely-sold-online product is a thin-web product.** Angel: *"they don't sell online… people
wanna feel it in their hand."* That is *why* they sell in the shop, and also why the web has little
to say about them. Expect a worse hit rate than papers, and budget for typing names by hand.

### 2b · ❓ Batch? Not yet — and here is the test that decides it

Angel: *"I'm thinking of somehow doing a batch… paste the folder where all the pictures are."*

**No batch endpoint exists** — `snap-find` takes one file. Building one is a new multi-file endpoint
plus a worklist screen in the shelf-intake shape.

**But batch only saves the UPLOAD clicks. It cannot batch the DECISIONS** — every grinder still needs
a human confirming the match, and that is where the time actually goes.

> ### 🎯 So: run **10 grinders** through `snap-find` first and measure ONE number — **how often does
> the photo find the right grinder in the 420 reference?**
>
> - **7+/10** → batch is clearly worth building, and the ten runs will have shown exactly what the
>   worklist needs to display.
> - **Poor** → batch would only be a faster way to fail; the real answer is typing names off the
>   photos, and no amount of upload plumbing helps.
>
> Same discipline that saved the enricher: **a sample you can check beats a sample that is merely
> large.** Twenty minutes buys the answer.

**Photographing:** phone (best camera in the kit), **one shot per model, not per unit**, price
sticker in frame. Then work them from `/pos/catalog` on the tablet or the ProBook.

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

> ### 🛑 FELIX SAID NO TO BARCODES ON GRINDERS — four ways round it
>
> *Angel, 2026-08-06: "Felix says I don't want to put barcodes on all the grinders. I said nothing at
> the time… but today I face the reality. How do we do it Felix's way?"*
>
> **#1 · Find out what the objection actually IS — because they already sticker.**
> Rafi *"does his own pricing, little sticker labels for the stuff, and restocks the shelf."* **Every
> grinder is already being marked today.** So Felix is not objecting to a sticker in principle:
> - *"It'll look ugly"* → a **design** problem. Ours can be smaller and neater than what is on there.
> - *"More work for Rafi"* → it is **the same work** — one label printed and stuck, either way.
> - *"Customers pick them up and handle them"* → the only version that needs a real alternative.
>
> **Ask it as: "You already put a price sticker on every grinder. What if that same sticker had a
> small code on it too?"** The QL prints price and barcode on one label. If that lands, this whole
> problem disappears.
>
> **#2 · A scan card at the till — nothing is marked.**
> A printed sheet on the counter: **thumbnail · name · price · barcode**, one row per grinder. The
> cashier finds the row and scans off the paper. 192 grinders ≈ **4–6 A4 pages**, laminated or in a
> ring binder. Normal retail practice, and it has a bonus nothing else has: **it shows a picture**, so
> a new cashier can match the object in the customer's hand to the row.
>
> **#3 · Shelf-edge labels.** Barcode on the shelf strip. Fine if grinders sit near the till; costs a
> walk when the customer carries one to the counter, which a 2-second till cannot afford.
>
> **#4 · Search by name.** Free, works today, slowest. **This is why the naming convention in step 3
> is load-bearing** — with a consistent shape, two typed words find it; without one, nothing does.
> Good enough as the fallback for the long tail even if the top sellers get stickers or a card.
>
> **Take it to Felix as a CHOICE, not a request:** print one sample label, put it on the smallest
> grinder, show him that beside the scan-card idea. *"Either the price sticker carries a code, or we
> keep a card at the till — which do you prefer?"* Both are workable, and that is a far easier
> conversation than asking permission to mark his stock.
>
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

## 🔴 BONGS ARE A DIFFERENT PROBLEM — and it is bigger than grinders

*Angel, 2026-08-05: "they have parts like you wouldn't believe… little screw pieces, different
millimeters. It goes on and on. **That scares the hell out of me.** None of that stuff is marked."*

He is right, and the catalogue confirms it. Measured on prod 2026-08-05:

| Category | Rows | Real EAN | Avg price | Range |
|---|---|---|---|---|
| Bong & Pipe Accessories | **253** | **0** | 12.51 | 1 – 299 |
| Vaporizers | **248** | **0** | 59.42 | 2.50 – 519 |
| Bongs | **178** | **0** | 80.34 | 5.90 – 590 |
| Dab & Concentrate Gear | **157** | **0** | 69.00 | 2.50 – 1199 |
| Pipes | **116** | **0** | 23.68 | 1.90 – 79 |
| | **952** | **0** | | |

**952 rows, not one real barcode between them.** That is five to six times the papers job.

### The thing that makes it *harder*, not just bigger

**Grinders are an IDENTIFICATION problem. Bong parts are a COMPATIBILITY problem.**

A customer walks in holding their own bong and asks *"will this fit?"* Answering needs exactly two
facts about every part:

1. **Joint size** — `10 mm` · `14.5 mm` · `18.8 mm` (the German *Schliff* standard)
2. **Gender** — male (*Stecker*) or female (*Muffe*)

A 14.5 male bowl fits a 14.5 female downstem. Nothing else does. **Two facts, and without them the
cashier cannot answer the only question anyone asks about these products.**

How many of the 431 bong/accessory rows carry it today:

| | Count | of 431 |
|---|---|---|
| Name contains a **mm size** | 52 | **12%** |
| Name contains a fitting word (*Schliff · Adapter · Joint*) | 66 | 15% |
| Any structured `attributes` at all | 61 | 14% |
| Bowls (*Kopf · Chillum · Steckkopf*) | 105 | |
| Downstems | 19 | |
| Screens (*Sieb*) | 30 | |

> **~88% of bong parts do not record the one fact that decides whether they fit.** No photograph
> fixes that — a picture cannot reliably tell 14.5 from 18.8. **It has to be measured or read off
> the supplier's spec.**

### The reframe that makes it tractable

**The parts that NEED compatibility data are the cheap ones. The expensive ones do not need it.**

- **Bongs themselves** (178 rows, avg **80.–**, up to 590.–) — a customer picks these **by eye**.
  They need a correct **price**, not a spec. Low urgency, high value: catalogue them for the money,
  not for the till.
- **Accessories** (253 rows, avg **12.50**) — chosen entirely **by fit**. This is where the two facts
  matter, and it is the harder, cheaper, more numerous half.

### 🛑 Recommendation: do NOT attack bongs tomorrow

Grinders first — that workflow is worth proving on ~50 items where a photo genuinely identifies the
thing. Bongs need a different tool and a decision that has not been made yet.

**When bongs do get done, the order should be:**

1. **Accessories that actually sell** — bowls, downstems, screens, adapters. Not all 253.
2. **Record size + gender as structured `attributes`**, not buried in the name. The column already
   exists and 61 rows already use it — no migration needed.
3. **Then make it searchable**: a cashier types `14.5 male` and gets everything that fits. *That* is
   the feature; the catalogue rows are just the input.
4. **Bongs themselves last**, priced and photographed, no spec work.

⚠️ **Do not let the parts problem stall the price problem.** Every one of those 952 rows needs a
verified price regardless of whether anyone ever records a joint size — and per doc 19, a bong sale
carried a **307.–** transaction. Wrong price on a 590.– bong is a far worse day than a missing spec.

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
