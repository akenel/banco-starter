-- Undo: Rips reclassified as rolls, 2026-08-21.
BEGIN;
UPDATE products SET price=4.00, price_tiers=NULL, tier_mode=NULL WHERE barcode='50717088';
UPDATE products SET price=4.00, price_tiers='[{"min_qty": 3, "unit_price": "10.00"}]'::jsonb, tier_mode='bundle' WHERE barcode='50717064';
UPDATE products SET price=4.00, price_tiers='[{"min_qty": 1, "unit_price": "3.50"}]'::jsonb, tier_mode='per_unit' WHERE barcode='5027978771232';
UPDATE products SET price=4.00, price_tiers=NULL, tier_mode=NULL WHERE barcode='5027978771201';
UPDATE products SET price=4.00, price_tiers='[{"min_qty": 3, "unit_price": "6.00"}, {"min_qty": 5, "unit_price": "9.00"}, {"min_qty": 10, "unit_price": "17.00"}]'::jsonb, tier_mode='bundle' WHERE barcode='50717095';
UPDATE products SET price=3.50, price_tiers=NULL, tier_mode=NULL WHERE barcode='5027978771249';
UPDATE products SET price=4.00, price_tiers=NULL, tier_mode=NULL WHERE barcode='50717071';
UPDATE products SET price=2.00, price_tiers='[{"min_qty": 3, "unit_price": "5.00"}]'::jsonb, tier_mode='bundle' WHERE barcode='5027978771263';
UPDATE products SET price=2.90, price_tiers=NULL, tier_mode=NULL WHERE barcode='2000000041407';
UPDATE products SET price=2.90, price_tiers=NULL, tier_mode=NULL WHERE barcode='2000000046440';
UPDATE products SET price=2.90, price_tiers=NULL, tier_mode=NULL WHERE barcode='2000000028323';
UPDATE products SET price=2.40, price_tiers=NULL, tier_mode=NULL WHERE barcode='2000000028330';
COMMIT;
