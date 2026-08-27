# Getting the real EANs from your distributor

*The single highest-leverage hour in standing up a shop's catalogue. Written 2026-08-27 at
Artemis Lucerne, after a day proving the alternative does not work.*

---

## Why this, and not clever matching

A catalogue seeded from a distributor's price list usually has **no barcodes** — a price list
carries an article number and a name, not the GTIN printed on the packet. Something then mints a
placeholder so every row has *a* code. Those placeholders are almost always in the GS1
**restricted-circulation range (prefix 20–29)**, which means: valid inside one building, nowhere
else. They cannot be on a packet, by definition.

The result is a catalogue that looks complete and **cannot be scanned**. At Artemis: 4,971 of
5,447 active products (91%) carried a minted `200…` code, and only 188 of 5,435 barcodes
(**3.5%**) existed in any real supplier feed. That 3.5% is what the shop owner experiences as
*"scan once, find it, move on — happens by luck 3% of the time."*

**Do not try to recover the EANs by matching product names.** Measured on this catalogue at
trigram similarity ≥ 0.80 — a threshold that sounds safe:

```
"Adapter NS 19/19 150mm"  → EAN 6097224146113
"Adapter NS 19/19 200mm"  → EAN 6097224146113      SAME EAN, two different products
"Adapter NS 19/19 120mm"  → a Dynavap adapter      wrong manufacturer
"Räucherstäbchenhalter Holz Hanfblatt"
                          → "…Holz Messing"        hemp leaf vs brass
```

Real catalogues differ by exactly the token that matters — a size, a material, a nicotine
strength, a pack count — and that token is a tiny fraction of the string, so trigrams cannot see
it. **A wrong barcode looks exactly like a right one** until someone re-scans the packet
(LESSON #9). Bulk name-matching does not save work; it manufactures invisible damage.

## Check the join key first — it is probably already there

Before asking for anything, check what your rows carry:

```sql
SELECT count(*) AS minted,
       count(supplier_sku) FILTER (WHERE supplier_sku <> '') AS has_article_no,
       min(sku) AS sample_sku, min(supplier_sku) AS sample_article_no
FROM products WHERE is_active AND barcode LIKE '2%' AND length(barcode) = 13;
```

At Artemis this returned **4,971 of 4,971** with the distributor's own article number, every SKU
prefixed `TAM-`. The minted barcode even *encodes* it — `2000000` + article no. + check digit:

```
article 1341  → 2000000013411      article 22535 → 2000000225357
article 23530 → 2000000235301      article 19883 → 2000000198835
```

If the article number is present, **there is no matching problem at all.** The distributor's list
joins on their own key, exactly, one column, no judgement calls, no review queue.

## The ask

Keep it to two columns. A distributor will say yes to two columns; they will stall on
"can we have your catalogue data" or "do you have an API".

> **Betreff: Artikelnummer → EAN-Liste**
>
> Guten Tag
>
> wir stellen unsere Kasse im Laden auf Barcode-Scanning um. Unsere Artikelstammdaten stammen aus
> eurem Sortiment, und wir führen zu jedem Artikel eure **Artikelnummer**. Was uns fehlt, ist die
> **EAN/GTIN, die auf der Packung aufgedruckt ist**.
>
> Könnt ihr uns eine Liste mit zwei Spalten schicken?
>
> ```
> Artikelnummer ; EAN
> ```
>
> Nur für die Artikel, die wir bei euch beziehen — die Artikelnummern sind in der beiliegenden
> Datei. Format egal: CSV, Excel, oder ein Export aus eurem System.
>
> Damit können wir jeden Artikel an der Kasse scannen. Ohne die EAN muss jede Packung von Hand
> erfasst werden.
>
> Besten Dank und freundliche Grüsse

Attach the article-number list so they never have to decide *which* articles you mean. Generate it
with:

```sql
COPY (SELECT supplier_sku AS "Artikelnummer", name AS "Bezeichnung"
      FROM products WHERE is_active AND supplier_sku <> '' AND barcode LIKE '200%'
      ORDER BY supplier_sku::bigint) TO STDOUT WITH CSV HEADER;
```

## When the list arrives

`POST /api/v1/pos/products/{id}/barcodes` already does the right thing per row, and it is the
only path that should be used:

- it **promotes** a real EAN into `products.barcode` and **demotes** the minted `2…` code to an
  alias in `product_barcodes` — never discards it, because shelf labels already printed with the
  minted code must keep scanning;
- it clears `barcode_is_internal`, so the catalogue, labels and exports stop showing the fiction;
- it 409s if the EAN already belongs to a different product, which is exactly the collision you
  want to hear about rather than silently resolve.

Feed it from the article-number join, not from a name match. Spot-check a random 20 against the
physical packets before running the rest — **verification against reality finds a class of error
that verification against the database cannot** (LESSON #8).
