#!/usr/bin/env python3
# ============================================================================
# import_reference_catalog — fill `reference_products` from a supplier feed.
#
# RUN IT INSIDE THE APP CONTAINER. The Dockerfile bakes in `src/` only (line 29), and from
# the host `postgres:5432` does not resolve — so this is a copy-in job, same as
# adopt-images.py. On the box:
#
#   docker exec banco-app mkdir -p /app/scripts
#   docker cp scripts/import_reference_catalog.py banco-app:/app/scripts/
#   docker cp /path/to/fourtwenty                 banco-app:/tmp/ft
#   docker exec banco-app python3 /app/scripts/import_reference_catalog.py /tmp/ft
#   docker exec banco-app python3 /app/scripts/import_reference_catalog.py /tmp/ft --apply
#
# DRY RUN unless --apply. The dry run walks identical code, so what it reports is what the
# apply does.
#
# WHY THIS EXISTS
# ---------------
# `reference_product_model.py` says, in its own docstring:
#
#     "Written to only by the importer (scripts/import_reference_catalog.py);
#      read-only at the counter."
#
# That file did not exist. Measured 2026-08-21: `reference_products` held
# **0 rows on Felix's shop, 0 on the sandbox, 0 on lapiazza**, and the table does not
# exist on wolfhold. So every FourTwenty path in the app — /reference/search,
# reference_matches in snap-find, /catalog/match-candidates, _reference_best_match,
# POST /reference/{id}/adopt — has been querying an empty table on every machine for
# its whole life. All correct, all green, all reading nothing.
#
# Angel, at the shelf: *"seems to me FourTwenty has the items, we just don't get matches
# and our 420 lookup is failing when it should be working… I have the feeling that they
# are the proper numbers."* Both halves are right. He was doing nothing wrong.
#
# The feed carries 10,082 rows, **9,977 with a real GTIN (99.8%)**, with prices and
# photos. Two of the three EANs he failed to look up on 2026-08-20 are in it with full
# data. It was sitting in `helixnet/debllm/feeds/fourtwenty/` — the monster repo Banco
# left — the entire time.
#
# WHAT THIS DOES NOT DO
# ---------------------
# It does not touch `products`. Nothing here sells, prices, or renames anything in the
# live catalogue. `reference_products` is a clipboard beside the catalogue: the counter
# reads it, a human adopts from it. Loading it cannot break a till.
#
# It also does not, on its own, fix the shelf. Two things still stand in the way and
# both are named in worklist-archive/2026-08-21-fourtwenty-reference.md:
#   - shelf-intake triage refuses to match unknowns ("a bare EAN carries no name") —
#     reasoning that was only ever true BECAUSE this table was empty;
#   - _find_catalog_matches searches this table by TITLE only, never by barcode.
#
# IDEMPOTENT. Upserts on (supplier, ref_key), so re-running a fresh dump updates in
# place. Run it again whenever the supplier sends a new one.
# ============================================================================
import argparse
import csv
import html
import json
import os
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation

# Works both on the host (repo root) and inside the container (/app), like the other
# scripts here — adopt-images.py hardcodes /app, which only runs one of the two ways.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, "/app"):
    if os.path.isdir(os.path.join(p, "src")) and p not in sys.path:
        sys.path.insert(0, p)

