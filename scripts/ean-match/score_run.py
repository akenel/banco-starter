#!/usr/bin/env python3
"""Score one run against its truth file.

    python3 score_run.py --run filters --decisions ~/Downloads/ean-match-decisions-v3.json

Two populations, and they answer different questions. Never merge them into one accuracy figure:
  CONTROLS (has_twin)  — the right answer exists. Measures RECALL.
  DECOYS   (scored, no twin) — no right answer exists. Measures GULLIBILITY.
"""
import json, os, re, sys, argparse, statistics

SP = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("EAN_WORK", os.path.join(SP, "work"))


def n(g):
    g = re.sub(r"\D", "", g or "")
    return g.lstrip("0") or g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--decisions", required=True)
    a = ap.parse_args()

    # The feed lists 31 titles under more than one GTIN, and separately a product whose
    # packaging changed carries a different EAN from the one on the shelf in Luzern. Both make
    # "picked GTIN == bound GTIN" too strict a test: it accuses a human who identified the right
    # PRODUCT of picking the wrong one. Score the product, and say so when the numbers differ.
    feed = {}
    fp = os.path.join(WORK, "poolfull.csv")
    if os.path.exists(fp):
        import csv as _csv
        for r in _csv.reader(open(fp, encoding="utf-8")):
            if len(r) >= 5 and r[0]:
                feed[n(r[0])] = r[1].strip().lower()

    d = json.load(open(os.path.expanduser(a.decisions)))
    D, TS = d["decisions"], d.get("stamps", {})
    T = {t["i"]: t for t in json.load(open(os.path.join(WORK, f"truth_{a.run}.json")))}

    ctrl = {"right": [], "wrong": [], "missed": [], "unseen": [], "unsure": [],
            "dupgtin": []}
    dec = {"rejected": [], "fooled": [], "unsure": [], "alias": []}
    work = {"match": 0, "none": 0, "skip": 0}

    for k, v in D.items():
        t = T[int(k)]
        if not t["scored"]:
            work["match" if isinstance(v, int) else v] += 1
            continue
        g = [n(x) for x in t["cand_gtins"]]
        true = n(t["true_ean"])
        row = (int(k) + 1, t["name"], t["cand_titles"][v] if isinstance(v, int) else "")
        if t["has_twin"]:
            if isinstance(v, int):
                # same GTIN, or a different GTIN on the very same feed title = same product
                same = g[v] == true or (feed.get(g[v]) and feed.get(g[v]) == feed.get(true))
                if same and g[v] != true:
                    ctrl["dupgtin"].append(row)
                (ctrl["right"] if same else ctrl["wrong"]).append(row)
            elif v == "skip":
                ctrl["unsure"].append(row)
            else:
                (ctrl["missed"] if true in g else ctrl["unseen"]).append(row)
        else:
            if isinstance(v, int):
                # A decoy is meant to be a product the feed does NOT carry. But it was built as
                # "our EAN is in no feed row", which is not the same claim — the same product can
                # legitimately hold two EANs (packaging changes). If the picked title is
                # essentially our own name, this is an ALIAS FIND, not gullibility. It still
                # needs a human eye; it is never silently scored correct.
                import difflib
                sim = difflib.SequenceMatcher(None, t["name"].lower(),
                                              t["cand_titles"][v].lower()).ratio()
                (dec["alias"] if sim >= 0.75 else dec["fooled"]).append(row + (round(sim, 2),))
            elif v == "skip":
                dec["unsure"].append(row)
            else:
                dec["rejected"].append(row)

    def show(title, rows):
        if rows:
            print(f"  {title}")
            for r in rows:
                i, name, got = r[0], r[1], r[2]
                tail = f"  (title match {r[3]})" if len(r) > 3 else ""
                print(f"    {i:>4}. {name[:44]:<44}" + (f" -> {got[:38]}" if got else "") + tail)

    nc = sum(len(v) for k, v in ctrl.items() if k != "dupgtin")
    nd = sum(len(v) for v in dec.values())
    print(f"=== {a.run} — {len(D)} decided ===\n")
    print(f"CONTROLS ({nc}) — the answer was findable. Did he find it?")
    print(f"  correct                {len(ctrl['right']):>3}/{nc}")
    print(f"  picked the wrong one   {len(ctrl['wrong']):>3}")
    print(f"  said no, but it was on screen {len(ctrl['missed']):>3}")
    print(f"  ranker never showed it {len(ctrl['unseen']):>3}   <- not his fault")
    print(f"  can't tell             {len(ctrl['unsure']):>3}")
    show("WRONG PICK:", ctrl["wrong"]); show("MISSED (it was there):", ctrl["missed"])
    show("counted correct — same product, second GTIN in the feed:", ctrl["dupgtin"])
    reach = len(ctrl["right"]) + len(ctrl["wrong"]) + len(ctrl["missed"]) + len(ctrl["unsure"])
    if reach:
        print(f"  -> of the {reach} he could actually have got, "
              f"{len(ctrl['right'])/reach*100:.0f}% correct")

    print(f"\nDECOYS ({nd}) — no answer existed. Did he decline?")
    print(f"  correctly rejected     {len(dec['rejected']):>3}/{nd}")
    print(f"  FALSE POSITIVE         {len(dec['fooled']):>3}")
    print(f"  same product, other EAN{len(dec['alias']):>3}   <- decoy was mis-built, not his fault")
    print(f"  can't tell             {len(dec['unsure']):>3}")
    show("FALSE POSITIVE — a different product:", dec["fooled"])
    show("NOT a false positive — same product under another EAN, CHECK THESE:", dec["alias"])

    print(f"\nWORK ({sum(work.values())} rows that needed an EAN)")
    print(f"  bound {work['match']} · no match {work['none']} · can't tell {work['skip']}")

    t = sorted(int(x) for x in TS.values())
    gaps = [(t[i] - t[i - 1]) / 1000 for i in range(1, len(t))]
    gaps = [g for g in gaps if 0 < g < 180]
    if gaps:
        gaps.sort()
        print(f"\nPACE  median {statistics.median(gaps):.0f}s · "
              f"fastest quartile {gaps[len(gaps)//4]:.0f}s · "
              f"under 3s: {sum(1 for g in gaps if g < 3)}/{len(gaps)}")
        print(f"      elapsed {(t[-1]-t[0])/60000:.0f} min for {len(D)} cards")


if __name__ == "__main__":
    sys.exit(main() or 0)
