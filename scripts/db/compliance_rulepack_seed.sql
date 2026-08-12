-- ============================================================================
-- Banco COMPLIANCE RULE PACK — Swiss head-shop retail, starter seed
-- ----------------------------------------------------------------------------
-- One row per sentence the shop asserts about itself, plus how to prove it.
-- Model: src/db/models/compliance_rule_model.py (+ compliance_check_run_model.py)
-- Research + authorities: docs/RULE-PACK.md
--
-- Idempotent — safe to re-run. Apply per environment (sandbox -> staging -> prod):
--   docker exec -i postgres psql -U helix_user -d banco_<env> -v ON_ERROR_STOP=1 \
--     < scripts/db/compliance_rulepack_seed.sql
--
-- The tables themselves come from create_all (they are models). This script only
-- seeds rules, hardens the evidence table, and attaches the audit trigger.
--
-- ⚠️ EVERY RULE SHIPS is_active = FALSE. Two things must happen first, by a human:
--   1. authority_checked_at — go read the actual source and confirm it still says
--      this. Until then the pack is RESEARCH, and the engine will say so.
--   2. check_spec — bind it to real columns and confirm the query is right.
-- Activating a rule nobody has verified would be the exact failure this whole
-- system exists to catch. Do not bulk-flip these to true.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1) Harden the evidence table. A record that can be edited is not a record.
--    "Records stored in editable folders" is itself a standing nonconformity.
-- ---------------------------------------------------------------------------
--    ⚠️ CORRECTED 2026-08-12 — after testing it. The first version used
--    REVOKE UPDATE, DELETE, and REVOKE DOES NOTHING HERE: the app role
--    (helix_user) OWNS these tables, and a PostgreSQL table owner always keeps
--    full rights on it, so a REVOKE against the owner is silently a no-op.
--    Verified — after the REVOKE, `UPDATE compliance_check_run SET verdict=…`
--    still succeeded. The protection was a comforting lie: exactly the failure
--    this system exists to catch, found in the system itself by going to look.
--
--    A trigger holds regardless of ownership. The REVOKE stays underneath it as
--    defence in depth for any future non-owner role.
CREATE OR REPLACE FUNCTION compliance_evidence_is_append_only() RETURNS trigger AS $fn$
BEGIN
  RAISE EXCEPTION
    'compliance evidence is append-only: % is not permitted on %. A verdict that '
    'can be edited is not evidence — to correct a wrong one, run the check again. '
    'The newer row supersedes it by timestamp and the mistake stays visible.',
    TG_OP, TG_TABLE_NAME;
END;
$fn$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables
             WHERE table_name = 'compliance_check_run') THEN
    DROP TRIGGER IF EXISTS trg_ccr_append_only ON compliance_check_run;
    CREATE TRIGGER trg_ccr_append_only
      BEFORE UPDATE OR DELETE ON compliance_check_run
      FOR EACH ROW EXECUTE FUNCTION compliance_evidence_is_append_only();
    EXECUTE 'REVOKE UPDATE, DELETE ON compliance_check_run FROM PUBLIC';
  END IF;
  -- age_check_event is evidence too: a refusal that can be deleted proves nothing.
  IF EXISTS (SELECT 1 FROM information_schema.tables
             WHERE table_name = 'age_check_event') THEN
    DROP TRIGGER IF EXISTS trg_ace_append_only ON age_check_event;
    CREATE TRIGGER trg_ace_append_only
      BEFORE UPDATE OR DELETE ON age_check_event
      FOR EACH ROW EXECUTE FUNCTION compliance_evidence_is_append_only();
    EXECUTE 'REVOKE UPDATE, DELETE ON age_check_event FROM PUBLIC';
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2) Audit rule edits with the machinery that already exists.
--    Who changed a rule, and when, is itself evidence an inspector may want.
--    (audit_capture() comes from scripts/db/audit_log_setup.sql — run that first.)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'audit_capture')
     AND EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_name = 'compliance_rule') THEN
    DROP TRIGGER IF EXISTS trg_audit_compliance_rule ON compliance_rule;
    CREATE TRIGGER trg_audit_compliance_rule
      AFTER INSERT OR UPDATE OR DELETE ON compliance_rule
      FOR EACH ROW EXECUTE FUNCTION audit_capture();
  ELSE
    RAISE NOTICE 'audit_capture() or compliance_rule missing — trigger skipped';
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 3) The pack.
--    check_kind = 'none' means: we have NOT found a way to prove this yet, and
--    the engine will honestly return UNSOURCED rather than a comfortable green.
--    Those rows are the build list.
-- ---------------------------------------------------------------------------

