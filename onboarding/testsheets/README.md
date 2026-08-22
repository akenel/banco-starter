# UAT test sheets

One self-contained HTML file per sheet. No build, no server, no dependencies — open it in a
browser, or publish it. Matches the rest of Banco: **you own it, you can read it, it will still
open in ten years.**

## Making a new one

```bash
cp TEMPLATE.html 2026-09-01-what-you-are-testing.html
```

Then edit **only** the `SHEET` object at the top of the file. Everything below it is the shell:
marking, timing, notes, persistence, the report. Change the `key` — a tester's saved marks are
keyed on it, and reusing one makes old ticks appear against new steps.

## What the shell gives you

| | |
|---|---|
| **PASS · ISSUE · FAIL** | three verdicts, not two. **ISSUE** is the one that earns its place: *it worked, but something was off.* Most of what a shop notices is an issue, and a two-state sheet forces it into the wrong box or throws it away |
| **Notes on every step** | not only on a failure. *"I didn't understand this step"* is the most valuable thing a first-time tester can tell you |
| **Timing** | starts on the first mark, stamps each step, freezes when the last one lands. Answers *"is this fast enough with a customer waiting?"* and gives training a benchmark |
| **Copy results** | one button → a plain-text report with who, where, which build, how long, and every note. Paste it into chat |
| **Training mode** | hides every expected result. The tester has to say what they saw **before** reading what they were told to see, then reveals it per step. A sheet that shows the answer first is a checklist; one that does not is a lesson |
| **Survives a reload** | localStorage, keyed per sheet |
| **Print / PDF** | drops the controls, keeps the content |

## Writing steps that are worth running

1. **Click for click.** Assume the reader has never seen the screen. `Catalog → ✏️ Edit →
   scroll to Quantity price breaks` beats "edit the product".
2. **One observable thing per step.** If the expected result cannot be written as something a
   person *sees*, it is not a UAT step — it is a unit test wearing a costume.
3. **Always include a step where nothing should happen.** A feature only ever tested for firing
   will end up firing on everything. On 2026-08-22 five of seventeen steps were silence checks,
   and the narrowing they forced is the reason the price warning is still switched on.
4. **Put the story in `why`.** That field is what makes this a training tool: Ralph should finish
   the sheet knowing why the shop cares, not just that a box went green.
5. **Save `callout` for the load-bearing step.** Two per sheet. More and it stops meaning anything.
6. **End every sheet with a section that puts the shop back.** Test rows are sellable.

## Sheets

| Date | Sheet | Result |
|---|---|---|
| 2026-08-22 | [The price warning](../TESTSHEET-price-warning.md) *(markdown, pre-template)* | 25/25 GO |
| 2026-08-22 | [The till explains the deal](2026-08-22-till-explains-the-deal.html) | — |
