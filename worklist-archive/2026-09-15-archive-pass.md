# Archive pass — 2026-09-15

*Moved out of `WORKLIST.md` **verbatim, nothing deleted**. The fifth cut. Triggered by
`scripts/worklist-check.py` after the file reached 507 lines: the alarm named THE DECK (172),
Standing facts (64) and THE TABLET (57), and all three are cut here.*

*Nine blocks, every one either **closed**, **settled**, or **parked by Angel's own call**. One was
**stale** — item 5 still said no sale had been completed on this build, four days after Angel spent
ninety minutes ringing them. A pointer stays in `WORKLIST.md` for each.*

---


## 0️⃣a · FR/IT — retired as a blocker

*Angel walked it in Italian and caught `Samstag` before any check did. What remained was REGISTER, not correctness. Retired 2026-09-06; kept because the 90% figure and the `Titolare`/`Proprietario` question are the ones that come back.*

0️⃣a **FR/IT — three passes done, call it 90%.** Written here, read by a vision model on ~25 real
   screens, walked by Angel in Italian — he caught `Samstag` before any check did. **The "nobody
   has read a word" framing was overstated and is retired (2026-09-06).** What is left is
   REGISTER: `Titolare` or `Proprietario`, is `Giornata` right for a nav slot. Perhaps 20–30
   judgement calls out of ~1,100, a minute each for Angel or Felix. A footnote, not a blocker.

---


## 0 · 1–3 · 4 · 6 — startup, keyboard, Pam's picker, kiosk leftovers, the tablet, Worldline

*All closed. Kept for the cold-boot finding — invisible for four months because every proof was `reboot` over SSH with nobody watching the screen (LESSON #1, the fourteenth) — and for the Worldline answer.*

0 · 1–3 · 4 · 6. ~~**Startup · keyboard · Pam's picker · kiosk leftovers · the tablet ·
   Worldline**~~ — **ALL CLOSED.** The till did not come up at all on a cold boot (five faults,
   now ~58s unattended, invisible for four months because every proof was `reboot` over SSH
   **with nobody watching the screen**); eleven tablet faults, none of them Banco's code; and
   Worldline is **answered — Phase 1 integrates NOTHING, Banco replaces the CALCULATOR.**
   → [`09-05`](worklist-archive/2026-09-05-archive-pass.md)

---


## 5 · THE COUNTER VISIT — closed by the day itself

***Stale when archived.** It read *"Nothing has completed a sale on this build. The last one was 2026-08-21 — sixteen days."* Angel worked the counter 2026-09-10, 11:33–13:04, and ran both sheets: 9 pass · 0 fail, then 25 pass · 2 issue · 0 fail. The prep prose was already archived on 09-10; this is the copy that stayed behind in the deck.*

5. 🔴 **THE COUNTER VISIT — THE BIGGEST OPEN RISK IN THIS FILE, and it is not code.**
   **Nothing has completed a sale on this build. The last one was 2026-08-21 — sixteen days.**
   Two sheets, prepped since 2026-09-05, needing only the drive.
   [`2026-09-05-standing-where-layla-stands.html`](onboarding/testsheets/2026-09-05-standing-where-layla-stands.html)
   — 21 steps: light, reach, their wifi at the counter, the gun on their surface, noise. No sale.
   [`2026-09-05-four-real-sales.html`](onboarding/testsheets/2026-09-05-four-real-sales.html)
   — 18 steps, and **the one sheet where the payment button IS pressed.** Same trip, second.
   Everything settleable from here was settled — barcodes, VAT **inclusive**, pack deals run
   through the real pricing function. **Print a receipt while you are there** (item 8).
   → [`09-05`](worklist-archive/2026-09-05-archive-pass.md)
   ~~**The window-drag bug**~~ — **CLOSED, a compromise Angel accepted:** the title bar is both
   the cause AND the escape hatch, so it is now a DRILL (steps B4a–c).
   → [`09-05`](worklist-archive/2026-09-05-archive-pass.md)

---


## The tablet · PORTRAIT and ⓪h–k

*Both done and proven on the glass. **Do not lock rotation** — at 1440 × 2160 the whole denomination table fits with no scrolling; landscape cannot.*

### ~~⚠️ PORTRAIT~~ — **DONE 2026-09-05, PASSED.** At 1440 × 2160 the whole denomination table
fits with no scrolling; landscape cannot. **Do not lock rotation.**
→ [`09-05`](worklist-archive/2026-09-05-archive-pass.md)

⓪h–k. ~~**The four portrait findings**~~ — **ALL DONE, b690–b693.** The note strip and the 💬
   anchor both passed on the glass 2026-09-06; `Samstag` proven in three languages; (j) withdrawn.
   → [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)

---


## The tablet · the title bar's close button — NOT A BUG, A PRICED TRADE

*Do not reopen. Angel priced it and the reasoning is in `banco-till.service`. Archived because it kept being re-raised, which is the LESSON #3 shape: a remembered decision is a hypothesis with a timestamp, and this one has its expiry written down.*

- ~~**The title bar's close button**~~ — **NOT A BUG, A PRICED TRADE. Do not reopen.** Angel,
  2026-09-05: *"I think it's fine the way it is ... or else in full screen mode all the time they
  don't see the battery level or the wifi."* He is right and it is written in
  `banco-till.service`: *"Dropping --kiosk left a title bar with a close button on it. A cashier
  who taps that has no way back. **Now it comes back in three seconds.**"* (`Restart=always`,
  `RestartSec=3`.) The trade bought a permanently visible GNOME bar — battery, wifi, bluetooth —
  plus Banco's own one-tap fullscreen toggle in the top bar, and a route to the OS for things like
  a screenshot with the folio detached. **I put this on the list without reading the comment**, the
  same shape as the kiosk loop. LESSON #3: a remembered decision is a hypothesis with a timestamp.

