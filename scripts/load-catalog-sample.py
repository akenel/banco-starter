#!/usr/bin/env python3
# ============================================================================
# load-catalog-sample — put a slice of the REAL catalogue into the dev DB.
#
#   python3 scripts/load-catalog-sample.py --csv /path/banco-products.csv --limit 200
#   python3 scripts/load-catalog-sample.py --csv ... --limit 200 --apply
#   python3 scripts/load-catalog-sample.py --purge          # remove the slice again
#
# WHY. `enrich-from-source.py` and `adopt-images.py` want to write ~5,111 products
# unattended, and neither can be exercised here: the dev database holds SIX products (the
# seeded treats), and `source_url IS NOT NULL` matches none of them. So the scripts have
# never actually been run against data shaped like the real thing — only against a
# shortlist of six URLs. Angel, 2026-08-03: *"should we take some samples a dump from prod
# to test the enricher locally first ... then if ok we move to prod or fix it first"*.
#
# WHAT IT DELIBERATELY DOES NOT CARRY. No transactions, no line items, no customers, no cost
# prices, no stock. A dev laptop is not the place for a working shop's sales history, and none
# of it is needed to answer the only question here: does the enricher read a page correctly
# and write the right row?
#
# WHAT IT MUST CARRY, AND ORIGINALLY DIDN'T. The classification columns — product_class,
# is_age_restricted, category, description. They are irrelevant to the enricher, which is
# exactly why the first version left them out, and exactly why that was wrong: a row missing
# them silently becomes `standard`, not-age-restricted. Running reclass-age-gate.py against
# that database then reported 24 products needing an 18+ gate — tobacco tins, nicotine salts,
# CBD joints — every one of which is classified correctly on UAT.
#
# A partial sample does not look incomplete. It looks WRONG, and it accuses working code.
# Hence the refusal below unless --partial is passed knowingly.
#
# EVERY ROW IS MARKED. `sku` keeps its real TAM-xxxxx value — the enricher's whole premise is
# that a row can re-find its own source page — but the rows are tagged in `attributes` with
# `_sample_load` so `--purge` can remove exactly what it added and nothing else. A sample that
# cannot be cleanly removed becomes permanent by accident.
# ============================================================================
import argparse
import csv
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