C = {"grn": "\033[32m", "yel": "\033[33m", "red": "\033[31m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}

# The FourTwenty dropship feed, per Angel's own reference-map.yaml which sat beside the
# CSVs waiting for this script. `--map` overrides any of it.
DEFAULT_MAP = {
    "title": "producttitle_de",
    "barcode": "gtin",
    "supplier_sku": "sku",
    "image_url": "mainimageurl",
    "category": "categorygroup_1",
    "suggested_price": "salespriceinclvat",
    # no description or cost column in this feed — description is assembled from the
    # specifications file below, which is where the real copy lives.
}

# Specification keys worth putting in the description, in the order a person reads them.
# The feed ships ~40 keys; most are logistics (packaging width, disposal class) that help
# nobody at a counter. These are the ones that answer "is this the right thing".
SPEC_ORDER = [
    ("Hersteller", "Hersteller"),
    ("genaue_materialbezeichnung", "Material"),
    ("materialgruppe", "Material"),
    ("farbe", "Farbe"),
    ("fullmenge", "Füllmenge"),
    ("gewicht", "Gewicht"),
    ("lange", "Länge"),
    ("breite", "Breite"),
    ("hohe_cm", "Höhe"),
    ("durchmesser", "Durchmesser"),
    ("artikel_pro_verkaufseinheit", "Stück pro VE"),
    ("Einheitenbezeichung", "Einheit"),
    ("einsatzbereich", "Einsatzbereich"),
    ("certificates", "Zertifikate"),
]


# ---------------------------------------------------------------- small helpers
def sniff_reader(path):
    """The products feed is semicolon-delimited and the stock feed is comma-delimited,
    in the same directory. Guessing wrong yields one giant column and a silent zero
    import, so read the header and decide rather than assuming."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        first = fh.readline()
    delim = ";" if first.count(";") > first.count(",") else ","
    fh = open(path, encoding="utf-8-sig", newline="")
    return csv.DictReader(fh, delimiter=delim), fh, delim


def read_flat_map(path):
    """Angel's reference-map.yaml is flat `key: value` with # comments. Parsed by hand so
    the script has no PyYAML dependency — a missing import must never be the reason the
    shop's lookup table stays empty."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip().strip('"\'')
            if k and v:
                out[k] = v
    return out


def txt(raw):
    """The feed ships HTML entities in plain CSV fields — `Zubehör Storz&amp;Bickel`. Stored
    raw they show up on the counter's screen as literal `&amp;`, and they poison a trigram
    match against a live product spelled with a real ampersand."""
    v = html.unescape((raw or "").strip())
    return " ".join(v.split()) or None


_BARCODE_JUNK = re.compile(r"[\x00-\x20\x7f]+")


def clean_barcode(raw):
    """A code is contiguous digits. Anything else is not a barcode and must not be stored
    as one — a junk 'code' in this table would resolve a scan to the wrong product, and
    Lesson 8 says a wrong bind looks exactly like a right one."""
    code = _BARCODE_JUNK.sub("", (raw or "").strip())
    if not code or not code.isdigit():
        return None
    if not (8 <= len(code) <= 14):
        return None
    if code.strip("0") == "":
        return None
    return code


def slug(s, n=120):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n] or None


def money(raw):
    try:
        v = Decimal(str(raw).replace("'", "").replace(",", ".").strip())
    except (InvalidOperation, AttributeError, ValueError):
        return None
    return float(v) if v >= 0 else None


def load_specs(path):
    """ProviderKey;SpecificationKey;SpecificationValue -> {sku: {key: value}}."""
    specs = {}
    rd, fh, _ = sniff_reader(path)
    try:
        for r in rd:
            k = (r.get("ProviderKey") or "").strip()
            key = (r.get("SpecificationKey") or "").strip()
            val = (r.get("SpecificationValue") or "").strip()
            if k and key and val:
                specs.setdefault(k, {})[key] = val
    finally:
        fh.close()
    return specs


def describe(spec):
    """Assemble the supplier's own spec table into a readable line.

    It goes in the DESCRIPTION rather than fields of its own, deliberately and for the
    same reason readPageFacts does it (catalog.html): `description` is saved, shown,
    editable AND searched — `word_similarity(q, name || ' ' || description)` is what lets
    an English query find a German-named row. A hidden field would not be findable."""
    if not spec:
        return None
    seen, bits = set(), []
    for key, label in SPEC_ORDER:
        v = txt(spec.get(key))
        if not v or label in seen:
            continue
        seen.add(label)
        bits.append(f"{label}: {v}")
    return " · ".join(bits) or None


def supplier_says_18(spec):
    """What the SUPPLIER's feed claims. Recorded, never believed.

    ⚠️ 2026-08-21, caught in the first dry run: FourTwenty marks a **USB wall plug adapter**
    and a **battery charger** as `age_verification: Yes, mindestalter: 18`. That flag is not
    a statement about the product — it is their own webshop's blanket checkout policy,
    because they also sell tobacco. Importing it would have gated 2,220 rows, and
    `/reference/{id}/adopt` copies `age_restricted` STRAIGHT ONTO THE LIVE PRODUCT
    (pos_router.py:2287), so every one of those becomes a real 18+ product at Felix's till.

    A till that demands ID for a phone charger teaches the cashier to click through the age
    gate, and a gate everybody clicks through is not a gate. Over-gating is not the safe
    direction here; it is the direction that quietly destroys the thing.

    So: OUR classifier decides (same call the till makes on create), this stays in `raw`
    for audit, and the import prints where the two disagree so a person can look."""
    if not spec:
        return False
    if (spec.get("age_verification") or "").strip().lower() in ("yes", "ja", "true", "1"):
        return True
    m = re.search(r"\d+", spec.get("mindestalter") or "")
    return bool(m and int(m.group()) >= 16)