---


## The tablet · Chromium security update + the patching policy

*Done, and it now patches itself — security origin only, 03:15 nightly, reboot 03:30 only when one is owed. Kept in full because of the three mechanisms that would each have silently defeated it (`Automatic-Reboot-WithUsers` under autologin, Debian's 06:58 default timer for a shop that opens at 08:00, and APT's `::` appending rather than replacing the origin list), and because of `banco-stale-browser-check` — a Chromium upgrade leaves the till running the deleted binary, patched on disk and unpatched on the glass, indefinitely.*

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

---


## The tablet · the power profile had DRIFTED to power-saver

*Not a setting anyone chose — one that drifted, on mains, at 100% battery, throttling the till, with nothing watching. Found only because Angel asked whether the idle test should be repeated on battery. `banco-lockdown.service` now sets `balanced` at every boot.*

- ~~**The power profile had DRIFTED to `power-saver`**~~ — on mains, at 100% battery, throttling
  the till. Found only because Angel asked whether the idle test should be repeated on battery.
  `banco-lockdown.service` now sets `balanced` at every boot — it is not a setting anyone chose,
  it is one that drifted, and nothing was watching. Also confirmed and left alone: UPower does
  **HybridSleep at 2%**, which is right — a Kassenbuch write interrupted by a flat battery is
  worse than a controlled shutdown.

---


## ⓜ BIRTH YEAR INSTEAD OF A FULL BIRTHDATE — analysed and parked

*Angel's idea, parked by his own call: *"if somebody complains about it, fine, then we'll fix it … it's better that we don't break anything and make our life more complicated for nothing."* Moved here whole because it exists so the thinking is not lost, not so someone picks it up — which is precisely the archive's job. **The hard edge is the design:** someone born in 2008 is 18 in January and 17 in December, so a year cannot decide age for exactly the cohort the gate exists to catch; the ambiguous year falls through to the human holding the ID.*

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


## Standing fact · hardware gets a label when it earns one

*Settled 2026-08-28. **Nothing needs writing** — the label button is already one tap (`catalog.html:414`) and a scanned label with no manufacturer EAN already resolves by SKU (`pos_router.py:2197`). A printed binder was considered and rejected. Archived in full because the reasoning — the shelf is the signal, MISC is self-correcting, staff read their own selling patterns better than any rule we could write — is what stops it being re-proposed.*

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
