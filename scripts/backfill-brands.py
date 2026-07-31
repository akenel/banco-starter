#!/usr/bin/env python3
# ============================================================================
# backfill-brands — put a BRAND on every product that already tells us one.
#
#   python3 scripts/backfill-brands.py            # DRY RUN — shows, changes nothing
#   python3 scripts/backfill-brands.py --apply    # writes
#
# WHY. Angel, 2026-07-31: "we are really having to make a proper master data —
# brand names, languages, unit of measure... this is what's really missing."
#
# The catalogue records a SUPPLIER (Tamar, the wholesaler) and nothing saying
# the packet is a Gizeh. Brand is what the customer says, what is printed
# largest on the box, the strongest token for finding the right web page, and
# the thing that separates `Canna` from `Cocanna`.
#
# Nothing here is invented: the brand is read out of the product's own name
# using brand_registry (68 brands, 35 fetch-verified official sites). A name
# that names no known brand is left alone — a blank is honest, a guess is not.
#
# Writes into the existing `attributes` JSONB as attributes->>'brand', so it
# needs no migration against a live shop's database. Re-runnable: a row that
# already carries a brand is never overwritten.
# ============================================================================
import argparse
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
    user = env.get("POSTGRES_USER") or "helix_user"
    db = env.get("POSTGRES_DB") or "helix_db"
    try:
        p = subprocess.run(
            ["docker", "exec", "-i", container, "psql", "-U", user, "-d", db,
             "-tA", "-F", "\x1f", "-v", "ON_ERROR_STOP=1"],
            input=sql, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"{C['red']}could not reach postgres: {e}{C['x']}", file=sys.stderr)
        return None
    if p.returncode != 0:
        print(f"{C['red']}psql failed:{C['x']}\n{p.stderr.strip()}", file=sys.stderr)
        return None
    return p.stdout


def main():
    ap = argparse.ArgumentParser(description="Record each product's brand (read from its name).")
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    ap.add_argument("--container", default="banco-postgres")
    args = ap.parse_args()

    env = read_env(os.path.join(ROOT, ".env"))
    try:
        from src.services.brand_registry import detect_brand
    except ImportError as e:
        sys.exit(f"{C['red']}cannot import brand_registry: {e}{C['x']}")

    rows = psql(env, "SELECT id, name, coalesce(attributes->>'brand','') "
                     "FROM products WHERE is_active ORDER BY name;", args.container)
    if rows is None:
        return 2

    changes, seen, already, unknown = [], 0, 0, []
    for line in rows.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) < 3:
            continue
        pid, name, has = parts[0], parts[1], parts[2]
        seen += 1
        if has.strip():
            already += 1
            continue
        brand = detect_brand(name or "")
        if brand:
            changes.append((pid, brand, name))
        else:
            unknown.append(name)

    print(f"{C['b']}Brand backfill{C['x']}  {C['dim']}({'APPLY' if args.apply else 'dry run'}){C['x']}\n")
    print(f"  active products          {seen}")
    print(f"  already have a brand     {already}")
    print(f"  {C['grn']}brand found in the name  {len(changes)}{C['x']}")
    print(f"  {C['yel']}no known brand           {len(unknown)}{C['x']}  "
          f"{C['dim']}(left blank — a guess would be worse){C['x']}")
    if seen:
        print(f"\n  coverage after this run: {C['b']}{(already + len(changes)) * 100 // seen}%{C['x']}")

    from collections import Counter
    top = Counter(b for _, b, _ in changes).most_common(12)
    if top:
        print(f"\n  {C['dim']}most common:{C['x']} " + ", ".join(f"{b} ({n})" for b, n in top))
    if unknown:
        print(f"\n  {C['dim']}a few with no brand detected — add them to brand_registry if they are real brands:{C['x']}")
        for n in unknown[:8]:
            print(f"    {n[:66]}")

    if not changes:
        print(f"\n{C['grn']}Nothing to do.{C['x']}")
        return 0
    if not args.apply:
        print(f"\n{C['dim']}Dry run — nothing was written. Re-run with --apply.{C['x']}")
        return 0
    if not args.yes:
        if input(f"\nWrite {len(changes)} brand(s)? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Stopped. Nothing was changed.")
            return 1

    # jsonb_set with create_missing, so a row with no attributes bag still gets one.
    stmts = ["BEGIN;"]
    for pid, brand, _ in changes:
        stmts.append(
            "UPDATE products SET attributes = jsonb_set(coalesce(attributes,'{{}}'::jsonb), "
            "'{{brand}}', to_jsonb({b}::text), true), updated_at = now() WHERE id = {i};".format(
                b=json.dumps(brand).replace('"', "'"), i=json.dumps(pid).replace('"', "'")))
    stmts.append("COMMIT;")
    if psql(env, "\n".join(stmts), args.container) is None:
        print(f"{C['red']}✗ failed — the transaction rolled back, nothing changed.{C['x']}", file=sys.stderr)
        return 2
    print(f"\n{C['grn']}✅ recorded {len(changes)} brand(s).{C['x']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
