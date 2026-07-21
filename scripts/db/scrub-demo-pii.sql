-- ---------------------------------------------------------------
-- scrub-demo-pii.sql — make a restored PRODUCTION database safe to
-- show on a DEMO / showroom box (e.g. banco.wolfhold.app).
--
-- WHY: restoring a real prod backup gives you the impressive 5,000+
-- product catalog — but the same dump carries real MEMBER identities
-- and real SUPPLIER COSTS/margins. Anyone you hand a demo login to
-- (pam/felix) would see them. This scrub keeps the catalog looking
-- alive (products, prices, photos, loyalty tiers, spend, visit counts)
-- while stripping the PII and the margin secrets.
--
-- WHAT IT DOES (idempotent — safe to run more than once):
--   customers : real_name/email/phone/socials/birthday/notes → NULL,
--               handle → generic "member-NNN" (loyalty data KEPT)
--   suppliers : trade_discount_pct (the margin key) + contact PII → NULL
--               (supplier NAMES kept — they're public brands / provenance)
--   products  : cost, supplier_price, work_note → NULL (price KEPT)
--
-- It NEVER touches product name/price/description/photo/category, so the
-- shop still demos beautifully. Run it AFTER restore-from-b2.sh, BEFORE
-- you hand anyone a login. Wrapper: scripts/scrub-demo-pii.sh
-- ---------------------------------------------------------------
BEGIN;

-- --- MEMBERS: anonymize identity, keep behavior --------------------
-- Deterministic generic handle per member (ordered by signup) so the
-- CRM list reads "member-001 … member-016" instead of real handles.
WITH ranked AS (
    SELECT id, row_number() OVER (ORDER BY created_at, id) AS rn
    FROM customers
)
UPDATE customers c
SET handle = 'member-' || lpad(ranked.rn::text, 3, '0')
FROM ranked
WHERE c.id = ranked.id;

UPDATE customers SET
    real_name = NULL,
    email     = NULL,
    phone     = NULL,
    instagram = NULL,
    telegram  = NULL,
    whatsapp  = NULL,
    birthday  = NULL,
    birthdate = NULL,
    notes     = NULL;

-- --- SUPPLIERS: blank the margin key + contact PII, keep the brand --
UPDATE suppliers SET
    trade_discount_pct = NULL,   -- cost = retail × (1 − pct/100): the secret
    contact_name       = NULL,
    contact_email      = NULL,
    contact_phone      = NULL,
    vat_number         = NULL,
    contacts           = NULL,
    notes              = NULL;

-- --- PRODUCTS: blank cost/margin, keep the shelf price + everything --
UPDATE products SET
    cost           = NULL,
    supplier_price = NULL,
    work_note      = NULL;

COMMIT;

-- --- Proof it took (0 real names, 0 costs left) --------------------
SELECT 'members'   AS scope, count(*) AS rows,
       count(real_name)     AS real_names_left,
       count(email)         AS emails_left
FROM customers
UNION ALL
SELECT 'suppliers', count(*),
       count(trade_discount_pct),
       count(contact_email)
FROM suppliers
UNION ALL
SELECT 'products',  count(*),
       count(cost),
       count(supplier_price)
FROM products;
