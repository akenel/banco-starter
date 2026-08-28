"""Round-3 sheet: side-by-side always on, no hover zigzag, title diffing, variable candidate count."""
import json, os, html, base64, re
def b64(h): return "data:image/jpeg;base64,"+base64.b64encode(bytes.fromhex(h)).decode() if h else ""
_W=re.compile(r"[a-z0-9]+")
def toks(s): return _W.findall((s or "").lower())
def diff_html(mine, theirs):
    """Mark words unique to each side. Shared words stay quiet; the differences are the decision."""
    a,b=set(toks(mine)),set(toks(theirs))
    def render(s, other):
        out=[]
        for w in re.split(r"(\W+)", s):
            k=w.lower()
            if _W.fullmatch(k) and k not in other: out.append(f'<u>{html.escape(w)}</u>')
            else: out.append(html.escape(w))
        return "".join(out)
    return render(mine,b), render(theirs,a)

STYLE="""
:root{--bg:#fbfbf9;--fg:#1a1a18;--mut:#6b6b64;--line:#e2e1db;--card:#fff;--sel:#1f7a3d;--warn:#b45309;
      --diff:#b8262b;--shade:#f2f1ec;--weak:#8a8a80}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141412;--fg:#eceae4;--mut:#9c9a90;
      --line:#33322d;--card:#1e1e1b;--sel:#4ec27a;--warn:#e0a35e;--diff:#ff8b8b;--shade:#26251f;--weak:#77756c}}
:root[data-theme=dark]{--bg:#141412;--fg:#eceae4;--mut:#9c9a90;--line:#33322d;--card:#1e1e1b;--sel:#4ec27a;
      --warn:#e0a35e;--diff:#ff8b8b;--shade:#26251f;--weak:#77756c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:20px 18px 110px}
h1{font-size:21px;margin:0 0 4px}.lede{color:var(--mut);margin:0 0 10px;max-width:78ch}
.sec{margin:24px 0 12px;padding:9px 13px;background:var(--shade);border-radius:8px;font-size:13px;color:var(--mut)}
.sec b{color:var(--fg)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:0 0 18px}
.card.done{opacity:.82}
.card.done .redo{display:block}
.redo{display:none;font-size:12px;color:var(--mut);margin-top:8px}
header{display:flex;gap:12px;align-items:center;margin-bottom:12px;font-size:13px;color:var(--mut)}
.n{font-weight:700;color:var(--fg)}.verdict{margin-left:auto;font-weight:700}
.conf{padding:2px 8px;border-radius:5px;font-size:11px;font-weight:700;letter-spacing:.3px}
.conf.s{background:var(--sel);color:#fff}.conf.m{background:var(--warn);color:#fff}
.conf.w{background:var(--weak);color:#fff}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.duo{grid-template-columns:1fr}}
.pane{min-width:0}
.pane .lbl{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--mut);margin-bottom:6px}
.pane img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border:1px solid var(--line);border-radius:10px}
.ttl{margin-top:9px;font-size:15px;font-weight:600;line-height:1.35;word-wrap:break-word}
.ttl u{text-decoration:none;color:var(--diff);font-weight:800;border-bottom:2px solid var(--diff)}
.meta{color:var(--mut);font-size:12px;margin-top:4px}
.alts{display:flex;gap:9px;margin-top:14px;align-items:center;flex-wrap:wrap}
.alts .al{width:74px;border:2px solid var(--line);border-radius:8px;padding:3px;cursor:pointer;background:transparent}
.alts .al.on{border-color:var(--fg)}
.alts .al img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:4px;display:block}
.alts .cap{font-size:10px;color:var(--mut);text-align:center;margin-top:2px}
.alts .hdr{font-size:12px;color:var(--mut);margin-right:2px}
.acts{display:flex;gap:10px;margin-top:15px;flex-wrap:wrap}
.acts button{border:1px solid var(--line);background:transparent;color:var(--fg);border-radius:8px;padding:9px 16px;cursor:pointer;font:inherit}
.acts .yes{border-color:var(--sel);color:var(--sel);font-weight:700}
.acts button.on{background:var(--sel);color:#fff;border-color:var(--sel);font-weight:700}
.acts .no.on{background:var(--weak);border-color:var(--weak)}
.flag{margin-top:11px;color:var(--warn);font-size:12.5px;font-weight:600}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);
     padding:10px 18px;display:flex;gap:16px;align-items:center;z-index:60}
.bar b{font-variant-numeric:tabular-nums}
#dl{margin-left:auto;background:var(--sel);color:#fff;border:0;border-radius:7px;padding:9px 17px;font:inherit;font-weight:700;cursor:pointer}
#dl:disabled{opacity:.4;cursor:default}
kbd{border:1px solid var(--line);border-radius:4px;padding:0 5px;font-size:11px;color:var(--mut)}
"""

