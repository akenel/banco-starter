# 09 · Shelf Intake — build the catalogue from the shelf, not from a spreadsheet

*The fastest honest way to get a real shop's stock into Banco, with the barcode that is actually
on each packet. Read [`CATALOG-IDENTITY.md`](../CATALOG-IDENTITY.md) first if you want the why —
this guide is the how.*

**Screen:** `/pos/shelf-intake` (manager) · **Time:** ~15 min per shelf section, done at the shelf

---

## The idea in one line

> Scan a shelf section, then resolve that section on the spot — batched, with nobody waiting
> behind you, and the packets still in your hands.

The trick is not doing it later. It is doing it in **batches, off the clock**, with the shelf in
front of you instead of a customer.

| | at the counter | shelf intake |
|---|---|---|
| per product | ~5 minutes | ~2 s to scan + ~15 s to bind |
| who is waiting | a customer | nobody |
| what you are doing | hunting the internet mid-sale | matching against a catalogue you already own |
| what defines the catalogue | a wholesaler's 5,000-row list | **the shelf** — what the shop actually stocks |

**Why it is fast:** 5,105 of this shop's 5,180 products are *already in the catalogue*, with price,
picture and description. Only the barcode is a fiction. So the job is not identifying products —
it is **binding** a real EAN onto a row that already exists. Two or three typed words, a glance at
a picture, one tap.

Measured, not estimated: capturing at the counter took a full day at Artemis Lucerne on
2026-07-30 and produced ~40 products in ~3.3 hours — **all of which already existed** in the
catalogue under a barcode that was never on any packet.

---

## Before you start

**One gun, set to inventory mode.** Confirmed on the Inateck BCST-35 (manual §4.6
"Inventurmodus", page 20). See [`testsheets/Scanners/README.md`](testsheets/Scanners/README.md)
for the five barcodes and the keyboard-layout trap that bites every shop once.

> ⚠️ Set the gun's keyboard layout **before** you walk the shop. A gun on US into a Swiss German
> session types `-` as `'`, which is invisible on pure-digit EANs and breaks every SKU. Twenty
> minutes of scanning is cheap to redo, but only if you notice.

---

## ⚠️ Correction from the field, 2026-07-31 — work a SHELF SECTION at a time

This guide originally said: scan the whole shop, then do the desk work later. **That is wrong for
most stock**, and the reason is worth understanding before planning an evening around it.

Angel, testing it for real: *"you could scan a few hundred but you will have no chance at the
description part... really you have to finish in small batches while you have the products."*

Searching is not the hard part — it is too easy. Typing `gizeh king size` returns **ten** catalogue
rows, every one a perfect match:

```
Gizeh King Size Slim            Gizeh King Size Slim mit Filter
Gizeh King Size Slim Super Fine Gizeh King Size Cones 3stk
Gizeh King Size Slim Pink Edition   …
```

Only the packet in your hand says which. A barcode carries no clue, and a score cannot separate ten
identical scores. **So the choosing step needs the physical product**, and a cache of 300 codes
carried back to a desk has thrown that away. You would be guessing — and a wrong guess binds a real
EAN to the wrong row, which is worse than no binding: it sends the wrong product to the till *and*
hides the right one.

**So: one shelf section at a time.** Scan 10–15 facings, resolve them standing there, move on. The
gun's offline mode still earns its place — you scan without watching a screen — but the batch must
be small enough that the products are still in front of you when you decide.

The clean physical/desk split this guide promised holds only for products with **no variants**. For
papers, filters and tips — most of a headshop — the two steps stay together.

> Want the separation back? **Photograph each packet as you scan it**, and the photo *is* the packet
> at the desk. Needs a camera on the capture device: the phone has one, the Windows tablet does not.

---

## Part 1 · The shop floor (one section at a time)

1. **Scan `Inventurmodus`.** The gun stops transmitting and starts collecting. It needs no
   Enter Setup / Save and Exit — scan that one barcode on its own.
2. **Scan ONE shelf section** — 10–15 facings. Don't think, don't check anything, don't skip an item
   because you're not sure — a code you scan twice costs nothing and a code you skip costs a
   scan miss at the till later.
3. **Scan `Anzahl der gescannten Barcodes`** into any text field and write the number down.
   This is the four seconds that catches a half-upload.

Nothing to look at, no screen, no decisions. That is the point.

---

## Part 2 · The desk (one evening)

Open **`/pos/shelf-intake`**.

### Step 1 — dump the gun

Type the count you wrote down, click into the big box, and scan **`Daten hochladen`**. The gun
types its whole cache out as keystrokes.

The screen tells you what arrived: total scans, distinct products, repeats, and anything that
wasn't code-shaped. **If the count disagrees, do not clear the cache** — click into the box and
upload again. A half-uploaded shelf looks exactly like a finished one, and you find out weeks
later when a product nobody scanned turns out to be missing.

Only once the numbers agree: scan `Daten im Cache löschen`, then `Normalmodus` to put the gun
back to till use.

### Step 2 — read the triage

Every code lands in one of two piles:

