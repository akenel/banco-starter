import io, re, urllib.request, numpy as np
from PIL import Image
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
def fetch(url, timeout=20):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
def _prep(b):
    im=Image.open(io.BytesIO(b)).convert("RGB")
    bg=Image.new("RGB",im.size,(255,255,255)); bg.paste(im); return bg
def dhash(b, s=16):
    g=_prep(b).convert("L").resize((s+1,s), Image.LANCZOS)
    a=np.asarray(g,dtype=np.int16); return (a[:,1:]>a[:,:-1]).flatten()
def phash(b, s=32, lo=8):
    from numpy.fft import fft2
    g=_prep(b).convert("L").resize((s,s), Image.LANCZOS)
    a=np.asarray(g,dtype=float); f=np.abs(fft2(a))[:lo,:lo].flatten()
    return f>np.median(f)
def hist(b, bins=6):
    a=np.asarray(_prep(b).resize((96,96), Image.LANCZOS),dtype=np.int32)*bins//256  # 0..bins-1
    idx=((a[:,:,0]*bins)+a[:,:,1])*bins+a[:,:,2]
    h=np.bincount(idx.flatten(), minlength=bins**3).astype(float)
    return h/h.sum()
def ham(x,y): return float((x!=y).mean())
def hsim(x,y): return float(np.minimum(x,y).sum())