SCRIPT = r"""
const K='banco-eanmatch-'+RUN;   // per-run key: a new deck NEVER inherits old answers
let S=JSON.parse(localStorage.getItem(K)||'{}'), TS=JSON.parse(localStorage.getItem(K+'-ts')||'{}');
let CUR={};                       // card -> which alternate is loaded in the right pane
const N=CARDS.length;
function save(){try{localStorage.setItem(K,JSON.stringify(S));localStorage.setItem(K+'-ts',JSON.stringify(TS));}catch(e){}}
function show(p,j){
  CUR[p]=j; const c=CARDS[p], k=c.cands[j];
  document.getElementById('bi'+p).src=k.img;
  document.getElementById('bt'+p).innerHTML=k.tdiff;
  document.getElementById('at'+p).innerHTML=k.mydiff;
  document.getElementById('bm'+p).textContent=(k.brand||'—')+(k.units!=='1'&&k.units!=='?'?'  ·  ⚠ '+k.units+' per unit':'');
  const cf=document.getElementById('cf'+p);
  cf.className='conf '+k.cls; cf.textContent=k.conf;
  document.querySelectorAll('#p'+p+' .al').forEach(b=>b.classList.toggle('on',+b.dataset.j===j));
}
function mark(p,v){S[p]=v;TS[p]=Date.now();save();render();}
function render(){
  CARDS.forEach(c=>{const p=c.i,el=document.getElementById('v'+p),card=document.getElementById('p'+p);
    const v=S[p];
    card.querySelector('.yes').classList.toggle('on', typeof v==='number');
    card.querySelector('.no').classList.toggle('on', v==='none');
    card.querySelector('.hm').classList.toggle('on', v==='skip');
    card.classList.toggle('done', v!==undefined);
    el.textContent=v===undefined?'—':(v==='none'?'no match':v==='skip'?"can't tell":'MATCH → #'+(v+1));
    el.style.color=v===undefined?'var(--mut)':(typeof v==='number'?'var(--sel)':'var(--weak)');});
  document.getElementById('prog').textContent=Object.keys(S).length+' / '+N;
  const t=Object.values(TS).map(Number).sort((a,b)=>a-b);
  let d=[];for(let i=1;i<t.length;i++){const x=(t[i]-t[i-1])/1000;if(x>0&&x<180)d.push(x);}
  d.sort((a,b)=>a-b);
  document.getElementById('spd').textContent=d.length?Math.round(d[Math.floor(d.length/2)])+'s':'—';
  document.getElementById('dl').disabled=Object.keys(S).length<N;
}
document.addEventListener('click',e=>{
  const a=e.target.closest('.al'); if(a){show(+a.dataset.p,+a.dataset.j);return;}
  const y=e.target.closest('.yes'); if(y){mark(+y.dataset.p, CUR[+y.dataset.p]??0);return;}
  const n=e.target.closest('.no');  if(n){mark(+n.dataset.p,'none');return;}
  const h=e.target.closest('.hm');  if(h){mark(+h.dataset.p,'skip');return;}
  const u=e.target.closest('.undo');if(u){delete S[+u.dataset.p];save();render();return;}
});
document.getElementById('dl').onclick=()=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([JSON.stringify({decisions:S,stamps:TS,at:new Date().toISOString()},null,1)],{type:'application/json'}));
  a.download='ean-match-decisions-v3.json';a.click();};
document.getElementById('rst').onclick=()=>{if(confirm('Clear all?')){S={};TS={};localStorage.removeItem(K);localStorage.removeItem(K+'-ts');render();}};
CARDS.forEach(c=>show(c.i,0)); render();
"""

