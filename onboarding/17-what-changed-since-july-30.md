# 17 · What changed since 30 July — the report for Felix

*Six days, 151 commits, 91 files. Written 2026-08-05 for the shop owner, not the developer: what is
different in the shop, what he has to decide, and what is still not finished.*

---

## The one-paragraph version

> Banco now **counts cash the way a shop actually does** — one drawer everyone sells into, totals
> that round to 5 rappen so they can be handed over, and a shift report that matches the money in
> the box. The **catalogue got the tools to clean itself up**: duplicates can be merged from the
> screen where you actually see them, and 5,111 products can be filled in from their own web pages
> without anyone clicking. **A scrapped Windows tablet is now a second till** that prints labels
> over Bluetooth. And an **18+ classification bug that mislabelled tobacco and CBD** was found and
> fixed.

---

## 💰 The money — the biggest block of work

### The cash box belongs to the shop, not to a cashier

Before: each cashier had their *own* box, and the shift report only showed that cashier's sales.
Two people on one drawer produced numbers that could not be reconciled.

Now: **one box, everybody sells into it.** The report shows the whole drawer.

- **X-report button** — read the drawer mid-shift without closing it
- **Named cash reasons** — *to the safe*, *supplier paid*, *petty cash* — instead of a free-text box
  that demanded a sentence the dropdown had already said
- **Opening float (baseline)** configurable **on a screen** — it existed on every layer a test can
  reach and on no screen, so it could only be set with `curl`, which means never
- **Force-close** now has a way in for a human. It used to be an endpoint that had to be run with
  `psql` on the night it was needed.

### Cash totals round to 5 rappen — and nothing else does

Switzerland has no 1- and 2-rappen coins. A CHF 12.47 cash total is not payable. Cash now rounds to
the nearest 5 rappen; **card and TWINT do not**, because only coins have the constraint. Rounding is
physics, not a discount — and the discount itself rounds first, so the ticket matches to the rappen.

### Seven defects a human found that the tests could not

Angel spent 62 minutes on the tablet after the cash box shipped with 35 unit tests and a 30-check
live proof. **Every one of the seven was a screen.** The two worst:

- The till screen would have **blocked the shop from opening** — the new refusals were dead ends
  with no way forward
- A green **"✅ Balanced within tolerance"** rendered over a box **nobody had counted**

Also fixed: a **CHF 500 skim to the safe that silently never saved** (the error appeared at the top
of a page the cashier had scrolled past), and a shift report that **totalled 2 transactions while
the log underneath listed 1** — one stale filter, twelve hundred lines from its twin.

### Reports agreed to disagree about "today"

`/transactions` and the reports were reading UTC against shop time, so late-evening sales could land
on the wrong day. Fixed. *(A related question — whether a sale belongs to the minute the cart opened
or the minute it was paid — is written down and still needs a decision.)*

---

## 🏷️ The catalogue — from "mostly right" to "fixable"

### Duplicates can now be merged where you can see them

`Canna Cannazym 1L` existed twice: **CHF 43.90** and **CHF 21.00**. The merge tool was built,
tested, correct — and reachable from exactly one place: a shelf-intake card whose barcode was still
unknown. Bind the barcode, which is the whole point of shelf intake, and the button vanished.

Now: **any product → Tap for details → 🔗 Duplicate of…** Both rows side by side, swap which one
survives, *"Show me what would happen"* before anything changes.

It also says the two things out loud that the Cannazym case taught: **merging does not resolve the
price**, and **a 2× price gap on the same name usually means two different products, not a typo.**

### 5,111 products can fill themselves in

Every product carries the address of its own web page, and those pages publish the spec table and
the retail price ladder. The enricher reads them — **no human, no clicking**, about 90 minutes
unattended. It refuses any "quantity break" that would cost more than buying one, and lists every
refusal so a human can check it.

### Shelf intake — the gun's offline cache becomes a catalogue

Scan a shelf section with the gun in store mode, upload the batch, and work the rows **with the
packets still in front of you**. Plus: re-scan a packet you already sold and finish it while holding
it; paste a product URL and get its facts including the EAN; clone a product into its next variant.

### The catalogue grew a `brand` field

The field it never had. *Canna* is not *Cocanna* — duplicate matching now knows the difference.

### Eight ways a correct answer was being thrown away

A run of bugs where the right row was in the database and something between the query and the screen
discarded it: HTML entities left encoded, `pc.` vs `Stk.`, `KingSize` losing by exactly 0.000, a
400 KB fetch cap on a 1.4 MB page, a tier scraper that **only spoke German and reported zero without
complaining**. Every one failed silently and looked like *"this source has no data"*.

---

## ⚖️ Compliance — the 18+ fix

The age-gate classifier depended on a **typo in a product title**, and read only titles — so a CBD
product with a funky brand name went ungated. It now reads descriptions too, and
`reclass-age-gate.py` fixes the rows the code change cannot reach.

The dry run also caught **over-gating**: accessories are not the substance, and gating a rolling
paper because it sits near tobacco is its own kind of wrong.

**Catalog Health** said *1%* about a catalogue that is **99% ready**, and *"Uncategorized: 0"* while
hiding 78 products in Unsorted and Other. Both were the same bug shape — a page-scoped number dressed
up as a total. Every stat strip in the app was swept for it.

---

## 🖥️ Hardware — a scrapped tablet became a till

Felix handed over a Windows 10 ThinkPad X1 tablet to be scrapped. In one evening it became a Banco
till: Debian, Banco full-screen with no browser visible, scanner gun working, and **shelf labels
printing over Bluetooth** — which matters because the tablet has one USB port and the gun needs it.

- **Hardware Check** — a five-second gun test on every till, because a gun and a machine can disagree
  about the keyboard layout and a scan silently comes out wrong
- **Two guns, two tablets**, everything charging at the counter. Either gun and either tablet covers
  the other.
- Total hardware for a two-till shop: **under CHF 500** — see
  [`16-bom-artemis-luzern.md`](16-bom-artemis-luzern.md)

---

## ❓ What Felix needs to decide

1. **The Cannazym** — CHF 43.90 and CHF 21.00, same name. One has no barcode, so nothing in the
   database can say what it physically is. **Only the bottles know.** This unblocks ~40 duplicates.
2. **Which paid-out reasons Artemis actually uses** — safe, supplier, petty cash, wages?
3. **The cash tolerance** — ±0.05 (one coin) is now possible. Tight, but it is as tight as physical
   cash allows.
4. **The German cash-box wording** — `Kasse` and `Kassensturz` are confirmed by a native speaker; the
   rest has never been read by one.

---

## ⚠️ What is NOT finished

- 🔴 **Prod authenticates against the DEMO realm**, whose users and passwords are in a **public
  GitHub repo**. **This must change before the shop trades on it.** Highest-priority item on the list.
- The **merge screen has never been used on a real pair** by a human.
- The **two bulk catalogue scripts have not been run on prod** — local dev has 6 products, prod has
  5,173.
- **Nobody is watching prod.** If it goes down at 03:00, we find out when Felix phones.
- **The backup has never been restored.** It exists and runs; nothing has ever come back.
- The **transactions PDF export stops after page one** (the CSV is fine).
- ~4,800 catalogue items are **not validated** — deliberately. See the 300-hottest decision in
  [`16`](16-bom-artemis-luzern.md).
