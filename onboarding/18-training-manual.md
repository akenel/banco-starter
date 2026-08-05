# 18 · The training manual — how the shop runs on Banco

*Written 2026-08-05. The rest of this kit explains **Banco**. This explains **the shop's day** — who
does what, when, standing where, and how you know a new person can actually do it.*

> **Who this is for:** a new cashier on day one, a manager planning a week, and the owner deciding
> whether the person in front of them is ready to be left alone with the till.

---

## 1 · The two jobs, and why they must never be the same screen

Everything else falls out of this. From [`10-devices-and-roles.md`](10-devices-and-roles.md):

> **Setup is not selling.**

| | **Setup** (owner / manager) | **Selling** (cashier) |
|---|---|---|
| When | evenings, before the shop relies on it | all day, customer waiting |
| Looks like | scan the shelf → find the product → judge it → set a price | scan → it rings up |
| Time per item | 30 s – 5 min, and that is fine | **2 seconds, or it is broken** |
| Decisions | many, and they need a human | **none** |

**A cashier must never be asked "is it one of these?" mid-sale.** If the till asks that, the
catalogue work was not finished — the answer is more setup, not a faster cashier.

---

## 2 · The people and what they may do

| Role | Who | May do | May **not** |
|---|---|---|---|
| **Cashier** | Leandra, Roger, Nathan | sell · refund · X-report · open and close a shift · pay in / pay out with a named reason | change prices · edit the catalogue · force-close |
| **Manager** | Angel, Felix | everything a cashier can, plus catalogue, prices, shelf intake, labels, settings | — |
| **Owner** | Felix | all of it, plus the decisions: price policy, tolerance, what gets stocked | — |

> ⚠️ **The gap we know about.** A cashier cannot fix a wrong price mid-sale, and signing out to a
> manager **loses the cart**. Today the answer is: *finish the sale honestly, note it, and tell a
> manager.* Do not invent a product at the till — that is how a one-word-name row with no category
> or cost gets into the catalogue. Filed in `WORKLIST.md`.

---

## 3 · The counter — where everything lives

The counter is a **charging station that happens to sell things.** See
[`16-bom-artemis-luzern.md`](16-bom-artemis-luzern.md).

```
        ┌──────────────────────── THE COUNTER ────────────────────────┐
        │                                                             │
        │   [ TABLET 1 ]        [ GUN STAND ]         [ LABELLER ]    │
        │    on charge          screwed down           QL-820NWB      │
        │    the till         Inateck │ Netum          on charge      │
        │                                                             │
        │   ══════════ POWER BAR · 5 sockets · cable slack ══════════ │
        └─────────────────────────────────────────────────────────────┘

   ROAMING:  [ TABLET 2 ] + [ the other gun ]  → out on the shop floor
   BACK:     [ HP laptop ] → reports, catalogue, photos
   POCKET:   [ phone ] → backup, hotspot, and the only good camera
```

**Rules that keep it working:**

- **Both guns and both tablets live on charge between uses.** Nothing is off-duty waiting to be needed.
- **The stand is screwed down** — a gun with no home gets lost.
- **Label the two gun cables.** They are not interchangeable.
- **Either tablet and either gun covers the other.** That is the whole point of buying two.

---

## 4 · The day

### 🌅 Opening — 5 minutes, every morning

1. **Everything on.** Tablet, labeller, guns off charge.
2. **`/pos/hardware` — scan a hyphenated test code.** Green means the gun and *this* machine agree
   about the keyboard. **Do this per machine, every time a gun moves.** A plain number code proves
   nothing — digits sit in the same place on every layout; the hyphen is what catches a mismatch.
3. **Open the shift.** Count the float **before** looking at what Banco expects.
   > 🔴 **Count first, look second.** If you read the expected figure first you will type it back,
   > and the count stops being a check at all.
4. Mismatch? **Say so in the note.** An explained difference is not a problem; an unexplained one
   costs somebody an evening.

### ☀️ Trading

**The normal sale is: scan → scan → take the money.** That is the whole job.

| Situation | What the cashier does |
|---|---|
| It scans and rings up | nothing — that is the system working |
| **Age-restricted item** | the screen says so — **check ID**, it is the law, not a suggestion |
| Cash total looks 1–2 rappen off | **correct.** Cash rounds to 5 rappen because the coins exist; cards do not round |
| Customer wants a deal | **Felix does not discount.** Hold the price, give a **free treat** — ring it at 0.00 |
| **It does not scan** | try the packet's other barcode, or the singles inside a multipack. Still nothing → sell it by name and **tell a manager** |
| Price is wrong | finish honestly, **note it**, tell a manager. Do not invent a product |
| Customer returns something | refund against the original sale |