- **Already scannable** — it resolves to a product today. Nothing to do.
- **Still unknown** — the work list.

Expect roughly **15–25%** to be already known on a shop whose catalogue came from a wholesale
import. That number is measured against the live Artemis catalogue on 2026-07-31, not guessed
(an earlier guess of 60% was wrong by a factor of three, which is why it's written down).

> **"Minted" badge.** A known code sometimes matched a row whose barcode Banco *invented* rather
> than read off a packet — meaning the gun read one of our own printed labels. Fine at the till;
> it just means that row's real EAN is still missing.

### Step 3 — work the unknowns, ten at a time, WITH THE PACKETS IN FRONT OF YOU

Ten, not one, and not fifty. Angel's rule, from doing it by hand:

> *"You scan ten of them. This is what we think it is. That's correct. That's not. Now we have
> to go into the deep dive."*

Ten keeps context. One at a time means re-orienting on every single product, which is where
most of those five minutes each went.

For each code, one of three things happens:

**(a) It's already in the catalogue under the wrong barcode — this is most of the shop.**
5,105 of 5,180 products are already there; only the barcode is a fiction. **Type two or three words
off the label** (`gizeh king size`) and hit *Check catalogue*. Pick the right variant by the **bold**
words — the ones you typed are greyed out, so what's left is exactly what distinguishes the rows —
and by the picture, which you can tap to enlarge. Then **That's it**. ~15 seconds, no web search.

**Unsure which variant?** *Skip it* and come back with the packet. A wrong bind is worse than none.

**(b) It's genuinely new.** Search the EAN (there's a button), find the manufacturer's or a
retailer's page, paste the URL, click **Read**. Banco pulls the name, description, price, picture
and GTIN off that page's own structured data and suggests a category. Then **create it new**.

**(c) You can't resolve it right now.** Skip it. It stays in the list and you can undo later.

### When a code returns nothing at all

Roughly one in ten. Two things it usually means, and both are worth checking before you spend
two minutes searching:

**It's an OUTER pack.** GS1 gives each packaging level its own code, and the multipack's code is
often registered nowhere public while the single unit's is everywhere. Angel, 2026-08-02: a
3-pack of OCB Premium Slim returned nothing on `3057067785033` — and the singles inside carried
`30058569`, which resolved instantly. **Open the pack and scan what's inside.**

**It isn't shop stock.** A code that resolves nowhere is often telling you the truth: it's a
packet of batteries that wandered in from somewhere else. Skip it and move on — that is the
button working, not failing.

**The country prefix is free information**, printed in the code itself: `761…` is a Swiss
company, `30…`–`37…` French, `40…`–`44…` German, `50…` UK. It won't name the product, but it
tells you which corner of the internet to search.

### Batch size is set by the FAILURES, not the scanning

Scanning is two seconds either way. What decides the batch is how many failures you can bear to
walk back to — **because a failed lookup gives you a number and nothing else.** No name, no
photo, no shelf position. You cannot even tell which product it was.

```
30 scanned  →  ~3 fail   →  you are still standing in that aisle
300 scanned →  ~30 fail  →  a second trip, and you don't know which 30
```

So: **one shelf section, 20–30 facings, resolve every one of them, then move on.** Angel found
his two failures in under a minute — because he had not walked away yet.

**The machine never chooses.** It proposes, you judge. About half the borderline proposals are
wrong on a real catalogue, and wrong in ways no text score can catch — `Canna` vs `Cocanna`,
`Spritz` vs `Spritze`, incense papers vs rolling papers. A human spots those in a quarter of a
second; a model does not, and is confidently wrong.

> Your progress is saved in the browser after every action, so closing the tab doesn't lose the
> evening. It is saved **on that machine** though — finish on the machine you started on.

---

## When you're done

Take the gun back to the shelf and **scan ten products at the till**. Not ten you just worked on —
ten at random.

That is the only proof that counts. Tests passing is not done; a human holding a packet and
watching the right product come up is done.

---

## Why not just import a supplier list?

You can, and `05-catalog-loading.md` covers it. It gets you prices, pictures and descriptions
fast, and it is a perfectly good starting point.

What it cannot give you is **the barcode on the packet**, because most wholesalers don't publish
one. If your import invents a code to fill that column, every scan of that product will miss —
which is the single most expensive mistake in this whole system, and the reason this screen exists.

Import for the *content*. Scan the shelf for the *identity*.

---

## The three ideas worth keeping

1. **A product is not a name. It is one identity (the EAN) plus many labels.** Names are
   translated, abbreviated, and typed by tired humans. The EAN is none of those things.
2. **Never invent an identifier that already exists in the physical world.** A blank barcode is
   honest and invites the first scan to fill it. A fabricated one silently guarantees a miss.
   *(The exception: unbranded or handmade stock that genuinely has no code — mint one and
   **print the label**. It stops being a fiction the moment it exists on the packet.)*
3. **Every EAN you bind is permanent and portable.** It's true in every language, forever, and
   it is the one piece of catalogue data that cannot be scraped or bought — only scanned, by
   someone holding the packet.
