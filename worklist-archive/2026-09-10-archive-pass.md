# Archive pass — 2026-09-10

*Moved out of `WORKLIST.md` the day the alarm fired at 548 of 500. **Verbatim, nothing deleted** —
the rule since the file reached 2,307 lines on 2026-09-04 with nine closed threads still in it.*

**What moved and why:** section **ⓞ THE COUNTER VISIT**. It closed on 2026-09-10 — Angel went, worked
the till from 11:33 to 13:04 and came back with 21 screenshots and four defects. The prep prose below
did its job and no longer needs to be read every session; the geometry advice in it is still true and
still unspent (the stand was never bought, and the two sheets were never run AS sheets — he worked the
counter freehand instead, which found more).

The record of what the visit actually produced, and everything still open from it, is in
[`2026-09-10-the-counter-and-the-afternoon.html`](2026-09-10-the-counter-and-the-afternoon.html).

---

## ~~ⓞ THE COUNTER VISIT~~ — **DONE 2026-09-10, 11:33–13:04** · 21 screenshots, four defects

*He went. It found more in ninety minutes than the whole tree had in a week — see the deck.
The geometry advice below still stands and the two sheets were NOT run as sheets.*

<details><summary>the original prep, kept</summary>


*Found on a kitchen table: Angel stood the tablet up in landscape, looked down at it the way a
cashier would, and it was unreadable — and **there is no chair behind that counter**. The cheapest
instance of LESSON #1 yet: a CHF 25 stand, caught three weeks early instead of on Layla's shift.*

**The checklist is now two sheets, not prose here** — steps a person can mark PASS/ISSUE/FAIL:
[`2026-09-05-standing-where-layla-stands.html`](onboarding/testsheets/2026-09-05-standing-where-layla-stands.html)
(21 steps, no sale) then
[`2026-09-05-four-real-sales.html`](onboarding/testsheets/2026-09-05-four-real-sales.html)
(18 steps, **the one sheet where the payment button is pressed** — nothing has completed a sale on
this build; the last transaction on the box was 2026-08-21).

**Take with you:** a cheap adjustable stand (~CHF 25, *not* the real one yet), a matte anti-glare
film (~CHF 20), the gun, the folio **to leave off**, and Layla. Photograph the geometry at the
counter, then buy the weighted one (~CHF 80–300) — a light stand slides on every tap.

**The one decision that touches the code: LANDSCAPE, LOCKED.** Every geometry proof runs at
1440 × 895. Portrait moves the fold, the cart total and the keypad. Lock rotation in the OS so a
bump mid-sale cannot reflow the till in front of a customer.

→ the original prose, with the full reasoning:
[`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)

</details>



---

## Also moved on 2026-09-10 — **ⓒ5 PAM'S RUN**

*A finished run from 2026-09-04 (14 pass · 3 issue · 0 fail, 18 minutes on the tablet), whose own
header already said **THE DECK IS CLEAR**. Six days old, nothing in it is pending, and its tail was
already a list of pointers to the 2026-09-04 archive. Verbatim below, nothing deleted.*

---

## ⓒ5 PAM'S RUN — 14 pass · 3 issue · 0 fail — 2026-09-04 23:02–23:20 · **THE DECK IS CLEAR**

*18 minutes on the tablet, folio OFF, landscape, `b629 · 6cc1bb5`. Her words: A1 **"buttery — IMHO
well done"**, B1 **"imho the search works way better this way — i love it"**, B4 **"yes, top bar is
not sticky — works fine"**.*

**All five blocking items are done.** Zero fails across three sheets tonight (19+1, 21+1, 14+3 —
every issue a request or a missing test fixture, none a defect).

### The three issues, and what they actually are

**A6 · "can you find me a test item name for this"** and **A7 · "maybe you can give me some real
tests samples"** — the same ask twice, and a fair one: I wrote steps that needed a long product
name and a big result set and left her to find them. **Fixed here, from the shop's own catalogue
(5,427 active), so the next sheet can name them instead of asking:**

| type this | matches | categories it touches |
|---|---:|---:|
| `elfbar` | 244 | 6 |
| `raw` | 230 | 26 |
| `king` | 147 | 21 |
| `cbd` | 123 | 11 |
| `papers` | 24 | 6 |
| `elements` | 20 | 5 |

**For the wrapping-row step, search `elements`** — it returns *"Elements Papers - Ultra Thin
Papers - King Size Slim - Blättchen - 32 Blättchen - Sugar Gum"*, **91 characters**, the longest
active name in the shop. Runners-up if that one is ever retired: the RAW Connoisseur (90) and
*CHOC OVO Crunchy (Nouveau) 20g — Le plaisir du chocolat croustillant avec Ovomaltine* (84).

*The lesson is small and repeats: a step that says "find a product with a long name" hands the
tester my homework. **Name the sample.** Both testers hit it in the same session.*

### B2 · ~~narrow the category dropdown~~ — **DONE 2026-09-05**, `c42a207` + `234a601`

Pam, on the pinned panel: *"this is exactly why you need it — look for a term and easy search with
categories — would be good to narrow the cats where only search term is applicable so cat list is
shortened."*

Live: **`papers` → 6 shelves, `elements` → 5, `lighter` → 2**, each with the count you get when you
pick it, full 52 underneath, capped at 8.

⚠️ **The numbers that used to be in this entry were measured with `name ILIKE`, and the first
implementation was built on them.** The search's own recall reaches into `description`,
`supplier_name` and fuzzy similarity, so by that predicate `papers` touches **39** shelves and
`king` **50 of 52**. Shelves are chosen by relevance and counted by recall — see the header comment
on `/search` in `pos_router.py`.

---

- **🔎 Found while fixing something else — 2026-09-02** — non-blocking, 3 days old. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **🌙 Where we stopped — 2026-09-03** — superseded. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **🌅 This week — from 2026-09-02** — superseded. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **▶️ Start here — the state at the end of Fri 2026-08-28** — superseded. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
