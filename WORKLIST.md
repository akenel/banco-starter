# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short — and it has now been cut back three times.** 1,734 lines on
> 2026-08-13, **1,201 on 2026-08-27**, and **2,307 on 2026-09-04** — the biggest yet, grown in a
> single week of shipping. Every pass was verified line-for-line and **nothing was deleted**:
> [`2026-08-27`](worklist-archive/2026-08-27-archive-pass.md) ·
> [`2026-09-04`](worklist-archive/2026-09-04-archive-pass.md) (1,730 lines out, 0 lost).
> **The rule is ~280 lines, not 150** — the 150 was set before item ⓪ existed, and a measurement
> that changes what the shop does next earns its space. The trigger is what matters, not the number:
> **when a thread closes, it moves the same day.** Growing back to four figures is what happens when
> "I'll archive it later" is the plan. When an item is finished it goes to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread grows
> a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-09-04, ~23:30 — **the blocking deck is clear.** Five items in, three UAT sheets
run on the real tablet, zero fails. Live on the shop: `b629 · 6cc1bb5`.*

---

## 🌙 CLOSE OF 2026-09-04, ~23:30 — READ THIS FIRST

**Live on the shop: `b629 · 6cc1bb5`.** Reload the tablet TWICE after any deploy — the first load
activates the new service worker, the second serves from it.

### What went in tonight

| | found by | proof |
|---|---|---|
| **Swiss dates on all seven filters** + a month grid Banco draws itself | Layla, 17:21 | `prove-swiss-dates.js` **97** |
| **Seven more dates** — Sales Reports, the 18+ record (a PRINTED compliance document), the closeout Z-report, the delivery slip | **Layla, after the sheet ended** | same file, sections M–Q |
| **The discount chips say the number** + "Your max discount: 100%" gone | Layla | `prove-discount-chips-tell-the-truth.js` **15** |
| **The product list ends on a whole row** + the Find Product controls pinned | Layla / Pam | `prove-nothing-is-cut-in-half.js` **12** |

Also green and unchanged: `prove-keypad.js` **81**, `prove-classes-exist.js` **5**.

**Three sheets, 54 pass · 5 issue · 0 fail.** Every issue was a request or a missing test fixture,
not a defect. The sheets themselves:
`2026-09-04-swiss-dates-everywhere.html` · `-chips-and-the-printed-dates.html` ·
`-the-list-and-the-controls.html`.

### Pick up here, in this order

0. **BUILD `scripts/worklist-check.py` — Angel's call, 2026-09-04 23:40, do this first.**
   *"a 500 line worklist should be a reasonable limit or time to archive."* **Yes — and the number is
   not what failed.** The rule was 150, then 280. The file hit **1,734 → 1,201 → 2,307** and has never
   once been met; tonight it grew a thousand lines in one session while the rule sat at the top of the
   file. A rule broken three times is not fixed by being made easier, it is fixed by being TRIGGERED.
   So: **the limit becomes 500** (honestly what the live file needs to hold), and it gets an alarm.

   ~15 lines. Print the line count, and count the sections still in the LIVE file whose header carries
   `FIXED`, `CLOSED` or `~~`. Over **500 lines** *or* more than **two closed threads** still sitting
   here → print **"archive pass due"** and name them. Wire it into the SESSION START list in
   `CLAUDE.md` so the first thing every session does is say it out loud.

   *The real rule was already written in this file — "when a thread closes, it moves the same day" —
   and it is the one that got ignored, not the line count. This is the difference between a limit and
   an alarm.*

1. **② Re-run the keyboard-buries-search test with the folio OFF.** The only blocking item still
   open, and it has been carried three days. The last result does not count — the pad never
   appeared, and the pad is the subject of the test.
2. **Pam's category-dropdown request** — ⓒ5 below. The shop has **52 active categories** and the
   picker lists all of them; a search for `papers` touches **6**. Continues ⓚ (archived), which
   grouped them into sections; this narrows them to the ones the search actually hit.
3. **The counter visit + the `--kiosk` flag** — ⓞ below. Two problems on one trip: everything this
   week was proved in a flat, and Chromium runs windowed on the tablet so a touch-drag walks the
   window off screen (Layla's D2 — she worked out for herself that a reboot was her only move).

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

- **A NAME ON A TESTSHEET IS THE LOGIN IT WAS RUN UNDER, NOT A SECOND PAIR OF EYES.** Every physical
  test in this repo to date — every sheet, every tablet screenshot, every "confirmed by Felix / Layla
  / Pam" — is **Angel**, on the real tablet, signed in as that role. The staff are real people; they
  have not run a sheet yet. He said so plainly on 2026-09-04 and it had been in the record all along
  (sheet 2, step 0.2: *"its me angel signed in as Lalya"*).
  **Two things follow, and both matter.**
  *One:* the practice is sound and should continue. Running as a cashier is not theatre — the role
  changes what the screen does (the discount ceiling only appears below 100%, and step A8 tested
  exactly that), and writing the sheet in a named person's voice is what keeps it about a counter
  instead of a codebase.
  *Two:* **"human-green" is true — "independently confirmed" is not.** A person on the real hardware
  did find every one of these, which is the bar that matters and the reason the count of found bugs
  is what it is. But the author of the software is also its tester, and an author cannot be surprised
  by his own work the way a stranger can. That gap is the argument for ⓞ, the counter visit, and it
  is the one thing on this list no amount of proof scripts can close.
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

