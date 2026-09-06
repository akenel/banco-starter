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