INSERT INTO compliance_rule
  (id, store_number, code, revision, statement, rationale,
   authority, authority_url, authority_checked_at,
   check_kind, check_spec, expectation, severity, frequency_hours,
   is_active, created_at, created_by)
VALUES

-- === AGE-18-TABAK ==========================================================
-- CORRECTED 2026-08-12 after tracing pos_router.py. An earlier draft of this
-- seed said "no age check exists". That was wrong, and the correction matters:
--
--   The CONTROL exists and is enforced. _assert_age_cleared() (pos_router.py
--   :5615) runs server-side on BOTH sale paths (checkout :5721, quick-sale
--   :6033), reads product_class through the taxonomy, and REJECTS the sale with
--   400 unless an of-age member is attached or the cashier attests. A member
--   proven under 18 by DOB cannot be overridden by attestation.
--
--   What was missing was the RECORD. The function returns the method used and
--   both call sites discarded it; clearance went to the application log only,
--   which rotates and does not survive a restart. Refusals produced nothing at
--   all — the raise path was silent.
--
-- So this was never "we don't check". It was "we check, and cannot prove it".
-- Fixed by transactions.age_check_outcome. Stays inactive until that column
-- exists AND authority_checked_at is set by a human.
(gen_random_uuid(), NULL, 'AGE-18-TABAK', 1,
 'Every completed sale containing an age-restricted line carries a recorded basis on which the buyer''s age was cleared.',
 'Testable by cantonal test purchase at any time; since 2024-10-01 a failed test purchase is usable in administrative and criminal proceedings. The control is already enforced server-side on both sale paths — this rule proves the record exists, not that the check happens. Requires transactions.age_check_outcome and line_items.was_age_restricted.',
 'Tabakproduktegesetz (TabPG), in force 2024-10-01 — national Abgabealter 18',
 'https://www.bag.admin.ch/de/faq-zur-umsetzung-des-tabakproduktegesetzes', NULL,
 'sql',
 'SELECT t.transaction_number, t.completed_at, t.age_check_outcome FROM transactions t JOIN line_items li ON li.transaction_id = t.id WHERE t.status = ''COMPLETED'' AND li.was_age_restricted = true AND (t.age_check_outcome IS NULL OR t.age_check_outcome IN (''not_required'')) GROUP BY t.transaction_number, t.completed_at, t.age_check_outcome;',
 '0 rows', 'critical', 24, FALSE, now(), 'seed'),

-- === AGE-18-BASIS-QUALITY ==================================================
-- Not every clearance is equal evidence. 'member_dob' rests on a date of birth
-- on file. 'member_confirmed' rests on someone having ticked a box at some
-- point, with no DOB behind it — the documented back-compat path in
-- customer_schema.member_of_age(). Both let the sale through, and should. But
-- an inspector asking "how do you know she was 18" gets a very different answer
-- for each, so the shop should be able to SEE how much of its trade rests on a
-- tick and go convert those members to a real DOB.
-- This rule reports rather than polices: a rising share is the signal.
(gen_random_uuid(), NULL, 'AGE-18-BASIS-QUALITY', 1,
 'The shop knows what share of its age-restricted sales were cleared on a legacy tick rather than a recorded date of birth, and that share is falling.',
 'member_of_age() lets a legacy member (age_confirmed=true, no birthdate) through on purpose, so no member or sale breaks. That is correct operationally and weak evidentially. Measuring it is how it gets fixed; hiding it behind a single boolean is how it never does.',
 'House control derived from TabPG; ISO 9001 cl. 7.5 evidence quality',
 NULL, NULL,
 'sql',
 'SELECT count(*) FILTER (WHERE age_check_outcome = ''member_confirmed'') AS on_a_tick, count(*) FILTER (WHERE age_check_outcome IN (''member_dob'',''member_confirmed'',''cashier_attest'')) AS age_gated FROM transactions WHERE status = ''COMPLETED'' AND completed_at > now() - interval ''90 days'';',
 'on_a_tick trending down; report only, never a hard fail',
 'minor', 720, FALSE, now(), 'seed'),

