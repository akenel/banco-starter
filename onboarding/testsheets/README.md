# UAT test sheets

One self-contained HTML file per sheet. No build, no server, no dependencies — open it in a
browser, or publish it. Matches the rest of Banco: **you own it, you can read it, it will still
open in ten years.**

## This format was already here

Thirteen sheets predate `TEMPLATE.html`, and they had converged on the same shape without anyone
writing it down:

| | in the 13 existing sheets |
|---|---|
| **PASS · ISSUE · FAIL** | 13 / 13 |
| Marks survive a reload (`localStorage`) | 13 / 13 |
| Copy the results out | 9 / 13 |
| Some kind of timing | 10 / 13 |
| Training mode | 0 / 13 |
| Who ran it, on which till | 0 / 13 |

So the template did not invent the house style — **it extracted one that already existed**, and
the real problem it solves is that every sheet was hand-built from scratch, which is why four of
them quietly lost the copy button and three lost the clock. Two things are genuinely new: training
mode, and recording who ran it.

## Making a new one

```bash
cp TEMPLATE.html 2026-09-01-what-you-are-testing.html
```

Then edit **only** the `SHEET` object at the top. Everything below it is the shell. Change the
`key` — a tester's saved marks are keyed on it, and reusing one makes old ticks appear against new
steps.

## What the shell gives you

| | |
|---|---|
| **PASS · ISSUE · FAIL** | **ISSUE** is the one that earns its place: *it worked, but something was off.* Most of what a shop notices is an issue, and a two-state sheet forces it into the wrong box or throws it away |
| **Notes on every step** | not only on a failure. *"I didn't understand this step"* is the most valuable thing a first-time tester can tell you |
| **Timing** | starts on the first mark, stamps each step, freezes when the last one lands. Answers *"is this fast enough with a customer waiting?"* and gives training a benchmark |
| **Copy results** | one button → plain text with who, where, which build, how long, and every note |
| **Training mode** | hides every expected result. The tester says what they saw **before** reading what they were told to see, then reveals it per step. A sheet that shows the answer first is a checklist; one that does not is a lesson |
| **Print / PDF** | drops the controls, keeps the content |

## Writing steps that are worth running

1. **Click for click.** Assume the reader has never seen the screen. `Catalog → ✏️ Edit → scroll
   to Quantity price breaks` beats "edit the product".
2. **One observable thing per step.** If the expected result cannot be written as something a
   person *sees*, it is not a UAT step — it is a unit test wearing a costume.
3. **Always include a step where nothing should happen.** A feature only ever tested for firing
   will end up firing on everything. On 2026-08-22 five of seventeen steps were silence checks,
   and the narrowing they forced is why the price warning is still switched on.
4. **Put the story in `why`.** That field is what makes this a training tool: Ralph should finish
   knowing why the shop cares, not just that a box went green.
5. **Save `callout` for the load-bearing step.** Two per sheet. More and it stops meaning anything.
6. **End with a section that puts the shop back.** Test rows are sellable.

## Sheets

Newest first. Only the top one uses the template.

| Date | Sheet | Result |
|---|---|---|
| 2026-08-22 | [The pack badge and the discount](2026-08-22-pack-badge-and-discount.html) | — |
| 2026-08-22 | [The till explains the deal](2026-08-22-till-explains-the-deal.html) | 17/17 GO |
| 2026-08-22 | [The price warning](../TESTSHEET-price-warning.md) *(markdown)* | 25/25 GO |

Hand-built, pre-template — [Shop day preflight](SHOP-DAY-PREFLIGHT.html) ·
[One day three roles](ONE-DAY-THREE-ROLES.html) ·
[Own your Banco E2E](OWN-YOUR-BANCO-E2E-TESTSHEET.html) ·
[Cashier shift E2E](CASHIER-SHIFT-E2E-TESTSHEET.html) ·
[UAT five gaps](UAT-FIVE-GAPS-TESTSHEET.html) ·
[Age evidence](AGE-EVIDENCE-TESTSHEET.html) ·
[Age gate human half](AGE-GATE-HUMAN-HALF.html) ·
[Age gate reclass](AGE-GATE-RECLASS-TESTSHEET.html) ·
[Refusal evidence retest](REFUSAL-EVIDENCE-RETEST.html) ·
[Cash box shop-owned](CASH-BOX-SHOP-OWNED-TESTSHEET.html) ·
[Enricher](ENRICHER-TESTSHEET.html) ·
[Grinder search](GRINDER-SEARCH-TESTSHEET.html) ·
[Photo AI five grinders](PHOTO-AI-FIVE-GRINDERS-TESTSHEET.html) ·
[Shadow day tally](SHADOW-DAY-TALLY.html)
