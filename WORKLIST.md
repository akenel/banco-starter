# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short — and it has now been cut back three times.** 1,734 lines on
> 2026-08-13, **1,201 on 2026-08-27**, and **2,307 on 2026-09-04** — the biggest yet, grown in a
> single week of shipping. Every pass was verified line-for-line and **nothing was deleted**:
> [`2026-08-27`](worklist-archive/2026-08-27-archive-pass.md) ·
> [`2026-09-04`](worklist-archive/2026-09-04-archive-pass.md) (1,730 lines out, 0 lost).
> **The rule is 500 lines, and since 2026-09-05 it has an alarm** — `python3 scripts/worklist-check.py`,
> run as step 4 of SESSION START. The 150 was set before item ⓪ existed and 280 was never met either;
> a measurement that changes what the shop does next earns its space, and 500 is honestly what this
> file needs to hold. The trigger is what matters, not the number:
> **when a thread closes, it moves the same day — and its header gets marked in the same commit,
> because the marked header is the only thing the alarm can see.** Growing back to four figures is what happens when
> "I'll archive it later" is the plan. When an item is finished it goes to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread grows
> a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-09-05 morning — the worklist alarm is in and runs at SESSION START.
Before that: **the blocking deck is clear** — five items in, three UAT sheets run on the real
tablet, zero fails. Live on the shop: `b629 · 6cc1bb5`.*

---

## 🌙 CLOSE OF 2026-09-04, ~23:30 — READ THIS FIRST

**Live on the shop: `b629 · 6cc1bb5`.** Reload the tablet TWICE after any deploy — the first load
activates the new service worker, the second serves from it.