def pick_category(row, mapping):
    """The feed nests three category groups plus a product category. Prefer the most
    specific non-empty one — 'Drehtabak und Zigaretten' says more than 'Headshop'."""
    for col in ("productcategory", "categorygroup_3", "categorygroup_2",
                mapping.get("category", "categorygroup_1"), "categorygroup_1"):
        v = txt(row.get(col))
        if v:
            return v[:100]
    return None


# ---------------------------------------------------------------- feed -> rows
def build_rows(products_csv, specs, mapping, supplier, limit=0):
    """Turn the feed into the exact column set reference_products wants.

    Returns (rows, stats, collisions, disagreements). Nothing is written here — a dry run and an apply
    walk identical code, so what the dry run reports is what the apply does.
    """
    # classify() — not canonicalize_category + resolve_class_on_create. Its own docstring
    # says "Map a REFERENCE ITEM to (our_category, our_class, age_restricted)" and its
    # second layer reads the SUPPLIER CATEGORY: "the reliable signal the title hides —
    # nicotine e-cigs, shisha tobacco, CBD flower/pollen". It was written for this table
    # and has never had a caller, because the importer it was written for did not exist.
    from src.services.catalog_taxonomy import classify

    rd, fh, delim = sniff_reader(products_csv)
    rows, by_key = [], {}
    stats = {"read": 0, "no_title": 0, "no_key": 0, "with_barcode": 0,
             "bad_barcode": 0, "with_image": 0, "with_price": 0,
             "age_gated": 0, "with_description": 0,
             "supplier_gates_we_do_not": 0, "we_gate_supplier_does_not": 0}
    collisions, disagreements = [], []
    try:
        for raw_row in rd:
            stats["read"] += 1
            if limit and len(rows) >= limit:
                break

            title = txt(raw_row.get(mapping["title"]))
            if not title:
                stats["no_title"] += 1
                continue

            sku = txt(raw_row.get(mapping.get("supplier_sku", "sku")))
            raw_code = raw_row.get(mapping.get("barcode", "gtin"))
            barcode = clean_barcode(raw_code)
            if (raw_code or "").strip() and not barcode:
                stats["bad_barcode"] += 1

            # ref_key is the idempotency handle: supplier_sku, else barcode, else a title
            # slug. Order matters — the SKU is the supplier's own stable identity and
            # survives a title being reworded between dumps.
            ref_key = (sku or barcode or slug(title))
            if not ref_key:
                stats["no_key"] += 1
                continue
            ref_key = ref_key[:150]

            spec = specs.get(sku or "", {})
            description = describe(spec)
            image = txt(raw_row.get(mapping.get("image_url", "mainimageurl")))
            price = money(raw_row.get(mapping.get("suggested_price", "salespriceinclvat")))
            category = pick_category(raw_row, mapping)
            claimed_18 = supplier_says_18(spec)

            # Our own shelf + gating class, through the same functions the till uses, so a
            # reference row and a live row are classified identically — by what the thing IS
            # (tobacco/nicotine/alcohol/CBD in the name or the blurb), not by what a
            # dropshipper's checkout policy says. See supplier_says_18 above.
            # Classify by what the thing IS — the title first, then the supplier's own
            # category groups — never by the dropshipper's checkout policy. `raw_row` goes
            # in whole because _reftags() reads categorygroup_1..3 and productcategory
            # straight off it; that is the signal the title hides.
            our_category, our_class, age = classify(
                title, ref_category=category, raw=raw_row, description=description)
            if str(our_category or "").lower() in ("unsorted", "other", ""):
                # "Other" on ten thousand rows is a label that means nothing dressed as one
                # that means something. NULL — the supplier's own wording stays in `category`.
                our_category = None
            if claimed_18 and not age:
                stats["supplier_gates_we_do_not"] += 1
                disagreements.append(category or "—")
            elif age and not claimed_18:
                stats["we_gate_supplier_does_not"] += 1

            if barcode:
                stats["with_barcode"] += 1
            if image:
                stats["with_image"] += 1
            if price is not None:
                stats["with_price"] += 1
            if age:
                stats["age_gated"] += 1
            if description:
                stats["with_description"] += 1

            row = {
                "supplier": supplier[:100],
                "ref_key": ref_key,
                "supplier_sku": (sku or None) and sku[:100],
                "barcode": barcode,
                "title": title[:255],
                "description": description,
                "image_url": image and image[:500],
                "category": category,
                "suggested_price": price,
                "our_category": (our_category or None) and str(our_category)[:60],
                "our_class": (our_class or None) and str(our_class)[:40],
                "age_restricted": bool(age),
                # FLAT, feed columns at the TOP LEVEL — _reftags() (catalog_taxonomy.py) reads
                # raw["categorygroup_1"]..["productcategory"] straight off this dict, so
                # anything re-classifying a stored row later needs them there, not nested
                # under a "feed" key. Our additions are underscore-prefixed so they cannot
                # collide with a future feed column.
                "raw": json.dumps({**{k: v for k, v in raw_row.items() if v},
                                   "_specs": spec or {},
                                   # kept so nothing is lost and the call is auditable
                                   "_supplier_claims_18plus": claimed_18}, ensure_ascii=False),
            }

            # A duplicate ref_key inside ONE file is the supplier's problem, not the
            # database's — the upsert would silently keep whichever landed last and the
            # count would look right. Say so instead.
            if ref_key in by_key:
                collisions.append((ref_key, by_key[ref_key]["title"], title))
                by_key[ref_key] = row
                rows[[r["ref_key"] for r in rows].index(ref_key)] = row
                continue
            by_key[ref_key] = row
            rows.append(row)
    finally:
        fh.close()

    stats["delimiter"] = delim
    return rows, stats, collisions, disagreements


