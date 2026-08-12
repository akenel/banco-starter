# The starter rule pack — Swiss head-shop retail

*Written 2026-08-12. Data model: `src/db/models/compliance_rule_model.py` +
`compliance_check_run_model.py`. Strategy: `docs/OPPORTUNITIES.md`.*

Rules that apply to Felix's shop **today, with no new law**. Each is a sentence
a person can read, an authority it comes from, and a way to prove it.

> ⚠️ Every `authority` line below needs `authority_checked_at` set by a human
> before it is trusted. This document is research, not legal advice, and the
> whole point of the model is that we do not take a written claim on faith.

---

## Who actually inspects a shop like this

Not the Federal Office of Public Health. **The cantonal chemist / cantonal
laboratory** (`Kantonschemiker` / `Kantonales Labor`) is the enforcement body
that walks in the door. Cantonal chemists run roughly **40,000 business
inspections a year** across Switzerland, covering food, consumer goods,
labelling and composition.

The federal bodies set the rules; the canton knocks. Anything written for an
inspector should be written for a cantonal inspector.

Second enforcement channel, and it is a different mechanism entirely:
**test purchases** (`Testkäufe`) under the Tobacco Products Act. Cantons run
them, or hire someone to. Since 1 October 2024 there is a **national legal
basis for using a test-purchase result in administrative and criminal
proceedings** — so a failed test purchase is now evidence against the shop,
not a warning letter.

---

## Why this is not hypothetical

**St. Gallen consumer-protection spot check: 32 hemp products tested,
30 rejected — 94%.** THC over the limit in 14 samples, *sometimes by a
multiple*. 16 failed labelling requirements.

**Kanton Zürich:** 13 people warned, sales and advertising bans issued against
two online shops over hemp/CBD food supplements.

A 94% failure rate is not a compliance market that needs to be created. It is
one where nearly every participant is already non-compliant and does not know
which rule they are breaking.

---

## The pack

### AGE-18-TABAK — *critical*

> **Statement:** No tobacco, nicotine or age-restricted product leaves this
> shop without the buyer's age being checked and recorded as 18 or over.

- **Authority:** Tobacco Products Act (TabPG), in force 1 October 2024.
  National minimum age 18, replacing the old cantonal patchwork where some
  cantons allowed 16. Enforced by cantonal test purchases usable in
  proceedings.
- **check_kind:** `sql`
- **check_spec:** transactions joined to products where the product class is
  age-restricted and no age-check flag is recorded on the line
- **expectation:** `0 rows`
- **Why critical:** this is the one an inspector can test directly, at will,
  by sending someone through the door.

### THC-1PCT — *critical*

> **Statement:** Every hemp product on sale has a recorded THC value below 1%,
> traceable to a lab result for its lot.

- **Authority:** Swiss narcotics law — hemp at or above 1% THC is a narcotic.
- **check_kind:** `sql`
- **check_spec:** hemp-class SKUs with `thc_pct IS NULL OR thc_pct >= 1.0`, or
  with no linked lab document
- **expectation:** `0 rows`
- **Note:** the St. Gallen campaign found overages *by a multiple*. The failure
  mode is not a shop cheating — it is a shop trusting a supplier's word and
  never holding the paper.

### LABEL-COMPLETE — *major*

> **Statement:** Every product on the shelf carries a compliant label: correct
> designation, composition, origin, warnings, and no health claims.

- **Authority:** Foodstuffs Act (LMG) and the consumer-goods ordinances,
  enforced by the cantonal laboratory.
- **check_kind:** `sql` → `manual`
- **check_spec:** SKUs missing any mandatory label field; then a physical
  shelf walk attested by a named person
- **expectation:** `0 rows`, plus a dated attestation
- **Note:** 16 of 32 products failed labelling in the St. Gallen campaign.
  This is the single most common way a Swiss shop gets written up.

### CBD-INGESTIBLE — *critical*

> **Statement:** No CBD product is sold, labelled or described for ingestion.
> Every CBD product carries an explicit legal product category — cosmetic,
> aroma, chemical, or tea.

- **Authority:** CBD extracts (other than hemp **seed** oil) are **Novel Food** —
  not consumed in meaningful quantities before 1997, so they require
  authorisation. **Not one CBD food authorisation has ever been granted in
  Switzerland.** Tea is the noted exception, because tea does not fall under the
  Novel Food rule. Sale as a medicine requires Swissmedic authorisation.
  Source: BLV Merkblatt / Vollzugshilfe — Produkte mit Cannabidiol.
