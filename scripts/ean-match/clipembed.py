"""Embed every cached thumbnail with CLIP ViT-B/32 (ONNX, CPU). Resumable."""
import os, sys, csv, pickle, hashlib, numpy as np
from PIL import Image
import onnxruntime as ort
SP=os.path.dirname(os.path.abspath(__file__))
MEAN=np.array([0.48145466,0.4578275,0.40821073],dtype=np.float32)
STD =np.array([0.26862954,0.26130258,0.27577711],dtype=np.float32)
def key(u): return hashlib.md5(u.encode()).hexdigest()
def prep(path):
    im=Image.open(path).convert("RGB")
    w,h=im.size; s=224/min(w,h)
    im=im.resize((max(224,round(w*s)),max(224,round(h*s))), Image.BICUBIC)
    w,h=im.size; l,t=(w-224)//2,(h-224)//2
    a=np.asarray(im.crop((l,t,l+224,t+224)),dtype=np.float32)/255.0
    return ((a-MEAN)/STD).transpose(2,0,1)
sess=ort.InferenceSession(SP+"/clip/model.onnx", providers=["CPUExecutionProvider"],
        sess_options=(lambda o:(setattr(o,'intra_op_num_threads',8),o)[1])(ort.SessionOptions()))
CACHE=SP+"/clip_vecs.pkl"
V=pickle.load(open(CACHE,"rb")) if os.path.exists(CACHE) else {}
BANCO="https://banco.wolfhold.app"
todo=[]
for f in ("pool.csv","pool2.csv"):
    for row in csv.reader(open(SP+"/"+f,encoding="utf-8")):
        if len(row)>=3 and row[2]:
            p=SP+f"/thumbs/{key(row[2])}.jpg"
            if os.path.exists(p) and row[2] not in V: todo.append((row[2],p))
for f in ("tam_rev.csv","tampf.csv"):
    for r in csv.DictReader(open(SP+"/"+f,encoding="utf-8")):
        p=SP+f"/thumbs/{key(BANCO+r['image_url'])}.jpg"
        if os.path.exists(p) and r["sku"] not in V: todo.append((r["sku"],p))
seen=set(); todo=[t for t in todo if not (t[0] in seen or seen.add(t[0]))]
print(f"cached {len(V)} · to embed {len(todo)}", flush=True)
B=16
for i in range(0,len(todo),B):
    chunk=todo[i:i+B]; arr=[]; ids=[]
    for k,p in chunk:
        try: arr.append(prep(p)); ids.append(k)
        except Exception: pass
    if not arr: continue
    out=sess.run(["image_embeds"],{"pixel_values":np.stack(arr)})[0]
    out=out/np.linalg.norm(out,axis=1,keepdims=True)
    for k,v in zip(ids,out): V[k]=v.astype(np.float32)
    if i % (B*20)==0:
        pickle.dump(V,open(CACHE,"wb")); print(f"  {i}/{len(todo)}", flush=True)
pickle.dump(V,open(CACHE,"wb"))
print(f"DONE {len(V)} vectors")