# ---------------------------------------------------------------- write
UPSERT = """
INSERT INTO reference_products
    (id, supplier, ref_key, supplier_sku, barcode, title, description, image_url,
     category, suggested_price, our_category, our_class, age_restricted, raw, imported_at)
VALUES
    (gen_random_uuid(), :supplier, :ref_key, :supplier_sku, :barcode, :title, :description,
     :image_url, :category, :suggested_price, :our_category, :our_class, :age_restricted,
     CAST(:raw AS jsonb), now())
ON CONFLICT ON CONSTRAINT uq_reference_products_supplier_refkey DO UPDATE SET
    supplier_sku    = COALESCE(EXCLUDED.supplier_sku, reference_products.supplier_sku),
    barcode         = COALESCE(EXCLUDED.barcode, reference_products.barcode),
    title           = EXCLUDED.title,
    description     = COALESCE(EXCLUDED.description, reference_products.description),
    image_url       = COALESCE(EXCLUDED.image_url, reference_products.image_url),
    category        = COALESCE(EXCLUDED.category, reference_products.category),
    suggested_price = COALESCE(EXCLUDED.suggested_price, reference_products.suggested_price),
    our_category    = COALESCE(EXCLUDED.our_category, reference_products.our_category),
    our_class       = COALESCE(EXCLUDED.our_class, reference_products.our_class),
    age_restricted  = reference_products.age_restricted OR EXCLUDED.age_restricted,
    raw             = EXCLUDED.raw,
    imported_at     = now()
"""
# COALESCE, not overwrite, on every enrichable column: a later dump that drops a photo or a
# price must not blank one we already have. Title is the exception — a reworded title IS the
# update. age_restricted ORs: a gate this table has ever asserted is never lowered by a feed.


async def write_rows(rows, batch=500):
    from sqlalchemy import text
    from src.db.database import AsyncSessionLocal as async_session_maker

    written = 0
    async with async_session_maker() as db:
        before = (await db.execute(text(
            "SELECT count(*) FROM reference_products WHERE supplier = :s"),
            {"s": rows[0]["supplier"]})).scalar_one()
        for i in range(0, len(rows), batch):
            chunk = rows[i:i + batch]
            for r in chunk:
                await db.execute(text(UPSERT), r)
            await db.commit()
            written += len(chunk)
            print(f"  {C['dim']}… {written}/{len(rows)}{C['x']}", end="\r", flush=True)
        after = (await db.execute(text(
            "SELECT count(*) FROM reference_products WHERE supplier = :s"),
            {"s": rows[0]["supplier"]})).scalar_one()
    print(" " * 40, end="\r")
    return before, after, written


