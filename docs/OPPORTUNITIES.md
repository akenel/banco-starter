# Opportunities — the compliance thesis

*Written 2026-08-12. Research record from the session that pivoted off the
writing-tool idea. Companion to `longhand/docs/POSITION.md`, which is where the
"claim checked against the running system" idea came from.*

**Placed in `banco-starter` because this is Felix/POS/catalogue strategy.**

---

## The one line

> Every quality and compliance system on the market **manages documents**.
> None of them checks whether the document still describes what the system
> actually does. That check is the product.

---

## 1. Corrections to the first-pass research

Three things the first sweep got optimistic about. Fix these before planning.

### 1.1 €20,000–80,000 is not a product price

That figure is an SME's **total year-one NIS2 cost**, and it is mostly people:
external NIS2 consultants bill **€1,000–2,000 per day**, plus internal staff
time, plus tooling, plus certification. Software captures a slice, not the whole.

Realistic ceilings for a solo vendor:

| Model | Realistic range |
|---|---|
| SME compliance/QMS SaaS | €200–800 / month |
| Per-audit evidence pack | €2,000–5,000 one-off |
| Implementation consulting | €1,000–1,500 / day |

The €20–80k number is useful as *proof the pain is expensive*, not as a price
tag. Do not build a plan on an €80,000 licence.

### 1.2 NIS2 does not directly bind Swiss companies

Switzerland is not in the EU and is **not directly bound by NIS2**. Swiss firms
are caught only if they:

- have an establishment in the EU, or offer IT services there, **and** exceed
  ~€10M EU revenue or ~50 EU staff; or
- sit in the **supply chain** of an EU essential entity — EU firms must assess
  supplier cybersecurity, so NIS2 gets exported down the chain as an evidence
  demand on Swiss suppliers.

Switzerland's own instrument is the revised **Information Security Act (ISG)**:
in force since January 2024, with a **mandatory 24-hour cyberattack report to the
NCSC** for critical-infrastructure operators since **1 April 2025**, sanctionable
since **1 October 2025**. In 2025 the NCSC handled ~65,000 incident reports, of
which ~220 came under the new obligation.

**Implication:** NIS2 is a *smaller and more indirect* home-market opportunity
than it first appeared. It is real for Swiss suppliers into the EU. It is not
relevant to Felix's shop at all.

### 1.3 The cannabis compliance market is not empty

Two incumbents found immediately:

- **Cannavigia** (`cannavigia.com`) — **Swiss**, track & trace for GACP, EU-GMP
  and the German KCanG. Direct competitor, on home ground.
- **GrowerIQ** — seed-to-sale, EU-GMP/GACP/GPP.

Both are **cultivation and manufacturing** tools: grow, harvest, batch, lab test,
release. Neither is a **retail counter**. The shop floor — the till, the age
check, the tobacco-tax treatment of CBD flower, the label, the shop's own
record — is much thinner ground, and it is exactly where Felix stands.

**Do not enter the grow/manufacture side. Enter at the counter.**

Also note **EudraLex Annex 11**: any computerised system used in a GMP-regulated
process needs validation, data-integrity controls, audit trail, electronic
signatures and supplier assessment. That is a heavy burden — and a moat, if ever
crossed. Not now.

---

## 2. The real find: ISO 9001, and why the instinct was right

The strongest signal in the entire research sweep:

> **Control of documented information (clause 7.5) is the most commonly cited
> source of audit nonconformity worldwide.**

And the named failure modes are, one for one, the thing `CHECK.md` was built to
catch:

| Standard audit finding | What it actually is |
|---|---|
| Outdated SOP in use at the workstation | The document drifted from practice |
| Operator on Rev C, master list says Rev E | Nobody reconciled the two |
| Uncontrolled copies on a shared drive | No single source of truth |
| Records stored in editable folders | Evidence that can't be trusted |
| External document register out of date | A dependency changed and nobody noticed |

Every QMS product on the market attacks this as a **document management**
problem: versioning, approval workflow, distribution, acknowledgement. That
controls the *master copy*. It does nothing about the actual failure, which is
that **the master copy is now a lie about the process**.

The only thing that currently closes that gap is a human auditor walking the
floor once a year. That walk is the product.

### The wedge inside the wedge

The walk cannot be automated for a physical process — you cannot grep whether an
operator degreased the part.

It **can** be automated when the process *is* the system:

- "Access to the till is restricted to named staff" → read the roles table
- "Backups are tested monthly" → read the job log
- "No product is sold without an age check" → query the transactions
- "All stock carries a lot number traceable to the supplier" → query the catalogue
- "THC content of every SKU is recorded below 1%" → query the product records

Every one of those is an SOP sentence that can verify itself continuously,
against the running system, and produce a dated verdict:
**VERIFIED / STALE / UNSOURCED / UNCHECKABLE.**

**Start where the process is the software.** Expand outward later, or never.

---

## 3. Are we close? Honest distances

Two very different answers, and conflating them is the main risk.

**To a working POS for Felix:** close. It is in flight, the catalogue exists,
there is a real user with a real shop.

**To a sellable compliance product:** not close. Missing:

1. A **check engine**. `CHECK.md` is a prompt, not a product. It needs to be a
   scheduled job with typed inputs, stored verdicts and a history.
2. An **evidence store** — immutable, dated, exportable. Records must be
   protected from change; an editable folder is itself a nonconformity.
3. **An auditor who has seen the output and said it would pass.** Until that
   happens, everything here is a theory.
4. A named **first buyer** who is not Felix.

Rough honest estimate: the POS is months. The compliance product is a year, and
only if a real auditor validates the format early.

