import csv, os, sys, re, random, pickle, hashlib, json
SP=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,SP)
from hash import ham, hsim
from difflib import SequenceMatcher
BANCO="https://banco.wolfhold.app"
def n(g):
    g=re.sub(r"\D","",g or ""); return g.lstrip("0") or g
def key(u): return hashlib.md5(u.encode()).hexdigest()

# --- both feed pools, both TAM hash caches -----------------------------------
feed=[]
P1=pickle.load(open(SP+"/pool_hashes.pkl","rb"))
for g,t,u,un,b in csv.reader(open(SP+"/pool.csv",encoding="utf-8")):
    if g and u and P1.get(u): feed.append({"gtin":g,"title":t,"url":u,"units":un,"brand":b,"h":P1[u]})
P2=pickle.load(open(SP+"/pool2_hashes.pkl","rb"))
for g,t,u,un,b,tg in csv.reader(open(SP+"/pool2.csv",encoding="utf-8")):
    if g and u and P2.get(u): feed.append({"gtin":g,"title":t,"url":u,"units":un,"brand":b,"h":P2[u]})
seen=set(); feed=[p for p in feed if not (p["url"] in seen or seen.add(p["url"]))]
TP=pickle.load(open(SP+"/tam_hashes.pkl","rb"))
tamrows=list(csv.DictReader(open(SP+"/tam_rev.csv",encoding="utf-8")))
tampf=list(csv.DictReader(open(SP+"/tampf.csv",encoding="utf-8")))
for r in tampf: r.setdefault("minted","false")
allt={r["sku"]:r for r in tamrows+tampf}
TH={}
for f in ("tam_hashes.pkl",):
    TH.update(pickle.load(open(SP+"/"+f,"rb")))
# papers/filters TAM hashes were computed inline in round 1 — recompute from thumbs if present
comb=lambda a,b: 0.55*(1-ham(a[0],b[0]))+0.45*hsim(a[1],b[1])
def sc(h,p,name): return comb(h,p["h"])+0.15*SequenceMatcher(None,name.lower(),p["title"].lower())\
        .ratio()-(0.05 if p["units"] not in ("1","?") else 0)
def conf(s):
    if s>=0.90: return ("STRONG","s")
    if s>=0.78: return ("WORTH A LOOK","m")
    return ("WEAK — probably nothing","w")

used={t["sku"] for t in json.load(open(SP+"/truth.json"))} | {t["sku"] for t in json.load(open(SP+"/truth2.json"))}
gset={n(p["gtin"]) for p in feed}
pool_by_sku=[r for r in allt.values() if r["sku"] in TH and r["sku"] not in used
             and r.get("barcode") and r.get("minted")=="false"]
real=[r for r in pool_by_sku if n(r["barcode"]) in gset]
deco=[r for r in pool_by_sku if n(r["barcode"]) not in gset]
print(f"feed pool {len(feed)} · unused hand-bound available: {len(real)} real / {len(deco)} decoy")
random.seed(7)
pick=random.sample(real,min(13,len(real)))+random.sample(deco,min(7,len(deco)))
random.shuffle(pick)

cards=[];truth=[]
for i,r in enumerate(pick):
    h=TH[r["sku"]]
    ranked=sorted(feed,key=lambda p:-sc(h,p,r["name"]))
    top=ranked[0]; s0=sc(h,top,r["name"])
    # VARIABLE count: keep alternates only if they are close to the leader
    keep=[top]+[p for p in ranked[1:6] if sc(h,p,r["name"]) >= s0-0.06][:2]
    cands=[]
    for p in keep:
        s=sc(h,p,r["name"]); c,cl=conf(s)
        tp=SP+f"/thumbs/{key(p['url'])}.jpg"
        cands.append({"title":p["title"],"brand":p["brand"],"units":p["units"],"gtin":p["gtin"],
                      "conf":c,"cls":cl,"score":round(s,3),
                      "img":open(tp,"rb").read().hex() if os.path.exists(tp) else ""})
    tt=SP+f"/thumbs/{key(BANCO+r['image_url'])}.jpg"
    cards.append({"i":i,"sku":r["sku"],"name":r["name"],"cat":r.get("cat",""),
                  "img":open(tt,"rb").read().hex() if os.path.exists(tt) else "",
                  "cands":[{k:v for k,v in c.items() if k!="gtin"} for c in cands]})
    truth.append({"i":i,"sku":r["sku"],"name":r["name"],"cat":r.get("cat",""),"scored":True,
                  "true_ean":r["barcode"],"has_twin":n(r["barcode"]) in gset,
                  "cand_gtins":[c["gtin"] for c in cands],"cand_titles":[c["title"] for c in cands],
                  "cand_mutual":[False]*len(cands)})
json.dump(cards,open(SP+"/cards3.json","w")); json.dump(truth,open(SP+"/truth3.json","w"),indent=1)
sc_real=[t for t in truth if t["has_twin"]]
hit=sum(1 for t in sc_real if n(t["true_ean"]) in [n(g) for g in t["cand_gtins"]])
avg=sum(len(c["cands"]) for c in cards)/len(cards)
print(f"cards {len(cards)} · avg candidates {avg:.1f} (was 8) · recall {hit}/{len(sc_real)}")
