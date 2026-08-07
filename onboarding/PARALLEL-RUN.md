# 21 · The parallel run — prove it against the paper book, in the shop, on a real day

*Set 2026-08-07. Angel: "i have coded enough and it needs a real one week test running parallel
with his paper or at least one day and see if it performs."*

*He is right, and this file is the plan. It is deliberately small. The point is not a demo — it is
a **measurement**, and it is allowed to fail. If it fails we learn the thing no amount of coding
finds, which is the entire reason to do it.*

---

## ⓵ TWO QUESTIONS FOR FELIX — ask these before anything else

*Angel, 2026-08-07: "not sure what he expects .. he says 2 things i want to scan stuff and know
what i sell but at the same time does not want more admin work."*

Those two statements are not a contradiction. They are a spec: **the catalogue must never be a
prerequisite for selling.** But two things inside it are unknown, and they change the size of this
project by roughly half. Ask them with the tablet in your hand. They take five minutes.

> ### ❓ Q1 — *"When you say 'know what I sell' — do you mean turnover, or profit per item?"*
>
> **If turnover:** cost prices are irrelevant. **5,328 rows with no cost block nothing.** Delete
> that worry entirely and never mention costs to him again.
>
> **If profit:** that is a genuine sit-down with a supplier invoice, and you need to know now, not
> in October. Scope it as its own project with its own date.
>
> *Best guess from a paper-method owner: turnover and best-sellers. But it is a guess, and it is
> free to replace with a fact.*

> ### ❓ Q2 — *"If the catalogue is only ever 30% filled in, but every sale is captured and the
> top 200 sellers are clean — is that a win, or a fail?"*
>
> **If win:** the project shrinks enormously. The 79 unpriced rows stop being homework, the long
> tail stops being a debt, and the catalogue becomes a **byproduct of selling** instead of a
> precondition for it.
>
> **If fail:** you have learned before go-live that he expects complete master data, and somebody
> — not you — has to be assigned to produce it. Better to hear it now than the week after.

**Write his answers here when you have them:**

```
Q1 (turnover or profit?):  ______________________________________  date: __________

Q2 (30% catalogue — win or fail?): _______________________________  date: __________
```

---

## ⓶ Why a shadow day, and not a simulation

*Angel: "or can i do that on my own with a simulation in 20 minutes and fake it to prove it"*

**No — and the reason is written in `CLAUDE.md` in blood.**

A simulation is written by the same person, from the same assumptions, as the software. It replays
what we *think* a shop day is. On **2026-08-03** the cash box shipped with 35 unit tests, a 30-check
live API proof and a verified prod deploy — and Angel then found **seven defects in 62 minutes,
every one of them a screen, none reachable from the API.** A simulation touches no screens. It
cannot find the class of thing this run exists to find.

The unfakeable part is not arithmetic. It is:

- the customer who wants two, and one is a giveaway from the treat bowl
- the phone ringing mid-basket
- half TWINT, half cash
- the delivery arriving while a queue forms
- the packet with no barcode, at the counter, with someone waiting
- **`Zigi einzeln 1.–`** — a loose cigarette out of a pack, which has no EAN and never will

**But there IS a 20-minute thing, and it is not optional — see ⓷.** It is not proof for Felix. It
is insurance so that the real day does not die on a defect we could have caught for free.

---

## ⓷ PRE-FLIGHT — do all of this before Felix sees anything

*The day book already tells us what the day will consist of. That is the whole trick: you do not
need 5,389 rows to be right. **You need about thirty names.***

### ⓷ⓐ The ~30 names that actually make up a day

From [`19-what-actually-sells.md`](19-what-actually-sells.md), read off a month of real pages.
Every one of these must **scan** and carry a **real price** — not `999.99`, not `99.00`:

| Tier | Lines | Status |
|---|---|---|
| **1** | `Pape`/papers · `Purize`/filters/tips/screens · `Blow` (CBD joints) · **`Grips`/grinders** · `Clipper`/lighters | papers + filters scanned 08-05; **grinders scanned 08-06** |
| **2** | `Local Mary` · `Blau` (tobacco) · `Medusa`/hash · `Rolls`/`Rips` · **`Getränke`/drinks** · `Zigi`/cigarettes | ⚠️ drinks never checked · `Local Mary` not scanned |
| **big** | `Mighty` 398.– · `CBD Öl` 69–138.– · `Zigi-Maschine` 55.– · `Raffco T.2` 89.– · `Farfalla` 57.– | rare, but a wrong `Mighty` costs more than 100 packets of papers |

> **Rank 4 is the one to double-check.** Angel's read was *"I don't sell grinders very often."*
> The book flatly disagrees — `Grips` is on nearly every page, twice on some. An assumption that
> was wrong once about the shape of the day may be wrong twice.

### ⓷ⓑ The three things that have no barcode and never will

Decide these **before** the day, not at the counter with a queue:

1. **`Zigi einzeln 1.–`** — a single cigarette out of an opened pack. Needs a button or a PLU.
2. **`Getränke`** — check `Cafe & Food` (46 products) actually contains what is in the fridge.
3. **The treat bowl** — `Lolly 1.–` appears in the book beside full-price items.
   `line_item.is_giveaway` already models it; confirm a cashier can reach it **on the screen**.

