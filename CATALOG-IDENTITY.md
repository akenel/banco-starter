# Catalog identity — what actually names a product

*Written 2026-07-30, after a full day capturing stock at Artemis Lucerne. Every number here was
measured against the live catalog, not estimated.*

---

## The one-line version

> **A product is not a name. A product is one identity plus many labels.**
>
> The identity is the EAN on the packet. Everything else — German title, English title, the
> Swiss hybrid the shop actually says — is a *label*, and there are always several.

Banco got this backwards, and it cost a shop day.

---

## What went wrong, in numbers

The 2026-07-07 import created 5,111 products from Tamar. Tamar publishes **no EAN**, so Banco
**invented** one for each:

| | count |
|---|---|
| Active products | 5,178 |
| …carrying a **minted** `2xxxxxxxxxxxx` code that exists on no packet | **5,105** |
| …carrying a real manufacturer EAN | 67 |
| …with no barcode at all | 6 |

Every other field was excellent — **100%** had a price, **99%** an image, **99%** a real category,
**96%** a description. One fabricated column made the whole thing unusable at a till: roughly
**half of all scans found nothing**, and the operator then rebuilt a product that was already
there. ~40 products, ~3.3 hours, all of them duplicates.

**There is no bulk fix, and this was verified rather than assumed:** Tamar's API carries no EAN
field; the shop's own site (artemisluzern.ch) serves 83 KB product pages with zero structured
data and no GTIN; free barcode databases resolve barcode → product, the wrong direction. The
codes exist only on the physical packets.

---

## Why names can never be the key

Swiss retail titles are roughly **80% English with German sprinkled in** — `mit`, `weiss`,
`Stk.` — while the packet itself is usually the manufacturer's international English. So the
same product legitimately has several names and none is authoritative:

```
on the packet     Blow Pre-built CBD Joint Pure "V1" 1 pc. black
in the wholesaler Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz
trigram similarity 0.417   → under the 0.5 dedup guard → duplicate created
```

`schwarz` ≠ `black`. `Stk.` ≠ `pc.` And this is not a Swiss quirk to be patched around — **every
country will do its own version of it.** A universal catalog cannot be keyed on a string that
changes at the border.

We shipped a DE↔EN normalisation dictionary for the dedup guard (0.417 → 0.857, folded forms
identical). It works, and it is a **patch on the wrong layer**: it makes one name look like
another. The right answer is to stop having *one* name.

---

## The three rules

### 1. Never mint an identifier that **already exists** in the physical world

A blank barcode is **honest** — it says "unknown", and it invites the first scan to fill it.
A fabricated one is a **trap**: it claims to be known, silently guarantees a miss, and there is
no way to tell it from a real code without inspecting the prefix.

If the source has no EAN, leave it null. `products.barcode_is_internal` already exists to mark
the difference.

**The exception — and it is the whole point of the label printer.** Roughly **30%** of the shop
is handmade or unbranded stock that carries no barcode at all: it never had one and never will.
For those, minting a code is **correct**, because we then *print it and stick it on the packet*.
The code stops being a fiction the moment it exists physically.

```
product HAS an EAN  →  minting is a LIE      (the real code is on the packet; yours guarantees a miss)
product has NONE    →  minting is the FIX    (print the label, and now it scans forever)
```

Same operation, opposite meaning. The test is not "does the row have a barcode" — it is
**"does this thing carry a code in the real world?"**

### 2. Names are labels, plural, and none of them wins

Store every name a product is known by — supplier German, packet English, whatever the counter
calls it — and **search across all of them**. Stop trying to elect a canonical title; the
question "what is this product really called?" has no answer and asking it wastes days.

### 3. The package is the source of truth

It carries both the EAN and the true international name. So capture should be *photograph the
packet*, not *type what you think it is called*. Everything else — description, category,
translations — can be filled in later, or by someone else, or never.

---

## The capture decision tree

Angel's rules, from a full day doing it by hand. Read top to bottom; **stop at the first match.**

```
Scan the packet
│
├─ it scans ──────────────► in the catalog?  ── yes ─► done. nothing to do.
│                                            └─ no ──► look it up BY EAN (§ below)
│
├─ it has a barcode but WON'T READ ─► TYPE the digits in. Get a magnifying glass.
│                                     Then print a label with that EAN and stick it on,
│                                     so it is never unreadable again.
│
└─ no barcode at all ─────► create it by hand, mint a code, PRINT the label.
                            (~30% of the shop. This is rule 1's exception.)
```

