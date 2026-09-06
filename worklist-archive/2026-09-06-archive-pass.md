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

---

## The language thread — the full narrative · 2026-09-06

Moved out of `WORKLIST.md` when the alarm hit 517. The deck keeps a pointer; this keeps the story.

### How it started

Angel walked the cashier screens in Italian, then the same Felix screens in German, Italian, French
and English, and sent **41 screenshots**. Read side by side they turned what looked like one bug
into five, then seven.

| | what it is | fixed |
|---|---|---|
| **A** | no key at all — 428 left | batch 1 ✅ |
| **B** | key exists, value IS the English — was 45/45 of `agerep` in FR *and* IT | ✅ all |
| **C** | written in `<script>`, never reaches `t()` | 3 left |
| **D** | key resolves in NO language, falls back to English | ✅ all 14 |
| **E** | English inside an `x-text` expression | 47 left |
| **F** | English in a `placeholder` attribute | 41 left |
| **G** | a `t()` call whose key does not exist — prints the RAW KEY | ✅ all 10 |

**A string with no key is English in EVERY language**, so German and French were hit exactly as hard
as Italian — which answered Angel's question better than a guess could. Only class B was
language-specific (fr 45 · it 45 · de 1).

### The instrument was wrong six times

`scripts/prove-one-box-one-language.py` was written to stop this class recurring, and it needed
correcting more often than the code it audits. All six are recorded in the file itself:

1. parsed the JS with a regex and died on a `//` **inside a string** — now asks node
2. asked about **adjacency instead of ancestry**, and reported **409** bare strings, three of which
   were fragments of one fully translated sentence containing a `<b>`. It was loudest exactly where
   the code was healthiest.
3. blind to keys whose **value is the English** — the class Angel's eyes found
4. blind to strings in `<script>`
5. blind to English **inside `x-text`**, having marked every `x-text` element "covered"
6. required **two Latin words**, so `Cancel`, `Saving…`, `buy`, `Barcode` were invisible — and a
   leading emoji made it worse, because `🔔 Notifications` does not start with a letter
7. never looked at `placeholder` attributes at all, and never checked that a `t()` call's key exists

**359 → 458.** The count went UP under scrutiny, the opposite of what the audit page predicted that
morning. The page was corrected to say so.

### Two bugs that were not translation at all

- **`transactions.html` printed "Artemis Store" hard-coded** at the top of the paper. Every third
  party who clones this starter has been printing Angel's shop on their own transaction history.
  Now `_cfg('store_name')`.
- **Ten `t()` calls whose key does not exist.** `t()` returns the RAW KEY on a miss, so a cashier
  reads `held.toast_load` as a toast. Nine were written `t('k') || 'English fallback'` — **dead
  code**, because the raw key is a non-empty string and therefore truthy, so `||` can never fire.
  A guard that looks like it works. LESSON #12.

### Two findings WITHDRAWN, both mine

I told Angel, in a page written for him to steer by, that `checkout.html` was hard-coded German and
`receipt.html` hard-coded Italian, and that a French cashier would get German at the terminal and
Italian on the paper. **Both wrong.** `checkout` is a `worldline_sim` SANDBOX gated on a store
setting Artemis does not have; `receipt.html:91` is the **Italian legal disclaimer**, printed only
for an Italian-regime tenant, and translating it would destroy what it exists to do.

**Both had a comment saying so three lines above the string.** That is LESSON #10 word for word.
Caught before any code changed on the strength of it, because the fix began by reading the block.

They are now marked in the code with `data-i18n-exempt="<why>"` rather than a skip-list hidden in
the harness — because with these two the REASON was the whole point, and a hidden list would have
hidden it again.

### Do not "fix" these

The scanner's **German firmware words** in Shelf Intake (`Daten hochladen`, `Normalmodus`) — they
are printed on the device in the reader's hand and must stay German in every language. **Category
names** (`Filters & Tips`) are catalogue data. The **de-CH numeric dates** were settled 2026-09-05.

### The standing gap

**Nobody who speaks French or Italian has read any of the ~720 strings written on 2026-09-06.**
Angel has no French. The English is off the glass; that is not the same as the Italian being good,
and `Sistemazione` — a real Italian word, and the wrong one — is the proof.

---

## The feedback → triage loop, proven end to end · 2026-09-06 afternoon

Angel's idea, and the better one: stop taking screenshots by hand, use the 💬 button — it already
captures the screen, files a numbered ticket, and `POST /feedback/triage` already runs an Ollama
brain with a vision pass over that screenshot. The loop was built; this was the first day it was
pointed at real work.

### Phase 0 — what each ticket settled

| | what it proved |
|---|---|
| **BL-016** | The brain is REAL — `model: gpt-oss:120b` on Turbo, not the graceful fallback. And it found a live regression *of mine* (below). |
| **BL-017** | Vision reads the screen truthfully — but asked whether **our own 💬 button** was a UI artifact. Prompt taught Banco's furniture. |
| **BL-018** | Off a body saying only *"Three boxes in the middle are in English"*, it named **"Price not verified yet", "Scannable at the till", "Margin known"** — three strings Angel never typed, all matching the harness exactly. `bug · medium · conf 96%`. **Thin tickets work.** |
| **BL-019** | **The failure.** A CLEAN screen, a neutral body — and it invented *"Fix Italian translation errors"* at **conf 92%**, quoting nothing. |
| **BL-021** | Dedup fired and linked it to #19 with good reporter-facing copy. |