### ⓷ⓒ The rehearsal — this is the 20 minutes, and it is worth it

**Ring a real day off the paper book, on the tablet, alone, before anyone watches.**

The book records complete days: **311 · 346 · 398 · 431 · 477 · 480 · 523 · 644 · 806 · 1292 ·
1325 CHF**. Pick a middling one — the **477** day — and ring its actual baskets.

- If Banco lands on **477.–**, the arithmetic is proved and the rehearsal was cheap.
- If it does not, you have found the defect **on your own time** instead of over Felix's shoulder.
- Either way you will hit three or four screens that annoy you. Fix those first. That is the point.

### ⓷ⓓ The blockers that must be closed first

- [ ] **START HERE item A** — the till guard and cashier price panel, human-tested. It sits between
      the shop and every sale and no person has touched it.
- [ ] **Cash box float** configured on a screen (it was API-only until 08-03; that was a hard FAIL).
- [ ] 🔴 **The demo realm.** A shadow day puts real transaction data on an instance whose passwords
      are in a public GitHub repo. Close it, or run the shadow day on a local instance — and
      **do not let the shadow run quietly become go-live.**

---

## ⓸ RUN 1 — the shadow day. Angel drives. Felix risks nothing.

**Design: paper stays the system of record. Banco is a silent second copy.** Felix and his staff
change *nothing* about how they work and do *no* extra typing. That is the version he will say yes
to, and it is why this must be run 1.

**How it works:** Felix rings the sale on paper exactly as he has for twenty years. Angel stands to
one side and duplicates it into Banco **as it happens — not reconstructed at closing.**

> ⚠️ **Live, not end-of-day.** Rebuilding the day from the sheet at 18:00 would prove the totals and
> hide every single interaction defect — the packet that will not scan, the price that is not there,
> the customer waiting. Those are the findings. Reconstruction erases them.

**Record four things, and nothing else:**

| # | The number | Why it is the one that matters |
|---|---|---|
| **1** | **Banco's day total vs. the paper day total** | One number at close, unambiguous, no interpretation. This is the proof. |
| **2** | **How many sales hit a product that would not scan, had no price, or was not there at all** | 🎯 **Nobody knows this number and everything depends on it.** It is the real adoption blocker, measured. |
| **3** | **Seconds per sale** | Doc 10 says *2 seconds or it is broken*. This is a many-small-baskets shop: card sales run 1.10–80.–, mostly 5–40.– |
| **4** | **Every screen where you had to stop and think** | The 62-minutes-seven-defects class. Write them down in the moment; you will not remember them. |

**Number 2 decides the project.** If it is 5% the till is ready and the catalogue fills itself from
sales. If it is 40% — which is Angel's own estimate of the shop — then no amount of software helps
and the honest next step is a scanning campaign with a person and a date, not more code.

---

## ⓹ RUN 2 — a staff member drives. Only after run 1 passes.

**Run 1 and run 2 answer different questions and must not be merged:**

- Run 1: *does Banco survive a real shop day?* — Angel drives.
- Run 2: *can a human who did not write it use it?* — Angel watches, hands in pockets, and says
  nothing for the first hour no matter how much it hurts.

**Pick the right person — this is the single highest-leverage choice in the whole plan.**

Angel's own words: *"if I could train his people for 1 hour and had someone who **wants** to use
it."* That is the real dependency, and it was named and then walked past.

> **Felix is the worst possible first user.** Twenty years of a paper method that works, he owns the
> alternative, and he has no incentive to make the new thing succeed. Handing it to him first is
> asking a skeptic to debug your software for free.
>
> **The day book names three cashiers: `Leila` · `Raphi` · `Lele`.** One of them is the answer.
> Pick whoever is youngest with a phone in their hand, and train that one person for an hour.
> **A shop adopts a till because a cashier likes it, not because an owner bought it.**

**One hour is realistic** for scan → cart → cash/TWINT → done. The hour is not for the happy path,
which is twenty minutes. It is for the four messy ones: no barcode · no price · a return · a
giveaway.

---

## ⓺ What "it performs" means — decide the pass mark BEFORE the day

*Otherwise the result is a conversation about feelings.*

| | Pass | Fail |
|---|---|---|
| Day total vs. paper | matches to the rappen | any unexplained gap |
| Sales blocked by missing catalogue data | **< 10%** | > 25% → stop coding, start scanning |
| Seconds per sale | at or under paper | slower than paper → nobody will ever adopt it |
| Screens that stopped you | ≤ 3, all cosmetic | any dead end with a customer waiting |

**Failing this is a successful run.** The failure mode to actually fear is a run so carefully staged
that it passes and teaches nothing.

---

## ⓻ Why one day, not one week

Angel floated a week. **Do one day first.** A week of shadow-typing every sale is unpayable in
attention, and day 1 tells you 80% of it — including whether a week is even survivable. If day 1
passes, run a week with a *cashier* driving (run 2), which is the version worth a week.

---

*Related: [`19-what-actually-sells.md`](19-what-actually-sells.md) (the paper book, transcribed) ·
[`18-training-manual.md`](18-training-manual.md) · [`GO-LIVE-CHECKLIST.md`](GO-LIVE-CHECKLIST.md) ·
[`10-devices-and-roles.md`](10-devices-and-roles.md) (the 2-second rule)*