**The bridge:** build the audit layer *inside* the POS from the start, because a
head shop already carries obligations — age verification (TabPG, testable by
cantonal test purchase), the <1% THC rule, correct tobacco-tax scope, labelling,
no health claims, lot traceability. The concrete pack is in
`docs/RULE-PACK.md`. Felix needs
those records anyway. Building them as **self-verifying SOPs** rather than as
dumb fields costs little extra now and is the entire second product later.

---

## 4. On forking (the `freehold → wolfhold` pattern)

Forking per customer works for one to three installs and is fatal at ten: every
bug fix becomes N cherry-picks, and the forks diverge until they are separate
products with one maintainer.

The pattern already in hand is the right one and it is **not** a fork:

- **Freehold** = the platform (Postgres, Keycloak, MinIO, Caddy, the method)
- **Verticals** = apps deployed *on* it, sharing one codebase
- **Per-tenant difference** = configuration, not a branch

Head-shop retail, and later a dispensary under the new Swiss framework, should be
**the same application with a different config and rule pack** — not a fork. The
rule pack (the SOP sentences and their checks) is where the vertical knowledge
lives, and it is the asset worth accumulating.

---

## 5. Timing — why this may genuinely be the right moment

Not certainty, but a real convergence:

- **Swiss adult-use cannabis**: consultation closed December 2025; the Federal
  Council is expected to put a national bill to Parliament during 2026. The
  proposed framework points at seed-to-sale tracking, lab-test documentation,
  dispensary-level record-keeping that satisfies **federal audits**, and sales
  only through **authorised, registered retail points**.
- Today CBD sits under the **<1% THC** rule. **Correction (2026-08-12):** CBD
  flower is *not* taxed as a tobacco substitute — the Federal Supreme Court
  struck that down. Only products actually **containing tobacco** carry the tax
  (25% + VAT). An earlier draft of this file said the opposite; it was true once
  and quietly stopped being true, which is the exact failure this product
  exists to catch.
- **Enforcement is cantonal, not federal.** The **cantonal chemist / cantonal
  laboratory** does the inspecting — ~40,000 business inspections a year
  nationally. Plus **test purchases** under the Tobacco Products Act (in force
  1 October 2024), which since that date have a national legal basis for use in
  administrative and criminal proceedings. Details in `docs/RULE-PACK.md`.
- **The pain is already measured:** a St. Gallen spot check rejected **94% of
  32 hemp products** (14 over the THC limit, 16 failing labelling). Zurich has
  warned 13 people and banned sales/advertising at two online shops.
- If the bill passes, **every authorised retail point becomes a forced buyer of a
  compliant till.** The design partner and the catalogue already exist.

The risk is the obvious one: legislative timelines slip, and the bill may change
shape. So — **the POS must be worth buying with no new law at all.** The
compliance layer is upside, not the premise.

---

## 6. Decision

**Do not pivot. Merge.**

1. Finish the catalogue/POS with Felix. Real user, real revenue, already moving.
2. Build the record-keeping as **self-verifying SOP checks**, not plain fields.
3. Accumulate the **rule pack** — that is the durable asset and the thing a
   competitor cannot copy from the outside.
4. Keep the platform/vertical split. No forks.
5. Get one real auditor to look at a generated evidence pack. Earliest possible
   reality check on the entire thesis.

Second bet, later and only if the first works: the same engine pointed at ISO
9001 clause 7.5 for Swiss SMEs, and at NIS2 supply-chain evidence for Swiss
firms selling into the EU.

## 7. Open questions

- Which auditor do we show a generated evidence pack to, and when?
- Does Felix's shop have an ISO or quality regime today, or is this net-new?
- Has Felix's shop ever been visited by the **cantonal laboratory / cantonal
  chemist**, or been through a **test purchase**? What did they look at, and
  what did they leave behind on paper? Cheapest possible validation.
- Is Cannavigia moving toward retail? If yes, the window is narrower.
- Pricing: per till, per shop, or per audit?

## Sources

Swiss cannabis timeline and framework — [GrowerIQ](https://groweriq.ca/2026/04/10/switzerland-cannabis-legalization-2026/),
[cannabisregulations.ai](https://www.cannabisregulations.ai/cannabis-and-hemp-regulations-compliance-ai-blog/switzerland-2025-adult-use-compliance-preview).
CBD status — [Essentia Pura](https://essentiapura.com/is-cbd-legal-in-switzerland/).
Competitors — [Cannavigia](https://www.cannavigia.com/), [GrowerIQ EU-GMP](https://groweriq.ca/eu-gmp-gacp-gpp/).
NIS2 and Switzerland — [SIDD](https://www.sidd.swiss/en/insights/nis2-self-assessment-switzerland/),
[Docusnap](https://www.docusnap.com/en/it-documentation/nis2-switzerland).
Swiss ISG reporting — [NCSC](https://www.ncsc.admin.ch/ncsc/en/home/aktuell/im-fokus/2025/meldepflicht-2025.html),
[Industrial Cyber](https://industrialcyber.co/regulation-standards-and-compliance/switzerland-mandates-24-hour-cyberattack-reporting-for-critical-infrastructure-operators-from-april/).
NIS2 costs — [NIS2Compass](https://nis2compass.de/en/blog/nis2-compliance-costs).
ISO 9001 nonconformities — [GloCert](https://www.glocertinternational.com/resources/articles/common-iso-9001-audit-findings/),
[AuditsReady](https://auditsready.com/blog/iso-9001-document-control).
GMP/GACP and Annex 11 — [ComplianceQuest](https://www.compliancequest.com/bloglet/gmp-compliance-software-for-cannabis-manufacturing/).
