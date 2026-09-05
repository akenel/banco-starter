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

## ▶️ THE DECK — READ THIS FIRST · last touched 2026-09-05 afternoon

**Live on the shop: `b647 · 234a601`.** Reload the tablet TWICE after any deploy — the first load
activates the new service worker, the second serves from it.
*The method note from the night of 2026-09-04 — name the sample, and a grep only finds a shape
somebody thought of — moved to [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md).*

*What went in that night — four fixes, five suites, three sheets, 54 pass · 5 issue · 0 fail —
moved to [`worklist-archive/2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md).*

### Pick up here, in this order

0. ~~**The worklist alarm**~~ — **DONE**, `fb00d2c`. `scripts/worklist-check.py`, step 4 of
   SESSION START. → [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)
1. ~~**② The keyboard buries the search results**~~ — **FIXED**, confirmed by Angel on the tablet
   10:34, `b644`. → [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)
2. ~~**Pam's picker + Angel's shelf pill**~~ — **DONE**, `b647`, needs eyes. It shipped wrong
   first, on a bad number of mine that was in this file.
   → [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)

3. ~~**One `--push` of `scripts/tablet-lockdown.sh`**~~ — **DONE**, 2026-09-05 11:2x, run by Angel
   from a real terminal. All four kiosk leftovers gone, verified from the laptop rather than taken
   from the script's own output: `/usr/local/bin/banco-kiosk`,
   `/usr/share/applications/banco-kiosk.desktop`, `/etc/xdg/autostart/banco-kiosk.desktop`,
   `/etc/default/banco-kiosk`. `banco-till.service` **active, NRestarts=0**. Also removed my own
   `~/.config/autostart/banco-kiosk.desktop` — the 00:12 `Hidden=true` override, which existed only
   to neutralise a file that no longer exists and whose `Exec=` named a deleted binary.
   ⚠️ **It took two goes:** the first died on `STAGE: unbound variable` (`0d6b910`). The two-step
   rewrite the night before fixed the no-terminal path and broke the working one, and nothing ran
   the working one — it needs a terminal, a live machine and a password. `--push --dry-run` now
   prints both commands and touches nothing, so the happy path is checkable from here.

   **Two of Angel's own files are still in `~/.config/autostart/`, inert and worth keeping:**
   `banco.desktop.disabled` and `banco.desktop.pre-kioskfix` (2 Sep). Neither ends in `.desktop`
   in a way GNOME reads, so nothing runs them — and `pre-kioskfix` is **evidence**: its `Exec=` is
   `chromium --kiosk --app=https://banco.wolfhold.app/pos`. **The till DID autostart in kiosk mode
   on 2 September and was backed out the same evening.** That is the third independent record that
   kiosk was tried and rejected, and it belongs with item 4 below.

4. **The tablet — two decisions left**, both for the counter, not for a flat: whether the screen
   should dim at all, and splitting `art` from an `admin` account so a cashier's password is not
   root. Everything else is fixed, locked and measured — see 🖥️ below.
5. **The counter visit — PREPPED, two sheets ready, needs the trip.** 2026-09-05.
   [`2026-09-05-standing-where-layla-stands.html`](onboarding/testsheets/2026-09-05-standing-where-layla-stands.html)
   — 21 steps: light, reach, their wifi at the counter, the gun on their surface, noise. No sale.
   [`2026-09-05-four-real-sales.html`](onboarding/testsheets/2026-09-05-four-real-sales.html)
   — 18 steps, and **the one sheet where the payment button IS pressed.** Same trip, second.
   Everything that could be settled from here has been: real barcodes verified through the shop's
   own endpoint, VAT confirmed **inclusive** (`tax = total × 8.10 ÷ 108.10`, exact on five past
   sales), and the pack-deal figures taken from the shop's own pricing function rather than read
   off the JSON — **3 → CHF 5.00, 4 → CHF 7.00 (not 6.67)**, which is Ralph's whole-packs rule and
   has never been checked on a stored record.
   **Nothing has completed a sale on this build.** Last transaction on the box: 2026-08-21, 50 ago.
   **And the window-drag bug rides along**, with kiosk now ruled out THREE ways: the note in
   `banco-till.service`, my 48-restart loop at 00:12, and Angel's own
   `~/.config/autostart/banco.desktop.pre-kioskfix` (2 Sep 17:36, `chromium --kiosk`), backed out
   63 minutes later. Next thing to try, on the machine: a GNOME rule that keeps it maximised, or an
   undecorated window from the compositor rather than from Chromium.

6. **⚠️ ESTABLISH ONE FACT BEFORE THE FELIX MEETING: does the shop have a Worldline terminal at the
   counter TODAY, or does it arrive with go-live?** It decides the payment-button question below —
   if the terminal is already there its settlement IS the card breakdown; if not, the paper
   breakdown is the only one they have. Ask it before deciding anything.
7. **The Felix conversation — four decisions that are HIS, written up, none agreed yet.**
   [`onboarding/the-felix-conversation.html`](onboarding/the-felix-conversation.html): the payment
   buttons (**Cash · Card · TWINT**, plus an ask-card-type setting so he can flip it himself),
   Worldline as **Phase 2** with the reasoning and the script, split tender parked, and the trial
   terms — **FAIL = free defect · ISSUE = quoted change**, agreed BEFORE the trial starts. Also the
   two asks worth more than they cost: one day's Banana CSV through his Treuhänder, and his real
   chart-of-accounts codes.
8. **The receipt QR — spec written, not built.**
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
## 🖥️ THE TABLET — two decisions left · 2026-09-05

*Saturday's question — "is everything in place when it boots?" — turned into nine faults, **none of
them Banco's code**: every one was the machine around it, shipping laptop defaults that are wrong
for a till. It booted to a login prompt, suspended after 15 minutes, resumed to a lock screen, went
black to a digitiser that goes deaf when it does, and had a power button that suspended the machine
you were trying to rescue. All fixed, locked, and measured over a 22-minute idle sample.
**Now: boots to the till in 17s unattended · never sleeps · never black · one touch restores it ·
80% fixed.** `scripts/tablet-postboot-check.sh` — **36 checks**.
→ the whole write-up, with the numbers:
[`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)*

### The two decisions left

1. ~~**Leave the dim on, or pin it at 80%?**~~ — **DECIDED, Angel, 2026-09-05: keep the dim.**
   *"30% dimmer is ok seems fine IMHO. I don't think it will be any problem if it dims mid sale —
   IMHO it's exactly what we want. It's not going black, so that is what really matters, so Layla
   is not touching the power button for any reason."* My 30% was a raw backlight register, not
   perceived brightness, and he was right to push back on it. **Still worth a look under shop
   lights at step A4** — but the decision is made and it is his, not a pending question.
2. ~~**Split `art` and the administrator.**~~ — **DONE, 2026-09-05**, step by step with Angel,
   verified at every gate. `admin` (uid 1001) holds sudo; `art` is out of the group and keeps
   everything a desktop till needs (audio, video, plugdev, netdev, lpadmin…). `sudo:x:27:admin`.
   **So `art`'s password is now safe to give Layla** — which was the question that started it.
   Two ssh doors: **`tablet` → art** for read-only checks (they read gsettings, which are
   per-SESSION — reading them as anyone else reports an empty session's defaults), and
   **`tablet-admin` → admin** for `--push`. Prompts made to match: art is RED ` TABLET `,
   admin is GREEN ` TABLET ADMIN `, so a shell can never be mistaken for the other.
   ⚠️ **The order was the whole risk** and it held: create → *prove sudo works* → copy the key →
   **prove the push works through the new door** → only then `deluser art sudo`. That fourth step
   was not in my first plan and should have been: a push that fails after the demotion means a
   tablet with no administrator at all.
   ✅ And it was the first real test of the `banco-till.service`-owner detection: the push ran as
   **admin** and still wrote *"autologin as art"*. Under the old `$SUDO_USER` logic that would have
   set the tablet to log itself in as the maintenance account.

### Still open on the tablet

- **The window has a title bar with a close button** — same family as Layla's window-drag bug.
- ~~**Chromium security update + no patching policy**~~ — **DONE 2026-09-05.** Chromium
  151 → **152.0.7977.75** and firefox-esr applied; till restarted and verified running the new
  binary (0 deleted inodes mapped). **And it now patches itself:** security origin ONLY, 03:15
  nightly, reboot 03:30 *only when one is owed*. Measured frequency on this machine: batches on
  08-22, 09-01, 09-05 — **one every ten days**, and it will not slow down.
  Three things that would each have silently defeated it: `Automatic-Reboot-WithUsers` (autologin
  means a user is ALWAYS logged in, so the default `false` would collect kernel updates forever
  and never reboot); Debian's default timer at **06:58** for a shop that opens at 08:00; and
  APT's `::` **appending** to Debian's existing origin list rather than replacing it, so
  "security only" quietly meant *all stable updates* until `#clear` was added.
  Also `banco-stale-browser-check`: a Chromium upgrade leaves the till running the **deleted**
  binary — patched on disk, unpatched on the glass, indefinitely, because the service only
  restarts when the browser exits. It measures `/proc/PID/exe`, marks a reboot owed, and lets the
  standard machinery handle it. **`tablet-postboot-check.sh` is now 46 checks.**
- **Wifi powersave is `default`** (likely on) — worth disabling for a till.
- ~~**The power profile had DRIFTED to `power-saver`**~~ — on mains, at 100% battery, throttling
  the till. Found only because Angel asked whether the idle test should be repeated on battery.
  `banco-lockdown.service` now sets `balanced` at every boot — it is not a setting anyone chose,
  it is one that drifted, and nothing was watching. Also confirmed and left alone: UPower does
  **HybridSleep at 2%**, which is right — a Kassenbuch write interrupted by a flat battery is
  worse than a controlled shutdown.
- **`shop-lte` is ACTIVE alongside wifi** — the failover exists and is live. Decide whether it is
  meant to be always-on, and test it at the shop, not in a flat.
- **These two scripts belong in the onboarding kit**, not just on Angel's tablet: anyone who clones
  Banco onto a tablet meets the identical defaults. → archive. The account split and the two
  coloured prompts belong in that write-up too — they are currently hand-made on this one machine.

---

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
## ⓞ THE COUNTER VISIT — GO BEFORE THE SHIFT, NOT ON IT

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

