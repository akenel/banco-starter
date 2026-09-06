# 2026-09-06 — archive pass

*Moved out of `WORKLIST.md` verbatim, nothing deleted. The pass was triggered by
`scripts/worklist-check.py` at 516 lines.*

---

## 0️⃣ — the cash box, finished · CLOSED, `b693`

Carried over from the night of 2026-09-05, which stopped at 21:40 on purpose, tired, with a
drawer OPEN at CHF 0.25 on the tablet. Four parts, all shipped.

**(a) The morning guard** — `4bed4a2`. It was English under a translated title, with raw
Decimals (`CHF 1216.90`, no apostrophe). The server already sent `reference` / `reference_is` /
`counted` separately, so the fix was to stop using its prose: `baseline_check` now also returns
`reference_is_key` (a machine key, not an English phrase) and the client assembles the sentence
with `t()` and `formatPrice()`. `message` stays as the fallback for an older server.

**(d) The 💬 anchor migration** — `b15ff34`. The 2026-09-05 fix taught the button to remember
which CORNER it was parked in rather than its pixels, and did nothing for anyone who had already
dragged it: an old record is `{left, top}` with no `ax`, `applyAnchor()` rejects it, and the first
rotation after the deploy fell straight through to the old clamp. So: place it where it was, read
where it actually landed, write the corner back. Measured on a mirror of the block, landscape
2160×1440 → portrait 1440×2160, with the button parked 8px off the bottom bar:

| | after the rotation |
|---|---|
| without the migration | **728px** from the bottom — stranded mid-screen |
| with it | **8px** — where he put it |

The harness was run both ways and watched go red first, with a rect that has a real `width` and
`height` — the omission that made the 2026-09-05 harness call every case `"left"`.

**(b) The note strip — PASSED ON THE GLASS.** The one that needed a person. At 11:00:48 on the
tablet, count corrected to CHF 1'216.00, variance +CHF 0.00, *✅ Within tolerance (±0.20) — good to
close* — and the amber strip underneath it: **`Filing with note: zztest3 · Remove`**. At 11:01:15
he tapped Remove and the strip was gone. At 11:01:27 the filed Shift Report carried **no Nota
line at all**. The whole chain, end to end: type → correct → the note becomes visible instead of
vanishing → Remove → gone from the record. This is the fix for LESSON #13 (the stored copy and the
screen disagreed, and the invisible one won) and it is now human-green.

**(c) The drawer** — closed **balanced at CHF 1'216.00, +CHF 0.00**, no note. The box is right for
the morning.

**And the rotation, unasked:** the 💬 held the bottom status bar through landscape → portrait →
landscape (10:53:41 · 10:54:09 · 10:54:37).

### ⚠️ What is deployed but NOT SEEN

Two of the four are shipped on evidence that is not a screen, and saying otherwise would be
LESSON #1 for the fifteenth time.

- **The guard's translated body has never been on a screen.** It only fires when the opening count
  differs from the reference, and the box opened clean this morning. Deployed, unwitnessed.
- **The migration path could not run on this tablet.** Angel's saved position already carries a
  corner from the drag on 2026-09-05, so `applyAnchor()` succeeded and the migration branch was
  never entered. What the rotation proved is the ANCHOR, which was already shipped. The migration
  runs for the first time on Felix's and Layla's devices, and there is no way to rehearse it here
  short of clearing `lpfb_pos` — which would also destroy the record it exists to repair.

---

## 0️⃣c — the byline, and the harness that came out of it · `972578a`

Angel closed a drawer in Italian on `b693` and photographed it: **"Rapporto turno"**, and directly
under it in grey, **"opened and closed by layla"**.

The third box in two days speaking two languages at once, and all three are one shape — a TITLE
with a key over a BODY without one:

| | |
|---|---|
| the receipt | "Sabato" over an Italian body · `c2fa231` |
| the guard | "È corretto?" over an English body · `4bed4a2` |
| the byline | "Rapporto turno" over English · `972578a` |

**None was findable by comparing the four language files.** The missing string was missing from
all four equally, so key-parity said 100%. And the reason all five bare strings in `shift.html`
survived every earlier pass is visible in them: each is a sentence with a variable in the MIDDLE,
which a single `data-i18n` cannot wrap. The file had already solved that three lines away
(`within_tol_pre` / `within_tol_post`), so the fix used its own precedent.

### The harness was wrong twice before it was right

`scripts/prove-one-box-one-language.py`, and both errors are recorded in the file itself:

1. It parsed the JS by hand and died on a `//` **inside a string**. Parsing a language file with a
   regex is how you get a fifth translation bug while fixing the fourth. It now asks node, which
   is right by construction.
2. It asked what tag sat immediately BEFORE each text node and reported **409** bare strings —
   including three fragments of one fully translated sentence, because that sentence contains a
   `<b>`. A string wrapped in inline markup is the normal case for a warning, so **the harness was
   loudest exactly where the code was healthiest.** Ancestry is the question, not adjacency.
   Rewritten on `html.parser` with a tag stack: **359**.

Then broken on purpose before being trusted (LESSON #4): with the byline key stripped back out it
reports `shift.html:342`; with it in place `shift.html` is clean, including the `<b>`-wrapped
`force_body` it used to cry about.

---

## The screenshots

Nine, from `art@art:~/Pictures/Screenshots`, 10:53–11:01. This is the second morning in a row that
the finding came from a photograph rather than from anything a terminal could reach — the byline
is grey 14px text under a heading, and nobody reading the template noticed it in four months.
