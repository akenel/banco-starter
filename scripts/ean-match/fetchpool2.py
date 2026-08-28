import csv, os, sys, time, pickle, hashlib, io
SP=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,SP)
from hash import fetch, dhash, hist
from PIL import Image
CACHE=SP+"/pool2_hashes.pkl"
D=pickle.load(open(CACHE,"rb")) if os.path.exists(CACHE) else {}
def key(u): return hashlib.md5(u.encode()).hexdigest()
def thumb(b, px=520):
    im=Image.open(io.BytesIO(b)).convert("RGB"); im.thumbnail((px,px), Image.LANCZOS)
    o=io.BytesIO(); im.save(o,"JPEG",quality=80); return o.getvalue()
rows=[r for r in csv.reader(open(SP+"/pool2.csv",encoding="utf-8")) if len(r)>=6 and r[2]]
todo=[r for r in rows if r[2] not in D]
print(f"pool={len(rows)} cached={len(D)} todo={len(todo)}", flush=True)
for i,r in enumerate(todo):
    u=r[2]
    try:
        b=fetch(u, timeout=15)
        open(SP+f"/thumbs/{key(u)}.jpg","wb").write(thumb(b))
        D[u]=(dhash(b), hist(b))
    except Exception: D[u]=None
    time.sleep(0.08)
    if i%100==0: pickle.dump(D,open(CACHE,"wb")); print(f"  {i}/{len(todo)}",flush=True)
pickle.dump(D,open(CACHE,"wb"))
print(f"DONE usable={sum(1 for v in D.values() if v)}/{len(D)}")
