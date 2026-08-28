#!/usr/bin/env python3
"""Prove the box-vs-packet PRICE tell, against the field it replaces.

    python3 scripts/prove-ean-box-price.py

Angel's idea, 2026-08-28: *a box costs 20x what a packet costs*, and nothing else on the card
reveals it. The picture cannot — a box of papers is photographed as a packet of papers — and
the title only sometimes says "Box".

The field that was supposed to do this job is the feed's `artikel_pro_verkaufseinheit`, and on
papers it is worse than nothing: it counts LEAVES IN A BOOKLET as often as items in a box, so a
CHF 2.00 packet reads "32 per unit". LESSON #2 says a SECOND way of asking a question must be
tested against the FIRST, on the input where a wrong predicate has to differ. That input is the
41 bindings a human confirmed on papers run 1, where the retail/case call was made by a person
looking at two photographs.

This runs entirely offline against that run. It touches no database and no shop.
"""
import csv, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "ean-match"))
WORK = os.environ.get("EAN_WORK", os.path.join(ROOT, "scripts", "ean-match", "work"))
import sheet3  # the shipped renderer — ratio() and BOX are what the card actually uses

C = {"grn": "\033[32m", "red": "\033[31m", "yel": "\033[33m", "dim": "\033[2m",
     "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty(): C = {k: "" for k in C}
FAILED = []


def check(ok, label, detail=""):
    print(f"  {C['grn']}PASS{C['x']}" if ok else f"  {C['red']}FAIL{C['x']}", label,
          f"{C['dim']}{detail}{C['x']}" if detail else "")
    if not ok: FAILED.append(label)


def norm(g):
    g = re.sub(r"\D", "", g or "")
    return g.lstrip("0") or g


def looks_like_case(units):
    """The OLD tell, exactly as apply.py reads it: a bare integer > 1 means a box."""
    m = re.match(r"\d+$", str(units).strip() or "")
    return bool(m and int(m.group()) > 1)


def main():
    need = [os.path.join(WORK, f) for f in ("poolfull.csv", "papers_prices.csv")]
    need.append(os.path.join(ROOT, "scripts", "ean-match", "data", "papers_apply.json"))
    if not os.path.exists(need[-1]):
        need[-1] = os.path.join(WORK, "papers_apply.json")
    for f in need:
        if not os.path.exists(f):
            print(f"{C['red']}missing {f}{C['x']}\n"
                  f"{C['dim']}  Regenerate with sql/export-feed.sql + select_run.py, "
                  f"or set EAN_WORK.{C['x']}")
            return 2

    feed = {}
    for row in csv.reader(open(need[0], encoding="utf-8")):
        if len(row) >= 6 and row[0]:
            feed.setdefault(norm(row[0]), {"units": row[3], "price": row[5]})
    ours = {r["sku"]: r["price"] for r in csv.DictReader(open(need[1], encoding="utf-8"))}
    run = json.load(open(need[2], encoding="utf-8"))

    print(f"{C['b']}the price tell vs the units field · papers run 1, "
          f"{sum(len(v) for v in run.values())} human-confirmed bindings{C['x']}\n")

    rows = []
    for kind in ("retail", "case"):
        for sku, name, gtin, ftitle, units in run[kind]:
            f = feed.get(norm(gtin), {})
            rows.append({"kind": kind, "sku": sku, "title": ftitle, "units": units,
                         "ratio": sheet3.ratio(ours.get(sku), f.get("price"))})

    priced = [r for r in rows if r["ratio"] is not None]
    check(len(priced) == len(rows), "every confirmed binding has a price on both sides",
          f"{len(priced)}/{len(rows)}")

    cases = [r for r in priced if r["kind"] == "case"]
    retail = [r for r in priced if r["kind"] == "retail"]

    # --- the new tell -------------------------------------------------------
    caught = [r for r in cases if r["ratio"] >= sheet3.BOX]
    false = [r for r in retail if r["ratio"] >= sheet3.BOX]
    check(len(caught) == len(cases), f"price flags every box a human called a box",
          f"{len(caught)}/{len(cases)} · " + "  ".join(f"{r['ratio']:.1f}x" for r in sorted(cases, key=lambda r: r["ratio"])))
    check(not false, "price raises no false alarm on a packet",
          f"{len(false)} of {len(retail)} retail rows · highest retail ratio "
          f"{max(r['ratio'] for r in retail):.1f}x")

    # --- the OLD tell, on the same rows, so the comparison is not a claim ----
    u_caught = [r for r in cases if looks_like_case(r["units"])]
    u_false = [r for r in retail if looks_like_case(r["units"])]
    print(f"\n  {C['yel']}the field it replaces, on the same 41 rows:{C['x']} "
          f"units caught {len(u_caught)}/{len(cases)} boxes and raised {len(u_false)} "
          f"false alarms {C['dim']}(" + ", ".join(f"{r['sku']} says {r['units']!r}" for r in u_false) + f"){C['x']}")
    check(len(caught) > len(u_caught) and len(false) < len(u_false),
          "the new tell beats the old one on BOTH counts", "not just on the one it was built for")

    # --- the band, and the guard broken on purpose --------------------------
    hi_retail = max(r["ratio"] for r in retail)
    lo_case = min(r["ratio"] for r in cases)
    check(hi_retail < sheet3.BOX < lo_case,
          f"BOX={sheet3.BOX} sits in an empty band",
          f"retail tops out at {hi_retail:.1f}x, cases start at {lo_case:.1f}x")
    # move the threshold into the observed data and it MUST start lying
    into_band = lo_case + 0.1
    still = [r for r in cases if r["ratio"] >= into_band]
    check(len(still) < len(cases),
          f"raising BOX to {into_band:.1f} loses a real box",
          "the threshold is load-bearing, not decoration")

    # --- an absent price must never read as a confident 0.0x ----------------
    check(sheet3.ratio(2.0, None) is None, "no feed price -> no ratio at all")
    check(sheet3.ratio(None, 40.0) is None, "no price of ours -> no ratio at all")
    check(sheet3.ratio(0, 40.0) is None, "a zero price -> no ratio (never a divide)")
    check(sheet3.ratio("", "") is None, "empty strings -> no ratio")
    check(sheet3.ratio(2.0, 40.0) == 20.0, "and a real pair still reads 20.0x")

    print()
    if FAILED:
        print(f"{C['red']}{len(FAILED)} FAILED{C['x']}")
        return 1
    print(f"{C['grn']}all green{C['x']} {C['dim']}· measured on papers only. "
          f"Re-run this per category before trusting BOX there.{C['x']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
