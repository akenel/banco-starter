#!/usr/bin/env python3
# ============================================================================
# ean-match apply — write reviewed picture-matches into the shop, as ALIASES.
#
#   python3 scripts/ean-match/apply.py --run papers          # DRY RUN (default)
#   python3 scripts/ean-match/apply.py --run papers --apply  # writes
#
# WHAT THIS DOES AND DOES NOT DO
#
#   Every binding goes through POST /products/{id}/barcodes with source='image-match'.
#   That endpoint refuses to promote an image-match to `products.barcode` (BL-90b), so:
#
#     · the minted 200… code stays primary  -> every printed label keeps scanning
#     · barcode_is_internal keeps telling the truth
#     · the packet still resolves, because lookup checks aliases
#     · a bad batch is one DELETE against the barcodes this script logs
#
#   It NEVER touches products.barcode, price, name, category or images. One column.
#
# THE BOX RULE. A wholesaler's GTIN is often the outer. Anything the feed says covers
# more than one unit is written kind='case' with its pack_qty — so scanning a box finds
# the product without anything claiming the box code is the packet code. Measured on the
# first papers run: 5 of 41 (12%). Two of those had titles identical to ours and were
# only distinguishable by `32 per unit` in the feed.
#
# NOTHING IS AUTOMATIC. Every row here was confirmed by a person looking at two
# photographs (LESSON #9 — a wrong barcode looks exactly like a right one).
# ============================================================================
import argparse, csv, json, os, re, sys, time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
C = {"grn":"\033[32m","yel":"\033[33m","red":"\033[31m","dim":"\033[2m","b":"\033[1m","x":"\033[0m"}
if not sys.stdout.isatty(): C = {k:"" for k in C}

def norm(g): 
    g = re.sub(r"\D", "", g or "")
    return g.lstrip("0") or g

