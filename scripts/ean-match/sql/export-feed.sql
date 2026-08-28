-- The FourTwenty side of every card: one row per feed product that has both a GTIN and a
-- photograph. Columns, in the order select_run.load_feed() expects:
--
--     gtin, title, image url, artikel_pro_verkaufseinheit, brand, PRICE
--
-- PRICE (`salespriceinclvat`) is the sixth column and it is why this file exists. It is the
-- box-vs-packet tell: on the papers run the four cases a human confirmed came out at 4.5x,
-- 15.4x, 20.0x and 26.7x our shelf price, and all 37 retail rows sat between 0.5x and 2.5x.
--
-- ⚠ Do NOT add a category filter here. FourTwenty files rolling papers under `Rolls` AND
-- under `Themen · Gizeh January Action 10%` — a seasonal promotion used as a product type —
-- and filtering by category hid 18 of 29 findable answers (LESSON #2). Rank the whole pool.
--
--   ssh banco 'cd /root/banco-starter && docker compose exec -T postgres \
--     psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < export-feed.sql > work/poolfull.csv
--
COPY (SELECT coalesce(raw->>'gtin',''),
             title,
             coalesce(raw->>'mainimageurl', raw->>'imageurl_1',''),
             coalesce(raw->'_specs'->>'artikel_pro_verkaufseinheit','?'),
             coalesce(raw->>'brandname',''),
             coalesce(raw->>'salespriceinclvat','')
      FROM reference_products
      WHERE raw->>'gtin' IS NOT NULL
        AND coalesce(raw->>'mainimageurl', raw->>'imageurl_1') IS NOT NULL)
TO STDOUT WITH (FORMAT csv);
