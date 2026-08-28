# Archive — the scanner gun, and the label PDF · 2026-08-28

*Both moved out of [`WORKLIST.md`](../WORKLIST.md) on 2026-08-28, **verbatim, nothing edited**, and
verified byte-for-byte against the pre-move file. Neither is abandoned — both are **parked with the
finding already banked**, which is exactly the state that does not deserve a slot in a file whose
job is "what's next, in order". `WORKLIST.md` had grown to 340 lines against its own ~280 rule, for
the third time this month.*

*Angel, 2026-08-28: "yes archive those two threads".*

---

## ③ The scanner gun — parked, and safe for everything the shop scans

*(was `WORKLIST.md` item ③)*

**③ The scanner gun is PARKED, deliberately.** ~8 reads in 14 corrupt a digit — but only ever the
digit immediately before an UPPERCASE letter, where the shift asserts early. Pure-numeric codes never
assert shift, so EAN-13/UPC-A are structurally immune, and Banco's SKUs put their letters at the
front. Safe for everything the shop scans. The NSL8 has **no inter-character delay setting** (all 28
pages read; manual now in `onboarding/testsheets/Scanners/`). Next test if it is ever picked up:
scan into a plain text editor, not Firefox — intermittent modifier corruption is as often the host's
input stack as the gun's.

**Why this is parked rather than open.** The corruption is real but *structurally cannot touch a
retail barcode*: it only ever hits the digit immediately before an uppercase letter, and EAN-13 /
UPC-A are pure numeric, so the shift is never asserted. Banco's own SKUs put their letters at the
front, ahead of any digit. So the gun is safe for every code that crosses that counter today, and
the open question only matters if someone later mints a SKU with letters in the middle.

**The one untried test, if it is ever picked up:** scan into a plain text editor rather than
Firefox. Intermittent modifier corruption is as often the host's input stack as the gun's, and that
has not been ruled out. Related and already fixed: `f3a4084` made the till's lookup case-tolerant,
so a late SHIFT arriving as `sKU-` still resolves (**LESSON #1, ×12** — green on the layer you can
reach said nothing about the counter).

---

## ④ Label → PDF paginates wrong

*(was `WORKLIST.md` item ④)*

**④ Label → PDF paginates wrong.** A sliver spills onto a second page and the first is cut.
`@page{62mm 28mm}` / `{62mm 55mm}` versus what Chrome lays out. Angel: *"we deal with that pdf later"*.

**Why this is parked.** Angel's call, in his own words. The label itself **prints and scans** — this
is only the *save-to-PDF* path, which nobody at the counter uses; the Brother QL-820 is fed
directly. Related work that did land: `b273e71` (the page title IS the PDF filename, and both label
sizes shared one, so saving one destroyed the other) and the SMALL/MEDIUM sizing in `3d5f878`.

**Still genuinely open, and it is item ⑤ in the live file, not this one:** the MEDIUM label's
CODE128 has never been read by a gun. 17 characters in 62 mm makes fine bars. If it will not read,
the answer is a **shorter SKU, not a bigger label**.