- **check_kind:** `none` today → the declared-category field does not exist yet
- **The correction worth knowing:** a pharmacy is **not** a loophole. Pharmacies
  selling CBD typically declare it as a **chemical or cosmetic**, exactly like a
  shop does — not as a medicine or a food. So the legal boundary is not *who
  sells it*, it is **what it is declared as**. That is a catalogue field, which
  is why this belongs in a POS and not in a grow-room system.

### NO-HEALTH-CLAIM — *critical*

> **Statement:** No CBD product is sold, described or advertised as a food
> supplement, and no health claim is made for any product in the shop.

- **Authority:** No novel-food authorisation exists for CBD extracts in
  Switzerland or the EU; CBD food supplements are not lawfully marketable.
  Zurich has issued sales and advertising bans on exactly this.
- **check_kind:** `sql`
- **check_spec:** product descriptions, categories and marketing copy matched
  against a banned-claim term list (*supplement, treats, cures, relieves,
  anti-inflammatory, …*)
- **expectation:** `0 rows`
- **Note:** this rule covers the **website and the shelf talker**, not just the
  till. That is where the bans landed.

### TOBACCO-TAX-SCOPE — *major*

> **Statement:** Tobacco tax is applied only to products that actually contain
> tobacco. Pure hemp flower without tobacco is not taxed as a tobacco
> substitute.

- **Authority:** Federal Supreme Court ruled that low-THC hemp flowers are
  **not** a tobacco substitute, striking the tobacco tax on them. Products
  *containing* tobacco remain taxable (25% + VAT).
- **check_kind:** `sql`
- **check_spec:** SKUs where the tobacco-tax flag disagrees with the
  contains-tobacco flag
- **expectation:** `0 rows`
- ⚠️ **This corrects an earlier note in `OPPORTUNITIES.md`** that said CBD
  flower is taxed as a tobacco substitute. It was, and then it wasn't.
  A perfect specimen of the problem this whole product exists to catch:
  a true statement that quietly stopped being true.

### LOT-TRACEABLE — *major*

> **Statement:** Every unit sold can be traced back to a lot, and that lot back
> to a named supplier with a date received.

- **Authority:** Food/consumer-goods traceability; and the anticipated
  seed-to-sale requirement under a future adult-use framework.
- **check_kind:** `sql` · **expectation:** `0 rows` without a lot link
- **Note:** the one rule here that is pure upside — it costs little now and is
  the foundation of everything a legalised market will demand.

### TILL-ACCESS — *major*

> **Statement:** Only named, currently-employed staff can open the till, and
> every transaction is attributable to one of them.

- **Authority:** house rule; also the generic control any auditor expects.
- **check_kind:** `sql` · **expectation:** `0 rows` for transactions with no
  actor, or actors not on the active staff list

### CASH-COUNT-DAILY — *major*

> **Statement:** The cash box is counted at the close of every shift, and any
> variance beyond tolerance carries a written reason.

- **Authority:** house rule / bookkeeping.
- **check_kind:** `sql` · **expectation:** `0 rows` for shifts closed with no
  count, or an out-of-tolerance variance with no note
- **Note:** `store_settings.cash_tolerance` already carries the tolerance, and
  the existing comment there says it well — *an auditor wants a complete,
  reasoned record, not a drawer that is always perfect.* That instinct is
  already in the codebase; this makes it checkable.

---

## What is deliberately not here

- Anything about **cultivation, GACP or EU-GMP**. Cannavigia (Swiss) and
  GrowerIQ already own that ground. Enter at the counter, not the grow room.
- Anything requiring **EudraLex Annex 11** computerised-system validation. That
  is a serious burden and a serious moat, and it is not for now.
- **Corrective actions / findings workflow.** Designed for, not built. It waits
  until a real auditor has seen an evidence pack.

## Next

1. Set `authority_checked_at` on every rule above by reading the actual source.
   Until then the pack is research, and the model will honestly report it.
2. Ask Felix the questions in `docs/OPPORTUNITIES.md` §7.
3. Generate one evidence pack from real shop data and show it to an auditor.