### 🔄 Shift change

**One box, everybody sells into it.** The drawer belongs to the shop, not to a person — so the
report covers everyone who sold, not just the one closing.

1. Outgoing cashier: **count, then close.**
2. Incoming cashier: **open on what was just counted.**
3. Difference? **Note it at the open** — that is the moment it is cheap to explain.

### 🌙 Closing

1. **Count the drawer before opening the close screen.**
2. Enter it. Short or over, **write the note**.
3. **Z-report** — the day's story: sales, refunds, treats, money in, money out.
4. **Whatever you reconcile to becomes tomorrow's expected.** Leave it honest.
5. Money to the safe: record it as a **paid-out with a named reason**. *"To the safe"* is a
   complete reason — no sentence needed after it.

---

## 5 · The week

| When | What | Who | Where |
|---|---|---|---|
| **Every day** | open · trade · shift changes · close | cashier | counter |
| **Every day** | glance at the Z-report | Felix | back office |
| **Weekly** | shelf intake — **one section**, packets in hand | manager | shop floor |
| **Weekly** | print labels for anything new or repriced | manager | counter |
| **Weekly** | work the unknown barcodes the till collected | manager | back office |
| **Monthly** | check the backup restored — not that it ran, that it **came back** | Angel | back office |
| **Monthly** | reprice review, slow movers, dead stock | Felix | back office |

### Shelf intake — the weekly rhythm that actually works

**One section at a time. Not three hundred items in a batch.**

> **Batch size is set by the failures, not the scanning.** A failed lookup hands you a number and
> nothing else — no name, no photo, no shelf position — so you cannot even tell which product it
> was. At a 90% hit rate: **30 scanned = 3 to re-find while you are still in that aisle. 300 scanned
> = 30, and a second trip.**

1. **Netum** gun into `Inventurmodus` (its printed booklet — keep it with the gun).
2. Scan **one shelf section**, 10–15 facings. ~2 s each, no thinking.
3. Scan `Anzahl der gescannten Barcodes`, check the count.
4. `/pos/shelf-intake` → type the count → scan `Daten hochladen`.
5. Counts agree → `Daten im Cache löschen`, then `Normalmodus`.
6. **Work the rows with the packets still in front of you.**
   - Type two or three words off the label — most of the shop is already in the catalogue and only
     its barcode is missing. ~15 seconds.
   - Only if nothing matches, find it on the web. ~1 minute.
   - **Unsure? Skip it. A wrong bind is worse than none.**
7. **Then go back and re-scan the same products with the packets in hand.**
   > 🔴 **A wrong bind looks exactly like a right one — only a re-scan can tell them apart.** In the
   > database both are a barcode pointing at a product: nothing missing, nothing erroring, no report
   > flagging it. This is what caught Cannazym bound to Cannaboost — same brand, same bottle,
   > adjacent barcodes, CHF 12 against CHF 35.

---

## 6 · When it goes wrong

Full ladder in [`14-when-it-goes-down.md`](14-when-it-goes-down.md). What a cashier needs:

| What broke | Can we sell? | Do this |
|---|---|---|
| A gun or tablet dies | ✅ | **Take the spare.** The cart does **not** transfer — re-scan the basket |
| **The labeller dies** | ✅ | **Keep selling.** Labels are shelf prep, **not part of a sale** |
| Labeller stuck | ✅ | Switch it off and on. First label after a wake takes **25–30 s** — that is calibration, not a fault |
| Shop Wi-Fi drops | ✅ | **One tap** — *Switch to Hotspot*. It will **not** switch itself, in either direction |
| All internet | ⚠️ **cash only** | Cards need the network. **Cash-only sign.** Scan barcodes into a text file — **never write EANs by hand** |
| Power | ⚠️ cash only | Tablets run on battery; the printer and card terminal do not |

> **Tell staff rung 2 in advance**, or someone will close the till over a printer. **A dead labeller
> does not stop a single sale.**

**Coming back:** tap back to shop Wi-Fi (it does not return by itself) → key in the scanned list →
use the cash-box note to say why the drawer is high → *then* print the labels you skipped.

---

## 7 · Training a new cashier — and testing them

**Half a day. Nobody is left alone with the till until step 5 is signed.**

### Step 1 · Watch (30 min)
Stand beside someone doing real sales. Say nothing. Watch how fast a normal sale is.

