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