### BL-016 — the AI found a regression I had shipped that morning

Angel filed a ZZTEST about something else. The 💬 button collected a console breadcrumb with it:

    ❌ unhandledrejection: TypeError: t is not a function at load (/pos/dashboard:3260:27)

Triage read the breadcrumb and wrote *"Fix TypeError on dashboard load in build b704 · bug · high
· conf 85%"*. It was right. `var t = j.today` in the Shop Pulse loader shadowed the global
translator — `var` is function-scoped, so it took the catch handler down too, which is why it
surfaced as an unhandled rejection instead of a message. **No check in this repo could see it:**
valid JavaScript, every template parsed, every key resolved, and it only threw when the panel was
opened. Now `scripts/prove-one-box-one-language.py` check (8).

### BL-019 — sycophancy, and the fix that cured it

A clean screen and a neutral body produced a confident phantom. The cause was in `_SYSTEM`: the
prompt had **no way to conclude "nothing is wrong"**. Every input had to become a ticket, so every
input became one. Four rules added — the reporter may be mistaken; a finding must QUOTE the exact
text; vague body + clean screenshot → Question, confidence ≤ 0.3; **confidence measures evidence,
not agreement**.

Re-triaged the same ticket, same screenshot, same model:

| | before | after |
|---|---|---|
| type | `bug` | **`Question`** |
| confidence | **92%** | **22%** |
| description | "displays incorrect or inconsistent Italian wording" | "**the screenshot shows the normal layout with no visible anomalies** … clarify which text appears wrong and where" |

**Four out of four against a prediction written before the result was seen.** The property that
matters is not that it finds bugs — it is that it can say *nothing is wrong here*, which is the
only reason to believe it when it says something is.

### Found along the way

- **Re-triage has no affordance.** Triage is idempotent; the only way to re-read a ticket after
  improving the prompt is `reporter-note`, `reopened` or `disputed` — i.e. impersonating the
  reporter. The prompt changed twice in one afternoon. A manager needs a plain "re-triage this".
- **Triage does not feed the KB.** `kb_contribution_model` and `/pos/kb-approvals` both exist and
  `feedback_triage.py` touches neither.
- The raw ticket was rendered `.slice(0,300)`, cutting every context block off mid-word — the AI
  always had it, the human never did.

### The judgement, asked and answered

Angel: *"can you see how this could actually be useful for Layla and Felix … or is it overkill?"*

**The valuable part is the evidence, not the AI.** Layla will never report a stack trace; she will
say the shop thing went funny. The button captures screen, build, language, orientation, console
errors and failed calls without her doing anything. **And it is not a system for Layla — her whole
interface is one button.** The cockpit is Angel's instrument for supporting a shop he is not
standing in. For a two-person shop a ticketing system would be absurd; for remote hypercare it is
exactly right. The AI rewrite stays on probation until it has earned more than one good day.

---

## The language day, end to end · 2026-09-06

Started as "deploy `4bed4a2` and finish the cash box". Ended with nine distinct bug classes, a
harness corrected eight times, and an AI triage system that found a regression in the copilot's own
code. What follows is the honest ledger, including the parts that were wrong.

### What was fixed

| screen | was | now |
|---|---|---|
| the till — scan · base · checkout · receipt · transactions · login | 47 bare strings | **clean** |
| `audit` | **100% English** — the Treuhänder's change log | **clean**, incl. the rows |
| `settings` | 36 | **clean** |
| `catalog_misses` | 50 | **clean** |
| `age_report` | **45/45 keys were the English string** in FR *and* IT | **clean** |
| `my_tickets` | the reporter's own progress timeline, built in Python | **clean** |

**~1,100 new FR/IT/DE strings.** Left for tomorrow: `shelf_intake` 173 · `hardware` 59 ·
`catalog` 22 · `catalog_health` 21.

### The nine classes — only ONE of which the harness could originally see

| | class | how it was found |
|---|---|---|
| **A** | no key at all | the harness (the only one it could see) |
| **B** | key present in all four, value IS the English | **Angel's eyes** — 45/45 of `agerep` |
| **C** | written in `<script>`, never reaches `t()` | chasing a date-range picker |
| **D** | key resolves in NO language → prints English | the harness, once corrected |
| **E** | English inside an `x-text` expression | **Angel's screenshots** of the product modal |
| **F** | English in a `placeholder` attribute | fixing E |
| **G** | a `t()` call whose key does not exist → prints the RAW KEY | a parity script written for something else |
| **H** | a JS map keyed by a database value (`entityLabel`, `roleDisplay`) | **the AI**, off a screenshot |
| **I** | English built in **Python** and sent as data | **the AI**, off a screenshot (BL-035) |

### The harness was wrong eight times

