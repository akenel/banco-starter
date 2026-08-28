import csv, os, sys, time, pickle, hashlib, io
SP=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,SP)
from hash import fetch, dhash, hist
from PIL import Image
BANCO="https://banco.wolfhold.app"
CACHE=SP+"/tam_hashes.pkl"
D=pickle.load(open(CACHE,"rb")) if os.path.exists(CACHE) else {}
def key(u): return hashlib.md5(u.encode()).hexdigest()
def thumb(b, px=520):
    im=Image.open(io.BytesIO(b)).convert("RGB"); im.thumbnail((px,px), Image.LANCZOS)
    o=io.BytesIO(); im.save(o,"JPEG",quality=80); return o.getvalue()
rows=list(csv.DictReader(open(SP+"/tam_rev.csv",encoding="utf-8")))
todo=[r for r in rows if r["sku"] not in D]
print(f"tam={len(rows)} cached={len(D)} todo={len(todo)}", flush=True)
for i,r in enumerate(todo):
    u=BANCO+r["image_url"]
    try:
        b=fetch(u, timeout=15)
        open(SP+f"/thumbs/{key(u)}.jpg","wb").write(thumb(b))
        D[r["sku"]]=(dhash(b), hist(b))
    except Exception: D[r["sku"]]=None
    time.sleep(0.06)                      # gentle on Felix's live app container
    if i%100==0: pickle.dump(D,open(CACHE,"wb")); print(f"  {i}/{len(todo)}",flush=True)
pickle.dump(D,open(CACHE,"wb"))
print(f"DONE usable={sum(1 for v in D.values() if v)}/{len(D)}")