*What went in that night — four fixes, five suites, three sheets, 54 pass · 5 issue · 0 fail —
moved to [`worklist-archive/2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md).*

### Pick up here, in this order

0. ~~**Build `scripts/worklist-check.py`**~~ — **DONE**, 2026-09-05 morning. Runs as step 4 of
   SESSION START and says the count out loud in the first reply of every session. Over **500 lines**
   *or* more than **two** finished threads still sitting here → **ARCHIVE PASS DUE**, and it names
   what to move and the three longest sections. Watched go red on three cases: the real 2,307-line
   file from before last night's pass, a 13-line file with three finished threads in it, and the
   boundary — 500 quiet, 501 loud. ⚠️ **It can only see what the HEADER says**, so the convention it
   depends on now sits in `CLAUDE.md`: *when you close a thread, mark its header in the same commit
   as the fix.* Last night nine threads closed and two headers said so.

1. ~~**② The keyboard buries the search results**~~ — **FIXED and confirmed on the tablet**,
   2026-09-05 10:34, `a615f81` + `987624d`, live as **`b644`**. The re-run was never needed: it
   reproduced in a browser at 1440×895 with touch on, which is what makes Banco's own pad appear.
   Measured on `b629` before touching anything — pad lid y=651, the result row 522..680, **zero
   whole rows above the keyboard**, and Angel's own 10:23 screenshot was worse than the report:
   with a name long enough to wrap (`CBD Joint Natural Rebel "Lemon Skunk" Pure 1stk`) the **price
   was not on the screen at all**. Two faults: `data-row-snap` knew the stylesheet's cap and not
   the keyboard's lid, and the pad's "is the field visible" check had grown field → field+warning
   and stopped there — a search box's reason to exist is the list under it (LESSON #12, sixth
   turn). `prove-the-pad-does-not-bury-the-answer.js` **21 checks**, both halves watched going red.
   Angel on the tablet at 10:34, as pam, folio off: name, SKU and **CHF 5.90** all above the keys.
   **Sheet not run and probably not needed** —
   [`2026-09-05-the-keyboard-and-the-answer.html`](onboarding/testsheets/2026-09-05-the-keyboard-and-the-answer.html)
   exists if a second pair of eyes is wanted; the screen was confirmed before it was written.
   ⚠️ **One guard in there is UNEXERCISED**: the clamp that stops the search box being scrolled off
   the top while reaching for a tall row. No fixture makes it bind (four-line names at 1440×895 and
   1440×620 both leave the field on screen). It is a rail, not a proven fix, and the code says so.
   **Decided, 2026-09-05, Angel: ONE row above the keyboard for now.** Three is possible but costs
   the Barcode / Search / New item buttons off the top of the screen while typing. Revisit only if
   it feels too few at a real counter — a question for the visit (item 4), not for a guess here.

2. **Pam's category-dropdown request** — ⓒ5 below. The shop has **52 active categories** and the
   picker lists all of them; a search for `papers` touches **6**. Continues ⓚ (archived), which
   grouped them into sections; this narrows them to the ones the search actually hit.
3. **One `--push` of `scripts/tablet-lockdown.sh` from a REAL terminal.** Not urgent, not risky:
   it deletes the leftover `/usr/local/bin/banco-kiosk`, `banco-kiosk.desktop` ×2 and
   `/etc/default/banco-kiosk` that the 00:12 experiment wrote. The tablet is already safe — a
   user-level override neutralises the autostart and `banco-till.service` owns the screen again —
   this is tidying, not a fix.
4. **The counter visit** — ⓞ below. Everything this week was proved in a flat.
   **And the window-drag bug is still open**, with the obvious answer now ruled out in writing:
   `--kiosk` HIDES GNOME's bar, which takes the battery indicator with it, which is why people reach
   for the top-right corner and drag. Kiosk is the cause of Layla's symptom, not the cure — it is
   written in `banco-till.service` on the tablet and I overrode it at 00:12 and put the machine in a
   **48-restart loop**. See `onboarding/21-supported-hardware.md`, which now carries the reasoning.
   Next thing to try, **on the machine before it goes in any script**: a GNOME window rule that keeps
   it maximised, or an undecorated window from the compositor rather than from Chromium.
5. **⚠️ ESTABLISH ONE FACT BEFORE THE FELIX MEETING: does the shop have a Worldline terminal at the
   counter TODAY, or does it arrive with go-live?** It decides the payment-button question below —
   if the terminal is already there its settlement IS the card breakdown; if not, the paper
   breakdown is the only one they have. Ask it before deciding anything.
6. **The Felix conversation — four decisions that are HIS, written up, none agreed yet.**
   [`onboarding/the-felix-conversation.html`](onboarding/the-felix-conversation.html): the payment
   buttons (**Cash · Card · TWINT**, plus an ask-card-type setting so he can flip it himself),
   Worldline as **Phase 2** with the reasoning and the script, split tender parked, and the trial
   terms — **FAIL = free defect · ISSUE = quoted change**, agreed BEFORE the trial starts. Also the
   two asks worth more than they cost: one day's Banana CSV through his Treuhänder, and his real
   chart-of-accounts codes.
7. **The receipt QR — spec written, not built.**
   [`onboarding/receipt-qr-spec.html`](onboarding/receipt-qr-spec.html). Every receipt fetches its QR
   from **`api.qrserver.com`** and points at `/join` → La Piazza. It should be drawn by Banco and
   point at the shop's own site from `store_settings.website`. The renderer already exists —
   `_qr_data_uri()`, server-side, measured to 10mm against both guns — so this wires three built
   things together and adds no component. **Not blocking**, but it prints on every receipt from day
   one, and the failure mode is a broken image box exactly when the wifi is already down.
   ⚠️ **One decision still open:** when `website` is blank, the spec falls back to the La Piazza
   invite — which means a THIRD-PARTY shop cloning the starter prints Angel's community on their
   customers' receipts by default. Probably wrong. No QR at all may be the right default, with La
   Piazza opt-in. **Angel's call before it is built.**

### The method note worth keeping from tonight

**Both testers asked for the same thing: name the sample.** Steps that said *"find a product with a
long name"* and *"search for something with a lot of matches"* handed them my homework. Real terms
from the shop's own 5,427 active products are in ⓒ5 — use them.

**And a grep only finds a shape somebody thought of.** Six of tonight's dates were found by
searching the code; five were found by Layla LOOKING AT THE SCREEN. `prove-swiss-dates.js` section
N2 now reads the rendered text of seven reports and fails on any slashed date — the only check in
that file that does not care how the string was produced.

---

- **Contact sheet batch 1 — the 11 tablet shots, 2026-09-03** — ⓐ–ⓓ · the scale factor, the VAT bug, the pack badge. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓔ The frozen stylesheet was missing 131 classes** — closed by ⓙ. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓕ The pad judged a masked box as if it were money** — fixed. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓖ A refusal nobody can see — 139 buttons, and 33.33.3333** — fixed. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓗ The dead effect — every date box blind since it shipped** — fixed. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓘ The red box did not stop the save** — fixed. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓙ The 131 no-op classes — closed, and the chat bubble** — closed. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓚ The Search tab’s category picker** — fixed — and the ancestor of Pam’s B2 in ⓒ5. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓛ The gun pressed the button again** — fixed. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
## ⓜ BIRTH YEAR INSTEAD OF A FULL BIRTHDATE — OPEN, DO NOT BUILD — 2026-09-04

*Angel's idea, analysed and parked by his own call: **"i will ask felix tomorrow if he brings the
issue up … if somebody complains about it, fine, then we'll fix it. Other than that let's just
leave it. We've done a lot of work there, so it's better that we don't break anything and make our
life more complicated for nothing."** That is the right call and this entry exists so the thinking
is not lost, not so someone picks it up.*

**The idea.** Members give a birth YEAR, not a full date. Faster to type (4 digits, not 8), more
anonymous, and — Felix's own point — *"the members don't wanna be known at all, they just want
their codes."*

**The shop already works this way.** Of 22 active members: **4 have a birthdate · 3 have a cashier
attestation and no birthdate · 15 have neither.** The till is already running on "the cashier
looked at the ID", not on stored dates.

**The one hard edge, and it decides the whole design.** On 2026-09-04, someone born in 2008 is 18
if born in January and 17 if born in December. A year cannot decide age for exactly the cohort the
gate exists to catch. Two ways to resolve it in code, both bad: assume January → sell to
17-year-olds; assume December → refuse genuine adults, which is a lost sale and an argument at the
counter.

**The design that would work**, using machinery that already exists (`member_of_age()` reads DOB
when present, else `age_confirmed`):

| birth year | outcome |
|---|---|
| ≤ current − 19 | unambiguously of age → instant pass |
| **= current − 18** | ambiguous → falls through to "check the ID and confirm" |
| ≥ current − 17 | refuse |

Faster, more private, and no less correct: the one ambiguous year lands on the human holding the ID.

**What must NOT be done:** store the year as `YYYY-01-01` in `birthdate`. That writes a false
precise date into a compliance record. It needs its own nullable `birth_year` column, with
`birthdate` kept for anyone who volunteers one.

**Scope if it is ever built:** ~half a day with proofs. Column + migration (4 rows today), the age
logic, the API schemas, the age report, three member-facing boxes. **Staff cards do not change** —
a full DOB there serves AHV and employment, a different purpose entirely.

**The question for Felix, if he raises it:** *what is the record FOR?* If it is proof of diligence
in a test purchase, year + attestation is still proof of diligence. If it only ever feeds the gate,
year-only is strictly better. Not a legal opinion — that is his call, possibly his Treuhänder's.
The obligation is not to SELL to a minor; it is not an obligation to record birthdates, and the
paper till records nothing at all.

---

- **ⓝ Close of 2026-09-04 (daytime)** — superseded by tonight’s close. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
## ⓞ THE COUNTER VISIT — GO BEFORE THE SHIFT, NOT ON IT — 2026-09-04 evening

*Found on a kitchen table, not at the shop. Angel stood the tablet up in landscape, looked down at
it the way a cashier would, and it was unreadable — and **there is no chair behind that counter**,
so Layla would have to pick the tablet up for every sale. `WHERE-WE-ARE.html` already carried the
warning in prose (*"everything this week was proved in the flat"*); this is that warning turned into
things you can actually check.*

**This is LESSON #1 again and it is the cheapest instance of it yet** — a mount costs CHF 25, and
it was caught three weeks early instead of on Layla's shift. Same shape as the folio keyboard that
invalidated two runs, and as the LTE proved at home on an SSID Luzern does not have: *tested in the
posture the tester happened to have, not the posture she will have.*

### The one decision that touches the code — LANDSCAPE, LOCKED

Every geometry proof runs at **1440 × 895** (measured off the device pixel ratio, section ⓐ).
Portrait is ~895 × 1440 and moves the fold, the pinned Save bar, the cart total and the keypad that
owns the bottom of the screen. **Choose a landscape stand and lock rotation in the OS**, so a bump
mid-sale cannot reflow the UI in front of a customer — and so this week's geometry work stays true.
The testsheet rig already has an orientation selector; this is the decision that pins it.

### Take with you

- **A cheap adjustable tablet stand (~CHF 25).** Do NOT buy the real one first — the right angle and
  height depend on Layla's height, the counter height and where their lights are, none of which can
  be worked out from here. Find the geometry at the counter, photograph it, then buy the weighted
  one (Bouncepad / Compulocks / Heckler / Durable / Kensington, ~CHF 80–300). **Weighted matters:**
  a light stand slides on every tap. A counter-edge clamp or VESA arm is worth considering — counter
  space is the scarcest thing at any till.
- **A matte anti-glare screen protector (~CHF 20).** A glossy panel lying flat is aimed straight at
  the ceiling lights. Tilting to 60–75° fixes most of it; the film fixes the rest.
- **The gun, the folio (to leave OFF), and Layla.**

### The checklist

**Light** — shop lights ON and the street door open; daylight is a second source and it moves
through the day.
- Readable **without leaning in**, standing where she stands?
- Re-look at this week's contrast work under those lights: the 139 disabled buttons, the 111 CSS
  classes, the refusal text. Every one of those judgements was made under flat lighting.
- Is the tablet's brightness capped by auto-brightness or a power-saving mode?

**Reach and geometry**
- Can she work the till **while facing a customer**, or does she have to turn away? Turning away
  from a customer is the thing owners hate.
- Where does the Worldline terminal sit relative to the tablet — can she work both without shuffling?
- Is there a socket, and does the cable reach without crossing where she stands?

**Network** — the LTE lesson wearing a different hat.
- Their wifi **at the counter**, and the dead spot behind it.
- Does the tablet roam or cling? Anything captive-portal?

**The gun**
- At the counter's angle, over their network, on their surface — not held at reading height in a chair.

**Noise**
- Is the scan beep audible over the shop's music and the door?

### Do the controlled sales on the SAME trip

Item 1 below and this are one visit. Four sales, not one — that button is the first execution of the
Kassenbuch write, the transaction number sequence, the receipt render, the shift totals, the drawer,
the credits award and the VAT split on a stored record:

1. **Cash, plain** — the drawer path.
2. **Card** — the one rehearsal the manual (unintegrated) path gets.
3. **With a pack deal in the basket** — where the VAT bug lived; a stored record is not a screen.
4. **With a member attached** — the credits award writes to a second place.

Then refund them. **The refund path is also first-time, is manager-only, and hands back CASH even on
a card sale** — so a refunded card sale takes money out of the drawer. Watch that land in the shift
close. Tell Felix beforehand: it is a rehearsal so that his shop's first real sale is not this
code's first sale.

---

- **ⓒ2 mm/dd/yyyy on the six report filters** — fixed · 04446b1. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓒ3 Layla’s run of the date sheet** — 19 pass · 1 issue. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **ⓒ4 The list, the controls, and two calls for Angel** — both answered — see ⓒ5. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
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

### B2 · NEW — narrow the category dropdown to the categories the search actually hit

Pam, on the pinned panel: *"this is exactly why you need it — look for a term and easy search with
categories — would be good to narrow the cats where only search term is applicable so cat list is
shortened."*

Not a bug; a real improvement to the thing she just said she loves. **The numbers make the case:
the shop has 52 active categories and the dropdown lists all of them, always.** Searching `papers`
touches **6**. Searching `elements`, **5**. So she scrolls a 52-line picker to choose between five
answers, on a touchscreen, with a customer waiting.

Shape of it: `searchProducts()` already has the result set — group its categories and offer those
first (or only), with a way back to all 52. Note `raw` touches **26** and `king` **21**, so this
does not always shorten much; the fix should degrade to today's behaviour rather than hide
anything. **Not started.**

---

- **🔎 Found while fixing something else — 2026-09-02** — non-blocking, 3 days old. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **🌙 Where we stopped — 2026-09-03** — superseded. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **🌅 This week — from 2026-09-02** — superseded. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
- **▶️ Start here — the state at the end of Fri 2026-08-28** — superseded. → [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md)
## 💡 FIRST-USE AGE CHECK + THE T&C PAGE — waiting on Angel, not on code

Angel's idea (2026-08-22): the first time a member buys, the cashier verifies their age once —
better than storing a date of birth, because no DOB is held at all and the check is a human looking
at a human. **Design notes moved to [`worklist-archive/backlog.md`](worklist-archive/backlog.md)**
(record HOW, a look does not self-correct, hang it off the SCAN never the spoken code).

▶️ **What is actually blocked here is the T&C wording, and it is Angel's to write.** He sketched it
— plain English, not lawyer talk — then said *"I'm just making stuff up."* A page telling a customer
what they agree to should not be invented by the copilot. Draft copy needed, then DE at minimum;
FR/IT need a speaker, not a guess.

## 🔜 NEXT

3. **🔐 Go-live hardening** — DNS preflight + a default-secret gate in `deploy-prod.sh`; and the DR
   restore (Move B), still **blocked on read-only B2 credentials**. The backup has never been
   restored, so it is a belief, not a capability.

4. **🌱 Seeded realm users are published — DEFERRED ON PURPOSE 2026-08-14, not forgotten.**
   `keycloak/import/realm-export.json` carries **six users with plaintext, non-hashed
   passwords**, and `github.com/akenel/banco-starter` is **public** (HTTP 200 unauthenticated):
   `felix` (`pos-admin`), `ralph` (`pos-manager`), `michael`, `pam`, `pos-developer`,
   `pos-auditor`. Both `compose.yml:39` and `compose.prod.yml:35` boot Keycloak with
   `--import-realm` from that same file — prod and dev seed from one export.
   **Angel's call, 2026-08-14: leave them.** The usernames aren't the secret, these are seeded
   demo accounts, and **he rotated `felix`'s password on the live box**, so the published one is
   dead for the account that actually has privilege. Reasonable.
   ⚠️ **The one mechanism that could quietly undo that:** Keycloak's `--import-realm` only seeds
   when the realm doesn't already exist. So today's rotation holds — *until the Keycloak DB
   volume is ever recreated* (`down -v`, a fresh box, a restore drill onto a clean box). Then the
   export re-imports and **`felix`'s password silently reverts to the published one**. The
   DR restore in item 3 is exactly that scenario. Whoever drills it: check `felix` afterwards.
   When it comes up the list: strip the six users from the export (freehold did this in
   `a202c32` — `kc-prd` ships `"users": []` and the first admin is made by hand), and treat all
   six published passwords as burned regardless. The other five still have live published
   passwords today.


---


## 🔭 SMALL, FOUND WHILE TALKING — 2026-09-04/05

- **`<select>` is the next native control to bite.** Seven date pickers, `type="date"`, `type="time"`
  and the keyboard have all had to be replaced because **the tablet's browser renders them and its
  locale is not ours to set**. A `<select>` on a touch device draws an OS picker by the same rule —
  the Find Product category picker is one. **Thirty seconds with the folio OFF** tells you whether
  it is an eighth item or a non-issue. Cheaper to check than to be surprised by.
- **Sweep the four locales for missing keys.** `[i18n] missing key: reorder.by` logs on every order
  book line, and `"8:00 AM"` shipped as an i18n VALUE in EN and FR. **Four working languages is a
  sales asset** — it is the differentiator for Romandie and Ticino, where the app can go but Angel
  cannot — and the first English string a French-speaking prospect finds discredits the rest.
- **Credits + cash is a split tender you already shipped.** A member paying CHF 12.00 with CHF 4.20
  of credits is a two-tender sale by any other name. If that path is not clean the cashier rings it
  full cash and adjusts credits by hand, and the member ledger and the cash book stop agreeing.
  Probe before the trial. (Real split tender stays parked — and is billable if Felix asks.)
- **A feature is not done until you can name the screen it is reachable from.** `/pos/kb-approvals`
  was the fifth or sixth instance of a working page with no door. At that count the fix is a rule in
  the definition of done, not another instance.


---


## 🧹 NEEDS TRIAGE — read before trusting

[`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) holds ~1,000
lines of catalogue, till and shelf-intake items written between 07-30 and 08-07. **Their status was
not re-verified when they were archived**, and at least one was already wrong:

> the shared cash box was filed as *"design agreed 2026-08-03, not built"* — it shipped in
> `fd035dd`, and the `cashier_id == user_id` filter it describes is gone from the code.

**So: check the code before acting on anything in there.** Promoting the still-live ones up to NOW
is a 20-minute job worth doing once, not a thing to re-derive every session.


---


## ⏲️ A decision the logs raised — how long may a till sit idle?

Angel's 15:46 logout was **correct**: 152 minutes idle against a 60-minute
`ssoSessionIdleTimeout`. Not the refresh bug returning — refresh verified 200 at the time
of writing. But it is worth deciding deliberately for the shop rather than inheriting it:
**60 minutes of a backgrounded tab and the cashier is logged out.** In the foreground the
till polls and the session stays warm; a tablet asleep over lunch does not. Overnight
logout is *desirable*; a quiet Tuesday afternoon one is not.


---


## 📌 Standing facts worth not re-learning

- **THE THREE NAMES ARE ROLES, AND THE ROLE IS THE POINT.** Angel runs every sheet himself on the
  real tablet, signed in as whichever role the sheet is about:

  | signed in as | the part being tested |
  |---|---|
  | **Felix** | owner / administrator — settings, staff cards, no discount ceiling |
  | **Layla** | cashier–manager — the counter, plus what a manager may override |
  | **Pam** | pure cashier — the narrowest permissions, the ones most easily got wrong |

  **This is deliberate role coverage, not a stand-in for absent people.** What the screen does
  depends on the role — the discount ceiling renders only for someone who HAS one, which is exactly
  what step A8 checked — and signing in as the person the feature is for is how you find out whether
  it appears correctly for them. It has never once thrown up a role bug, which is the result you
  want from it. Writing the sheet in that person's voice is also what keeps it about a counter
  instead of a codebase. **Keep doing it.**

  One thing to keep straight when reading a count on this page: **"a human confirmed it on the real
  hardware" is true; "independently confirmed" is not** — the author is also the tester. That is not
  a flaw in the method, it is the argument for ⓞ, getting the shop's own staff in front of it before
  the shift.