def read_env(path):
    env = {}
    if not os.path.exists(path): return env
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.strip().startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def main():
    ap = argparse.ArgumentParser(description="Write reviewed EAN picture-matches as alias barcodes.")
    ap.add_argument("--run", required=True, help="name of the run (expects <run>_apply.json beside the data)")
    ap.add_argument("--data", default=os.environ.get("EAN_DATA", ""), help="directory holding <run>_apply.json and skumap.csv")
    ap.add_argument("--apply", action="store_true", help="actually write (default is a dry run)")
    ap.add_argument("--base", default="https://banco.wolfhold.app/api/v1/pos")
    ap.add_argument("--kc",   default="https://banco-auth.wolfhold.app/realms/kc-pos-realm-dev/protocol/openid-connect/token")
    ap.add_argument("--user", default="felix")
    ap.add_argument("--password", default=os.environ.get("BANCO_PASSWORD", ""))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    data = args.data or os.path.join(ROOT, "scripts", "ean-match", "data")
    payload = json.load(open(os.path.join(data, f"{args.run}_apply.json"), encoding="utf-8"))
    skumap = {r["sku"]: r["id"] for r in csv.DictReader(open(os.path.join(data, "skumap.csv"), encoding="utf-8"))}

    jobs = []
    for kind, rows in (("retail", payload.get("retail", [])), ("case", payload.get("case", []))):
        for sku, name, gtin, ftitle, units in rows:
            pid = skumap.get(sku)
            # pack_qty: only when we actually know it. The feed's
            # artikel_pro_verkaufseinheit is AMBIGUOUS — on papers it counts LEAVES IN A
            # BOOKLET as often as items in a box ("32" on an Elements Phantom the shop sells
            # for CHF 2.00 is 32 leaves, not 32 booklets). So a case whose size we cannot
            # establish gets NULL, which is the honest answer. What matters is kind='case',
            # so nothing downstream treats a box code as a packet code.
            if kind == "case":
                m = re.match(r"\d+$", str(units).strip() or "")
                qty = int(m.group()) if (m and int(m.group()) > 1) else None
            else:
                qty = 1
            jobs.append({"sku": sku, "name": name, "product_id": pid, "barcode": gtin,
                         "kind": kind, "pack_qty": qty, "source": "image-match",
                         "evidence": f"picture-match vs FourTwenty '{ftitle}' (units={units}), "
                                     f"confirmed by a human {datetime.now(timezone.utc).date()}"})
    if args.limit: jobs = jobs[:args.limit]

    missing = [j for j in jobs if not j["product_id"]]
    if missing:
        print(f"{C['red']}{len(missing)} rows have no product id in skumap.csv — refusing to run.{C['x']}")
        for j in missing[:5]: print(f"   {j['sku']}  {j['name'][:50]}")
        return 2

    print(f"{C['b']}ean-match apply · run '{args.run}'{C['x']}  "
          f"{C['dim']}({'APPLY' if args.apply else 'DRY RUN'}, {len(jobs)} bindings){C['x']}\n")
    for j in jobs:
        tag = (f"{C['yel']}case ×{j['pack_qty']}{C['x']}" if j["kind"] == "case" and j["pack_qty"]
           else f"{C['yel']}case (size?){C['x']}" if j["kind"] == "case" else "retail      ")
        print(f"  {tag}  {j['sku']:<12} {j['name'][:40]:<40} <- {j['barcode']}")
    n_case = sum(1 for j in jobs if j["kind"] == "case")
    print(f"\n  {len(jobs)-n_case} retail · {n_case} case")

    if not args.apply:
        print(f"\n{C['dim']}  Dry run. Nothing was written. Re-run with --apply.{C['x']}")
        print(f"{C['dim']}  Deploy first: the kind/pack_qty/source columns need ./scripts/rebuild.sh on banco.{C['x']}")
        return 0

    import httpx
    pw = args.password or read_env(os.path.join(ROOT, ".env")).get("BANCO_PASSWORD", "")
    if not pw:
        print(f"{C['red']}No password. Pass --password or set BANCO_PASSWORD.{C['x']}")
        return 2
    tok = httpx.post(args.kc, data={"client_id": "helix_pos_web", "username": args.user,
                                    "password": pw, "grant_type": "password"}, timeout=30)
    if tok.status_code != 200:
        print(f"{C['red']}login failed: {tok.status_code} {tok.text[:200]}{C['x']}"); return 2
    client = httpx.Client(headers={"Authorization": "Bearer " + tok.json()["access_token"]}, timeout=30)

    log = []
    ok = dup = conflict = fail = 0
    for j in jobs:
        r = client.post(f"{args.base}/products/{j['product_id']}/barcodes",
                        json={k: j[k] for k in ("barcode", "kind", "pack_qty", "source", "evidence")})
        status = r.status_code
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"text": r.text[:200]}
        if status in (200, 201) and body.get("status") == "linked": ok += 1;  mark = f"{C['grn']}linked{C['x']}"
        elif body.get("status") == "already_linked":               dup += 1; mark = f"{C['dim']}already{C['x']}"
        elif status == 409:                                        conflict += 1; mark = f"{C['yel']}CONFLICT{C['x']}"
        else:                                                      fail += 1; mark = f"{C['red']}{status}{C['x']}"
        log.append({**j, "status": status, "response": body})
        print(f"  {mark:<22} {j['sku']:<12} {j['barcode']}"
              + (f"  {body.get('detail','')[:60]}" if status >= 400 else ""))
        time.sleep(0.05)

    out = os.path.join(data, f"{args.run}_applied_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json")
    json.dump(log, open(out, "w"), indent=1)
    print(f"\n  {C['grn']}linked {ok}{C['x']} · already {dup} · {C['yel']}conflict {conflict}{C['x']} · {C['red']}failed {fail}{C['x']}")
    print(f"  log: {out}")
    print(f"{C['dim']}  To undo this batch: DELETE FROM product_barcodes WHERE barcode IN (…) "
          f"— every barcode written is in that log.{C['x']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