C = {"grn": "\033[32m", "yel": "\033[33m", "red": "\033[31m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}

MARK = "_sample_load"


def read_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def psql(env, sql, container):
    """Same both-sides-of-the-container-wall trick as enrich-from-source.py."""
    user = env.get("POSTGRES_USER") or os.environ.get("POSTGRES_USER") or "helix_user"
    db = env.get("POSTGRES_DB") or os.environ.get("POSTGRES_DB") or "helix_db"
    try:
        import psycopg
    except ImportError:
        psycopg = None

    if psycopg is not None:
        host = os.environ.get("POSTGRES_HOST") or env.get("POSTGRES_HOST") or "postgres"
        pwd = os.environ.get("POSTGRES_PASSWORD") or env.get("POSTGRES_PASSWORD") or ""
        port = os.environ.get("POSTGRES_PORT") or env.get("POSTGRES_PORT") or "5432"
        try:
            with psycopg.connect(host=host, port=port, user=user, password=pwd,
                                 dbname=db, connect_timeout=10, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if cur.description is None:
                        return ""
                    return "\n".join("\x1f".join("" if v is None else str(v) for v in row)
                                     for row in cur.fetchall())
        except Exception as e:
            print(f"{C['red']}postgres: {type(e).__name__}: {str(e)[:120]}{C['x']}",
                  file=sys.stderr)
            return None

    try:
        p = subprocess.run(["docker", "exec", "-i", container, "psql", "-U", user, "-d", db,
                            "-tA", "-F", "\x1f", "-v", "ON_ERROR_STOP=1"],
                           input=sql, capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"{C['red']}could not reach postgres: {e}{C['x']}", file=sys.stderr)
        return None
    if p.returncode != 0:
        print(f"{C['red']}psql failed:{C['x']}\n{p.stderr.strip()}", file=sys.stderr)
        return None
    return p.stdout


def _lit(s) -> str:
    """A SQL string literal. Doubling the apostrophe is the SQL way — and spec values really
    do contain them ("Rastaman's Weisheiten"), which is how enrich-from-source's first
    version terminated its own literals and failed every apply."""
    if s is None or s == "":
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def _jsonb(s) -> str:
    if not s or str(s).strip() in ("", "null", "{}", "[]"):
        return "NULL"
    try:                                  # must be valid JSON or Postgres rejects the row
        json.loads(s)
    except Exception:
        return "NULL"
    return _lit(s) + "::jsonb"


def main():
    ap = argparse.ArgumentParser(
        description="Load a slice of the real catalogue into the dev DB for testing.")
    ap.add_argument("--csv", default="", help="CSV exported from prod (see the guide)")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--purge", action="store_true", help="delete previously loaded sample rows")
    ap.add_argument("--partial", action="store_true",
                    help="allow a CSV with no classification columns (enricher testing only)")
    ap.add_argument("--container", default="banco-postgres")
    args = ap.parse_args()

    env = read_env(os.path.join(ROOT, ".env"))

    if args.purge:
        n = psql(env, f"SELECT count(*) FROM products WHERE attributes ? '{MARK}';",
                 args.container)
        if n is None:
            return 2
        print(f"{(n or '0').strip()} sample row(s) present.")
        if not args.apply:
            print(f"{C['dim']}Dry run — nothing deleted. Re-run with --purge --apply.{C['x']}")
            return 0
        # product_barcodes / translations cascade on product delete; sales history cannot
        # exist for these because they were never sold — they are a few minutes old.
        out = psql(env, f"DELETE FROM products WHERE attributes ? '{MARK}';", args.container)
        if out is None:
            return 2
        print(f"{C['grn']}✅ sample rows removed.{C['x']}")
        return 0

    if not args.csv:
        print(f"{C['red']}--csv is required (or use --purge).{C['x']}", file=sys.stderr)
        return 2
    if not os.path.exists(args.csv):
        print(f"{C['red']}No such file: {args.csv}{C['x']}", file=sys.stderr)
        return 2

    with open(args.csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    need = {"sku", "name", "source_url"}
    missing = need - set(rows[0].keys() if rows else [])
    if missing:
        print(f"{C['red']}CSV is missing column(s): {sorted(missing)}{C['x']}", file=sys.stderr)
        print(f"{C['dim']}got: {sorted(rows[0].keys()) if rows else '(empty file)'}{C['x']}")
        return 2

    # A PARTIAL COPY IS A LIE TO EVERY OTHER SCRIPT. Learned the hard way, 2026-08-03.
    #
    # The first version copied eight columns — enough for the enricher, which only reads
    # source_url. But `product_class` and `is_age_restricted` were not among them, so all 200
    # rows landed on the column defaults: `standard`, not age-restricted, no category, no
    # description. Then `reclass-age-gate.py` was run against that database and correctly
    # reported 24 products needing an 18+ gate — Parisienne tobacco tins, nicotine salts, CBD
    # joints. Every one of them is classified perfectly well on UAT.
    #
    # It read exactly like a compliance disaster and was entirely an artifact of MY narrow
    # SELECT. Angel: "this is wrong tigs -- i go to banco UAT and these same products are fine".
    # He was right, and the twenty minutes it cost him is the point: a sample that is missing
    # columns does not look incomplete, it looks WRONG, and it indicts innocent code.
    #
    # So: carry the classification columns when they are there, and refuse to load without
    # them unless somebody knowingly asks for a partial slice.
    CLASS_COLS = {"product_class", "is_age_restricted", "category", "description"}
    have = set(rows[0].keys())
    lacking = sorted(CLASS_COLS - have)
    if lacking and not args.partial:
        print(f"\n{C['red']}✗ Refusing to load: the CSV has no {', '.join(lacking)}.{C['x']}")
        print(f"{C['yel']}Rows would default to product_class='standard', is_age_restricted=false, "
              f"no category and no description.{C['x']}")
        print(f"{C['dim']}That is fine for the enricher, which only reads source_url — but any "
              f"other script\nreading this database will draw a false conclusion. "
              f"reclass-age-gate.py did exactly\nthat on 2026-08-03 and reported 24 phantom "
              f"age-gate failures.\n\nRe-export including them:\n{C['x']}"
              f"  SELECT id, sku, name, price, source_url, image_url, price_tiers, raw_facets,\n"
              f"         product_class, is_age_restricted, category, description\n"
              f"  FROM products WHERE is_active AND source_url IS NOT NULL\n")
        print(f"{C['dim']}Or pass --partial if you truly only want to exercise the enricher.{C['x']}")
        return 2
    if lacking:
        print(f"{C['yel']}⚠ PARTIAL SLICE — no {', '.join(lacking)}. These rows are for the "
              f"enricher ONLY.\n  Do not run reclass-age-gate.py or any classifier against this "
              f"database.{C['x']}\n")

    # Prefer rows that still have work to do — a sample made entirely of already-enriched
    # products would prove nothing about the enricher.
    def _todo(r):
        return (not (r.get("price_tiers") or "").strip()
                or (r.get("price_tiers") or "").strip() in ("[]", "null"))

    todo = [r for r in rows if r.get("source_url") and _todo(r)]
    done = [r for r in rows if r.get("source_url") and not _todo(r)]
    picked = todo[:args.limit] or done[:args.limit]

    print(f"{C['b']}Load a real-catalogue sample{C['x']}  "
          f"{C['dim']}({'APPLY' if args.apply else 'dry run'}){C['x']}")
    print(f"  csv rows              {len(rows)}")
    print(f"  with a source_url     {len(todo) + len(done)}")
    print(f"  still needing tiers   {len(todo)}")
    print(f"  loading               {len(picked)}\n")
    for r in picked[:5]:
        print(f"  {C['dim']}{r['sku']:<12} {r['name'][:44]:<44} {r['source_url'][:44]}{C['x']}")
    if len(picked) > 5:
        print(f"  {C['dim']}… and {len(picked) - 5} more{C['x']}")

    if not args.apply:
        print(f"\n{C['dim']}Dry run — nothing written. Re-run with --apply.{C['x']}")
        return 0

    stmts = ["BEGIN;"]
    for r in picked:
        price = (r.get("price") or "").strip() or "0"
        try:
            float(price)
        except ValueError:
            price = "0"
        attrs = json.dumps({MARK: True}, ensure_ascii=False)
        # Carry the real classification when the export included it. Defaulting these is what
        # made 200 correctly-gated products look like a compliance failure (see above).
        pclass = (r.get("product_class") or "").strip() or "standard"
        aged = (r.get("is_age_restricted") or "").strip().lower() in ("t", "true", "1", "yes")
        stmts.append(
            "INSERT INTO products (id, sku, name, price, source_url, image_url, price_tiers, "
            "  raw_facets, attributes, product_class, is_age_restricted, category, description, "
            "  stock_quantity, is_active, "
            "  barcode_is_internal, vending_compatible, sync_override, needs_translation, "
            "  created_at, updated_at) VALUES ("
            f"gen_random_uuid(), {_lit(r['sku'])}, {_lit(r['name'])}, {price}, "
            f"{_lit(r.get('source_url'))}, {_lit(r.get('image_url'))}, "
            f"{_jsonb(r.get('price_tiers'))}, {_jsonb(r.get('raw_facets'))}, "
            f"{_lit(attrs)}::jsonb, {_lit(pclass)}, {str(aged).lower()}, "
            f"{_lit(r.get('category'))}, {_lit(r.get('description'))}, "
            "0, true, false, false, false, false, now(), now()) "
            "ON CONFLICT (sku) DO NOTHING;")
    stmts.append("COMMIT;")

    if psql(env, "\n".join(stmts), args.container) is None:
        print(f"{C['red']}✗ failed — rolled back, nothing changed.{C['x']}", file=sys.stderr)
        return 2

    n = psql(env, f"SELECT count(*) FROM products WHERE attributes ? '{MARK}';", args.container)
    print(f"\n{C['grn']}✅ loaded. {(n or '?').strip()} sample row(s) now in the dev DB.{C['x']}")
    print(f"{C['dim']}Next:  python3 scripts/enrich-from-source.py --limit 20"
          f"\n       (dry run first — it writes nothing without --apply)"
          f"\nUndo:  python3 scripts/load-catalog-sample.py --purge --apply{C['x']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