async def verify(supplier):
    """Ask the DATABASE what it now holds — never report the numbers this script computed.
    A script that reports its own arithmetic can be wrong in exactly the way that matters
    (LESSONS.md: get the reference figure FROM the system)."""
    from sqlalchemy import text
    from src.db.database import AsyncSessionLocal as async_session_maker
    async with async_session_maker() as db:
        return (await db.execute(text("""
            SELECT count(*) AS rows,
                   count(barcode) AS with_barcode,
                   count(image_url) AS with_image,
                   count(suggested_price) AS with_price,
                   count(*) FILTER (WHERE age_restricted) AS age_gated,
                   count(DISTINCT barcode) AS distinct_codes
            FROM reference_products WHERE supplier = :s"""), {"s": supplier})).mappings().one()


# ---------------------------------------------------------------- main
def find_feed(target):
    """Accept a directory (the usual case — the feed ships as a set) or a single CSV."""
    if os.path.isfile(target):
        d = os.path.dirname(os.path.abspath(target))
        return target, os.path.join(d, "specifications_latest.csv")
    if not os.path.isdir(target):
        sys.exit(f"{C['red']}no such feed: {target}{C['x']}")
    products = None
    for name in ("products_latest.csv", "products.csv"):
        if os.path.isfile(os.path.join(target, name)):
            products = os.path.join(target, name)
            break
    if not products:
        cands = sorted(f for f in os.listdir(target) if f.startswith("products") and f.endswith(".csv"))
        if not cands:
            sys.exit(f"{C['red']}no products*.csv in {target}{C['x']}")
        products = os.path.join(target, cands[-1])
    return products, os.path.join(target, "specifications_latest.csv")


