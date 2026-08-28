import csv, os, sys, re, random, pickle, hashlib, json
SP=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,SP)
from hash import ham, hsim
from difflib import SequenceMatcher
BANCO="https://banco.wolfhold.app"
def n(g):
    g=re.sub(r"\D","",g or ""); return g.lstrip("0") or g
def key(u): return hashlib.md5(u.encode()).hexdigest()
FP=pickle.load(open(SP+"/pool2_hashes.pkl","rb")); TP=pickle.load(open(SP+"/tam_hashes.pkl","rb"))
feed=[{"gtin":g,"title":t,"url":u,"units":un,"brand":b,"tag":tg,"h":FP[u]}
      for g,t,u,un,b,tg in csv.reader(open(SP+"/pool2.csv",encoding="utf-8")) if g and u and FP.get(u)]
tam=[r for r in csv.DictReader(open(SP+"/tam_rev.csv",encoding="utf-8")) if TP.get(r["sku"])]
print(f"feed pool {len(feed)} · tam pool {len(tam)}")
comb=lambda a,b: 0.55*(1-ham(a[0],b[0]))+0.45*hsim(a[1],b[1])
def score(h,p,name): return comb(h,p["h"])+0.15*SequenceMatcher(None,name.lower(),p["title"].lower()).ratio()-(0.05 if p["units"] not in ("1","?") else 0)
gset={n(p["gtin"]) for p in feed}
bound=[r for r in tam if r["minted"]=="false" and r["barcode"]]
real=[r for r in bound if n(r["barcode"]) in gset]; deco=[r for r in bound if n(r["barcode"]) not in gset]
print(f"hand-bound in these categories: {len(bound)}  (twin in pool: {len(real)}, no twin: {len(deco)})")
random.seed(99)
A=random.sample(real,min(14,len(real)))+random.sample(deco,min(6,len(deco)))
random.shuffle(A)
B=random.sample([r for r in tam if r["minted"]=="true" and r["cat"] in ("Grinders","Bongs")],12)
cards=[]; truth=[]; sections={}
for idx,(r,scored_flag) in enumerate([(x,True) for x in A]+[(x,False) for x in B]):
    h=TP[r["sku"]]
    top=sorted(feed,key=lambda p:-score(h,p,r["name"]))[:8]
    cands=[]
    for p in top:
        back=max(tam,key=lambda x: comb(TP[x["sku"]],p["h"]))
        tp=SP+f"/thumbs/{key(p['url'])}.jpg"
        cands.append({"title":p["title"],"brand":p["brand"],"units":p["units"],"gtin":p["gtin"],
                      "mutual":back["sku"]==r["sku"],
                      "img":open(tp,"rb").read().hex() if os.path.exists(tp) else ""})
    tt=SP+f"/thumbs/{key(BANCO+r['image_url'])}.jpg"
    cards.append({"i":idx,"sku":r["sku"],"name":r["name"],"cat":r["cat"],
                  "img":open(tt,"rb").read().hex() if os.path.exists(tt) else "",
                  "cands":[{k:v for k,v in c.items() if k!="gtin"} for c in cands]})
    truth.append({"i":idx,"sku":r["sku"],"name":r["name"],"cat":r["cat"],"scored":scored_flag,
                  "true_ean":r["barcode"],"has_twin": scored_flag and n(r["barcode"]) in gset,
                  "cand_gtins":[c["gtin"] for c in cands],"cand_titles":[c["title"] for c in cands],
                  "cand_mutual":[c["mutual"] for c in cands]})
sections[0]=f"<b>Part 1 — scored ({len(A)} products).</b> Wraps, tobacco, CBD, disposables you bound by hand. Some have no right answer."
sections[len(A)]=f"<b>Part 2 — not scored ({len(B)} products).</b> Grinders and bongs with placeholder EANs. Nothing to check against — this is the real job, and the question is whether 3-D objects match at all."
json.dump(cards,open(SP+"/cards2.json","w")); json.dump(truth,open(SP+"/truth2.json","w"),indent=1)
json.dump({str(k):v for k,v in sections.items()},open(SP+"/sections2.json","w"))
sc=[t for t in truth if t["has_twin"]]
hit=sum(1 for t in sc if n(t["true_ean"]) in [n(g) for g in t["cand_gtins"]])
mut=sum(1 for t in sc if any(m and n(g)==n(t["true_ean"]) for g,m in zip(t["cand_gtins"],t["cand_mutual"])))
print(f"cards={len(cards)}  ranker recall (twin in the 8): {hit}/{len(sc)} = {hit/len(sc):.0%}")
print(f"  of those, flagged BOTH AGREE: {mut}")
