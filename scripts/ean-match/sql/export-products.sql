-- Our side of every card: the shop's own products for ONE category, with the price the till
-- charges. `\set cat` before running, e.g.  psql -v cat="'Rolling Papers'" -f export-products.sql
--
--     sku, name, barcode, image_url, cat, minted, price
--
-- `minted` is the whole point of the run: true = a 200… code that exists only inside this
-- building and can never be on a packet, so this row NEEDS an EAN. false = already bound off
-- a real packet, so it rides along as a CONTROL and measures the run against itself.
--
-- `price` is new (2026-08-28) and it is what puts the box-vs-packet ratio on the card.
-- Rows are joined to their FIRST image; a product with no photograph cannot be matched by
-- picture and is left out on purpose.
--
--   ssh banco 'cd /root/banco-starter && docker compose exec -T postgres \
--     psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v cat="'"'"'Rolling Papers'"'"'"' \
--     < export-products.sql > work/ours_papers.csv
--
COPY (SELECT p.sku AS sku,
             p.name AS name,
             coalesce(p.barcode,'') AS barcode,
             '/api/v1/pos/products/' || p.id || '/images/' || i.id AS image_url,
             coalesce(p.category,'') AS cat,
             CASE WHEN p.barcode_is_internal THEN 'true' ELSE 'false' END AS minted,
             p.price AS price
      FROM products p
      JOIN LATERAL (SELECT id FROM product_images
                    WHERE product_id = p.id
                    ORDER BY sort_order, created_at LIMIT 1) i ON true
      WHERE p.is_active
        AND p.category ILIKE '%' || :'cat' || '%')
TO STDOUT WITH (FORMAT csv, HEADER);
