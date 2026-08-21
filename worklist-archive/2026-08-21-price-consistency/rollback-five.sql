-- Undo: five King Size papers set to standard / no age gate, 2026-08-21.
BEGIN;
UPDATE products SET product_class='tobacco_nicotine', is_age_restricted=true, category='Tobacco' WHERE id='baedcfb8-b277-4a6d-9442-8f59020a29e1';   -- Smoking KS Slim Thinnest Papers
UPDATE products SET product_class='tobacco_nicotine', is_age_restricted=true, category='Tobacco' WHERE id='72f2da5f-c851-4000-a6cf-e81dee83b35c';   -- JaJa Noir King Size XXL Black Zigarettenpapier
UPDATE products SET product_class='tobacco_nicotine', is_age_restricted=true, category='Tobacco' WHERE id='c37bbf08-7b35-4114-a6ba-21b8a632be50';   -- JaJa Noir King Size XXL Black Zigarettenpapier
UPDATE products SET product_class='tobacco_nicotine', is_age_restricted=true, category='Tobacco' WHERE id='4d3c08b6-c5fc-4fef-9946-a1f6acfe2753';   -- JaJa Noir King Size XXL Black Zigarettenpapier
UPDATE products SET product_class='cbd_hemp', is_age_restricted=true, category='Other' WHERE id='5f752f0e-0a5c-4d54-9508-f00e2dba7514';   -- Purize King Size Slim "420 Papers"
COMMIT;