### Step 2 · The five things that are not obvious (30 min)
1. **Cash rounds to 5 rappen, cards do not.** The till is not wrong.
2. **Age-restricted means check ID.** The screen tells you; the law means it.
3. **Count the drawer before you look at what Banco expects.**
4. **A dead labeller does not stop selling.**
5. **Never invent a product.** Sell it, note it, tell a manager.

### Step 3 · Supervised selling (2 h)
Real customers, manager beside them. The manager watches for: does the gun get used, or is the
cashier typing? Does an age-restricted item get an ID check *every* time?

### Step 4 · The scripted day (1 h) — do this with the shop closed
The trainee does the whole thing alone, watched:

- [ ] Hardware check with a **hyphenated** code
- [ ] Open a shift, counting **before** looking
- [ ] A cash sale with change
- [ ] A card sale
- [ ] **A cash sale with an uneven total** — 1 × Rips at 1.67 → **1.65**. Ask them why
- [ ] An **age-restricted** item — do they check ID unprompted?
- [ ] An item that **does not scan** — do they invent it, or note it?
- [ ] A customer wanting a deal — do they discount, or **reach for the treat bowl**?
- [ ] A **refund**
- [ ] A **paid-out to the safe** with a named reason
- [ ] Close the shift **short by 10**, and write the note
- [ ] Correct it and close honestly
- [ ] **The Wi-Fi drops** (turn it off) — do they find the one-tap switch?

### Step 5 · Sign it off

> **Trainee:** ______________________  **Date:** ____________
> **Signed off by:** ______________________
>
> This person opened a shift, sold, refunded, took money out, closed short, explained it, and closed
> honestly — **watched, and without prompting.**

**Machine-green is not trained.** A person who has read this document has not been trained; a person
who has *done* step 4 in front of somebody has.

---

## 8 · "What's in it for me?" — the honest answer for a cashier

*Angel, 2026-08-05: "Felix probably [understands], and you and I do, but Rafi and Leila and Leandra
not so much. **So what's in it for them?**"*

**The right question, and it deserves a straight answer rather than a pitch.** Most tills make the
cashier's day worse: the owner gets reports, the cashier gets extra steps. If that is what this is,
they will be right to resist it.

### What they do today — counted off the real day book, 5 August 2026

| | Per day |
|---|---|
| Sales written out by hand (name + price) | **~28 cash + ~21 card ≈ 50** |
| Card slips stapled into the book | ~21 |
| Coin and note denominations counted and added | every close |
| Day totalled by hand, cash and card separately | every close |

**That is the job Banco removes.** Not "improves" — removes.

### The four things that get better, in their order of interest

**1. You stop writing.** Scan, take the money, next customer. **No name, no price, no column, no
adding up.** Fifty handwritten lines a day become zero. This is the whole pitch and everything else
is a footnote.

**2. You stop being on the hook for the drawer.** Today a short till is somebody's word against the
arithmetic. Banco records **every** sale with who rang it and when, and the box belongs to the shop,
so the report and the drawer are checked against each other, not against a person's memory. **The
count protects you.** And when something genuinely does not match, there is a note field to say why —
an explained difference is not a problem.

**3. You stop hunting for a price.** No sticker to find, no colleague to ask, no guessing on a
product you have not seen before. It scans and the price is there. *(This is only true once the
catalogue is done — which is what the shelf work is for. Say so honestly; it will not all work on
day one.)*

**4. Closing gets shorter.** X-report mid-shift to see where you are, Z-report at the end. **No
hand-totalling, no adding coin columns twice.**

### What honestly gets worse — say this too

- **There is a new thing to learn.** Half a day, and §7 is how.
- **Every sale is now attributed to whoever rang it.** That is a real change and it is fair to name
  it. The purpose is that the drawer stops being a group accusation — but it does mean individual
  mistakes are visible. **Better to say this out loud than to let someone discover it.**

### The line that lands

> **"You never write a sale down again, and if the till is short, the system can show it wasn't
> you."**

**Do not sell them the reporting.** *"We'll finally know which papers to reorder"* is a real benefit
and it is **Felix's** benefit, not theirs. A cashier does not care which paper sells best. They care
that the queue moves and that nobody blames them at closing time.

---

## 9 · The five things worth putting on the wall

1. **Count the drawer before you look at what Banco expects.**
2. **Cash rounds to 5 rappen. Cards do not. The till is right.**
3. **A dead labeller does not stop a single sale.**
4. **Never invent a product. Sell it, note it, tell a manager.**
5. **Unsure about a barcode? Skip it. A wrong bind is worse than none.**
