-- Undo the 2026-08-22 category tidy: 18 bundle-priced papers moved to 'Rolling Papers'.
-- Angel: "can you fix them all so they are all Rolling Papers ... then they are all the same".
-- Nothing but the category changed; prices, tiers and modes were untouched.
UPDATE products SET category = 'Other' WHERE barcode = '2000000070070';  -- Greengo Rolls King Size
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '85966789';  -- Greengo Wide Rolls
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '2000000204109';  -- RAW Black Classic Rolls King Size 3 m
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '716165280293';  -- Raw Rolls Classic King Size
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '716165174905';  -- Raw Rolls Organic Hemp
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '2000000107073';  -- Smoking Blue Rolls 1pcs
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '2000000071015';  -- Smoking Brown Rolls
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '84196248';  -- Smoking Deluxe Black Rolls
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '84157089';  -- Smoking Gold Kingsize
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '84190369';  -- Smoking Green Kingsize
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '8414775015749';  -- Smoking King Size organic Slim
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '8414775022778';  -- Smoking King Size Supreme Zigarettenpapier
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '84196941';  -- Smoking Master Silver Rolls
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '84157065';  -- Smoking Red Kingsize
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '8414775015763';  -- Smoking Rolls organic
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '2000000163079';  -- Smoking Rolls organic XL
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '8414775018023';  -- Smoking Rolls red thinnest
UPDATE products SET category = 'Papers & Filters' WHERE barcode = '2000000262321';  -- Smoking Supreme Smoqueen Sapphire Blue King Size Slim