async def main(args):
    products_csv, specs_csv = find_feed(args.feed)
    mapping = dict(DEFAULT_MAP)
    if args.map:
        mapping.update({k: v for k, v in read_flat_map(args.map).items() if k in DEFAULT_MAP})
    elif os.path.isfile(os.path.join(os.path.dirname(products_csv), "reference-map.yaml")):
        auto = os.path.join(os.path.dirname(products_csv), "reference-map.yaml")
        mapping.update({k: v for k, v in read_flat_map(auto).items() if k in DEFAULT_MAP})
        print(f"{C['dim']}using column map {auto}{C['x']}")

    specs = {}
    if os.path.isfile(specs_csv) and not args.no_specs:
        specs = load_specs(specs_csv)
        print(f"{C['dim']}specifications: {len(specs)} SKUs from {os.path.basename(specs_csv)}{C['x']}")
    elif not args.no_specs:
        print(f"{C['yel']}no specifications file beside the feed — "
              f"descriptions and the supplier's 18+ flag will be missing{C['x']}")

    rows, stats, collisions, disagreements = build_rows(
        products_csv, specs, mapping, args.supplier, args.limit)

    mode = f"{C['grn']}APPLY{C['x']}" if args.apply else f"{C['yel']}dry run{C['x']}"
    print(f"\n{C['b']}Reference catalogue import{C['x']}  {C['dim']}({mode} · supplier "
          f"{args.supplier} · {os.path.basename(products_csv)} · '{stats['delimiter']}'-delimited){C['x']}\n")
    n = len(rows) or 1
    print(f"  rows read from the feed   {stats['read']}")
    print(f"  importable                {len(rows)}")
    print(f"  with a real barcode       {stats['with_barcode']}  ({100*stats['with_barcode']/n:.1f}%)")
    print(f"  with a photo              {stats['with_image']}  ({100*stats['with_image']/n:.1f}%)")
    print(f"  with a price              {stats['with_price']}  ({100*stats['with_price']/n:.1f}%)")
    print(f"  with a description        {stats['with_description']}  ({100*stats['with_description']/n:.1f}%)")
    print(f"  18+ by OUR classifier     {stats['age_gated']}  "
          f"{C['dim']}(what the till would decide){C['x']}")
    if stats["supplier_gates_we_do_not"]:
        print(f"  {C['dim']}supplier gates, we do not {stats['supplier_gates_we_do_not']}  "
              f"— their shop-wide policy, NOT imported{C['x']}")
    if stats["we_gate_supplier_does_not"]:
        print(f"  {C['dim']}we gate, supplier does not {stats['we_gate_supplier_does_not']}{C['x']}")

    # THE DECISION LIST. Most of the disagreement is FourTwenty gating chargers and coils,
    # which is theirs to do and not ours to copy. But some of it is a real question about
    # this shop's policy that a script must not answer on its own — e-liquids and pod
    # systems, where the existing classifier deliberately lets `0 mg` / `nikotinfrei`
    # through. Show the buckets where the supplier gates a lot and we gate none, ranked,
    # and let a person decide. Silence here would read as "nothing to see".
    if disagreements:
        from collections import Counter
        gated_by_cat = Counter()
        for r in rows:
            if r["age_restricted"] and r["category"]:
                gated_by_cat[r["category"]] += 1
        wholly_open = [(c, n) for c, n in Counter(disagreements).most_common()
                       if gated_by_cat.get(c, 0) == 0 and n >= 5]
        if wholly_open:
            print(f"\n  {C['yel']}Buckets the supplier gates and we gate NOT AT ALL "
                  f"— your call, not this script's:{C['x']}")
            for c, n in wholly_open[:12]:
                print(f"    {n:5d}  {c}")
            print(f"    {C['dim']}Most of these are accessories and are right to be open "
                  f"(coils, chargers, pouches,\n    filters). The ones worth a decision are "
                  f"liquids and pod systems: the classifier lets\n    `0 mg` / `nikotinfrei` "
                  f"through on purpose, so an unlabelled liquid stays open.{C['x']}")
    if stats["no_title"]:
        print(f"  {C['yel']}skipped, no title         {stats['no_title']}{C['x']}")
    if stats["no_key"]:
        print(f"  {C['yel']}skipped, no key           {stats['no_key']}{C['x']}")
    if stats["bad_barcode"]:
        print(f"  {C['yel']}barcode dropped as junk   {stats['bad_barcode']}{C['x']}  "
              f"{C['dim']}(non-numeric or wrong length — never stored as a code){C['x']}")
    if collisions:
        print(f"  {C['yel']}duplicate ref_key in file {len(collisions)}{C['x']}  "
              f"{C['dim']}(last one wins){C['x']}")
        for k, a, b in collisions[:3]:
            print(f"      {C['dim']}{k}: {a[:34]!r} -> {b[:34]!r}{C['x']}")

    if not rows:
        sys.exit(f"\n{C['red']}nothing importable — check the column map{C['x']}")

    print(f"\n  {C['dim']}sample:{C['x']}")
    for r in rows[:4]:
        print(f"    {(r['barcode'] or '—'):>14}  {r['title'][:42]:42s}  "
              f"{('CHF %.2f' % r['suggested_price']) if r['suggested_price'] is not None else '—':>10}"
              f"  {'🔞' if r['age_restricted'] else '  '} {C['dim']}{r['our_category'] or ''}{C['x']}")

    if not args.apply:
        print(f"\n{C['yel']}Dry run — nothing written.{C['x']} Re-run with --apply to load them.")
        print(f"{C['dim']}This table is read-only at the counter; it cannot change a price or a "
              f"live product.{C['x']}")
        return

    before, after, written = await write_rows(rows)
    v = await verify(args.supplier)
    print(f"{C['grn']}✅ upserted {written} row(s){C['x']}  "
          f"{C['dim']}({args.supplier}: {before} -> {after} rows){C['x']}\n")
    print(f"  {C['b']}the database says{C['x']}, asked fresh:")
    print(f"    rows            {v['rows']}")
    print(f"    with barcode    {v['with_barcode']}   distinct codes {v['distinct_codes']}")
    print(f"    with photo      {v['with_image']}")
    print(f"    with price      {v['with_price']}")
    print(f"    18+             {v['age_gated']}")
    print(f"\n{C['dim']}Next: an EAN miss still does not CONSULT this table by barcode "
          f"(_find_catalog_matches searches it by title only).\n"
          f"See worklist-archive/2026-08-21-fourtwenty-reference.md.{C['x']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Fill reference_products from a supplier CSV feed. Dry run unless --apply.")
    ap.add_argument("feed", help="feed directory (with products_latest.csv) or a single CSV")
    ap.add_argument("--supplier", default="FourTwenty",
                    help="source name stored on every row + half the upsert key (default: FourTwenty)")
    ap.add_argument("--map", help="flat key: value column map (e.g. the feed's reference-map.yaml)")
    ap.add_argument("--no-specs", action="store_true",
                    help="ignore specifications_latest.csv (no descriptions, no supplier 18+ flag)")
    ap.add_argument("--limit", type=int, default=0, help="only build the first N rows (testing)")
    ap.add_argument("--apply", action="store_true", help="actually write to the database")
    a = ap.parse_args()

    import asyncio
    asyncio.run(main(a))