Every correction is in `scripts/prove-one-box-one-language.py`, with the evidence:

1. parsed JS with a regex and died on a `//` **inside a string**
2. asked about **adjacency, not ancestry** → reported 409, three of them fragments of ONE translated
   sentence containing a `<b>`. Loudest exactly where the code was healthiest.
3. blind to keys whose VALUE is the English
4. blind to strings in `<script>`
5. blind to English inside `x-text` — having marked every `x-text` element "covered"
6. required TWO Latin words, so `Cancel`, `Saving…`, `buy` were invisible; and a leading emoji made
   it worse, because `🔔 Notifications` does not start with a letter
7. never looked at `placeholder` attributes, nor checked that a `t()` key exists
8. **it was CRASHING and printing partial results.** A splice deleted the collection blocks for
   checks 7 and 8 and left their reporting, so it died on `NameError` for several commits — and
   every run was piped through `grep`, which ate the traceback and the exit code.

**359 → 458 → 312.** The number went UP under scrutiny before it came down. The morning's audit
page predicted the opposite and was corrected to say so.

### Four findings withdrawn — two mine, two the AI's

- **`checkout.html` hard-coded German** — a `worldline_sim` SANDBOX that never renders at Artemis.
- **`receipt.html` hard-coded Italian** — the IT legal disclaimer, printed only for an IT-regime
  tenant. Translating it would break what it exists to do.
  *Both had a comment saying so three lines above the string. LESSON #10, twice in one sitting.*
- **dashboard "truncation"** (AI, conf 92%) — a deliberate `text-overflow: ellipsis` in the dense
  list. Real weakness, not a defect: the design is calibrated for English lengths.
- **"the Home tab is highlighted"** (AI, conf 92%) — no `data-tab` matches that path. The model read
  the 🏠 emoji's warm colour as an active state.

### The `t` shadow, three times in one day

`t` is the global translator. Three separate disguises, all shipped or nearly shipped by the
copilot:

1. `var t = j.today` in Shop Pulse — **shipped in b704**, took the catch handler with it, surfaced
   as an unhandled rejection. Found by the AI reading a console breadcrumb attached to a ZZTEST
   about something else entirely.
2. `const c = …, t = []` in `audit.html` — written *hours after* adding the check for it, and the
   check missed it because its regex only matched `t` first in the declarator list.
3. `x-for="t in shown()"` in `my_tickets.html` — an Alpine loop variable shadowing it across 103
   expressions. Check (8) cannot see this one at all; it is not a JS declaration. Avoided by putting
   the lookup in a method.

### What the AI triage system actually proved

Real brain (`gpt-oss:120b` on Turbo). Across ~20 tickets:

- **It found a live regression in the copilot's code** from a console breadcrumb on an unrelated
  ticket, and wrote it up correctly at conf 85%.
- **It named three strings Angel never typed** off a screenshot (BL-018, conf 96%).
- **It found `CRACK` on the cashier's customer screen** — a correctly translated, key-having,
  perfectly valid string that reads as a drug name in a hemp shop. **No static check can ever find
  that.** Renamed to *member* at Angel's call; CRACK survives in `kb-approvals`, where only Felix
  sees it.
- **It stayed quiet on clean screens four times running** — after being taught that a reporter can
  be WRONG. Before that fix it invented a defect on a clean screen at **conf 92%**; after, the same
  ticket and the same screenshot came back **Question, conf 22%**.
- **Its confidence is calibrated**: 96% with quotes, 22% with none, 30% on a vague report.
- **The graceful fallback fired for real** (BL-041) and looks tidy enough to be mistaken for a
  result: *other · annoying · conf 0% · model "? (fallback)"*.

**And it files phantoms when the picture is bad.** Three tickets were captured at Pixel ratio 0.5–0.8
— a zoomed-out browser — and it reported compression artifacts as defects: `13R`, `CHF ?'28?'.95`, a
franc figure "missing its decimal separator". The prompt now distrusts fine detail below ratio 1.
**Do the walk at 100% zoom.**

### The division of labour, settled by evidence

- **the script** finds every untranslated string exactly, free, repeatably — and finds ones a
  screenshot cannot show (a placeholder you must click into, a toast that needs an error)
- **Angel's eyes** find what is *wrong* rather than *missing*
- **the AI** finds what is wrong in a picture: a word that reads badly in a room, text too long for
  its box, a language that does not match its neighbours

On `catalog` Angel marked PASS with 22 English strings on screen. Not a failure — the proof that
scattered English hides from a person and cannot hide from a script. Both instruments, or neither.

### Still open

- **`0️⃣a`** — nobody who speaks French or Italian has read ANY of ~1,100 strings. Not a translation
  gap, a **review** gap. `Sistemazione` is the proof it is real.
- **the bench** — 275 strings, nobody sells with it
- **triage has no re-triage button**, and does not feed the KB it was built to grow
- **the dense-list ellipsis** is calibrated for English lengths — Angel's call
- **`Unsorted` vs `Uncategorized`** — two names for "we do not know", from two code paths, in one
  report. A catalogue smell, not a language one.
