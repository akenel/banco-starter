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

