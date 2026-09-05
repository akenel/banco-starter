# Archive pass — 2026-09-05, morning

*Moved out of `WORKLIST.md` verbatim, nothing deleted. The first pass triggered by
`scripts/worklist-check.py` rather than by somebody noticing: the file crossed 500 lines the moment
the keyboard fix was written up, and the alarm named this section.*

## From "🌙 CLOSE OF 2026-09-04, ~23:30" — what went in that night

*Kept because it is the receipt for four fixes and five suites, and because two of the four were
found by a person looking at a screen after the sheet had ended. It is history now; the deck it sat
above is still live in `WORKLIST.md`.*

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



---

## The three that closed on 2026-09-05

*Moved the same day they closed, which is the rule the alarm exists to enforce. Pointers stay in
`WORKLIST.md`.*

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

2. ~~**Pam's category-dropdown request**~~ + ~~**Angel's shelf pill**~~ — **BOTH DONE**,
   2026-09-05, `c42a207` + `234a601`, live as **`b647`**. Needs eyes on the tablet.
   The picker now opens with the shelves the search is about: **`papers` → 6, `elements` → 5,
   `lighter` → 2** (`raw` and `king` hit the cap of 8), each with the count you actually get,
   and the full 52 still underneath. And every result row carries a third pill — 🔞 18+ · 🌿 CBD ·
   **🏷️ its shelf** — which is a BUTTON: tapping it filters to that shelf without opening the
   picker at all. Angel's idea, and it is Pam's request through the other door. Row height
   measured before and after: **142px → 142px**, so it costs nothing under the keyboard.
   `prove-category-facet-is-honest.py` **16** · `prove-the-shelf-is-on-the-row.js` **16**.

   ⚠️ **It shipped wrong first, and the wrong number was in THIS FILE.** The line above used to
   read *"searching `papers` touches 6"* — measured with `name ILIKE`, which is not the predicate
   the search uses. Built on that, the first version offered **39 shelves for `papers` and 50 of
   52 for `king`**, because search recall deliberately reaches into `description`,
   `supplier_name` and fuzzy similarity, so nearly every shelf holds something that mentions the
   word. Shelves are now CHOSEN by a strong signal (the word is in the shelf's name or the
   product's own name/sku/barcode) and COUNTED by the real search, so the number on the option is
   the number you get when you pick it. **The dev fixture could not have caught it** — every test
   row had the term in its name — so it now carries a decoy whose only link is a passing mention.



---

## The tablet, 2026-09-05 afternoon — the narrative

*Moved the same day, because the alarm said so about my own write-up thirty seconds after I wrote
it. The open decisions stayed in `WORKLIST.md`; this is the evidence behind them.*

## 🖥️ THE TABLET — 2026-09-05 afternoon · FIXED AND MEASURED, two decisions left

*Angel, Saturday: "make sure when the tablet boots up that all the configurations are in place
and we test a few hard starts and restarts." Everything below was found by asking that question.
**Not one of these was Banco's code** — every one was the machine around it, shipping sensible
laptop defaults that are wrong for a till.*

| | before | after |
|---|---|---|
| boots to | a **GDM login prompt**, waiting for a password nobody at the counter has | the till, **17s**, unattended (`gdm-autologin`, measured) |
| after 15 min idle | **suspended**, resumed to a **lock screen** | stays awake — 0 suspend events over 22 min |
| screen | went **fully black**, and the digitiser goes **deaf** when it does | never black; dims, and **one touch restores it** |
| power button | **suspended** on a press — the obvious recovery made it worse | asks (`interactive`); long-press still force-offs |
| brightness | 19–25%, driven by the ambient light sensor | 80% fixed, sensor off |
| all of the above | writable — one tap from changing | **locked** |

**`scripts/tablet-postboot-check.sh`** — 36 checks, run from the laptop, read-only, no sudo. It
checks settings **in force** (gsettings + writable), not files on disk; that the compiled dconf db
is newer than its keyfile; that the kiosk files stayed absent; that restarts are not CLIMBING after
boot; and that the session was created by **gdm-autologin** rather than by a human — the first
version read the config file and would have passed on a boot where autologin silently failed.

**Proof, not assertion.** 22-minute idle sample, 30s reachability polls, and the touch caught in a
3-second window: `2093 (30%) idle 1132s` → `5468 (80%) idle 0s`.


### And this belongs in the onboarding kit, not just on Angel's tablet

Anyone who clones Banco onto a tablet meets the **identical** defaults. `tablet-lockdown.sh` and
`tablet-postboot-check.sh` are part of the product now and belong beside the go-live runbook.



---

## The method note from the night of 2026-09-04

### The method note worth keeping from tonight

**Both testers asked for the same thing: name the sample.** Steps that said *"find a product with a
long name"* and *"search for something with a lot of matches"* handed them my homework. Real terms
from the shop's own 5,427 active products are in ⓒ5 — use them.

**And a grep only finds a shape somebody thought of.** Six of tonight's dates were found by
searching the code; five were found by Layla LOOKING AT THE SCREEN. `prove-swiss-dates.js` section
N2 now reads the rendered text of seven reports and fails on any slashed date — the only check in
that file that does not care how the string was produced.



---

## ⓞ The counter visit — the prose version, superseded by the two sheets

*Every step below now lives in `onboarding/testsheets/2026-09-05-standing-where-layla-stands.html`
and `-four-real-sales.html`, where a person can actually mark it PASS/ISSUE/FAIL. Kept for the
reasoning, not as a checklist — two copies of one list is how the list stops being true, and this
repo lost time to exactly that shape on 2026-09-04.*

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

---

## The two tablet decisions — both answered on the day

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



---

## The GNOME Shell extension that was built and removed, 2026-09-05

   ⚠️ **A GNOME Shell extension was built for this and REMOVED ON PURPOSE — do not rebuild it.**
   It snapped the window back, reported `State: ACTIVE`, and did nothing at all, because it matched
   `wm_class` "chromium" and an `--app=` window is called something else entirely. **Angel found
   that by dragging a window; no check could have.** Dropped even though it was fixable: custom
   code inside the compositor on a machine that takes money, silently undoing anything deliberate,
   and it taught nobody anything.

---

## Counter-visit prep — what was settled from the laptop

   Everything that could be settled from here has been: real barcodes verified through the shop's
   own endpoint, VAT confirmed **inclusive** (`tax = total × 8.10 ÷ 108.10`, exact on five past
   sales), and the pack-deal figures taken from the shop's own pricing function rather than read
   off the JSON — **3 → CHF 5.00, 4 → CHF 7.00 (not 6.67)**, which is Ralph's whole-packs rule and
   has never been checked on a stored record.
   **Nothing has completed a sale on this build.** Last transaction on the box: 2026-08-21, 50 ago.


---

## The tablet section, as it stood at the end of 2026-09-05

## 🖥️ THE TABLET — fixed, locked and self-patching · 2026-09-05

*Saturday's question — "is everything in place when it boots?" — turned into nine faults, **none of
them Banco's code**: every one was the machine around it, shipping laptop defaults that are wrong
for a till. It booted to a login prompt, suspended after 15 minutes, resumed to a lock screen, went
black to a digitiser that goes deaf when it does, and had a power button that suspended the machine
you were trying to rescue. All fixed, locked, and measured over a 22-minute idle sample.
**Now: boots to the till in 17s unattended · never sleeps · never black · one touch restores it ·
80% fixed.** `scripts/tablet-postboot-check.sh` — **36 checks**.
→ the whole write-up, with the numbers:
[`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)*

### Both decisions answered, 2026-09-05

- **Keep the 30% dim.** Angel: *"it's not going black, so that is what really matters, so Layla is
  not touching the power button for any reason."* My "30%" was a raw backlight register, not
  perceived brightness — he was right to push back. Still worth a look at step A4 under shop lights.
- **`art` and `admin` are split.** `sudo:x:27:admin`; `art` keeps audio/video/plugdev/netdev/lpadmin
  and can change nothing. Proven: *"Sorry, user art may not run sudo on art."*
  **So `art`'s password is now safe to give Layla** — the question that started it.
  Two ssh doors: **`tablet` → art** for read-only checks (gsettings are per-SESSION), **`tablet-admin`
  → admin** for `--push`. Prompts match: art RED ` TABLET `, admin GREEN ` TABLET ADMIN `.
  → the order, the gates and why step 3½ mattered:
  [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)



---

## Window-drag: what was considered and rejected, 2026-09-05

   Considered and rejected on the day: `--kiosk` (third rejection), a 90%-centred restore geometry,
   PWA `display: fullscreen`, and `window-controls-overlay` — all remove the title bar, and the
   title bar is the thing that always works.

- `--kiosk` — third rejection. Hides the GNOME bar, which is *why* people reach for the corner.
- **A 90%-centred restore geometry** — Chromium `--window-size`. Would have made the accident tidier; the window still has a title bar, so it can still be dragged anywhere.
- **PWA `display: fullscreen`** — removes the title bar, and with it the only escape that cannot be blocked.
- **`window-controls-overlay`** — Angel's own idea and the most elegant of them: OS bar always visible, no Chrome title bar, and drag regions are opt-in so we would declare none. Rejected for the same reason as fullscreen, plus uncertain support on Linux/Wayland and it needs the PWA properly installed rather than launched with `--app=`.
- **A GNOME Shell extension that snapped the window back** — built, loaded, reported `State: ACTIVE`, did nothing at all (matched `wm_class` "chromium"; an `--app=` window is not called that). Removed on purpose even once fixable: compositor code on a machine that takes money, silently undoing anything deliberate, teaching nobody anything.


---

## The deck's closed items, as they read at the end of 2026-09-05

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



---

## The window-drag decision, in full

   ~~**And the window-drag bug rides along**~~ — **CLOSED as a compromise Angel accepted,
   2026-09-05.** Not fixed, and deliberately so. The window CAN still be dragged off; what changed
   is that there are now **four independent ways back**, and Angel found the best one himself:
   **drag the grey title bar back**, tap the amber **"⛶ Tap to fill the screen"**, tap **⛶**, or
   press the app in Activities (`Restart=always`).
   **The insight that settled it:** the title bar is both the cause AND the escape hatch. It lives
   OUTSIDE the web page, so no modal, error or popup Banco ever draws can cover it or block it.
   Angel's worst fear — *"a popup 90% covered blocks the possibility to restore"* — cannot happen.
   **Fullscreen and window-controls-overlay would remove the accident and remove that escape with
   it**, leaving us trusting our own code never to trap anyone. The OS is the better bet.
   ⚠️ **The real gap is knowledge, not code.** Angel: *"i did not know i could re-drag the window
   to a useable location"* — after a week of testing. Layla met this on 4 Sep and **rebooted the
   till**. So it is now a DRILL, not a hope: steps **B4a/B4b/B4c** of
   [`2026-09-05-standing-where-layla-stands.html`](onboarding/testsheets/2026-09-05-standing-where-layla-stands.html)
   have her break it on purpose and recover it three ways, unaided, with nobody waiting.
   *"If she cannot, that is a FAIL and it is the most useful failure on this sheet."*
   Five alternatives were considered and rejected on the day — kiosk, a 90%-centred restore, PWA
   fullscreen, window-controls-overlay, and a GNOME Shell extension. All of them remove the title
   bar, and the title bar is the thing that always works.
   → [`2026-09-05-archive-pass.md`](worklist-archive/2026-09-05-archive-pass.md)



---

## Portrait — the reasoning, 2026-09-05

### ⚠️ PORTRAIT — the close-out has never been seen in the orientation it will be used in

**Angel, 2026-09-05, describing what actually happens at closing:** *"they are unplugging the tablet
… walk to the back of the shop most likely now in **portrait view** as it sits in the hand and is on
the lap … Pam or Layla start counting the cash and working the tablet numbers."* And: *"I say portrait
because **they will do that**, not because we say hey run this in landscape view — they will just
naturally go to portrait like they do with their phones."*

**The tablet can and will rotate.** Measured: three accelerometers, `iio-sensor-proxy` **active**,
and the lockdown says **nothing** about rotation — 0 matches.

**Every proof in this repo runs at 1440 × 895, landscape.** The keypad, the search list, the row
snap, the date grids, the discount chips — all of it measured on a stand. **The one flow that will
happen in portrait, on a lap, is the close-out: counting cash, the Z-report, the shift close.
The flow with all the money in it is the flow we have never looked at in the posture it will be
used in.** Same shape as the folio keyboard and the LTE proved in a flat.

**This reverses the plan.** ⓞ said *"choose a landscape stand and lock rotation in the OS."*
Locking landscape would break their real end-of-day routine. **Do not lock it — test portrait.**

Roughly 960 × 1440 logical. Two-column layouts collapse, the keypad takes proportionally more of
the screen, sticky bars move. Start with `/pos/closeout` and `/pos/my-day`, then the drawer count.
Not started.



- **[`the-till-morning-to-night.html`](onboarding/the-till-morning-to-night.html)** — the one-page
  card to pin by the till, written 2026-09-05 from Angel's own description of the day. Opening,
  what "dim" means, the three ways back if the window moves, closing, and the three don'ts
  (the ×, the web in the till's window, unplugged overnight). **Needs Angel's corrections, then
  Layla's eyes.** Ends by saying the stricter kiosk mode exists and what it would cost — *"your
  call, once you have lived with it."*


---

## ⑥ Does the shop have a Worldline terminal today? — ANSWERED by Angel, 2026-09-05

**Yes — TWO, at the counter, used for every card sale today.** Both do TWINT, and **TWINT in
Switzerland is Worldline-only**, so there is no alternative vendor to consider. The second is a
spare: if one breaks down or runs flat they pick up the other. Angel is not certain they are the
identical model — *"I'm not sure if it's exactly the same one with the same buttons, but it does
it all"* — and both do the same job.

**Phase 1 integrates nothing.** Worldline told Felix, by email and by phone, that if he wants to
hook up his own POS they will supply a **sandbox** to test against. That offer is real and it is
**Phase 2** — after the shop likes the app, after Banco's own problems and features are worked
out. Angel, plainly: *"we're not gonna integrate it. We're not gonna do the sandbox work. We're
not gonna do anything. We're gonna move on and really do it exactly the same way as what they do
today."*

**What they do today, and what Banco replaces.** Rafi or Layla pulls out a **calculator**, adds
the items up, turns it round and shows the customer: *this is what it is*. The customer nods.
They pick up the Worldline terminal, **type that amount in by hand**, and take the card or the
TWINT. The number on the calculator is the number typed into the terminal. A fat-finger is
possible and is not a common problem there.

So **Banco replaces the calculator, not the terminal** — and that settles the shape of ⑦'s
payment buttons: they are a **record of tender** (which way the money came in), never a payment
instruction. The card breakdown they reconcile against is the terminal's own settlement, which
they already have and already trust.

---

## ⓪ Walking the card on the tablet — four cold boots, 2026-09-05 evening

*Angel drove; every observation below is his, watching the glass with a kitchen clock. The plan
was a five-minute sanity smoke test before running the instruction sheet properly. It found a bug
that would have met Layla on Monday morning.*

### What the card claimed, and what actually happened

`onboarding/the-till-morning-to-night.html` said: *"Press the power button once. Wait about twenty
seconds. The till comes up on its own — no password, nothing to tap."*

Four power-offs later, every clause of that sentence was wrong except "press the power button
once".

**Round 1 · 17:36.** Boot ran long, text screens scrolled, then **`Authentication required — the
login keyring did not get unlocked when you logged into your computer`**, with the on-screen
QWERTZ keyboard under it (photo taken on Angel's phone; GNOME's own screenshot is blocked by
lockdown). He typed `art`'s password. Three minutes later the till was there, so it looked fine.

**Round 2 · 17:54.** Same password box, and this time he looked immediately after unlocking:
**a white window. No page. No title.** He waited **thirteen minutes**, hands off. Tapping the
middle did nothing but maximise the emptiness. The title bar read `banco.wolfhold.app_/pos` —
Chromium's fallback when a window **has no page title at all**, which is what gave it away.

### The cause

`/etc/gdm3/daemon.conf` has `AutomaticLoginEnable=true` / `AutomaticLogin=art`. Autologin means
**GDM never has art's password**, so the login keyring stays **locked**. Chromium asks
gnome-keyring for its safe storage at startup, that request blocks, and **Chromium never
navigates**. Unlocking the keyring does not rescue it — Chromium does not retry. The window sits
empty until the process is restarted.

Everything downstream was healthy the whole time, which is why nothing ever flagged it:

```
banco-till.service   active (running), 855 MB, 0 restarts
curl https://banco.wolfhold.app/   → 200 in 0.086s   (from the tablet itself)
```

**Angel's × recovered it in 3 seconds**, exactly as the card promises — because the restart
happens *after* the keyring is open.

### Why nobody had ever seen it

Every previous boot proof was `reboot`, **issued over SSH, with nobody looking at the screen** —
and the one time Angel did watch, in round 1, three minutes passed before he looked, by which
point the × was not needed because he had already unlocked and the window had been restarted
by... nothing; it had simply had time. LESSON #1 and #6 in one: green on every layer reachable
from a terminal, dead on the only layer a person stands on.

### The fix

One flag in our own unit, `~/.config/systemd/user/banco-till.service`:

```
--password-store=basic
```

Chromium then keeps its own local store and never asks gnome-keyring anything. Chosen over
blanking the login keyring's password, which also works but weakens a real credential store to
solve a problem that is not about credentials. Banco's own login is Keycloak inside the page, so
Chromium stores nothing worth protecting. **The cookies survived the switch** — the till came back
as Layla with no re-login, so the theoretical one-time Keycloak prompt did not happen.

*(First write of the flag used a doubled backslash and would have been parsed as a stray argument;
caught with `systemctl show -p ExecStart` before it reached a boot.)*

**Rounds 3 and 4 · 18:24 and 18:31 — both clean.** No password box, no white window, page loaded,
Layla signed in. `journalctl -b | grep -c "did not get unlocked"` → **0**.

### The numbers, from the machine, identical across both good boots

```
firmware 7.86s + loader 14.99s + kernel 7.99s + userspace 1m15.17s  =  1m 46s
kernel start → till launch                                          =  68s
1min 11.257s  plymouth-quit-wait.service     ← waiting behind the next line
     51.692s  banco-lockdown.service         ← OURS. the biggest single item in the boot
      4.410s  NetworkManager-wait-online.service
```

### What else the walk turned up

- **It lands in the GNOME Activities overview, not the till** — search bar on top, a dock with
  Firefox, a terminal, a file manager and a calculator along the bottom, the till small in the
  middle. It does not leave on its own; Angel sat in it for minutes. **I wrongly withdrew this
  finding once**, explaining round 1's screenshot away as the screenshot tool's own UI — then his
  phone photo of round 3 showed exactly the same screen. One tap on the till fills the screen.
  Shell 48.7, no extensions installed, Debian ships no `no-overview` package. Angel: *"I don't
  have a problem with this."*
- **The power button is `power-button-action = 'interactive'`** — a gentle click, not a hold.
  It does **not** wake a dim screen; it raises a confirmation box that says the tablet will power
  off **in sixty seconds** if nobody answers. Angel pressed it deliberately and cancelled:
  **everything intact — till, cart, session.** Residual risk accepted rather than fixed: a brushed
  button nobody notices for a minute powers the till off mid-trading. Making the button do nothing
  would remove the easy way to switch it off at night, so it is documented instead.
- **Power off is one click → confirm → under 10 seconds.** The card said *hold*.
- **The red Lenovo "press enter to interrupt normal startup" prompt**, then a blue GRUB 2.12
  screen, then pages of scrolling text. Nobody had ever told Layla to ignore all three.
- **`Other users are logged in` in the shutdown dialog was my own SSH session** — my harness
  changing what Angel was reading. Confirmed by its absence once I stayed off the machine.

### Settings that back up the daytime section (all correct as written)

```
idle-dim true · idle-brightness 30 · idle-delay 0 (never blanks) · sleep-inactive-ac 'nothing'
```

### The card, rewritten the same evening

Opening now says: gentle click · ignore the red Lenovo writing · a blue screen and scrolling text
are normal · **about two minutes**, switch it on before you take your coat off · it finishes on the
overview, **tap the till once**. The power-button box is now a red `stop` note carrying the sixty
seconds and *tap Cancel, nothing is lost*. Closing says press once, not hold, off in under ten
seconds.

**Still open:** the overview tap (⓪a), `banco-lockdown`'s 51.7s (⓪b), and whether the cashier
should log out at night — Layla closes, Rafi opens, and the till stays signed in as whoever was
last on it (⓪c).

---

## ⓪b The 51 seconds — two things waiting on each other, in front of the cashier

**Before → after, from the machine, cold boots either side:**

```
total boot            1m 46.0s   →   58.1s
userspace                75.1s   →   27.3s
banco-lockdown.service   51.7s   →    3.6s
plymouth-quit-wait     1m 11.3s  →   22.7s
kernel start → till         68s  →     19s
```

### The two wrong answers first

**Wrong answer #1: profile it.** `scripts/tablet-lockdown-profile.sh` ran the real script under a
clock — **1.28 seconds**. Same script, same machine, forty times faster than at boot. The harness
could not make the shape the bug lived in, so it reported the code was fine. (It also could not
see the LAST command's duration at all — a gap is measured to the next timestamp, and there
isn't one.)

**Wrong answer #2: the self-install.** Tracing the real boot showed the script rewriting its own
unit file and calling `systemctl daemon-reload` **from inside the unit that was starting**. That
looked like the answer, and it is genuinely wrong — installing is something you do TO a machine,
not something a machine does to itself on the way up — so it was guarded with `INVOCATION_ID`.
**The boot after that fix: 51.0s. Unchanged.** Diagnosis wrong; the guard was right and stayed.
(The trace also lost its timestamps, because systemd expands `${...}` in `ExecStart` itself, so
the `PS4` in the drop-in came out empty.)

### The real one

File timestamps narrowed it: lockdown wrote its last file at 18:57:38 and did not exit until
18:58:28. Fifty seconds after it had stopped doing anything.

```
banco-lockdown          18:57:37 → 18:58:28    (last file written 18:57:38)
power-profiles-daemon   active at 18:58:49     — 21s AFTER lockdown gave up
```

`powerprofilesctl get` is a **D-Bus call**. D-Bus tries to activate `power-profiles-daemon`, which
comes up with `multi-user.target` — and `banco-lockdown.service` is `Before=display-manager.service`,
so the daemon **cannot start until lockdown finishes**. Lockdown waits for the daemon, the daemon
waits for lockdown, D-Bus times out — twice, 25s each. **Fifty of the fifty-one seconds.**

The comment three lines above that call already recorded the daemon coming up 72 seconds late in a
*different* failure (the `|| echo` that stopped `set -e` aborting the script). It stopped the
script dying and did nothing about it blocking.

**And the step had never once worked at boot.** It always printed *"daemon not up yet — left
alone"*. It has only ever cost time.

**Fix, both halves:** `timeout 3` on the call so it can never do this again, and the profile is now
set by **`banco-power-profile.service`** — ordered after the daemon and after the display manager,
so if it ever waits, it waits *behind* the till instead of in front of it.

### Which then had a cycle of its own

First version was `WantedBy=multi-user.target` + `After=power-profiles-daemon.service` — and
`power-profiles-daemon` is itself `After=multi-user.target`. systemd resolves a cycle by **silently
dropping a job**: the unit was enabled, had its symlink, and never ran, with nothing in the log.
Caught only because the boot check said `inactive`. Moved to `WantedBy=graphical.target`, and
installed with `systemctl reenable` — `enable` adds the new symlink without removing the old one,
which would have left the cycle in place on any machine that had seen the first version.
Now: **runs at kernel+35s, after the till is on screen, `active`, profile `balanced`.**

### And then the fast boot exposed a race that had always been there

With lockdown fixed, the till launches at **19s** instead of 68s — **three seconds** after
`NetworkManager-wait-online` instead of sixty-eight. It lost the race and came up as a **white
window titled `banco.wolfhold.app/pos`**. Angel's × brought it back in three seconds, same
network, same page, just later.

`wait-online` going active means an interface has an address. It does **not** mean wifi has
associated or that DNS answers. **We did not break the till — we removed the 50-second cushion
that had been hiding this since the day it was built.** Note the two white screens are
distinguishable by their window title: `..._/pos` with an underscore is Chromium with **no page
at all** (the keyring stall); `.../pos` with a slash is **a page that failed to load**.

Fix: `ExecStartPre` on `banco-till.service` waits for `https://banco.wolfhold.app/` to answer
before Chromium opens. `timeout 90` does the counting — **no shell variables**, because systemd
expands `$WORD` in `ExecStart*` itself and would have blanked a loop counter — and it ends in
`|| true` so a genuine outage still opens the browser and shows its own error. It costs nothing
when the network is up: `ExecStartPre` and `ExecMainStart` land in the same second.

### Nine cold boots

Every number above came from the machine, not from a stopwatch, and every fix was proven by
powering the tablet off and on again with somebody watching the screen.

---

## ⓪a The overview tap — fixed, and the dconf default that wasn't enough

**The problem.** GNOME Shell starts a session in the Activities overview when no window exists yet,
and it does not leave on its own. The till appears ~19s in, so every morning ended on a search box,
a dock holding **Firefox, a terminal and a file manager**, and the till shrunk to a card in the
middle, waiting for somebody to press it. Angel sat in it for minutes, hands off, twice. It is also
the reason the very first sighting was mis-explained: on 2026-09-05 I withdrew it as an artefact of
the screenshot tool, and a phone photo of the next boot showed the identical screen.

**The fix.** GNOME 48 has no gsettings key for this and Debian ships no `no-overview` package, so:
`banco-no-overview@banco`, fifteen lines, written by `scripts/tablet-lockdown.sh` into
`/usr/share/gnome-shell/extensions/` — **system-wide, so a wiped user profile still gets it**. It
hooks `startup-complete` and calls `Main.overview.hide()`, and only when
`Main.layoutManager._startingUp` is true, so re-enabling it by hand never yanks the overview away
from somebody who opened it deliberately.

**And the part that did not work first time.** Adding
`[org/gnome/shell] enabled-extensions=['banco-no-overview@banco']` to the system dconf keyfile was
**not enough** — after a cold boot `gnome-extensions info` still said `Enabled: No`, and
`dconf read` returned `@as []`. The key needed a **LOCK**
(`/org/gnome/shell/enabled-extensions` in the locks list). With the lock in place the value took
**immediately, without a reboot**: `writable: false`, `State: ACTIVE`.

**Proven on cold boot eleven: straight to the till, full screen, no press.**

Failure modes, deliberately: a GNOME upgrade that rejects the extension degrades to **one press on
the till**, never a blank screen. And because locking the key means GNOME cannot switch the
extension off by itself, `disable-user-extensions` is left **unlocked** as the escape hatch.

### What that boot then showed — a THIRD white screen, and a real defect behind it

Boot eleven came up full screen on **our own Login page, rendering blank**, titled
`Login - HelixPOS - Artemis Store`. Angel's × brought it back **as Layla** — so the session was
never gone.

Three distinguishable white screens now, all cured by the × in three seconds, and the **window
title tells them apart**:

| title | meaning | status |
|---|---|---|
| `banco.wolfhold.app_/pos` (underscore) | Chromium with **no page at all** | the keyring — FIXED |
| `banco.wolfhold.app/pos` (slash) | **a page that failed to load** | the network race — guarded |
| `Login - HelixPOS - Artemis Store` | **our login page, drawn blank** | OPEN |

**The hard fact found while chasing it, true regardless of whether it is the cause:**

```
curl https://banco.wolfhold.app/pos   →   200,  <title>Login - HelixPOS - Artemis Store</title>
```

`GET /pos` returns **200 with the Login page** when unauthenticated — and `src/static/pos/sw.js`
caches **any** `resp.ok` response under the `/pos` key:

```js
if (url.pathname === '/pos' || url.pathname.startsWith('/pos/')) {
  event.respondWith(fetch(req).then((resp) => {
    if (resp && resp.ok) { caches.open(CACHE_NAME).then((c) => c.put(req, clone)); }
```

So the service worker will store a login page under the till's own URL and hand it back to a
**signed-in cashier** on any later fetch failure. That is LESSON #13 exactly: the server is right,
the tests are green, and the stored copy the screen renders from is wrong — and the shadow always
wins, because the shadow is what renders. Needs a marker on that response the SW refuses to cache,
plus a `CACHE_NAME` bump to evict what is already stored.

Not chased further on the night: three diagnoses had already been wrong, and guessing a fourth on
Angel's boots was the wrong trade.


---

## ⓪d The third white screen — and the diagnosis above it that was WRONG

**Correction, written the same night.** The section above says the service worker "can hand a
signed-in cashier a login page" because `GET /pos` returns 200 with the Login page. **That is
wrong and it is not a bug.** `/pos` IS the login route — `@html_router.get("/pos", name="pos_login")` —
and the dashboard is `/pos/dashboard`. The service worker caching `/pos` is caching the login page
under the login page's own URL, which is correct. `/pos/scan` and `/pos/dashboard` both return
real 200 pages when signed out too (auth is a token in sessionStorage, checked client-side), so
the cached shell is fine as well. Both of my theories died on one `curl`.

### What the white screen actually was

`login.html` runs on `DOMContentLoaded`, finds the token, and does
`window.location.href = '/pos/dashboard'`. While that navigation is in flight the browser shows
nothing and **keeps the old title** — which is exactly what Angel photographed: pure white, titled
`Login - HelixPOS - Artemis Store`.

And there was a way for that navigation to end in nothing at all:

```js
.catch(() => caches.match(req).then((cached) => cached || caches.match('/pos/scan')))
```

**`caches.match` resolves to `undefined` on a miss**, so `respondWith(undefined)` handed the
browser nothing. Network fails (still settling, seconds after boot) + nothing in cache (first boot,
or a deploy that just evicted every cache — `CACHE_NAME` carries the build stamp) = **a blank white
screen**. The × worked because a restart happened later, when the network was warm.

### The fix

The fallback chain now ends in a real page instead of `undefined` — `offlinePage()`, served 503,
saying *"Reconnecting to the till… nothing has been lost… it will come back on its own"*, with a
**Try now** button and a `location.reload()` every 4 seconds. So the ordinary case — the network a
few seconds behind the browser at boot — **heals with nobody touching the tablet**, and the worst
case is a sentence a cashier can read instead of a white rectangle. LESSON #12: a white screen
tells a person nothing and offers them nothing.

**Not yet proven on the tablet** — it needs a deploy to `banco.wolfhold.app` and then a cold boot,
plus a wifi-off test to see the page deliberately.

### The method note

Three wrong diagnoses in one evening — the profiler that said the script was fast, the
self-install, and the login-page caching — and every one of them died on a measurement that cost
under a minute. What worked each time was the same move: **stop theorising and ask the machine**
(`stat` the file it writes, `curl` the URL, `systemctl show` the timestamps). What did not work was
reading code and reasoning about what it must be doing.

---

## ⓪d part 2 — deployed, cold-booted, and the offline story proved itself sideways

**Deployed** `10be05f` → **build b684**, `./scripts/deploy-prod.sh` on `ssh banco`. Backup first
(helix_db 6.7M + keycloak 116K, encrypted, in B2), twelve smoke checks green, HTTPS live. New
worker confirmed live: `CACHE_NAME = banco-pos-10be05f-8eebf01a8a`, `offlinePage` present.

**Cold boot after the deploy — the sharpest possible test**, because a new `CACHE_NAME` evicts
every cache, which is exactly the empty-cache half of the white screen. **It landed perfectly:
full screen, Layla logged in.**

### Breaking it on purpose (LESSON #4) found something better than the test

Wifi off → **everything still worked.** The tablet has **wifi AND a SIM**, and the till rode out a
wifi outage on mobile data with nobody noticing. That failover had never been proven; it proved
itself by accident, in real conditions. (It also explains why `art.local` went unreachable
afterwards: airplane-mode-off restored the SIM only, because wifi had been left off.)

**Airplane mode** — everything down — and the till is *good*:

- a brown banner across the top: **"Sales are paused. Your cart is safe. Switch to mobile data or
  a hotspot."**
- **My Day and Catalog still open**, served from the service-worker cache
- airplane mode off → **the banner cleared on its own in 2 seconds**, unattended

**`offlinePage()` never fired, and that is correct.** It is the FLOOR: it only runs when the fetch
fails *and* nothing is cached — not the page, not `/pos/scan`. Angel had visited those pages since
the deploy, so the layer above caught it. Reaching the floor deliberately would mean wiping the
browser's storage on a working till, which is not worth doing. **So the fix is
correct-by-construction (never `respondWith(undefined)`) and not proven live.** Said plainly rather
than counted as green.

### And the airplane-mode test condemned something I had just added

With the network genuinely down at boot, `ExecStartPre` held the window shut for **90 seconds** —
while the cache sat there, able to serve those exact pages instantly with the "Sales are paused"
banner. A blank screen in front of a working offline mode. **Cut to `timeout 20`**: the race it
exists to win was THREE seconds, so 20 wins it many times over without stranding anybody.

### Open, from this run

- **`banco-till.service` lives only on the tablet.** It is hand-maintained at
  `~art/.config/systemd/user/`, deliberately outside `tablet-lockdown.sh` ("THIS SCRIPT DOES NOT
  START THE TILL and must not learn to"). It now carries three fixes and long comments that exist
  on exactly one machine, with no copy in this repo. A second tablet gets none of it.
- **My Day showed a red `could not load your profile: failed to fetch`** under "Good evening,
  Layla" while offline. The banner above it already said there is no internet; this is a second,
  scarier way of saying the same thing, in red, next to her name.

---

## ⓪ Rock-solid check — three consecutive cold boots, criteria agreed first

Angel: *"let's do some more smoke sanity checks and few more restarts so we know we have a rock
solid start."* Pass criteria were written down **before** the first boot, so the bar could not move:
till on screen full-screen with Layla and no press · 0 keyring prompts · lockdown ≤5s · total
55–70s · postboot check 0 failed.

```
boot 12   total 57.810s   banco-lockdown 3.639s   kernel->till 19s
boot 13   total 58.303s   banco-lockdown 3.782s   kernel->till 19s
boot 14   total 58.188s   banco-lockdown 3.443s   kernel->till 19s
```

Every one: **0 keyring prompts · overview extension ACTIVE · banco-power-profile active · 0 till
restarts · 0 failed units**, and Angel confirmed the glass each time — *"it's at the dashboard for
Layla and looks clean and perfect."*

**Spread across the three: 0.49 seconds end to end, and `kernel->till` was 19s every single time.**
The numbers were kept per-boot rather than averaged, deliberately — LESSON #5 is that a mean hides
a bimodal split, and a spread this tight is only meaningful because you can see all three.

Closing state, after fourteen cold boots in one evening:

```
./scripts/tablet-postboot-check.sh     45 passed · 0 failed · 1 to look at
                                       (the 1: "no unattended-upgrades log yet" — it has not
                                        run its first night; expected)
./scripts/install-till-unit.sh --check ✅ identical — the tablet is running what this repo says
serving build                          10be05f (b684)
```

**Where the morning stands now, against where it started this evening:**

| | before | after |
|---|---|---|
| the till on a cold boot | **never came up** — password, then white | full screen, Layla, no press |
| time to a usable till | ~1m 46s, then a password, then a press | **~58s, unattended** |
| `banco-lockdown` | 51.7s in front of the display manager | 3.6s |
| what the cashier does | type a password, press the till | **nothing** |

---

## PORTRAIT — the close-out, walked in the hand, 2026-09-05 evening

The deck said this flow *"has never been seen in the orientation it will be used in"*, and named it
the one that happens in portrait, on a lap, at the back of the shop — the flow with all the money
in it. Angel rotated the tablet and we walked it. **1440 × 2160.** It rotated on its own; rotation
is not locked and the sensors are live.

### It passed — and portrait is BETTER for the money screen

**The whole denomination table fits with no scrolling** — CHF 1000 down to CHF 0.05, thirteen rows,
all visible at once. Landscape is 1440 tall minus the chrome and cannot show it. The one flow we
were worried about is the one that gains most.

- **The number pad**: tapping the bottom row (CHF 0.05) pushed that row up so it sat directly above
  the pad, still highlighted, with every other row visible. **The `b644` fix holds in an
  orientation it was never written for.** Big digits, `C` and `OK` across the top under the thumb.
- **The full QWERTZ keyboard** for the note did the same — note field AND the green button both
  stayed visible above it.
- **The guard was broken on purpose** (LESSON #4): "Close Drawer & File Report" with no note does
  nothing. Add a note, it goes green.
- **The variance panel** reads clearly: `Expected 1'216.90 / Counted 0.05 / Variance CHF-1'216.85`
  in red, with **"⚠️ Outside tolerance — add a note to close."**
- **My Day** in portrait: clean, the two time fields side by side without cramping.

### A real close was filed

Counted to match (1×1000, 1×200, 1×10, 1×5, 1×1, 1×0.50, 2×0.20 = **CHF 1'216.90**), variance zero,
button green **without** a note — the branch we had not tested. Filed.

```
Shift Report — opened by pam · counted & closed by layla
2.9.2026, 20:09:30 → 5.9.2026, 20:40:53  (72.52 h)
⚠️ This drawer was open for 3.0 days — the figures below cover the whole period, not one day.
✅ Balanced within tolerance   +CHF 0.00
```

**That warning caught the exact gap Angel had described from the shop ten minutes earlier**, before
either of us knew the drawer had been open since the 2nd: whoever finishes counts and closes, and
nobody had, so every shift since inherited an uncounted box. It does not just print a number, it
says the number does not mean what you would assume. The box is now **closed** for the first time
in three days, deliberately left that way so tomorrow morning is a genuine open-and-count.

### Three bugs

1. **A note typed for a variance survives onto a BALANCED report.** Typed at −CHF 1'216.85, count
   then corrected to zero variance — the note was still filed (`Note: zztest`). Real version:
   *"gave wrong change once"* printed on a perfectly balanced Z-report that Felix's Treuhänder
   reads. Angel proposed a confirm step; the cheaper shape is *Filing with note: "…"* ✕ **beside
   the button**, because a confirm on every close at eleven at night is a tap people learn to swat.
2. **`Samstag, 5. September` with EN selected**, directly under an English "Good evening / Hi
   Layla". One page, two locales.
3. **`CHF-1'216.85`** — no space after CHF, unlike every other amount on the page, and it is the
   figure a cashier reads out loud.

### One withdrawn

I called the floating 💬 button a portrait layout fault across three screens. **It is draggable and
Angel had parked it there himself.** Withdrawn. The residual question — whether a dragged position
stored in pixels lands somewhere unhelpful after a rotation nobody asked for — is not a finding
until it happens without a hand on it.

**The standing instruction stands: do NOT lock rotation.** ⓞ's "lock it to landscape" is reversed
on evidence.
