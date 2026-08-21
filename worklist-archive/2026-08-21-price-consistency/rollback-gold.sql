-- Undo the Smoking Gold change of 2026-08-21 (stripped the min_qty:1 rung, price 2.00 -> 2.50).
BEGIN;
UPDATE products SET price = 2.00,
  price_tiers = '[{"min_qty": 1, "unit_price": "2.00"}, {"min_qty": 50, "unit_price": "0.90"}]'::jsonb,
  tier_mode = 'per_unit'
WHERE barcode = '84157089';
COMMIT;
