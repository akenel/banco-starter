-- Undo the 2026-08-22 fix that flipped three plain King Size papers from
-- tier_mode 'per_unit' to 'bundle' and dropped the no-op {min_qty:1} rung.
-- Prices were NOT touched; only the mode and the dead rung.
UPDATE products SET tier_mode='per_unit',
  price_tiers='[{"min_qty": 1, "unit_price": "2.00"}, {"min_qty": 3, "unit_price": "5.00"}]'::jsonb
WHERE id::text LIKE 'cedc2897%'   -- Elements Phantom King Size Slim
   OR id::text LIKE '958f694f%'   -- Elements Zushi King Size Slim
   OR id::text LIKE '7d848508%';  -- Greengo King Size slim
