#!/usr/bin/env python3
"""Turn a run's downloaded decisions into the payload apply.py writes.

    python3 build_apply.py --run filters --decisions ~/Downloads/ean-match-filters-252.json

Papers run 1 was assembled BY HAND, which is why this exists (WORKLIST ⓪b). Three rules,
each measured rather than assumed:

RETAIL vs CASE — from the price ratio, never from the feed's artikel_pro_verkaufseinheit,
  which counts leaves in a booklet as often as items in a box. On papers the four confirmed
  cases came out at 4.5-26.7x and every retail row sat at 0.5-2.5x, so BOX=3.0 sits in an
  empty band. RE-CHECK THE BAND PER CATEGORY: this prints the distribution and refuses to
  guess if anything lands near the line.

ONE GTIN, ONE PRODUCT — a barcode that resolves to two products is not a barcode. Wholesalers
  sell "Assortiert" packs that our catalogue splits by design, so this collision is common and
  quiet. Those rows are held back, never bound arbitrarily to the first of the group.

CONTROLS AND DECOYS ARE NOT WORK — a row that already carries a real EAN is scored, not
  applied. Its second GTIN may well be a legitimate alias, but that is a separate decision.
"""
import argparse, collections, csv, json, os, sys

SP = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("EAN_WORK", os.path.join(SP, "work"))
DATA = os.environ.get("EAN_DATA", os.path.join(SP, "data"))
BOX = 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--decisions", required=True)
    a = ap.parse_args()

    T = {t["i"]: t for t in json.load(open(os.path.join(WORK, f"truth_{a.run}.json")))}
    C = {c["i"]: c for c in json.load(open(os.path.join(WORK, f"cards_{a.run}.json")))}
    D = json.load(open(os.path.expanduser(a.decisions)))["decisions"]

    acc, bonus = [], []
    for k, v in D.items():
        i = int(k)
        if not isinstance(v, int):
            continue
        t, c = T[i], C[i]
        row = {"sku": t["sku"], "name": c["name"], "gtin": t["cand_gtins"][v],
               "ftitle": t["cand_titles"][v], "units": c["cands"][v]["units"],
               "ours": c["price"], "theirs": t["cand_prices"][v]}
        (bonus if t["scored"] else acc).append(row)   # scored = control/decoy, already bound

    # --- rule 2: a GTIN that would land on more than one product is held back
    by_g = collections.defaultdict(list)
    for r in acc:
        by_g[r["gtin"]].append(r)
    clash = {g: v for g, v in by_g.items() if len(v) > 1}
    held = [r for g in clash for r in clash[g]]
    jobs = [r for r in acc if r["gtin"] not in clash]

    # --- rule 1: retail vs case from the price ratio, with the band shown
    for r in jobs:
        r["ratio"] = (r["theirs"] / r["ours"]) if (r["ours"] and r["theirs"]) else None
        r["kind"] = "case" if (r["ratio"] is not None and r["ratio"] >= BOX) else "retail"
    rr = sorted(x["ratio"] for x in jobs if x["ratio"] is not None)
    near = [x for x in rr if 2.0 <= x <= 4.5]
    print(f"price ratio: {len(rr)} rows, {rr[0]:.1f}x .. {rr[-1]:.1f}x   (BOX = {BOX}x)")
    if near:
        print(f"  ⚠ {len(near)} rows sit in 2.0-4.5x — the band is NOT empty for this category.")
        print(f"    Papers had a clean gap. Check these by hand before applying: {near}")
    else:
        print(f"  band 2.0-4.5x is empty -> the split is unambiguous here")
    print(f"  case {sum(1 for x in jobs if x['kind']=='case')} · "
          f"retail {sum(1 for x in jobs if x['kind']=='retail')}\n")

    if clash:
        print(f"HELD BACK — {len(held)} rows on {len(clash)} GTINs that would bind to >1 product:")
        for g, v in clash.items():
            print(f"  {g}  \"{v[0]['ftitle'][:46]}\"")
            for r in v:
                print(f"      {r['sku']:<12} {r['name'][:52]}")
        print()
    if bonus:
        print(f"NOT APPLIED — {len(bonus)} rows that already carry a real EAN (controls/decoys).")
        print("  A second GTIN on these may be a legitimate alias; that is its own decision:")
        for r in bonus:
            print(f"      {r['sku']:<12} {r['name'][:40]:<40} -> {r['gtin']}  {r['ftitle'][:34]}")
        print()

    out = {"retail": [], "case": []}
    for r in jobs:
        out[r["kind"]].append([r["sku"], r["name"], r["gtin"], r["ftitle"], r["units"]])
    os.makedirs(DATA, exist_ok=True)
    p = os.path.join(DATA, f"{a.run}_apply.json")
    json.dump(out, open(p, "w"), indent=1, ensure_ascii=False)
    print(f"wrote {p}: {len(out['retail'])} retail · {len(out['case'])} case")
    return 0


if __name__ == "__main__":
    sys.exit(main())