-- === AGE-18-REFUSALS =======================================================
-- The most valuable evidence in the whole pack, and the only one that proves a
-- control BITES rather than merely exists. A shop with thousands of 18+ sales
-- and zero refusals reads exactly like a shop that never checks.
--
-- This is the same instinct already written into store_settings.cash_tolerance:
-- "a box balancing to 0.00 every day for a year is a red flag, not a gold star."
-- Same principle, different control.
--
-- Deliberately NOT a hard fail — a small shop can genuinely go a quiet month.
-- It asks a question; a human answers it.
(gen_random_uuid(), NULL, 'AGE-18-REFUSALS', 1,
 'Refused age-restricted sales are recorded, and the shop can show that the age gate has actually turned someone away.',
 'Proof that a control works is the record of the times it said no. Before the age_check_event table the refusal path raised a 400 and left nothing behind — the single most useful piece of evidence was the one thing not kept.',
 'House control; evidential support for TabPG compliance',
 NULL, NULL,
 'sql',
 'SELECT count(*) AS refusals_90d FROM age_check_event WHERE outcome = ''refused'' AND occurred_at > now() - interval ''90 days'';',
 'at least 1 over 90 days; zero is a question for a human, not an automatic fail',
 'minor', 720, FALSE, now(), 'seed'),

-- === AGE-FLAG-COVERAGE =====================================================
-- Checkable TODAY. Before you can prove the age check happened, you must know
-- which products need one. This catches the upstream error: a product in an
-- age-restricted class that nobody flagged.
(gen_random_uuid(), NULL, 'AGE-FLAG-COVERAGE', 1,
 'Every product belonging to an age-restricted class is flagged as age-restricted, with a stated reason.',
 'The age check cannot fire on a product nobody marked. This is the upstream half of AGE-18-TABAK and it is provable with what is already in the database.',
 'Tabakproduktegesetz (TabPG) — house control derived from it',
 NULL, NULL,
 'sql',
 'SELECT sku, name, product_class FROM products WHERE is_active = true AND product_class IN (''tobacco'',''nicotine'',''cbd'',''vape'') AND (is_age_restricted = false OR age_reason IS NULL);',
 '0 rows', 'critical', 24, FALSE, now(), 'seed'),

-- === THC-1PCT ==============================================================
-- cbd_products.thc_percentage already exists and its own column comment says
-- "must be < 1% for Swiss legal". The instinct was already in the codebase.
-- This makes it checkable instead of aspirational.
(gen_random_uuid(), NULL, 'THC-1PCT', 1,
 'Every hemp or CBD product offered for sale has a recorded THC value below 1%.',
 'St. Gallen spot check: 14 of 32 hemp products were over the limit, sometimes by a multiple. The failure mode is not cheating — it is trusting a supplier''s word and never holding the paper.',
 'Swiss narcotics law — hemp at or above 1% THC is a narcotic (BetmG)',
 NULL, NULL,
 'sql',
 'SELECT id, product_name, thc_percentage FROM cbd_products WHERE thc_percentage IS NULL OR thc_percentage >= 1.0;',
 '0 rows', 'critical', 24, FALSE, now(), 'seed'),