### Never fall back to a name search while an EAN exists

This is the rule that saves the most time, and it is easy to break under pressure.

> *"If it has a barcode, it's better to put the barcode number in and get the magnifying glass and
> type it in — before going and searching the wrong way with the name."* — Angel

A name is ambiguous, translated, and typed by a tired human. **The EAN is none of those things.**
The moment you abandon it for a name search you have thrown away the only unambiguous key you had,
and you are now guessing between `Gizeh King Size Slim + Tips` and `Gizeh King Size Slim mit
Aktivkohlefilter` — which are different products.

Seen for real: a Biobizz Cal-Mag whose barcode would not read. Typing the digits found it. Hunting
by name would not have.

### An EAN means the product is already described somewhere

> *"If it has an EAN number, there's no point in making the product out. There's gonna be a nice
> picture or description somewhere on the internet, guaranteed."* — Angel

A product with an EAN has been photographed, described and listed by somebody — the manufacturer,
a retailer, a marketplace. **Authoring it from scratch is redundant work.** The job is to *find*
the record, not to *write* one:

1. Look the EAN up in our own catalog first — including under a minted barcode, by name.
2. Then search the web for the EAN. It resolves ~9 times in 10.
3. The human picks the right result in 5–30 seconds (the machine must not choose — see below).
4. `POST /catalog/page-facts` reads title, description, image, price and GTIN off that page.

Only when *all* of that fails does anyone photograph a packet and type a description.

**Which is why the minted barcodes are the whole problem — stated precisely, because the loose
version is wrong in two ways:**

Nothing was *replaced*. The real EANs were never in Banco to begin with — Tamar does not publish
them, so the import found a **blank** and, instead of leaving it blank, **invented a number**.

That is worse than losing data. A blank says *"we don't know this product's code"*, which is true
and fixable by the first scan. An invented code says *"we know it, and here it is"* — which is
false, and indistinguishable from a real one without inspecting the prefix.

And it is not true that every product has an EAN: **roughly 30% of the shop is handmade or
unbranded and has none**, which is exactly the case rule 1's exception covers.

So, accurately:

> For the branded stock that **does** carry an EAN on the packet, we wrote **5,105 invented codes
> into a field that should have stayed empty** — and every one of them guarantees a scan miss for
> a product whose real code was findable all along.

---

## The architecture already supports this

This is the part worth knowing: **no rewrite is needed.** The tables exist and are correct.

| Table | Models | Rows today |
|---|---|---|
| `product_barcodes` | many codes per product ("scan once, known forever") | **6** |
| `product_translations` | many names per product, per language, with provenance | **41** (25 products) |

They are simply **empty and unsearched**. The catalog search queries `name`, `sku`, `barcode`,
`supplier_name` and `description` — and **neither of these tables**. The model was designed for
exactly this problem and then bypassed by an import that flattened everything into one name and
one invented code.

---

## Why this is the product, not a chore

The scraped catalog is **not** a moat. Anyone can scrape a wholesaler.

The **EAN → product binding** is. It can only be created by a human holding the packet and
scanning it — and once created it is true everywhere, forever, in every language. It is the one
piece of data that cannot be bought or generated.

And it compounds. Shop #1 binds `7640183261763` → *Blow Pure Diesel*. Shops #2–#50 get it free.
Every shop that joins makes the database better for the shops already in it.

Which reframes the 59 EANs captured by hand on 2026-07-30. That was not data entry. **It was the
first deposits into the asset** — 59 products no other Swiss headshop ever has to identify again.

---

## What follows, in order

1. **Scan miss offers catalog matches; one tap binds the EAN.** Turns ~5 minutes of rebuilding a
   product into ~30 seconds of completing one. Everything it needs is already built — the
   cross-language match, the alias table, and search ranking that puts the right product at
   rank 1 — it merely runs on the *create* screen instead of the *scan-miss* screen.
2. **Search across `product_translations`**, so an English packet name becomes findable the
   moment anyone records it.
3. **Stop minting.** Blank the 5,105 fakes, or at minimum set `barcode_is_internal` so a
   known-unknown is distinguishable from a real code. One `UPDATE`.

None of it is a rewrite. The design was right; the data was filled in wrong.

---

## The lesson, stated plainly

> **"The data is good" and "the data is usable" are different claims.**

Hours went into proving the search worked — and it did, ranking the right product #1. But the
operator was not searching. He was **scanning**, and a scan cannot fall back to a name. Answer
the job the person is actually doing, not the one that is easy to measure.