- **The app image bakes `src/` in — there is no bind mount.** `docker compose restart app` restarts
  the **old** code and says nothing. Any change under `src/` needs `./scripts/rebuild.sh`.
- **Prod authenticates against the DEMO realm** (`kc-pos-realm-dev`, users felix/pam/ralph),
  imported from a file **in a public GitHub repo**. Still the go-live blocker.
- **Banco is zero-perpetual.** `stock_quantity = 1` is the *design*, not missing data. Never set
  `min_stock` / `max_stock` / reorder points — `/reorder/suggestions` ranks by what the till sold.
- **`age_check_event` is append-only** (a PL/pgSQL trigger, not `REVOKE` — which is a no-op against
  a table owner). Nothing can tidy a row away, including a mis-tap.
- **Hardware gets a label when it earns one. There is nothing to build, and no binder.** Settled
  2026-08-28. Of 1,062 bongs / grinders / trays / shishas / accessories, **20 carry a real EAN** —
  they are house-brand goods that exist in no other catalogue, so image-matching finds nothing
  (12 tested, 0 matched) and their minted `200…` code is the *correct* answer, not a failure.
  **The rule is: something sells twice, it gets a label.** Nobody plans it, nobody maintains a
  binder, and the work is done by the person who noticed the demand.
  **The shelf is the signal.** Four jars of ~20 Crank pipes behind the counter → obviously needs a
  scan method, and *Layla asked for exactly that unprompted* ("give me a label per type, I'll stick
  it on the jar lid"). One hookah on the top shelf for two years → obviously does not. Staff read
  their own selling patterns better than any rule we could write, and MISC is self-correcting:
  Felix asks why everything is MISC, they notice they sold the same thing four times this week, and
  they print a label. **That is ownership of their own catalogue, and it is worth more than
  completeness.** Felix: *"I don't want to put a barcode on every grinder"* — and he is right; it
  is their call, not ours.
  ⚠️ **Nothing needs writing.** The label button is already one tap for any staff on any item
  (`catalog.html:414`, "Pam's one-tap"), and a scanned label with no manufacturer EAN already
  resolves by SKU (`pos_router.py:2197`, proven on three Crank pipes 2026-08-27). A printed paper
  binder was considered and rejected: it does not scale past a few hundred rows, a printed price is
  wrong the day after it prints (**LESSON #13** — the stored copy always wins), and it adds a second
  checkout procedure for a minority of goods, which is the opposite of idiot-proof. **Build it only
  if Ralph or Felix asks for it.**
  *Keep the department-code escape hatch exactly as it is.* "Accessories, 39 francs, move on" is
  correct behaviour at a busy till.


---


## 🧪 How to prove it before claiming it

| what | command |
|---|---|
| stand up | `./scripts/rebuild.sh` → `./scripts/standup.sh` |
| server-side 18+ evidence | `BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py` |
| **the actual screens** | `BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-till-18plus.js` |
| **the unit tests** | `POSTGRES_HOST=localhost POSTGRES_PORT=5442 python3 -m pytest src/tests/ -q` |

⚠️ **`python3 -m pytest src/tests/` on its own looks half-broken, and is not.** 30 test files import
`pos_router`, which opens a DB connection at IMPORT time, and the app's default host is the
in-network name `postgres:5432` — which resolves only inside the container. From the host you must
point it at the mapped port (`POSTGRES_HOST_PORT` in `.env`, **5442** here, not 5432). Without it:
30 collection errors and 49 failures, none of them real. With it: **2,488 pass, 12 fail** — and
those 12 fail on a clean `HEAD` too. Found 2026-08-28 after reporting the bare run's numbers as if
they meant something.

⚠️ Both scripts **ring real completed sales** and refund them afterwards; a completed transaction is
a line in the Kassenbuch. `BANCO_ALLOW_FAKE_SALES=1` exists so it cannot happen by accident.
Playwright is **borrowed via `NODE_PATH`, not vendored** — this repo has no node build, on purpose.


---

## 📚 The archive

| file | what's in it |
|---|---|
| [`worklist-archive/2026-09-04-archive-pass.md`](worklist-archive/2026-09-04-archive-pass.md) | **the third cut** — 1,730 lines moved out verbatim on the night of 2026-09-04, 0 lost: the 11-shot contact sheet, the 131 no-op classes (ⓔ + ⓙ), the masked-box pad bug (ⓕ), the invisible refusal (ⓖ), the dead effect (ⓗ), the ungreyed save (ⓘ), the category picker (ⓚ), the gun that pressed the button (ⓛ), the daytime close (ⓝ), the date-filter thread (ⓒ2–ⓒ4), and everything written before 2026-09-03 |
| [`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md) | **the second cut** — 889 lines moved out verbatim 2026-08-27: the member card, ART-AB12, the join offer, the counter card, bundle pricing, the price warning, the whole FourTwenty thread, the six till reports, adopt-images, both prod-live days |
| [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md) | Gate Zero, and the whole 18+ evidence thread 08-10 → 08-13 |
| [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) | catalogue, shelf intake, till and search, through 08-07 — **status unverified** |
| [`worklist-archive/2026-08-20-till-reports.md`](worklist-archive/2026-08-20-till-reports.md) | the evidence behind BL-9…BL-14 |
| [`worklist-archive/2026-08-21-fourtwenty-reference.md`](worklist-archive/2026-08-21-fourtwenty-reference.md) · [`2026-08-21-price-consistency/`](worklist-archive/2026-08-21-price-consistency/) · [`2026-08-22-pooling/`](worklist-archive/2026-08-22-pooling/) · [`2026-08-22-anon-member-card.md`](worklist-archive/2026-08-22-anon-member-card.md) | the days themselves |
| [`worklist-archive/backlog.md`](worklist-archive/backlog.md) | not yet scheduled — credits redemption (waiting on Felix), dark mode, the till that felt slow, the offline kit, monitoring, labels, exports |
| [`worklist-archive/done.md`](worklist-archive/done.md) | shipped, most recent first, with commit hashes |

