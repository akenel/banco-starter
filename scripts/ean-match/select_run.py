"""Build the review deck for one category — the REAL run, not a measurement round.

Supersedes select2.py / select3.py, which were the blind rounds that chose the ranker.
Those stay for the record; this is the one that produces a deck a person works through.

RANKER: SequenceMatcher + token Jaccard on the titles. No CLIP. Measured on papers and it
HURTS there (top-3 54% vs 79%) — a packet of papers looks like a packet of papers, so the
picture carries almost no signal and the text carries all of it. CLIP earns its place on
visually distinctive goods. Re-measure per category before assuming either way.

PRICE: both sides of every card carry one, and the feed price divided by ours is the
box-vs-packet tell (see sheet3.BOX for the measurement). Nothing is filtered or re-ordered
on it — the number is shown to the person deciding, and that is all.
"""
import csv, os, sys, re, random, hashlib, json
from difflib import SequenceMatcher

SP = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("EAN_WORK", os.path.join(SP, "work"))
sys.path.insert(0, SP)
BANCO = "https://banco.wolfhold.app"


def n(g):
    g = re.sub(r"\D", "", g or "")
    return g.lstrip("0") or g


def toks(s):
    return set(w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 1)


def key(u):
    return hashlib.md5(u.encode()).hexdigest()


def money(v):
    """A price or None. The feed leaves it blank often enough that '' must not become 0.0 —
    a zero would render as 0.0x and read as a confident 'this is not a box'."""
    try:
        f = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


def load_feed(path):
    """FourTwenty rows: gtin, title, image url, units, brand[, price].
    The price column is what sql/export-feed.sql adds; a 5-column file still loads."""
    feed = []
    for row in csv.reader(open(path, encoding="utf-8")):
        if len(row) >= 5 and row[0] and row[2]:
            feed.append({"gtin": row[0], "title": row[1], "url": row[2],
                         "units": row[3], "brand": row[4],
                         "price": money(row[5]) if len(row) >= 6 else None})
    seen = set()
    return [p for p in feed if not (p["url"] in seen or seen.add(p["url"]))]


def load_ours(path, prices=None):
    """Our own rows: sku, name, barcode, image_url, cat, minted[, price].
    `prices` is an optional sku,price CSV for exports made before price was added."""
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    if prices and os.path.exists(prices):
        extra = {r["sku"]: r["price"] for r in csv.DictReader(open(prices, encoding="utf-8"))}
        for r in rows:
            r.setdefault("price", "")
            if not r["price"]:
                r["price"] = extra.get(r["sku"], "")
    for r in rows:
        r["price_f"] = money(r.get("price"))
    return rows


def conf(x):
    if x >= 1.40: return ("STRONG", "s")
    if x >= 1.05: return ("WORTH A LOOK", "m")
    return ("WEAK — probably nothing", "w")


def build_deck(ours, feed, controls=12, topk=6, seed=23):
    """Everything with a minted code is work; a sample of hand-bound rows rides along as
    CONTROLS, shuffled in and indistinguishable, so the run measures itself.

    ⚠ Controls measure RECALL — they are all findable. They do NOT measure gullibility.
    For that a run needs DECOYS too: rows whose EAN is in no feed at all, where the only
    correct answer is 'no match'. Papers run 1 had none. Pass decoys=… when that lands."""
    titles = [p["title"] for p in feed]
    ftok = [toks(t) for t in titles]
    gset = {}
    for i, p in enumerate(feed):
        gset.setdefault(n(p["gtin"]), i)

    work = [r for r in ours if r["minted"] == "true"]
    withtwin = [r for r in ours if r["minted"] == "false" and r.get("barcode")
                and n(r["barcode"]) in gset]
    random.seed(seed)
    ctrl = random.sample(withtwin, min(controls, len(withtwin)))
    deck = work + ctrl
    random.shuffle(deck)

    cards, truth, rank = [], [], []
    for i, r in enumerate(deck):
        tk = toks(r["name"])
        sc = [SequenceMatcher(None, r["name"].lower(), t.lower()).ratio()
              + len(tk & f) / max(1, len(tk | f)) for t, f in zip(titles, ftok)]
        order = sorted(range(len(feed)), key=lambda j: -sc[j])
        if r["minted"] == "false" and n(r.get("barcode", "")) in gset:
            rank.append(order.index(gset[n(r["barcode"])]) + 1)
        cands = []
        for j in order[:topk]:
            p = feed[j]
            c, cl = conf(sc[j])
            tp = os.path.join(WORK, "thumbs", key(p["url"]) + ".jpg")
            cands.append({"title": p["title"], "brand": p["brand"], "units": p["units"],
                          "gtin": p["gtin"], "price": p["price"], "conf": c, "cls": cl,
                          "score": round(sc[j], 3),
                          "img": open(tp, "rb").read().hex() if os.path.exists(tp) else ""})
        tt = os.path.join(WORK, "thumbs", key(BANCO + r["image_url"]) + ".jpg")
        cards.append({"i": i, "sku": r["sku"], "name": r["name"], "cat": r.get("cat", ""),
                      "price": r["price_f"],
                      "img": open(tt, "rb").read().hex() if os.path.exists(tt) else "",
                      "cands": [{k: v for k, v in c.items() if k != "gtin"} for c in cands]})
        isc = r["minted"] == "false"
        truth.append({"i": i, "sku": r["sku"], "name": r["name"], "cat": r.get("cat", ""),
                      "scored": isc, "control": isc,
                      "true_ean": r.get("barcode", "") if isc else "",
                      "has_twin": bool(isc and n(r.get("barcode", "")) in gset),
                      "cand_gtins": [c["gtin"] for c in cands],
                      "cand_titles": [c["title"] for c in cands],
                      "cand_prices": [c["price"] for c in cands],
                      "cand_scores": [c["score"] for c in cands],
                      "cand_mutual": [False] * len(cands)})
    return cards, truth, rank, len(work), len(ctrl)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build one category's review deck.")
    ap.add_argument("--run", required=True, help="run name, e.g. papers")
    ap.add_argument("--ours", required=True, help="CSV of our products for this category")
    ap.add_argument("--feed", default=os.path.join(WORK, "poolfull.csv"))
    ap.add_argument("--prices", default="", help="optional sku,price CSV")
    ap.add_argument("--controls", type=int, default=12)
    ap.add_argument("--topk", type=int, default=6)
    a = ap.parse_args()

    feed = load_feed(a.feed)
    ours = load_ours(a.ours, a.prices or None)
    cards, truth, rank, nwork, nctrl = build_deck(ours, feed, a.controls, a.topk)
    json.dump(cards, open(os.path.join(WORK, f"cards_{a.run}.json"), "w"))
    json.dump(truth, open(os.path.join(WORK, f"truth_{a.run}.json"), "w"), indent=1)

    noprice = sum(1 for c in cards if c["price"] is None)
    nofeed = sum(1 for c in cards for k in c["cands"] if k["price"] is None)
    tot = sum(len(c["cands"]) for c in cards)
    rank.sort()
    print(f"cards {len(cards)} ({nwork} need an EAN + {nctrl} controls) · pool {len(feed)}")
    print(f"control ranks: {rank}  -> in the {a.topk} shown: "
          f"{sum(1 for x in rank if x <= a.topk)}/{len(rank)}")
    print(f"price on file: ours {len(cards)-noprice}/{len(cards)} · feed {tot-nofeed}/{tot}")
    if noprice or nofeed:
        print("  ⚠ cards without a price show no ratio at all — never a 0x")


if __name__ == "__main__":
    sys.exit(main() or 0)
