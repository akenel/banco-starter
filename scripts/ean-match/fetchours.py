"""Fetch OUR product photographs for one category's deck into work/thumbs/.

Resumable and gentle — this pulls from Felix's live app container, so it sleeps between
requests and never re-fetches a thumbnail that is already on disk. Supersedes fetchtam.py,
which was hardcoded to one CSV and wrote to a directory that moved (LESSON: the working set
lived in /tmp until it nearly got cleaned away).

    python3 fetchours.py work/ours_filters.csv
"""
import csv, os, sys, io, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hash import fetch
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("EAN_WORK", os.path.join(SP, "work"))
THUMBS = os.path.join(WORK, "thumbs")
BANCO = "https://banco.wolfhold.app"


def key(u):
    return hashlib.md5(u.encode()).hexdigest()


def thumb(b, px=520):
    im = Image.open(io.BytesIO(b)).convert("RGB")
    im.thumbnail((px, px), Image.LANCZOS)
    o = io.BytesIO()
    im.save(o, "JPEG", quality=80)
    return o.getvalue()


def main(path):
    os.makedirs(THUMBS, exist_ok=True)
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    todo = [r for r in rows
            if not os.path.exists(os.path.join(THUMBS, key(BANCO + r["image_url"]) + ".jpg"))]
    print(f"rows={len(rows)} cached={len(rows)-len(todo)} todo={len(todo)}", flush=True)
    ok = fail = 0
    for i, r in enumerate(todo):
        u = BANCO + r["image_url"]
        try:
            open(os.path.join(THUMBS, key(u) + ".jpg"), "wb").write(thumb(fetch(u, timeout=15)))
            ok += 1
        except Exception as e:
            fail += 1
            if fail <= 5:
                print(f"  ! {r['sku']}: {e}", flush=True)
        time.sleep(0.06)                    # gentle on a live till
        if i and i % 50 == 0:
            print(f"  {i}/{len(todo)}  ok={ok} fail={fail}", flush=True)
    print(f"DONE ok={ok} fail={fail}")
    # A card with no picture cannot be matched by picture — say so rather than ship a blank.
    miss = [r["sku"] for r in rows
            if not os.path.exists(os.path.join(THUMBS, key(BANCO + r["image_url"]) + ".jpg"))]
    if miss:
        print(f"⚠ {len(miss)} rows still have no thumbnail: {miss[:10]}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) or 0)
