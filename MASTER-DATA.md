# Master data — the fields a product needs, and which ones we actually have

*Angel, 2026-07-31: "we are really having to make a proper master data. You know how SAP does it —
basic data, unit of measure, category, class, supplier. This is what's really missing."*

*Companion to [`CATALOG-IDENTITY.md`](CATALOG-IDENTITY.md), which covers **identity** (the EAN).
This covers everything else a row should carry.*

---

## The finding that shapes this

**Almost none of it needs building. It needs filling.**

The columns exist and are empty. `attributes` (JSONB, queryable), `source_lang`, `product_translations`,
`raw_facets`, `supplier_name`, `product_class` — all present in the model since before today, and all
blank or unused. The catalogue is not missing a schema. It is missing *data in the schema it has*.

| Field | Where it lives | State on 2026-07-31 |
|---|---|---|
| **identity** — barcode | `products.barcode` | 5,105 of 5,180 are **minted fictions**; 69 real |
| **sku** | `products.sku` | ✅ complete (`TAM-…` = Tamar's real article number) |
| **brand** | `attributes->>'brand'` | ⚠️ **0 → 1,277 (24%)** via `scripts/backfill-brands.py` |
| **supplier** | `products.supplier_name` | partial — and it is the *wholesaler*, not the maker |
| **category** | `products.category` | ✅ 99%, canonicalised through one funnel |
| **class** (18+, VAT) | `products.product_class` | ✅ complete, audited 2026-07-30 |
| **source language** | `products.source_lang` | ⚠️ NULL almost everywhere → **reads as English** |
| **unit / count / size** | `attributes` | ❌ empty — parsed ad-hoc from the name by `_product_size` |
| **names per language** | `product_translations` | ❌ 41 rows for 25 products, and **never searched** |
| **price** | `products.price` | ✅ 100% |
| **picture** | `products.image_url` | ✅ 99% |

**Brand and supplier are different things and the catalogue only knew one.** Tamar is who Felix buys
from. Gizeh is what the customer asks for, what is printed largest on the packet, and the strongest
single token for finding the right page on the web.

---

## On "English through and through"

Angel's proposal: *"we need a master catalogue that is English based through and through — titles,
everything. Whenever we find something, sanitise it, make sure the English is correct, even if we
got the German description."*

**Half of this is right and worth doing. Half of it is a trap, and it is worth being precise about
which is which**, because the two look identical from a distance.

### ✅ Right: a language slot must contain that language

If a row says its English description is *"su ekstra fine, gotovo prozirni papirići"*, that is a
**bug**, and a nasty one — the reader has no way to know they are being lied to. Every language slot
should hold that language or be honestly empty. `product_translations` already models exactly this
(per-language rows with provenance) and `source_lang` says what the base text actually is.

That is a real, bounded job: **fill the slots, and never store text under the wrong flag.**

### ⛔ Trap: electing one canonical title

Making English the single master title means throwing away the German name — and the German name is
what the shop says out loud, what the wholesaler's record uses, and what a Swiss cashier recognises.
Worse, it means every future product has to be *translated before it can be stored*, which puts a
translation step in the path of every capture.

`CATALOG-IDENTITY.md` rule 2 already settles this: **names are labels, plural, and none of them
wins.** The EAN is the identity; every name is an alias. Store them all, search across all.

Angel arrived at the same place himself the same afternoon, from the other direction: *"all of these
products have that Swissy local name, so I don't know if it even makes a difference… maybe that's
okay for Artemis, and they love that because they're Swissy."*

### So, concretely

```
products.name          what the counter says          (German here — leave it)
products.source_lang   what language that actually is  (say it, don't assume)
product_translations   every other name it is known by (English packet name, maker's name)
                       — and SEARCHED, which today it is not
```

The English name is not a replacement for the German one. It is another way in.

---

## What is worth doing next, in order

1. **Search `product_translations`.** The table exists, holds real rows, and no query touches it.
   Until it is searched, every alias anyone records is write-only. *This is the cheapest large win
   left.*
2. **Record the English packet name as an alias** at capture time, instead of discarding it. The
   shelf-intake screen already has it in hand.
3. **Backfill `source_lang`** where the base text is confidently German — `ensure_description`
   already self-heals one row at a time; do it in bulk so nothing is served as English that is not.
4. **Merge the two brand lists.** `catalog_brands.py` (96 entries, used to *suppress* wrong matches)
   and `brand_registry.py` (68 entries + 35 official sites, used to *find* the right page) overlap
   and disagree. One list, two uses.
5. **Unit / count into `attributes`.** `_product_size` already parses `34stk`, `250er`, `10ml` out
   of names on every comparison. Parse it once, store it, and stop re-deriving it.

None of this is a rewrite. The model was right; the import filled it in wrong, and the capture
screens were throwing away facts they already had.
