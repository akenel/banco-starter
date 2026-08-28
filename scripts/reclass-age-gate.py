#!/usr/bin/env python3
# ============================================================================
# reclass-age-gate — re-run the age classifier over the EXISTING catalog.
#
#   python3 scripts/reclass-age-gate.py            # DRY RUN — shows, changes nothing
#   python3 scripts/reclass-age-gate.py --apply    # actually writes
#   python3 scripts/reclass-age-gate.py --apply --yes    # no prompt (CI/scripted)
#
# WHY THIS EXISTS. Fixing the classifier does not fix rows already in the table.
# Found live at Artemis 2026-07-29: four BLOW pre-rolled CBD joints sat in the
# catalog classed `standard` and sellable with NO 18+ check, because the titles
# either never said "CBD" or transposed it to "CDB" — a typo made while copying
# off a package at the counter. Whether a customer was asked for ID depended on
# someone's spelling.
#
# THE ONE RULE: THIS ONLY EVER TIGHTENS.
# A row is updated only when the classifier now says it is age-restricted AND
# the stored row says it is not. It will never un-gate a product, never relax a
# class a manager set deliberately, and never touch a row that is already
# correct. The worst case of a bad run is a product that asks for ID when it
# need not — annoying, and fixable in the cleanup cockpit; the opposite is a
# compliance failure.
#
# Reads the DESCRIPTION as well as the title, because a strain or brand name
# ("Gorilla Glue #4") says nothing about what a thing legally is.
#
# Safe to run repeatedly. Run it after every capture session.
# ============================================================================
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def read_env(path):
    """Parse .env into a dict. Never executes it (values may hold shell specials)."""
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
    """Run SQL in the postgres container. Returns stdout, or None on failure."""
    user = env.get("POSTGRES_USER") or "helix_user"
    db = env.get("POSTGRES_DB") or "helix_db"
    try:
        p = subprocess.run(
            ["docker", "exec", "-i", container, "psql", "-U", user, "-d", db,
             "-tA", "-F", "\x1f", "-v", "ON_ERROR_STOP=1"],
            input=sql, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"{C['red']}could not reach postgres: {e}{C['x']}", file=sys.stderr)
        return None
    if p.returncode != 0:
        print(f"{C['red']}psql failed:{C['x']}\n{p.stderr.strip()}", file=sys.stderr)
        return None
    return p.stdout


def main():
    ap = argparse.ArgumentParser(
        description="Re-run the age classifier over existing products (tighten-only).")
    ap.add_argument("--apply", action="store_true",
                    help="write the changes (default is a dry run)")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    ap.add_argument("--container", default="banco-postgres", help="postgres container name")
    ap.add_argument("--limit", type=int, default=0, help="only consider the first N rows")
    args = ap.parse_args()

    env = read_env(os.path.join(ROOT, ".env"))

    try:
        from src.services.catalog_taxonomy import classify
    except ImportError as e:
        sys.exit(f"{C['red']}cannot import the classifier: {e}{C['x']}\n"
                 f"Run this from the repo root, on a machine with the app's deps.")

    print(f"{C['b']}Re-running the age classifier over the catalog{C['x']}")
    print(f"{C['dim']}container={args.container}  db={env.get('POSTGRES_DB')}  "
          f"mode={'APPLY' if args.apply else 'dry run'}{C['x']}\n")

    # Pull the fields the classifier reads. \x1f as the separator: product names contain
    # commas, pipes and quotes, and a mis-split row here would mis-gate a product.
    rows = psql(env,
                "SELECT id, name, coalesce(description,''), coalesce(product_class,''), "
                "       is_age_restricted "
                "FROM products WHERE is_active ORDER BY created_at;", args.container)
    if rows is None:
        return 2

    changes, seen = [], 0
    for line in rows.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) < 5:
            continue
        pid, name, desc, cls_now, age_now = parts[0], parts[1], parts[2], parts[3], parts[4]
        seen += 1
        if args.limit and seen > args.limit:
            break

        _, cls_new, age_new = classify(name, description=desc or None)

        # TIGHTEN ONLY. Anything else is left exactly as it is.
        if age_new and age_now.strip() != "t":
            changes.append((pid, name, cls_now or "standard", cls_new))

    print(f"scanned {seen} active products\n")
    if not changes:
        print(f"{C['grn']}✅ nothing to tighten — every product is gated as the classifier "
              f"expects.{C['x']}")
        return 0

    print(f"{C['yel']}{len(changes)} product(s) are NOT age-gated but should be:{C['x']}\n")
    print(f"  {'PRODUCT':<46} {'now':<16} -> {'becomes'}")
    for _, name, cls_now, cls_new in changes:
        print(f"  {name[:46]:<46} {cls_now:<16} -> {cls_new}  {C['red']}18+{C['x']}")

    if not args.apply:
        print(f"\n{C['dim']}Dry run — nothing was changed. Re-run with --apply to write.{C['x']}")
        print(f"{C['dim']}Only ever tightens: no product is un-gated or re-classed downward.{C['x']}")
        return 0

    if not args.yes:
        print()
        ans = input(f"Apply these {len(changes)} change(s)? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("Stopped. Nothing was changed.")
            return 1

    # One statement per row, id-matched. A products table is small and this is rare —
    # clarity in the audit trail beats a clever bulk UPDATE nobody can read later.
    stmts = ["BEGIN;"]
    for pid, _, _, cls_new in changes:
        stmts.append(
            "UPDATE products SET product_class = {c}, is_age_restricted = true, "
            # age_reason records WHY the gate was raised, and it is not decoration: the
            # compliance rulepack (scripts/db/compliance_rulepack_seed.sql) reports any gated
            # row where it IS NULL as a finding. A run that tightened 40 products and left the
            # column empty would trade one compliance flag for another. COALESCE so a reason a
            # human set deliberately is never overwritten — same spirit as tighten-only.
            "age_reason = coalesce(age_reason, {r}), "
            "updated_at = now() WHERE id = {i};".format(
                c=json.dumps(cls_new).replace('"', "'"),
                r=json.dumps("class:" + cls_new).replace('"', "'"),
                i=json.dumps(pid).replace('"', "'")))
    stmts.append("COMMIT;")
    out = psql(env, "\n".join(stmts), args.container)
    if out is None:
        print(f"{C['red']}✗ the update failed — the transaction rolled back, "
              f"nothing changed.{C['x']}", file=sys.stderr)
        return 2

    print(f"\n{C['grn']}✅ tightened {len(changes)} product(s).{C['x']}")
    print(f"{C['dim']}Re-run without --apply to confirm it now reports nothing to do.{C['x']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