-- === THC-LAB-PAPER =========================================================
-- The other half of THC-1PCT: a number typed into a field is not evidence.
-- traceable_items carries batch_id / batch_code / origin — the hooks exist.
(gen_random_uuid(), NULL, 'THC-LAB-PAPER', 1,
 'Every recorded THC value is traceable to a lab result for that specific batch, and the document can be produced on request.',
 'An inspector does not want the number, they want the paper behind it. A typed figure with no document is exactly how the St. Gallen shops failed.',
 'Lebensmittelgesetz (LMG) traceability; anticipated seed-to-sale requirement',
 NULL, NULL,
 'none', NULL, 'every batch with a THC value has a linked lab document',
 'critical', 168, FALSE, now(), 'seed'),

-- === CBD-INGESTIBLE ========================================================
-- Felix''s instinct, made precise. There is NO legal route to sell CBD oil for
-- ingestion in Switzerland — not in a shop, and not in a pharmacy either. A
-- pharmacy is not a loophole; it just declares the product as a cosmetic or a
-- chemical like everyone else. WHAT THE PRODUCT IS DECLARED AS decides legality.
(gen_random_uuid(), NULL, 'CBD-INGESTIBLE', 1,
 'No CBD product is sold, labelled or described for ingestion. Every CBD product carries an explicit legal product category — cosmetic, aroma, chemical, or tea.',
 'CBD extracts (other than hemp SEED oil) are Novel Food: not consumed in meaningful quantities before 1997, therefore requiring authorisation. Not one CBD food authorisation has ever been granted in Switzerland. Tea is the noted exception — tea does not fall under the Novel Food rule. Selling as a medicine requires Swissmedic authorisation. So the declared category IS the compliance boundary, and it is a catalogue field.',
 'BLV Merkblatt / Vollzugshilfe — Produkte mit Cannabidiol (CBD); Novel Food',
 'https://www.blv.admin.ch/dam/blv/de/dokumente/lebensmittel-und-ernaehrung/rechts-und-vollzugsgrundlagen/merkblatt-produkte-cannabidiol.pdf.download.pdf/cannabidiol-merkblatt-vollzugshilfe-final-de.pdf',
 NULL,
 'none', NULL, 'every CBD SKU has a declared legal category, and none is ingestible',
 'critical', 168, FALSE, now(), 'seed'),

