# 09 · Shelf Intake — build the catalogue from the shelf, not from a spreadsheet

*The fastest honest way to get a real shop's stock into Banco, with the barcode that is actually
on each packet. Read [`CATALOG-IDENTITY.md`](../CATALOG-IDENTITY.md) first if you want the why —
this guide is the how.*

**Screen:** `/pos/shelf-intake` (manager) · **Time:** ~20 min in the shop + one evening at a desk

---

## The idea in one line

> Walk the shop scanning everything, then do the thinking afterwards — batched, at a desk,
> with nobody waiting behind you.

That is the whole trick, and it is worth stating plainly because the obvious alternative feels
more natural and is roughly ten times slower.

| | at the counter | shelf intake |
|---|---|---|
| per product | ~5 minutes | ~2 seconds scanning + ~30 s at a desk |
| who is waiting | a customer | nobody |
| what you are doing | scanning **and** identifying, at once | one, then the other |
| what defines the catalogue | a wholesaler's 5,000-row list | **the shelf** — what the shop actually stocks |

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

## Part 1 · The shop floor (~20 minutes)

1. **Scan `Inventurmodus`.** The gun stops transmitting and starts collecting. It needs no
   Enter Setup / Save and Exit — scan that one barcode on its own.
2. **Walk the shop. Scan every facing.** Don't think, don't check anything, don't skip an item
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

### Step 3 — work the unknowns, ten at a time

Ten, not one, and not fifty. Angel's rule, from doing it by hand:

> *"You scan ten of them. This is what we think it is. That's correct. That's not. Now we have
> to go into the deep dive."*

Ten keeps context. One at a time means re-orienting on every single product, which is where
most of those five minutes each went.

For each code, one of three things happens:

**(a) It's already in the catalogue under the wrong barcode.** Type roughly what it is, or paste
a product page. The screen offers candidates — tap **That's it** and the scanned EAN binds to
that product. It scans forever after. *This is the 30-second path, and it is most of the value.*

**(b) It's genuinely new.** Search the EAN (there's a button), find the manufacturer's or a
retailer's page, paste the URL, click **Read**. Banco pulls the name, description, price, picture
and GTIN off that page's own structured data and suggests a category. Then **create it new**.

**(c) You can't resolve it right now.** Skip it. It stays in the list and you can undo later.

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
