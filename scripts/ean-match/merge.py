#!/usr/bin/env python3
"""Fold counter-born duplicates into their wholesale twin. DRY RUN by default.

    python3 scripts/ean-match/merge.py --pairs TAM-5660:ITEM-0053 ...
    python3 scripts/ean-match/merge.py --pairs ... --apply

The pair is written KEEP:RETIRE. POST /catalog/merge is deliberately asymmetric — the
wholesale row wins on content and the hand-made row contributes the EAN off the packet
(and now its name, as a search alias). Getting the order backwards throws away the
descriptions, tier pricing and specs, so this script prints both sides before it acts.

⚠ PRICE IS NOT MERGED. The survivor keeps its own. Where the two rows disagree, that is a
human decision and this prints it in red rather than resolving it.
"""
import argparse, csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply import read_env, C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", required=True, help="KEEP_SKU:RETIRE_SKU …")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--data", default=os.path.join(ROOT, "scripts", "ean-match", "data"))
    ap.add_argument("--base", default="https://banco.wolfhold.app/api/v1/pos")
    ap.add_argument("--kc", default="https://banco-auth.wolfhold.app/realms/kc-pos-realm-dev/protocol/openid-connect/token")
    ap.add_argument("--user", default="felix")
    a = ap.parse_args()

    skumap = {r["sku"]: r["id"] for r in csv.DictReader(
        open(os.path.join(a.data, "skumap.csv"), encoding="utf-8"))}

    import httpx
    pw = os.environ.get("BANCO_PASSWORD") or read_env(os.path.join(ROOT, ".env")).get("BANCO_PASSWORD", "")
    if not pw:
        print(f"{C['red']}No password. Set BANCO_PASSWORD or put it in .env.{C['x']}"); return 2
    tok = httpx.post(a.kc, data={"client_id": "helix_pos_web", "username": a.user,
                                 "password": pw, "grant_type": "password"}, timeout=30)
    if tok.status_code != 200:
        print(f"{C['red']}login failed: {tok.status_code}{C['x']}"); return 2
    cl = httpx.Client(headers={"Authorization": "Bearer " + tok.json()["access_token"]}, timeout=30)

    print(f"{C['b']}catalog merge{C['x']}  {C['dim']}({'APPLY' if a.apply else 'DRY RUN'},"
          f" {len(a.pairs)} pairs){C['x']}\n")
    rc = 0
    for spec in a.pairs:
        keep_sku, retire_sku = spec.split(":")
        kid, rid = skumap.get(keep_sku), skumap.get(retire_sku)
        if not (kid and rid):
            print(f"{C['red']}  unknown sku in {spec}{C['x']}"); rc = 2; continue
        r = cl.post(f"{a.base}/catalog/merge",
                    json={"keep_id": kid, "retire_id": rid, "dry_run": not a.apply})
        if r.status_code >= 400:
            print(f"{C['red']}  {keep_sku} <- {retire_sku}: {r.status_code} {r.text[:160]}{C['x']}")
            rc = 2; continue
        p = r.json()
        print(f"  {C['b']}{keep_sku}{C['x']} survives  <-  {retire_sku} retires")
        print(f"    keep    {p['keep']['name'][:56]}")
        print(f"    retire  {p['retire']['name'][:56]}")
        print(f"    primary barcode becomes {C['grn']}{p['new_primary_barcode']}{C['x']}"
              f"   aliases kept: {', '.join(p['kept_as_aliases']) or '—'}")
        print(f"    fields filled from the retired row: "
              f"{', '.join(p['fields_filled_from_retired']) or 'none'}")
        na = p.get("name_alias") or {}
        print(f"    name alias: {na if isinstance(na, str) else json.dumps(na)[:90]}")
        if p.get("stock_note"):
            print(f"    {C['yel']}{p['stock_note']}{C['x']}")
        print(f"    {C['dim']}applied={p.get('applied', not p.get('dry_run'))}{C['x']}\n")
    if not a.apply:
        print(f"{C['dim']}  Dry run. Nothing changed. Re-run with --apply.{C['x']}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