-- === NO-HEALTH-CLAIM =======================================================
-- Kanton Zürich warned 13 people and banned sales/advertising at two online
-- shops over exactly this. Note the scope: the WEBSITE too, not just the shelf.
(gen_random_uuid(), NULL, 'NO-HEALTH-CLAIM', 1,
 'No product in the shop, on the shelf talker, or on the website is described with a health claim or sold as a food supplement.',
 'Trade AND advertising of CBD food supplements is illegal; violators face chargeable measures from the food control authority plus a criminal complaint. Zurich has already issued sales and advertising bans. The bans landed on the ADVERTISING, so this rule must cover the website.',
 'Lebensmittelgesetz (LMG) / LIV — health claims; BLV CBD Merkblatt',
 NULL, NULL,
 'sql',
 'SELECT sku, name FROM products WHERE is_active = true AND (lower(coalesce(name,'''') || '' '' || coalesce(description,'''') || '' '' || coalesce(tags,'''')) ~ ''(nahrungsergänz|supplement|heilt|heilung|lindert|entzündungshemmend|therapeut|medizinisch|cures|treats|relieves|anti-inflammatory)'');',
 '0 rows', 'critical', 24, FALSE, now(), 'seed'),

-- === LABEL-COMPLETE ========================================================
-- 16 of 32 St. Gallen products failed labelling. Most common write-up there is.
-- Two-stage by design: the database half is provable, the shelf half needs a
-- named human to walk and attest. Both are legitimate evidence; only one is
-- automatic, and the model refuses to blur them.
(gen_random_uuid(), NULL, 'LABEL-COMPLETE', 1,
 'Every product on the shelf carries a compliant label: correct designation, composition, origin and any required warning.',
 'The single most common way a Swiss shop gets written up. The database can prove the fields are populated; only a person walking the shelf can prove the physical label matches.',
 'Lebensmittelgesetz (LMG) and consumer-goods ordinances; enforced by the cantonal laboratory',
 NULL, NULL,
 'manual', 'Shelf walk: sample 10 SKUs across classes, photograph labels, attest.',
 'a dated attestation by a named person, at least monthly',
 'major', 720, FALSE, now(), 'seed'),

-- === LOT-TRACEABLE =========================================================
-- Pure upside. Cheap now, and it is the foundation of everything a legalised
-- adult-use market will demand.
(gen_random_uuid(), NULL, 'LOT-TRACEABLE', 1,
 'Every unit sold can be traced back to a batch, and that batch back to a named supplier with a date received.',
 'Required in weaker form today; central to any future seed-to-sale regime. Build it now while the catalogue is small.',
 'LMG traceability; anticipated Swiss adult-use framework',
 NULL, NULL,
 'sql',
 'SELECT item_code, item_name FROM traceable_items WHERE batch_code IS NULL OR origin_farm_name IS NULL;',
 '0 rows', 'major', 168, FALSE, now(), 'seed'),

-- === TILL-ACCESS ===========================================================
-- Checkable today: transactions.cashier_id is NOT NULL and joins to users.
(gen_random_uuid(), NULL, 'TILL-ACCESS', 1,
 'Every transaction is attributable to a named member of staff who was active at the time.',
 'The generic access control any auditor expects, and the one that makes every other record trustworthy. If you cannot say who sold it, nothing else in the record means much.',
 'House control; general bookkeeping and audit expectation',
 NULL, NULL,
 'sql',
 'SELECT t.transaction_number, t.cashier_id FROM transactions t LEFT JOIN users u ON u.id = t.cashier_id WHERE u.id IS NULL;',
 '0 rows', 'major', 24, FALSE, now(), 'seed'),

-- === CASH-COUNT-DAILY ======================================================
-- store_settings.cash_tolerance already exists, and its column comment already
-- says it better than any auditor would: "an auditor wants a complete, reasoned
-- record, NOT a drawer that is always perfect."
(gen_random_uuid(), NULL, 'CASH-COUNT-DAILY', 1,
 'The cash box is counted at the close of every shift, and any variance beyond tolerance carries a written reason.',
 'A box that balances to 0.00 every day for a year is a red flag, not a gold star. The record must be complete and reasoned, not perfect.',
 'House control; bookkeeping',
 NULL, NULL,
 'sql',
 'SELECT id, closed_at FROM cash_shifts WHERE closed_at IS NOT NULL AND counted_total IS NULL;',
 '0 rows', 'major', 24, FALSE, now(), 'seed'),

-- === AUTHORITY-FRESH =======================================================
-- The rule that audits the rule pack. "Nobody owned the external document
-- register and it went stale" is a standard finding — so the pack watches
-- itself. This is also the rule that would have caught the tobacco-tax error.
(gen_random_uuid(), NULL, 'AUTHORITY-FRESH', 1,
 'Every rule in this pack has had its legal source re-read by a person within the last 12 months.',
 'Laws change; the SOP quoting them does not. The Federal Supreme Court struck down the tobacco tax on low-THC hemp flower and our own notes carried the old position for a day before anyone looked. This rule is the tripwire for exactly that.',
 'ISO 9001 cl. 7.5 — control of external documented information',
 NULL, NULL,
 'sql',
 'SELECT code, revision, authority, authority_checked_at FROM compliance_rule WHERE is_active = true AND (authority_checked_at IS NULL OR authority_checked_at < now() - interval ''12 months'');',
 '0 rows', 'major', 720, FALSE, now(), 'seed')

ON CONFLICT (code, revision) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 4) What you just loaded
-- ---------------------------------------------------------------------------
DO $$
DECLARE n_total INT; n_checkable INT;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE check_kind <> 'none')
    INTO n_total, n_checkable FROM compliance_rule;
  RAISE NOTICE 'rule pack: % rules, % with a check defined, 0 active (by design)',
    n_total, n_checkable;
  RAISE NOTICE 'next: set authority_checked_at by READING the source, then activate one rule at a time';
END $$;
