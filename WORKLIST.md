# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short — and it has now been cut back twice.** 1,734 lines on
> 2026-08-13, and **1,201 again on 2026-08-27** despite a warning sitting inside it for three days.
> Both times the split was verified line-for-line and **nothing was deleted**; the second pass is in
> [`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md).
> **The rule is ~280 lines, not 150** — the 150 was set before item ⓪ existed, and a measurement
> that changes what the shop does next earns its space. The trigger is what matters, not the number:
> **when a thread closes, it moves the same day.** Growing back to four figures is what happens when
> "I'll archive it later" is the plan. When an item is finished it goes to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread grows
> a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-09-01 (evening) — ⑳ the keypad Banco draws itself is LIVE and human-green on the till: no browser on that tablet raises a keyboard, and `inputmode` is ignored there, which killed the 290-field fix before it shipped. The week is set: **Wed the 31 fields, Thu ask Layla in the shop, Fri ask Felix.** Ask Layla FIRST — she is the one who has to stand there.*

---

## 🌅 THIS WEEK — from 2026-09-02, in order

*Written at the end of an eleven-hour day so the next session does not have to reconstruct it.*

**MORNING — wire the 31 demo-path fields.**

```bash
python3 scripts/keypad-inventory.py --cashier      # the list, keyed on the words on screen
```

The demo Angel will actually give — **New Sale → Shelf Intake → Checkout** — is
**31 fields to wire, 4 already done, 3 do-not-touch.** Not 65, not 290. Wire them in small batches
and run the proof between each:

```bash
NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-keypad.js
```

**51 assertions, 0 fail, 1 known gap** is the baseline (`docs/keypad-baseline.json`). Anything that
goes red is a regression, not a debate.

⚠️ **Read `docs/keypad-inventory.md` before touching a field, and go by the LABEL, not the variable.**
That is the entire lesson of 2026-09-01: `otfName` and `lazyName` look identical to a grep, and one
of them is the screen a cashier stands on.

⚠️ **`type="number"` must become `type="text"`** for the caret to work — and then the field needs
`priceOnly()`-style sanitising, because the browser's own policing leaves with the type and a
**scanner gun is a real keyboard**. `maxlength` does not work on `type=number` either.

> **✅ DONE, morning of 2026-09-02 — all 31 wired, 62 pass / 0 fail.** The demo path now reads
> **35 wired · 0 to wire · 3 barcode boxes left alone.** Sheet for the tablet:
> [`2026-09-02-keypad-31-fields.html`](onboarding/testsheets/2026-09-02-keypad-31-fields.html).
> **DEPLOYED 2026-09-02** — prod is on **`9f5f14e`**, all gates green, `https://banco.wolfhold.app`
> live and healthy. Verified on the shop itself, not from the deploy log: the service worker's
> cache is `banco-pos-9f5f14e-…` and the served `pos-keypad.js` carries the change dispatch.
> **The proof also runs against prod: 62 pass · 0 fail · 1 known gap.**
>
> Three things the morning turned up, none of them in the plan:
>
> 1. **A proof run came back 51 pass / 0 fail having seen NONE of the change.** Templates are baked
>    into the image here — there is no bind mount — and I had not rebuilt. LESSON #5 in a clean
>    shirt. `prove-keypad.js` now opens with **H0: the SERVER is running the scan.html on disk**,
>    which names the field that is missing rather than counting; counting lied twice on the way
>    (base.html mentions `data-keypad` in a comment, and the first version fetched whatever page
>    sections F and G had left loaded).
> 2. **`otfPrice` and `lazyPrice` — yesterday's two human-green fields — had no `inputmode`.** On
>    that tablet `inputmode` is ignored, which is exactly why nobody saw it; on a phone and on a
>    laptop it is the difference between a number keyboard and a letter one. Fixed, and there is
>    now a check that every number box still declares one.
> 3. **A measurement lied about a fix — the fourth time this pattern has been logged.** The
>    page-does-not-jump guard was GREEN locally and RED on prod, `828 -> 766`. The pad was
>    innocent: typing into Item name fires `searchOwnedForOtf()` on a 400ms debounce, and against
>    a **5,479-product catalogue** the results land BETWEEN the two measurements. A demo catalogue
>    returns nothing, so the same code passed here and failed there. The assertion also re-found
>    *"the first visible button matching create|add|save"* each time — a moving ruler, not a moving
>    button. Now: settle the debounce, tag one element, measure that one. `763 -> 763` on prod.
> 4. **`x-model.number` eats the decimal point mid-keystroke.** It re-parses `"20."` as `20` and
>    writes it back, so **Amount received** on Checkout could not have taken a decimal at all once
>    it stopped being `type="number"`. Four fields had it. Checked for now.
>
> Two things that need Angel, not code — **neither is a blocker:**
> - **Discount % accepts 12.5 on New Sale and refuses it on Checkout.** Not something I introduced:
>   one was `step="0.1"` and the other `step="1"`. Both behaviours are now explicit and on the sheet
>   (A5 and D3). Which one is right is a shop decision.
> - **The inventory's label column is wrong wherever a `<label>` WRAPS its input** — it reads the
>   line above, so on Shelf Intake's deal row it attributed *"Every one of these costs"* to the
>   Buy box. The *kinds* came out right, but only because I read every one in the template. Worth
>   fixing before anyone trusts that column for the remaining 34.

**AFTERNOON — the human half on the tablet**, folio detached, gun charged:
[`onboarding/testsheets/2026-09-01-keypad-retest.html`](onboarding/testsheets/2026-09-01-keypad-retest.html).
**B4 is the one the machine cannot check** — press OK and hold a beat too long. If that holds across
31 fields, apply the same treatment to the rest (65 on the cashier path, 172 across all screens).

**THURSDAY — Luzern anyway, so put your head in the shop. Ask LAYLA FIRST.**

Decided the evening of 2026-09-01. Layla is the one who has to stand at that counter — Felix can
say yes on her behalf but he cannot make it work. **Ask her first.** If she is in, Friday is a
formality; if you ask Felix first and he asks her and she balks, you have spent your one ask and
you cannot un-spend it.

Tommy in the morning (an hour or two), the shop after lunch. **Say this in the first thirty
seconds** — it is the whole reason this is not going around Felix:

> *"I'm asking Felix on Friday. I wanted to ask you first, because if you don't want it, I won't
> ask him at all."*

**The sheet:**
[`onboarding/testsheets/2026-09-03-ask-layla-first.html`](onboarding/testsheets/2026-09-03-ask-layla-first.html)
— 18 steps, built on `TEMPLATE.html`, PASS/ISSUE/FAIL with a note box under every question so her
words get written down as she says them.

📱 **Open it on your PHONE, not the tablet** — the tablet is the thing she is holding. Get it there
however you like (mail it to yourself, or `python3 -m http.server` in `onboarding/testsheets` and
browse to the laptop). It also prints.

**The four questions.** Go through them WITH her — the two of you reading the same page is a
conversation; handing her a page to read is a pitch.

1. **"Would you want to be the one who tries it?"** — not *is it good*, not *would it work*. Would
   **you** want it. If she says no here, stop. Everything after this is noise.
2. **"If it's one morning, alongside the paper, and you can walk away at any point — is that
   different?"** — where a soft no turns into a yes. The ask is small on purpose.
3. **"What's the worst part of the till the way it is now?"** — she will say something you do not
   know. This question is for you, not for her.
4. **"What would make you say afterwards, that was worth it?"** — her definition of done, in her
   words, before you have told her yours.

Then stop talking and let her talk. That is the visit.

⚠️ **Do NOT show her the Felix page** — it is written for an owner (costs, ownership, the lease).
⚠️ **Do NOT demo the whole thing.** Scan one item, ring one sale, let her hold the tablet for two
minutes. Curiosity beats a tour.

✅ **The bonus:** you will be in the shop, with the tablet, on the SHOP's network. Everything proved
this week was proved in the flat — and that has bitten before (LESSON #1: the LTE proved at home on
an SSID Luzern does not have). An hour at that counter is worth more than a day here. Take the gun
and the charger.

**THEN — the meeting.** Friday afternoon, Felix. The ask is **one shift, not a verdict**: can Layla
run 11:00–16:00 alongside paper next week. The page to put in front of him:
**https://claude.ai/code/artifact/766b35d2-83e0-479b-8b4a-f832dfaee90e** (private — share from the
page's own menu, or just turn the laptop round).

### The state at close of 2026-09-01

| | |
|---|---|
| **live on prod** | `6c65d7d` — the keypad on NEW ITEM's two fields, human-green on the tablet |
| **fixed today, all human-green** | keyboard rises with no swipe · caret honoured · hold-to-backspace · caps lock · price ceiling CHF 99999.99 · `999.ab` refused from a real keyboard · OK no longer navigates out of a half-built product · the page holds still while a tap completes · phones keep their own keyboard |
| **instruments built** | `/pos/selftest` · `scripts/keypad-inventory.py` · `scripts/prove-keypad.js` · two testsheets |
| **decided** | go-live **1 Oct**, not tied to the lease · **Layla first, not Felix** · phones and dates left alone · the catalogue stays the shop's |
| **not started** | the shelf count (`pos_stock_movements` still 0 rows) · a scan-test a cashier can reach · the debug `[keypad]` beacons still logging on prod |

---

## ▶️ START HERE — the state at the end of Fri 2026-08-28

**Three things shipped and all three are live on the shop.** None was the hard problem it looked
like from the counter; each one was a capability that already existed with no way to reach it.

| | |
|---|---|
| `27e94c1` | **the feed PRICE is on the match card.** Angel's idea, and it beats the `units` field **4/4 vs 1/4** at telling a box from a packet. Every thumbnail carries its price, so the box shows before you click it |
| `5f9632c` | **42 blunts and wraps sold with no ID check** — a regex that needed two words touching. 40 now gate; the 2 `Herbal Tea` ones stay open on purpose |
| `1bd17fe` | applied on prod: **44 rows tightened**, re-run reports nothing to do |
| `d761595` | **`2024VL099B` is saveable again.** The override had been on the server the whole time and on no screen. ✅ Angel scanned the pack at the till — *"it worked perfectly"* |

**Also done:** the 18 duplicate pairs are merged by hand, and Angel correctly left the
with/without-filter pairs alone — which showed that **one supplier EAN sits on two products**, so a
barcode conflict is not proof of a duplicate.

⚠️ **Two loose ends from tonight, both written up below:** four rolling papers are now gated 18+
that should not be (**①b**), and the ⓪b carry-forwards are down to two (decoys, per-category
ranker).

**Where the EAN-match working data lives:** `scripts/ean-match/work/` — 800 MB, gitignored, moved
out of a `/tmp` session scratchpad on 2026-08-28. The SQL exports are checked in at
`scripts/ean-match/sql/`.

### Open, in order

**㉓ SHELF INTAKE FOR A CASHIER — SCAN AND REPORT, NEVER CREATE.** *(Angel's idea, 2026-09-02.
The best thing said all day, and it is not a tomorrow job.)*

His words: Shelf Intake is *"such a fantastic tool and super powerful"* and the best way to check
three or more products — but it is not fully a cashier's job. What a cashier SHOULD be able to do is
**scan twenty codes and hand back a list**: these eighteen were found, these three were not, and the
three are hot sellers so a manager should create them when there is time.

**Why this is the right shape and not just a permission trim:** every duplicate row in this
catalogue was born because somebody at the counter was made to CREATE under time pressure — see
LESSON #1 and LESSON #2. *Scan and report* removes the pressure without removing the person. The
cashier becomes the shop's best sensor for what the catalogue is missing, which is exactly the thing
nobody currently measures.

**The shape:**
- Cashier role gets Shelf Intake with **create, edit and price change removed** — scan/paste, check,
  and read the result.
- Unknown codes land on a **needs-a-manager queue** with the code, the time, who scanned it, and an
  optional one-line note (*"we sell ten a week"*). That is the handoff, as data instead of *"hey
  Felix"*.
- A manager sees the queue and clears it with the create flow that already exists.

**Not before Thursday.** Tomorrow is a person saying yes or no, not a new screen. Size it after.

**㉒ ✅ FIXED — the pad now fires `change` field-to-field, not only on DONE.** *(Angel found it on
the tablet 2026-09-02, fixed the same afternoon.)* `open()` reassigned `active` without ever closing
the box it was leaving, so a `@change` field — Checkout's **Qty** — kept its old value until DONE was
pressed. A real keyboard fires `change` on blur and a tap into the next field IS a blur. One line in
`open()`, mirroring the one already in `shut()`.

The test that would have caught it now exists: **H6 moves between TWO probe boxes** and asserts the
one you left fired exactly one `change` with nobody pressing DONE. **Watched go red on purpose** —
the line reverted inside the running container gives `fired 0×`. A one-probe test could never see
that door, which is why it was green while this was broken.

**㉑ THE CUTOVER HAS NO RUNBOOK — and it is not a `deploy-prod.sh` run.** *(raised by Angel, evening
of 2026-09-01, because it was about to be missed.)* `banco.wolfhold.app/pos` is **pre-prod**, not the
box the shop will run on. At go-live Angel stands up a **fresh Hetzner VPS for the shop alone**, on
the shop's own domain (`artemisluzern.ch/pos` or whatever Felix picks), rooted to our Keycloak — then
a clean-slate build: **the catalogue and every barcode binding carry over; transactions, stock
movements and the cash box start empty**, the float counted on the day. Full picture in
[`ROADMAP.md`](ROADMAP.md#what-we-run-on-today-is-pre-prod-not-prod--and-go-live-is-a-cutover-not-a-switch).

The consequence for every day between now and 1 October: **guard the catalogue like production,
treat the ledger as a rehearsal.** A test row or a wrong price on pre-prod is worth fixing and is
**not** fatal — none of it crosses the cutover. The catalogue is the one thing that does.

What is missing: a catalogue export→import that is proved lossless (bindings included), DNS + cert
preflight, the cash-box opening balance step, and a rollback if the new box does not come up.
**Rehearse it on a throwaway VPS before the date**, not on the day. Sizing this is a morning's work;
doing it is not.

**⓪ THE 3% IS NOT A MATCHING PROBLEM — 91% OF THE CATALOGUE IS KEYED ON INVENTED CODES.**
→ the full measurement, and the reasoning that killed bulk name-matching:
[`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md)

**4,971 of 5,447 active products (91%) carry a minted `200…` barcode** — GS1's restricted-circulation
range, valid inside one building, by definition never on a packet. **Only 3.5% of shop barcodes exist
in the FourTwenty feed.** Angel's *"happens by luck 3% of the time"* was not a mood; it is the scan
hit-rate, and it is a property of the **seed data**, not of the idea. He is not failing at intake —
he is **re-creating products he already owns**, because the packet's code can never match the code
we filed it under.

**The fix is a list, not an algorithm.** All 4,971 minted rows carry `supplier_sku` = Tamar's own
article number (100% populated, `TAM-` prefixed), and the minted barcode literally encodes it
(`2000000` + article no. + check digit). **Tamar's EAN list joins on one column, exactly** — no fuzzy
match, no review queue, no wrong-bind risk. Name-matching cannot substitute: measured at similarity
0.80, two different adapter sizes took the same EAN. **A wrong barcode looks exactly like a right
one (LESSON #9).**

⚠️ **And the job is much smaller than 5,447.** The catalogue is **Tamar's dropship range, not
Artemis's shelf** — `pos_stock_movements` holds **0 rows**, so nothing in Banco has ever recorded
what is physically in that store. Only what sits on the shelf has to scan. **Before any bulk EAN
work: establish what is actually in the room.**

▶️ **The next action is an email, not a sprint.** Ask Rafi/Felix for a **sample** first — "the EAN
for these 20 article numbers" needs no data-sharing decision and the reply measures the coverage
exactly. Better diagnostic question than *"do you have EANs?"*: **"when you receive goods from the
manufacturers, what do you scan?"** German text, export SQL and how to apply the list:
[`onboarding/supplier-ean-request.md`](onboarding/supplier-ean-request.md). The 4,971-row CSV is
generated and with Angel.

**The real UI bug behind it — FIXED 2026-08-27 late, and it was on a different screen than this
note said.** The find-and-bind panel *does* search our own catalogue on a miss, and has since
08-21; `prove-no-duplicate-on-a-miss.js` holds it there in nine assertions. But that panel only
opens when the **supplier feed can name the code**. When nobody can — the ordinary case here — the
cashier is left with the department strip and the **on-the-fly create form**, and nothing between
the name she types and `POST /products/quick` ever asked the catalogue. That is where the twins
were born. The form now runs the same two-source search (ranked + DE↔EN folded) as she types and
offers "you may already have this → bind" above the Create button. Never auto-binds (LESSON #9).
Four new assertions, red on the shipped image first. → `done.md`.
▶️ **Needs a human on the live till:**
[`onboarding/testsheets/2026-08-27-no-duplicate-on-a-miss.html`](onboarding/testsheets/2026-08-27-no-duplicate-on-a-miss.html)
— 14 steps, ~12 min. Section B is the fix; B2 is the one that matters.


**⓪b PICTURE-MATCHING WORKS, AND IT HALVES THE JOB.** Blind, three rounds, against 116 products
Angel had bound off the packet: **100% correct when the twin was on screen (round 3), 0 false
positives in 19 decoys.** Numbers, the CLIP ranker and the four rules it obeys:
[`LESSONS.md`](LESSONS.md) *"the pictures matched, the RANGE did not"* · `scripts/ean-match/README.md`

| | | |
|---|---|---|
| **CONSUMABLE** — papers, filters, wraps, tobacco, CBD, vapes | **2,425** | twins exist → worth matching, ~9 h |
| **HARDWARE** — bongs, grinders, accessories | **2,555** | no twins (12 tested, 0 matched). Minted EAN is the RIGHT answer |

✅ **DONE and on prod (`6db45e0`):** the BL-90b migration (`kind`/`pack_qty`/`source`/`confirmed_at`/
`evidence`), the no-promote rule for an image-match, `apply.py`, and **Rolling Papers run 1 — 23
aliases live**. Do not redo these.

✅ **Filters & Tips run 1 — 50 aliases live on prod, 2026-08-30.** 252 cards in 83 minutes,
median 13s, one gap under 3s in 249 — no rushing. Scored **14/15 controls** and **1 false positive
in 11 valid decoys** (`actiTube Slim` bound to `actiTube EXTRA SLIM` — the near-twin trap, which is
exactly what decoys are for). 62 accepted → 53 applied → **50 linked · 3 conflict · 0 failed**.
Prod now carries **73 image-match aliases** (69 retail + 4 case) beside 154 scanned.

▶️ **Next: `scripts/ean-match/SCHEDULE.md`** — every category costed against prod 2026-08-29.
**4,931 cards ≈ 14 h total**, but only **2.5 h of it is Tier A** (has controls, proven findable);
5.8 h is Tier C hardware that should probably never be opened. Filters is done; **CBD Flower is
next** (195 cards, 24 controls, 54% findable), then Pipes, Tobacco, the 46 remaining papers.
⚠️ **E-Liquids is the trap**: 699 cards, the biggest single block left, against ~**179** feed rows
that could be a liquid and zero controls — a perfect matcher tops out at 26%. Pilot 30 cards
before opening any Tier B category.

**⓪e FIFTY-FIVE ACTIVE PRODUCTS ARE PRICED AT CHF 999.99.** Found while checking the RAW rows,
2026-08-30. All are `ITEM-` rows created at the counter, all carry a REAL scanned barcode, and all
sit at stock 0 — so this is a typed placeholder that nobody came back to, the same thing
`ITEM-0158` "Trip 2" turned out to be in the papers run. They cluster in blunts/wraps/cones
(Cyclones, Juicy, Double Platinum), which is the same family as the age-gate work.

Two questions, neither answered yet: **does a stock-0 row still ring up at the till** (if it does,
one scan charges CHF 999.99), and **are these duplicates of TAM- rows** the way every other
counter-born row has been — in which case the fix is 55 more merges and not 55 price edits.
Check the first before deciding; `SELECT … WHERE is_active AND price = 999.99` is the list.

**⓪d THE THREE FILTERS DUPLICATES ARE MERGED — ✅ 2026-08-30, `scripts/ean-match/merge.py`.**
All three TAM- rows now carry the real EAN as PRIMARY with `barcode_is_internal = false`, their
minted `200…` code demoted to an alias so printed labels keep scanning, and the `ITEM-` rows
deactivated (never deleted — they are somebody's sales history).

| survivor | retired | primary barcode now |
|---|---|---|
| `TAM-5660` Aktivkohlefilter actiTube 8mm 100stk · 12.90 | `ITEM-0053` | `4260641140084` |
| `TAM-6296` Filterpapier Rasta nicht perforiert · 2.00 | `ITEM-0320` | `4260219150064` |
| `TAM-8614` Filterpapier RAW perforiert · 2.00 | `ITEM-0087` | `716165177555` |

The third looked like it might not be a duplicate at all — one row said *perforiert*, the other
said *Wide*, and the prices differed 2×. It is one: **`ITEM-0095` "RAW Black Filter Extra Breit"
already holds `716165305378`**, which is the feed's genuine Extra Wide tips, while `ITEM-0087`'s
own scanned barcode is the plain "RAW Perforierte Tips". The name was mistyped at the counter and
the barcode is the identity (CATALOG-IDENTITY.md). *A disagreeing NAME is not evidence of two
products; a disagreeing CODE is.*

⚠️ **Price left as-is on purpose.** `POST /catalog/merge` never touches price, so each survivor
kept its own. `TAM-8614` sits at **2.00 against the feed's 1.00** — the only one of the 53 at 0.5×.
Worth a look, but it is a pricing decision and not a merge.

⚠️ **My conflict prediction missed the third, on the leading zero.** `ITEM-0087` stores
`716165177555` (UPC-A, 12 digits); the feed gives `0716165177555` (EAN-13). I compared the strings
raw and saw no clash; the server normalises and refused it. **LESSON pattern #2, in the code that
exists to warn about pattern #2.** Any future pre-flight must normalise both sides.

⚠️ **9 rows held back — one GTIN, several of our products.** FourTwenty sells
`Blackout Filter Assortiert` / `Freak Show Filters Assortiert` / `Anonymous Filter Assortiert` as
ONE SKU where our catalogue carries one product per design (4 + 3 + 2). Angel was right on every
card; the binding is one-to-many and a barcode that resolves to two products is not a barcode.
`build_apply.py` holds these back automatically. The real fix is a merge, not a bind.

⚠️ **A live data error the run was not looking for: `TAM-22371`** "Purize Regular 9mm 50stk
allcolor", CHF 7.90, carries `4260748412541` — which FourTwenty lists as **"Purize Regular 100 All
Color", CHF 19.00**. The 50-pack is bound to the 100-pack's code. The price confirms it (7.90 vs a
50er at 9.50, not a 100 at 19.00). Angel picked the 50er and the scorer called him wrong; the
binding underneath was wrong. **Re-scan the packet and rebind.**
✅ **The feed PRICE is on the card — done 2026-08-28.** Angel's idea, and it beat the field it
replaces on both counts. Against the 41 bindings he confirmed on papers run 1: the 4 he called a
CASE came out at **4.5× / 15.4× / 20.0× / 26.7×** our shelf price — the four highest ratios in the
deck — and all 37 retail rows sat between **0.5× and 2.5×**. Nothing in between; `BOX = 3.0` sits in
the empty band. The feed's own `artikel_pro_verkaufseinheit` got **1 of those 4** and called two CHF
2.00 packets a box. Every thumbnail in the line-up now carries its price too, so the box is visible
**before** you click it. `python3 scripts/prove-ean-box-price.py` — 11 assertions, offline, screen
confirmed in a browser. ⚠️ **Measured on papers only — re-run it per category**, like the ranker.

Still to carry forward: **re-measure the ranker per category** — CLIP helped on mixed goods and
actively HURT on papers (top-3 54% vs 79% for name-only). ✅ Decoys landed 2026-08-29
(`select_run.py --decoys`); filters run 1 carries 15 controls + 12 decoys in 252 cards.

⚠️ **The ranker does not speak German colours — found by Angel mid-run, 2026-08-29.** For
`Aktivkohlefiter Kailar 5.9mm 250 Stk. schwarz` the top guess is **Pink 250pcs** while
**Black 250pcs** sits in the feed twice; `schwarz` and `black` share no characters, so neither
SequenceMatcher nor token Jaccard can see it. This is the ORIGINAL hypothesis that started ⓪b —
German titles against international ones — surviving in the variant words. Sized on filters:
33 cards whose top guess is the same brand and the same numbers, 9 where the colour disagrees,
**2 where the right colour is in the feed and merely ranked below #1** — and the top-6 rescues
both, so no answer is lost, only a click and a moment of doubt. Worth a synonym bonus
(schwarz/black, weiss/white, grün/green, blau/blue, bunt/mix) **for the next category, not this
one**: rebuilding a deck re-orders the candidate lists that a run's saved answers point at
(`card → candidate number`), so it would silently repoint everything already decided.
The other 7 are true no-matches — FourTwenty stocks 12 Kailar rows and no green at all. That is
*"the pictures matched, the RANGE did not"* again, not a ranker fault.

⚠️ **Two things found while doing it, neither urgent.** (a) The whole 800 MB working set — both
pools, 11,215 thumbnails, the CLIP vectors — was living in a **`/tmp` session scratchpad**, one
cleanup away from re-fetching every image. It now has a home at `scripts/ean-match/work/`
(gitignored) and the exports are checked in as `scripts/ean-match/sql/*.sql`. (b) **The retail-vs-case
split has no script.** `papers_apply.json` was assembled by hand last session; the sheet records
*which candidate*, never *which kind*. The price banner is the input to that call, so the sheet
should capture it — otherwise the box knowledge is re-derived by hand every run.
The found EAN goes in as an **alias**; `products.barcode` and every printed label stay untouched, so
a bad batch is one DELETE. Never auto-bind, never add a confidence threshold (both measured — README).
⚠️ Do **not** category-filter the FourTwenty side: it files papers under `Rolls` and under
`Themen · Gizeh January Action 10%`, and doing so hid 18 of 29 findable answers (**LESSON #2**).

**⓪c THE 18 DUPLICATE PAIRS ARE MERGED — ✅ Angel, 2026-08-28 evening, by hand on `/pos/catalog`.**
List (shop data, gitignored): `scripts/ean-match/data/MERGE-LIST-papers.md`

Applying the papers run wrote 23 aliases and hit **18 conflicts** — every one a real duplicate the
till's uniqueness constraint refused to create twice. **15 were `ITEM-` rows born at the counter**;
3 were Tamar-vs-Tamar twins inside the supplier catalogue itself. Angel merged them, keeping the
Tamar row and taking the price call on each.

⚠️ **He did NOT merge the last couple, and he was right to stop.** *"those were not dupes — one has
filters and one without. The pictures look the same (bad pictures, not our fault) but the titles are
different, so I left them."* Those are the **Tamar-vs-Tamar** pairs, and it means the supplier
catalogue puts **one EAN on two different products** — a with-filter and a without-filter variant
sharing a code. So: **a barcode conflict is not proof of a duplicate.** It is proof that two rows
claim one code, and which of the two things that means is a human's call every time. The photos
cannot settle it (both are the supplier's own bad stock shots) — **the title and the price can.**
This is LESSON #14's "145 codes on more than one product", met in the wild for the first time.
He left them deliberately: *"we will see the issue again if there really is an issue with the
shelf intake."*

⚠️ **This is why the duplicate guard never fires, and it is not the cashier's fault.** Median name
similarity between rows *proven identical by barcode*: **0.67. Only 3 of 18 clear 0.80**, which is
the lowest threshold we proved safe. `Rips Extra Dünn Slim schwarz` ↔ `Rolls Xtra Thin Slim`;
`Smoking DW kurz silver` ↔ `Smoking Master Silver Rolls`. **Tamar names in German house-shorthand;
the cashier types what is printed on the packet.** No name matcher can bridge that, and loosening
the threshold buys a mis-ring instead of a duplicate.

▶️ **STILL OPEN — the fix for FUTURE duplicates: use FourTwenty as a translator, not Tamar as a
target.** FourTwenty's titles *are* packet names (that is why text ranking hit 79%). So: cashier
types the packet name → search the FEED → take that row's GTIN → look the GTIN up in our catalogue
→ land on the Tamar row. Two hops, no Tamar name-matching anywhere. **Would have caught 18 of 18
where names caught 3.** Not built.

**① The gate audit — the classifier is FIXED; the live rows still need one command.**
[`onboarding/testsheets/2026-08-27-gate-audit.html`](onboarding/testsheets/2026-08-27-gate-audit.html)

**It was not Felix's decision after all — it was a regex that needed two words touching.** The rule
was `blunt\s*wraps?`, so "Blunt Wrap Platinum" gated and `Cyclones Blunt **Hemp** Wraps` did not.
No real title puts those words together: they read *Blunt Hemp Wraps*, *Blunt Clear mit Filter*,
*Cone Blunts*, or drop one word entirely (*Juicy Jays Blunts*, *Hemp Wraps*, *Super Wrap*). The
policy was already settled and written in the code — *"blunt wraps are gated CONSERVATIVELY —
over-gating a tobacco wrap is the safe error"* — the pattern just never implemented it.

✅ **Fixed and tested.** `_BLUNT` now matches the word, with a hardware veto, because **"Blunt" is
also a design name and a shape name**: a *Glas Blunt* is a reusable pipe, *Blunt Orbit* is artwork
printed on tins and rolling trays, and there is a *Blunt Geko Grinder*. Swept over **11,009 feed
titles + 5,061 of our own products**: `+35 / +23` newly gated, **0 un-gated, 0 class changes**, and
every one of our 23 is in category *Blunts & Wraps*. **40 of the audit's 42 now gate.** Six new
tests; each of the three guards reverted on its own and watched go red.

⚠️ **One regression the age gate could never have caught:** *Legendary Premium CBD Blunt 2g* moved
`cbd_hemp → tobacco_nicotine`. Both gate 18+, so nothing about ID checking changed — but `cbd_hemp`
carries the `thc_report` compliance obligation and tobacco does not. Found only by sweeping for
CLASS changes rather than GATE changes. Vetoed, and pinned by a test.

✅ **APPLIED ON PROD 2026-08-28 by Angel** — deployed `5f9632c`, then `reclass-age-gate.py --apply`
over 5,408 active products: **44 tightened**, and a re-run reports *nothing to tighten*. That is the
40 blunts and wraps from the audit (the 2 herbal ones correctly left open) **plus 4 the audit never
counted** — see below. ⚠️ Still needs one scan at the till to be human-green: `716165283911`
(*Cyclones Blunt Hemp Purple – Grape*) must now show 🔞 18+ · 🚬 Tobacco.
*(Deploy on the shop box is `./scripts/deploy-prod.sh` — NOT `rebuild.sh`, which omits
`compose.prod.yml` and would drop Caddy and HTTPS.)*

**①b FOUR ROLLING PAPERS ARE NOW GATED 18+ AND SHOULD NOT BE — pre-existing, surfaced by the run.**

```
Smoking King Size Supreme Zigarettenpapier
Rizla Blau DW Kurz - Zigarettenpapier aus natürlichem Zellstoff
JaJa Noir King Size XXL Black Zigarettenpapier
OCB Bamboo Slim + Filter Tips: Nachhaltiges Ba…
```

**The German compound is the bug.** `_TOBACCO` matches `zigar|sigaret|cigaret` as a substring, and
**Zigarettenpapier** contains `zigaret`. So a rolling paper reads as a cigarette. `_TOBACCO_ACCESSORY`
(which knows `papier|paper|filter|hülse|stopf`) exists to stop exactly this — but it is only
consulted on the SUPPLIER-CATEGORY layer, never on the title layer, and these products were created
by hand at the counter with no supplier tags. Verified identical under `HEAD~1`: **not caused by the
blunt fix.** It surfaced now only because nobody had run the reclass since those rows were created.

*Why my sweep missed it:* I measured against `artemis.csv`, a **5,061-row snapshot taken at 10:07**;
the shop has **5,408 active**. The four were in the 347 I could not see. A partial copy of prod hid
them — the mirror image of LESSON #5, where a partial copy invented a compliance scare.

⚠️ **`reclass-age-gate.py` only ever tightens, so it cannot undo these.** They need un-gating by
hand (or one targeted UPDATE), and the classifier needs the compound fix or the next run re-raises
them. The direction is the safe one — over-gating, not under — but the code's own comment is that
over-gating **trains staff to wave prompts away**, which is worse than the leak.

▶️ **The fix, not yet written:** run `_TOBACCO` against a copy of the title with the accessory
compounds removed (`zigaretten(papier|hülsen|stopf|maschine|etui|spitze|halter|dose)`), so a
standalone "Zigaretten" still gates and "Zigarettenpapier" does not. Must NOT apply
`_TOBACCO_ACCESSORY` wholesale at the title layer — it contains `filter`, and real cigarette packs
say "Filter".

▶️ **What is genuinely Felix's, and it is now two rows, not forty-two:**
`G-Rollz Terpene Infused **Herbal Tea** Blunt` (Natural OGK · Strawberry Cheesecake). They stay open
because `_AGE_NEG` treats "herbal" as a tobacco-free substitute — deliberate, and pinned by a test
so it cannot drift. If Felix says they gate, it is one word in `_AGE_NEG`.

⚠️ **Latent, in `reclass-age-gate.py`, not hit today:** values are quoted with
`json.dumps(...).replace('"', "'")`, which emits `\uXXXX` for non-ASCII and would not survive a
value containing a quote. Today every value is a UUID or a class name, so it is ASCII and safe.
Worth replacing with proper parameter binding before anything user-typed goes through it.

**①c THE ODD BARCODE IS SAVEABLE AGAIN — ✅ done 2026-08-28.** The pack of **JaJa Noir King Size
XXL Black** carries `2024VL099B`. Letters and all, a real printed code, and no EAN stripe anywhere
on the packet. Angel spent **over an hour** on it and could not save it from any screen.

**`allow_nonstandard=true` had been on the server the whole time, and on NO SCREEN** — a query
parameter, in zero templates. Its twin `allow_duplicate=true` *is* wired up (`catalog.html:2391`,
`shelf_intake.html:1331`): one override got a button, its sibling never did (**standing rule 9**).
And the refusal actively misdirects — *"scan the stripe under the EAN digits instead"* — sending you
to look for something that is not on the box. The guard's own comment had called it: *"a guard with
no way past it is a trap — the operator would just put the code in the name field instead, where
nothing can ever scan it."* Written, then not wired.

Now: the objection appears with **"That IS the code on the packet — save it"** beside it, and the
retry carries the flag. The objection itself is unchanged — it is right most of the time. The 422
detail became structured (`conflict: 'barcode_format'`) so the button attaches to **this** refusal
and never to the missing-price 422 on the same endpoint.

▶️ **Proved end to end in a browser on the local stack**, not by reading the template: create with
`2024VL099B` → refused → click → saved → **`GET /products/barcode/2024VL099B` returns 200** and the
right product. Test rows cleaned up, 0 left behind. 7 new tests in `test_barcode_objection.py`.

⚠️ **And it was hiding LESSON #12 a fourth time.** The refusal was placed next to the save button —
the fix from last time — and was *still* unreadable: the modal body scrolls independently while the
button strip is pinned, so with the form scrolled up the message rendered at **y=1372 in a 1050px
viewport**, 322px below the fold. Press Create, and from where you are sitting nothing happens.
`isVisible()` said `true` the whole time; only a screenshot showed it. Both refusals now scroll
themselves into view — and `$nextTick` was **not** enough, because `x-show` flips `display` on its
own pass and scrolling to a zero-height box does nothing. It waits for a real box instead.

✅ **HUMAN-GREEN ON THE LIVE SHOP, 2026-08-28.** Deployed `d761595`; Angel saved JaJa Noir with
`2024VL099B` and **scanned the pack at the till — it rings.** *"it scans and it worked perfectly."*
That is the finish line (standing rule 5).

**② Layla's product-grouping idea is BUILT and unreachable.** `POST /products/{id}/clone` — its own
docstring describes her exact case. On no screen. She reinvented it from the counter without seeing
the code, which is the strongest argument for it. **This is the next feature.**

**③④ The scanner gun and the label PDF are PARKED — both moved out 2026-08-28.** The gun is
safe for every code this shop scans (EAN-13/UPC-A are pure numeric, so the late SHIFT can never
fire); the PDF path is save-to-file only and the printer is fed directly. Findings, the one
untried test, and why neither is abandoned:
[`worklist-archive/2026-08-28-scanner-and-label-pdf.md`](worklist-archive/2026-08-28-scanner-and-label-pdf.md)

**⑤ The MEDIUM label's CODE128 is still unproven by a gun.** 17 characters in 62mm makes fine bars.
If it will not read, the answer is a SHORTER SKU, not a bigger label.

**⑥ The vocabulary gap has no fix yet.** Angel searched *rainbow*, the feed says *rasta*. The new
panel's empty state names the trade words (rasta, Kopf, Schliff, Kawumm) but nothing translates them.
A synonym table is the obvious next step and has NOT been thought through.

**⑳ ✅ THE KEYPAD IS LIVE ON THE TILL — 2026-09-01, `6e586da`.** Human-green on the tablet,
folio detached, as pam: NEW ITEM → tap **Item name** → letters, tap **Price (CHF)** → digits,
**no swipe either time.** Angel: *"it works — you did it"*. The beacons agree:

```
[keypad] focusin on <input> data-keypad=text    -> MINE   open kind=text    padHeight=252
[keypad] focusin on <input> data-keypad=decimal -> MINE   open kind=decimal padHeight=352
```

⚠️ **An hour went on a bug that was one wrong field.** The keypad worked as a standalone file and
did nothing in Banco; four hypotheses (touch gate, modal z-index, service worker, focus-stealing)
were all wrong. There are **two** create-an-item forms on the scan screen: `lazyName`/`lazyPrice`
(:1074, :1157) after a SCANNED barcode misses — which I wired — and `otfName`/`otfPrice` (:305,
:351), the on-the-fly form reached with no barcode, which is the one a cashier uses. Angel said
*"Item Name"* from his first message; the form I wired says *"Product name"*. **LESSON #1 ×14.**
The failure was SILENT — no error in Chromium's own log — so `console.log('[keypad] …')` beacons
had to be added before anything could be found. `/pos/selftest` was built the same hour and is the
rung that was missing: real app shell, two inputs, nothing else.

### The sheet was run on the real tablet — 2026-09-01 evening, **NO GO**

Angel, 47 minutes, folio off then on: **14 pass · 3 issue · 1 fail · 3 not run.** The keypad
itself passed every step of section A — it rises on its own, shift releases, umlauts land, the
caret works, hold-to-backspace repeats, the price box stays visible, and CHF 12.50 saved as
CHF 12.50. What failed was **scope and validation**, both now fixed and guarded:

| | |
|---|---|
| **D2 FAIL → fixed** | *"the mobile phone keypad should be left alone and native… our fixes should only be for the tablet."* Right, and the numbers agreed: 28px keys in portrait, 91% of the screen in landscape. Phones are now excluded by `posIsMobileOS()`. A phone raises a good keyboard by itself; the Debian tablet is the only machine that does not. |
| **B2 → fixed, and it was MY regression** | With the folio attached you can type `999.ab`. These fields were `type="number"`, which the browser policed for free; I made them `type="text"` so the caret would work and the policing went with it. Our pad filters as you tap, so the fault is invisible until a REAL keyboard is attached — **and a scanner gun is a real keyboard.** Now sanitised on input, same shape as BL-16. |

**Decided, no action:** ⓑ3 — the pad appearing even with the folio attached is *fine*. Angel:
*"they are so good and clean it does not interfere, it only eats 25% of the screen… users will
still be in soft mode and expect both working, so we should leave it."*

**Measured, for the runbook:** a folio hot-attach needs **a few seconds** before the trackpoint
works. It is not dead, it is slow — Angel recorded a failure and then it came good. That is the
difference between a known quirk and a cashier concluding the till is broken.

### ▶️ THE DECISION TODAY ACTUALLY SURFACED: name the supported hardware

**Angel, 2026-09-01, after a day of it:** *"I sold the idea of a web app works on any device, but
that's not really true. It works, but it works rough and clunky unless you customize it for that
device. Is that the truth?"*

**Half of it.** The SCREENS are portable — Banco renders the same on Android Chrome, iPad Safari and
Debian Chromium. Everything that hurt today lives where software meets hardware, and a *native* app
would hit the same wall:

| | Debian ThinkPad | Android tablet | iPad |
|---|---|---|---|
| raises its own keyboard | ❌ **the whole of 2026-09-01** | ✅ | ✅ |
| prints Brother QL via CUPS | ✅ | ❌ | ❌ |
| takes the gun's USB dongle | ✅ | ~ (OTG) | ❌ |
| runs the stack locally if the network dies | ✅ | ❌ | ❌ |

**So the answer is a supported-hardware list, and that is a product decision, not a retreat.**
Square, Lightspeed and Shopify all publish one; none of them says "any tablet". It also gives Angel
a sentence he does not currently have: when Felix buys Layla an iPad, *"that is a new configuration
and here is what it costs to add"* — instead of a silent emergency.

▶️ **Not started.** A page in `onboarding/` naming the reference kit (this tablet, this gun, this
printer), what each part is for, and what it takes to qualify another. **The new requirement nobody
knew this morning: the counter device must raise its own keyboard.** The next shop self-hosting
Banco on a spare touchscreen laptop hits exactly this.

⚠️ **And the rule that came out of it:** *simulate for coverage, one real device for truth.* Proved
twice in one evening — the harness called phone-portrait fine when a thumb said otherwise, and the
automated test for the OK-navigates bug passed with the fix REMOVED.

### Still open on this thread — and ⓒ3 is NOT ours

✅ **ⓒ3 shelf intake — CLOSED, and it was the gun's battery.** Angel found it: the gun had *also*
stopped working on New Sale, a screen that worked an hour earlier. **One symptom on two unrelated
screens means the thing they share is what changed.** The tell is a **double beep and no red
flash**; there is no low-battery warning at all. Nothing was changed in the app —
`shelf_intake.html` and `pos-scanner.js` are both untouched since 22 August, the box carries no
`data-keypad`, our keypad script returns early on any machine without a touchscreen (`typeof
window.posKeypad === 'undefined'` on that page), and a 0ms Playwright burst lands cleanly in the
box **on the live build**. → written up in
[`onboarding/13-tablet-x1-debian.md`](onboarding/13-tablet-x1-debian.md).
▶️ **Worth deciding:** should `/pos/hardware` show **when Banco last saw a scan**? "No scan in 3
minutes" turns a silent hardware failure into a visible one. Second time a hardware fault has read
as a Banco fault — the camera was the first, 2026-08-22.

⚠️ **ⓒ1 the create form opens holding the LAST product's name and price.** Found with the gun. Not
a show-stopper (backspace works) but it is LESSON #13's shape again — a reset that does not reset
everything. `otfName`/`otfPrice` are cleared at `scan.html:1943` and `:2183`; whichever path the
gun takes to that form is not calling either.

⚠️ **ⓒ2 the barcode box gives the TEXT keyboard when typed into.** Correctly has no pad of ours —
but 99% of what is typed there is digits, so the OS keyboard it falls back to is the wrong one.
Noticed, not urgent.

⚠️ **ⓔ1 Clear on an empty cart did nothing visible** until an item was added. Possibly a test
artefact; possibly the same shape as the sessionStorage clear-that-clears-one-key-of-three.



| | |
|---|---|
| **the pad covers the Price box** | `open()` pads `.app-content`, which is not what holds a field inside a `fixed inset-0` modal. The old system keyboard pushed the screen up and Angel misses it. Fix: pad the modal instead. |
| **debug beacons are live on prod** | `[keypad]` logs on every focus. Harmless, useful while more fields get wired, but they come out. |
| **the readout is hard to read** | `/pos/selftest` green-on-black, too low contrast on that screen. |
| **every other field** | department keypad (`deptPrice`), quantity, cost, discount, customer lookup, login. ~15–20 on the cashier's path — NOT 300. Each one confirmed on the tablet, a few at a time. |
| **the system keyboard can still be swiped up** | Cannot be blocked from a web page. GNOME's OSK can be switched off (`screen-keyboard-enabled false`) and should be — but **not until our keypad covers every field**, or the uncovered ones become untypeable. |
| **a wedged kiosk has no way out** | `--kiosk` leaves no address bar; the power button and the folio both did nothing. Recovered with `pkill -f chromium` over SSH. A cashier alone at the counter has no SSH. |

*Not a bug, checked: `[keypad] gate` appearing several times is one line per page load, not a
double-init.*

---

**⑳a THE MEASUREMENT BEHIND IT — measured on the real machine 2026-09-01, and the obvious fix was
the wrong one.** Angel: *"it sure does not have the feel of the desktop."* Two separate problems
were hiding inside that one sentence.

**A · No browser on that tablet raises the on-screen keyboard. Not fixable in Banco.** Proved by
elimination, on the tablet, over SSH:

| | auto-raises the keyboard? |
|---|---|
| GDM login screen | ✅ |
| GNOME Text Editor (native Wayland/GTK) | ✅ |
| Banco in Chromium | ❌ |
| Banco in Firefox | ❌ |
| **a blank `file:///tmp/kbtest.html` with three plain inputs** | ❌ |

That last row is the one that matters — **no Banco code, no CSS, no Alpine, same failure.** Our
templates are not the cause. Tried and did NOT fix it: `gsettings … screen-keyboard-enabled true`
(survives reboot, keep it — it is what makes GNOME's half work), a session restart, folio detached,
a full system + Chromium update, and `--ozone-platform=wayland --enable-wayland-ime
--wayland-text-input-version=3`. Chromium was on **XWayland** all along — it said so itself,
`ozone_platform_x11.cc:257 Missing X server or $DISPLAY` — but forcing native Wayland changed
nothing. The cashier must swipe the keyboard up by hand, every field, every time.
➡️ **The only fix we control is an on-screen keypad Banco draws itself.** It also removes the
dependency entirely, which is the point: it works the same on Debian, on an iPad, on whatever Felix
buys next week. Not started, not scoped.

**B · `inputmode` is IGNORED on this stack. `type` is what picks the keyboard.** Two fields, one
difference, tested back to back with the keyboard already up:

| field | markup | keyboard shown |
|---|---|---|
| cart quantity · `scan.html:515` | `type="text" inputmode="numeric"` | ❌ **letters** |
| Agreed Final Total · `scan.html:616` | `type="number" step="0.05"` | ✅ **numeric** |

⚠️ **This killed the fix I was about to ship.** 290 of ~300 inputs carry no `inputmode` and the plan
was to add it everywhere — **290 edits that would have changed nothing on this tablet.** Only
testing the one field already built the "right" way exposed it. Worse, that field is `type=text`
*on purpose* (BL-16, to kill the ▲▼ arrows that duplicated the −/+ buttons) — it bought that with
the wrong keyboard here, a trade made for a phone and never re-checked on the counter machine.

**The fix that serves both:** `type="number"` for the desktop hint + keep `inputmode` for iOS/Android
+ one CSS rule to hide the spinners. **Not a find-and-replace** — `maxlength` does not work on
`type=number` (the quantity field depends on `maxlength="4"` → needs `max="9999"`), and the
`@input` digit-strip reads `$event.target.value`, which returns empty on an invalid `type=number`.

▶️ **Next, and not yet started:** an inventory of every input on every screen a **cashier** can
reach — screen, field, current `type`, and whether it sits low enough to end up under the keyboard —
then a walk-through sheet from `onboarding/testsheets/TEMPLATE.html`. Angel: *"for the cashier role
we need to test all the screens and all the inputs one at a time."*

**Also found, unrelated and unfixed: a wedged kiosk has no way out.** `--kiosk` leaves no address
bar, the power button did nothing, and re-attaching the folio did nothing. Recovered over SSH with
`pkill -f chromium`. A cashier alone at the counter has no equivalent.

**⑦ Adopting from the supplier copies its 18+ answer with no safety net**, while the till's quick-add
applies one — same operation, two answers. And the classifier does not know the words "blunt" or
"wrap", so the safety net would not have caught the wraps anyway. Both real, both unfixed.

### Not bugs — decided today

- **58 products at CHF 999.99 are DELIBERATE.** Angel: *"the number is so high it can't be missed"*.
  A not-priced-yet marker with a human as the check. `/pos/cleanup?mode=bench&gap=price` lists them.
- **"A couple at a time" is the right shape for intake**, not a limitation to engineer around.
  5,430 products against 50 transactions in the box's whole life.


### Also open — smaller, each one verified in code on 2026-08-27

- **⑧ BL-11 — the stale snap panel, and it is LESSON #13 again.** `snapPreview` is cleared in
  **exactly one place**, `snapClose()` (`catalog.html:2088`). `openCreate()` resets `gallery`,
  `pendingPhotos`, `pendingImageUrl` and `_aiTail` — and **not** `snapPreview`, `snapName` or
  `pageUrl`. So the create panel can still show the *previous* product's photo under the words
  "read from this photo". A clear that clears four keys of seven. *(BL-9 and BL-10 ARE fixed —
  verified in the code, now in `done.md`.)* Needs a browser to confirm the screen effect (LESSON #7).
- **⑨ BL-14 — the cursor is not where the work is.** Now specified, by Angel: *"annoying when you
  have to put the cursor at the logical spot when the screen is refreshed."* After a refresh, focus
  lands nowhere useful and the cashier reaches for the mouse mid-sale. Find every screen that
  re-renders under Alpine and give it one deliberate focus target.
- **⑩ Run `GET /catalog/price-check` over the whole catalogue.** This replaces an 08-21 list of
  individual papers (OCB Premium Slim, OCB Virgin Slim, 8 King Size, 6 Rips, Old School) that Angel
  no longer recognised six days on. **Not dropped — those are money rows**, and a `per_unit` tick is
  exactly the CHF 6.00 bug. The sweep is the net that already caught two live leaks on its first run;
  it answers the whole list at once and does not depend on anyone remembering.
- **⑪ `--proxy-headers` on uvicorn** (plus `--forwarded-allow-ips`). Three call sites carry a
  forwarded-header workaround and **a fourth that forgets it will be wrong in a way nobody notices,
  because http works.** `entrypoint.sh` runs uvicorn without it, so `url_for` behind Caddy mints
  `http://` — it caught a printed `http://` QR on the counter card before anything went to paper.
- **⑫ `enrich-from-source.py --apply`** — dry run clean (40 fetched, 0 failed). The spec half is safe
  and is most of the value (~4,500 products). The tier half writes **~510 new ladders on a live
  till** against 92 today. **Run it, then run ⑩ before the shop opens.** Not a job for the end of a
  long day.
- **⑬ The tablet's LTE — Luzern-only, whenever Angel is next at the shop.** Working, and proved in
  Angel's flat, not on the counter: set `ipv4.route-metric 100` on the **shop** Wi-Fi profile,
  measure signal where the till stands (29% at home, concrete will be worse), and pull the Fritzbox
  WAN cable mid-sale. Cold boot and the FCC unlock are ✅ machine-level and do not need redoing.
  🔋 Still to buy: a **USB-C PD** power bank — this tablet refuses 5V, so a USB-A bank does literally
  nothing. Runbook: [`onboarding/13-tablet-x1-debian.md`](onboarding/13-tablet-x1-debian.md).
- **⑭ Mint `qr_code` for the live members.** The card is deployed, but 0 of 18 members had one when
  last measured — **no card exists to scan yet.** 🧹 Also: three `ZZTEST-*` members seeded in LOCAL
  dev only (never prod) — `DELETE FROM customers WHERE handle LIKE 'ZZTEST-%';`
- **⑮ The miss rate is still not recorded.** `catalog_miss` holds **1 row, ever.**
  `_record_catalog_miss` is gated `if ln.department_code and ln.unresolved_barcode`, so only a miss
  rung through the department strip counts — and the *good* path (create-and-bind) carries neither.
  ⓪'s "telemetry is blind" is this. Until it is fixed, "three of four scans miss" has no live
  measurement behind it; that figure is a stock, not a rate.
- **⑯ A cashier still cannot create an anonymous member at the till.** `customer_lookup.html:566` +
  `CustomerCreate` still demand a handle, the way the kiosk did before `85154c0` fixed it there.
  Same "invent a name at a counter with a queue" problem the ART code exists to kill. Sibling of a
  shipped fix, and standing rule 9 says check the siblings.
- **⑰ A second wholesale feed is the big lever** — Kings Castle took reach ~40% → ~56% as tier 3.
  neardark needs credentials.
- **⑲ There is no un-bind.** `POST /products/{id}/barcodes` exists; nothing removes a code from a
  row — no endpoint, no screen, no button. Found while writing the sheet above, which has to warn a
  tester that section C cannot be taken back. Binding is the operation the whole miss flow now
  pushes people towards, and it is one-way. LESSON #9 says a wrong bind looks exactly like a right
  one; today the only repair is psql. A manager-only remove, with the code shown, is small.
- **⑱ The catalogue CSV eats a leading apostrophe** — barcodes export as `'7610…`; Excel eats it,
  LibreOffice shows it, and no fix is clean in both. **An .xlsx export sidesteps it entirely** and
  the openpyxl machinery already exists for the BL-131 worklist. Angel's call.


---

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
| [`worklist-archive/2026-08-27-archive-pass.md`](worklist-archive/2026-08-27-archive-pass.md) | **the second cut** — 889 lines moved out verbatim 2026-08-27: the member card, ART-AB12, the join offer, the counter card, bundle pricing, the price warning, the whole FourTwenty thread, the six till reports, adopt-images, both prod-live days |
| [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md) | Gate Zero, and the whole 18+ evidence thread 08-10 → 08-13 |
| [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) | catalogue, shelf intake, till and search, through 08-07 — **status unverified** |
| [`worklist-archive/2026-08-20-till-reports.md`](worklist-archive/2026-08-20-till-reports.md) | the evidence behind BL-9…BL-14 |
| [`worklist-archive/2026-08-21-fourtwenty-reference.md`](worklist-archive/2026-08-21-fourtwenty-reference.md) · [`2026-08-21-price-consistency/`](worklist-archive/2026-08-21-price-consistency/) · [`2026-08-22-pooling/`](worklist-archive/2026-08-22-pooling/) · [`2026-08-22-anon-member-card.md`](worklist-archive/2026-08-22-anon-member-card.md) | the days themselves |
| [`worklist-archive/backlog.md`](worklist-archive/backlog.md) | not yet scheduled — credits redemption (waiting on Felix), dark mode, the till that felt slow, the offline kit, monitoring, labels, exports |
| [`worklist-archive/done.md`](worklist-archive/done.md) | shipped, most recent first, with commit hashes |