def build(cards, out, title, intro, sections, run_id='v3'):
    body=[]
    for c in cards:
        if c["i"] in sections: body.append(f'<div class="sec">{sections[c["i"]]}</div>')
        for k in c["cands"]:
            md,td = diff_html(c["name"], k["title"]); k["mydiff"], k["tdiff"] = md, td
        alts="".join(
            f'<button class="al" data-p="{c["i"]}" data-j="{j}"><img src="{b64(k["img"])}" alt="">'
            f'<div class="cap">{j+1}</div></button>' for j,k in enumerate(c["cands"]))
        brands=[k.get("brand","") for k in c["cands"]]
        dup={b for b in brands if b and brands.count(b)>1}
        flag='<div class="flag">⚠ two candidates share a brand — the difference is in the <u style="color:var(--diff)">red words</u>, not the picture</div>' if dup else ""
        weak='<div class="flag">⚠ nothing here scored well. Expect no match.</div>' if c["cands"][0]["cls"]=="w" else ""
        body.append(f'''
<section class="card" id="p{c["i"]}">
  <header><span class="n">{c["i"]+1}/{len(cards)}</span><span>{html.escape(c["cat"])}</span>
    <span class="conf w" id="cf{c["i"]}">—</span><span class="verdict" id="v{c["i"]}">—</span></header>
  <div class="duo">
    <div class="pane"><div class="lbl">your product · {html.escape(c["sku"])}</div>
      <img src="{b64(c["img"])}" alt=""><div class="ttl" id="at{c["i"]}"></div></div>
    <div class="pane"><div class="lbl">FourTwenty candidate</div>
      <img id="bi{c["i"]}" alt=""><div class="ttl" id="bt{c["i"]}"></div>
      <div class="meta" id="bm{c["i"]}"></div></div>
  </div>
  <div class="alts"><span class="hdr">other guesses:</span>{alts}</div>
  {flag}{weak}
  <div class="redo">↺ changed your mind? click any option again — nothing is locked</div>
  <div class="acts"><button class="yes" data-p="{c["i"]}">✓ Same product — bind it</button>
    <button class="no" data-p="{c["i"]}">✗ No match</button>
    <button class="hm" data-p="{c["i"]}">Can't tell</button><button class="undo" data-p="{c["i"]}">↺ clear</button></div>
</section>''')
    js=json.dumps([{"i":c["i"],"name":c["name"],
        "cands":[{"img":b64(k["img"]),"tdiff":k["tdiff"],"mydiff":k["mydiff"],
                  "brand":k.get("brand",""),"units":k["units"],"conf":k["conf"],"cls":k["cls"]}
                 for k in c["cands"]]} for c in cards])
    doc=f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{STYLE}</style></head><body><div class="wrap"><h1>{html.escape(title)}</h1>
<p class="lede">{intro}</p>{"".join(body)}</div>
<div class="bar"><span>reviewed <b id="prog">0</b></span><span>median <b id="spd">—</b>/decision</span>
<button id="rst" style="border:1px solid var(--line);background:transparent;color:var(--mut);border-radius:7px;padding:7px 12px;cursor:pointer;font:inherit">reset</button>
<button id="dl" disabled>Download decisions</button></div>
<script>const RUN={run_id!r};const CARDS={js};{SCRIPT}</script></body></html>'''
    open(out,"w").write(doc); return len(doc)
