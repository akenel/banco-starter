-- Undo: the two rolls stored per_unit "3 for 10" that rang 13.33 at qty 4 (2026-08-21).
BEGIN;
UPDATE products SET price_tiers='[{"min_qty": 1, "unit_price": "4.00"}, {"min_qty": 3, "unit_price": "10.00"}]'::jsonb,
  tier_mode='per_unit' WHERE barcode IN ('42470342','716165174905');
COMMIT;
