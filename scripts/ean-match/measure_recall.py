"""How findable is one category BEFORE a human is asked to work through it?

Every row already bound off a packet whose EAN is also in the feed is a question with a known
answer. Rank it against the whole pool and see where the right row lands. If the truth is not
in the top-K the sheet shows, no amount of human care can find it — that is the ceiling, and it
costs nothing to measure.

    python3 measure_recall.py work/ours_filters.csv work/ours_papers.csv
"""
import csv, os, re, sys
from difflib import SequenceMatcher

SP = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("EAN_WORK", os.path.join(SP, "work"))
sys.path.insert(0, SP)
from select_run import n, toks, load_feed, load_ours   # same ranker the deck uses


def measure(path, feed, titles, ftok, gset, topk=6):
    ours = load_ours(path)
    minted = [r for r in ours if r["minted"] == "true"]
    bound = [r for r in ours if r["minted"] == "false" and r.get("barcode")]
    ctrl = [r for r in bound if n(r["barcode"]) in gset]

    ranks = []
    for r in ctrl:
        tk = toks(r["name"])
        sc = [SequenceMatcher(None, r["name"].lower(), t.lower()).ratio()
              + len(tk & f) / max(1, len(tk | f)) for t, f in zip(titles, ftok)]
        j = gset[n(r["barcode"])]
        ranks.append(sum(1 for x in sc if x > sc[j]) + 1)
    ranks.sort()
    return minted, bound, ctrl, ranks


def main(paths, topk=6):
    feed = load_feed(os.path.join(WORK, "poolfull.csv"))
    titles = [p["title"] for p in feed]
    ftok = [toks(t) for t in titles]
    gset = {}
    for i, p in enumerate(feed):
        gset.setdefault(n(p["gtin"]), i)
    print(f"pool {len(feed)} feed rows\n")

    for path in paths:
        minted, bound, ctrl, ranks = measure(path, feed, titles, ftok, gset, topk)
        name = os.path.basename(path).replace("ours_", "").replace(".csv", "")
        nc = len(ctrl)
        top1 = sum(1 for x in ranks if x == 1)
        topK = sum(1 for x in ranks if x <= topk)
        print(f"=== {name} ===")
        print(f"  deck (minted, needs an EAN) : {len(minted)}")
        print(f"  bound off a packet          : {len(bound)}")
        print(f"  ...of those, EAN is in feed : {nc}  ({nc/max(1,len(bound))*100:.0f}% — the CEILING)")
        if not nc:
            print("  no controls — nothing to measure\n")
            continue
        print(f"  ranked #1                   : {top1}/{nc}  ({top1/nc*100:.0f}%)")
        print(f"  ranked in the {topk} shown       : {topK}/{nc}  ({topK/nc*100:.0f}%)")
        print(f"  -> a human working this deck can find at best "
              f"{topK/max(1,len(bound))*100:.0f}% of what is there")
        print(f"  ranks: {ranks}\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or [os.path.join(WORK, "ours_filters.csv")]) or 0)
