"""v2 sheet: 2x product image, hover-to-compare, same-brand warning, mutual-agreement badge."""
import json, os, html, base64
SP=os.path.dirname(os.path.abspath(__file__))
def b64(hexs): return "data:image/jpeg;base64,"+base64.b64encode(bytes.fromhex(hexs)).decode() if hexs else ""

STYLE = """
:root{--bg:#fbfbf9;--fg:#1a1a18;--mut:#6b6b64;--line:#e2e1db;--card:#fff;--sel:#1f7a3d;
      --warn:#b45309;--mutual:#1d6fa5;--skip:#8a8a80;--shade:#f2f1ec}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141412;--fg:#eceae4;--mut:#9c9a90;
      --line:#33322d;--card:#1e1e1b;--sel:#4ec27a;--warn:#e0a35e;--mutual:#6ab6e8;--skip:#77756c;--shade:#26251f}}
:root[data-theme=dark]{--bg:#141412;--fg:#eceae4;--mut:#9c9a90;--line:#33322d;--card:#1e1e1b;
      --sel:#4ec27a;--warn:#e0a35e;--mutual:#6ab6e8;--skip:#77756c;--shade:#26251f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1360px;margin:0 auto;padding:20px 18px 110px}
h1{font-size:21px;margin:0 0 4px}
.lede{color:var(--mut);margin:0 0 8px;max-width:76ch}
.sec{margin:26px 0 12px;padding:9px 13px;background:var(--shade);border-radius:8px;font-size:13px;color:var(--mut)}
.sec b{color:var(--fg)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px;margin:0 0 16px}
.card.done{opacity:.5}
header{display:flex;gap:12px;align-items:center;margin-bottom:11px;font-size:13px;color:var(--mut)}
.n{font-weight:700;color:var(--fg)}
.verdict{margin-left:auto;font-weight:600}
.row{display:grid;grid-template-columns:400px 1fr;gap:20px}
@media(max-width:1000px){.row{grid-template-columns:1fr}}
.mine img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border:1px solid var(--line);border-radius:9px}
.mt{font-weight:650;margin-top:9px;font-size:15px}
.cm{color:var(--mut);font-size:12px;margin-top:3px}
.cands{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;align-content:start}
@media(max-width:1000px){.cands{grid-template-columns:repeat(3,1fr)}}
.cand{position:relative;background:transparent;border:2px solid var(--line);border-radius:9px;padding:6px;
      cursor:pointer;text-align:left;color:inherit;font:inherit}
.cand img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:5px}
.cand:hover{border-color:var(--mut)}
.cand.sel{border-color:var(--sel);box-shadow:0 0 0 3px color-mix(in srgb,var(--sel) 28%,transparent)}
.ct{font-size:12px;margin-top:5px;line-height:1.3}
.badge{position:absolute;top:5px;left:5px;font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px;
       background:var(--mutual);color:#fff;letter-spacing:.3px}
.bwarn{position:absolute;top:5px;right:5px;font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px;
       background:var(--warn);color:#fff}
.same{outline:2px dashed var(--warn);outline-offset:2px}
.acts{display:flex;gap:10px;margin-top:13px;flex-wrap:wrap}
.acts button{border:1px solid var(--line);background:transparent;color:var(--fg);border-radius:7px;
      padding:8px 14px;cursor:pointer;font:inherit}
.acts button.on{border-color:var(--sel);color:var(--sel);font-weight:700}
.hint{color:var(--warn);font-size:12px;margin-top:8px}
/* hover compare */
#cmp{position:fixed;inset:0;background:color-mix(in srgb,var(--bg) 93%,transparent);z-index:50;
     display:none;align-items:center;justify-content:center;gap:26px;padding:30px;pointer-events:none}
#cmp.on{display:flex}
#cmp figure{margin:0;text-align:center;max-width:44vw}
#cmp img{max-width:100%;max-height:70vh;object-fit:contain;background:#fff;border-radius:10px;
     border:1px solid var(--line);box-shadow:0 10px 40px rgba(0,0,0,.25)}
#cmp figcaption{margin-top:9px;font-size:14px;font-weight:600;max-width:44vw}
#cmp .lbl{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--mut);margin-bottom:5px}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);
     padding:10px 18px;display:flex;gap:16px;align-items:center;z-index:60}
.bar b{font-variant-numeric:tabular-nums}
#dl{margin-left:auto;background:var(--sel);color:#fff;border:0;border-radius:7px;padding:9px 17px;
    font:inherit;font-weight:700;cursor:pointer}
#dl:disabled{opacity:.4;cursor:default}
"""

SCRIPT = """
const K='banco-eanmatch-v2';
let S=JSON.parse(localStorage.getItem(K)||'{}');
let TS=JSON.parse(localStorage.getItem(K+'-ts')||'{}');
const N=CARDS.length;
function save(){try{localStorage.setItem(K,JSON.stringify(S));localStorage.setItem(K+'-ts',JSON.stringify(TS));}catch(e){}}
function mark(p,v){ S[p]=v; TS[p]=Date.now(); save(); render(); }
function render(){
  CARDS.forEach(c=>{
    const p=c.i, card=document.getElementById('p'+p); if(!card)return;
    const v=S[p], el=document.getElementById('v'+p);
    card.querySelectorAll('.cand').forEach(b=>b.classList.toggle('sel', v===+b.dataset.c));
    card.querySelector('.none').classList.toggle('on', v==='none');
    card.querySelector('.skip').classList.toggle('on', v==='skip');
    card.classList.toggle('done', v!==undefined);
    el.textContent = v===undefined?'—':(v==='none'?'no match':v==='skip'?"can't tell":'match #'+(v+1));
    el.style.color = v===undefined?'var(--mut)':(v==='none'||v==='skip'?'var(--skip)':'var(--sel)');
  });
  const done=Object.keys(S).length;
  document.getElementById('prog').textContent=done+' / '+N;
  const t=Object.values(TS).map(Number).sort((a,b)=>a-b);
  let d=[]; for(let i=1;i<t.length;i++){const x=(t[i]-t[i-1])/1000; if(x>0&&x<180)d.push(x);}
  document.getElementById('spd').textContent = d.length? Math.round(d.reduce((a,b)=>a+b,0)/d.length)+'s':'—';
  document.getElementById('dl').disabled = done<N;
}
const cmp=document.getElementById('cmp');
document.addEventListener('mouseover',e=>{
  const c=e.target.closest('.cand'); if(!c)return;
  const card=CARDS[+c.dataset.p], k=card.cands[+c.dataset.c];
  document.getElementById('cmpA').src=card.img; document.getElementById('cmpAt').textContent=card.name;
  document.getElementById('cmpB').src=k.img;    document.getElementById('cmpBt').textContent=k.title;
  cmp.classList.add('on');
});
document.addEventListener('mouseout',e=>{ if(e.target.closest('.cand')) cmp.classList.remove('on'); });
document.addEventListener('click',e=>{
  const c=e.target.closest('.cand'); if(c){mark(+c.dataset.p,+c.dataset.c);cmp.classList.remove('on');return;}
  const n=e.target.closest('.none'); if(n){mark(+n.dataset.p,'none');return;}
  const s=e.target.closest('.skip'); if(s){mark(+s.dataset.p,'skip');return;}
});
document.getElementById('dl').onclick=()=>{
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([JSON.stringify({decisions:S,stamps:TS,at:new Date().toISOString()},null,1)],{type:'application/json'}));
  a.download='ean-match-decisions-v2.json'; a.click();
};
document.getElementById('rst').onclick=()=>{if(confirm('Clear all decisions?')){S={};TS={};localStorage.removeItem(K);localStorage.removeItem(K+'-ts');render();}};
render();
"""

def build(cards, out, title, intro, sections):
    body=[]
    for c in cards:
        if c["i"] in sections: body.append(f'<div class="sec">{sections[c["i"]]}</div>')
        brands=[k.get("brand","") for k in c["cands"]]
        dup={b for b in brands if b and brands.count(b)>1}
        tiles=""
        for j,k in enumerate(c["cands"]):
            bl='<span class="badge">BOTH AGREE</span>' if k.get("mutual") else ""
            bw=f'<span class="bwarn">{html.escape(k["units"])}×</span>' if k["units"] not in ("1","?") else ""
            cls="cand"+(" same" if k.get("brand") in dup else "")
            tiles+=(f'<button class="{cls}" data-p="{c["i"]}" data-c="{j}">{bl}{bw}'
                    f'<img src="{b64(k["img"])}" alt="">'
                    f'<div class="ct">{html.escape(k["title"][:70])}</div>'
                    f'<div class="cm">{html.escape(k.get("brand","") or "—")}</div></button>')
        hint='<div class="hint">⚠ two or more candidates share a brand — check the variant, not just the logo</div>' if dup else ""
        body.append(f'''
<section class="card" id="p{c["i"]}" data-p="{c["i"]}">
  <header><span class="n">{c["i"]+1}/{len(cards)}</span><span>{html.escape(c["cat"])}</span>
    <span class="verdict" id="v{c["i"]}">—</span></header>
  <div class="row">
    <div class="mine"><img src="{b64(c["img"])}" alt="">
      <div class="mt">{html.escape(c["name"])}</div><div class="cm">{html.escape(c["sku"])}</div></div>
    <div><div class="cands">{tiles}</div>{hint}</div>
  </div>
  <div class="acts"><button class="none" data-p="{c["i"]}">None of these</button>
    <button class="skip" data-p="{c["i"]}">Can't tell</button></div>
</section>''')
    js_cards=json.dumps([{"i":c["i"],"name":c["name"],"img":b64(c["img"]),
        "cands":[{"title":k["title"],"img":b64(k["img"])} for k in c["cands"]]} for c in cards])
    doc=f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{STYLE}</style></head><body>
<div id="cmp"><figure><div class="lbl">your product</div><img id="cmpA"><figcaption id="cmpAt"></figcaption></figure>
<figure><div class="lbl">FourTwenty candidate</div><img id="cmpB"><figcaption id="cmpBt"></figcaption></figure></div>
<div class="wrap"><h1>{html.escape(title)}</h1><p class="lede">{intro}</p>
{"".join(body)}</div>
<div class="bar"><span>reviewed <b id="prog">0</b></span><span>avg <b id="spd">—</b>/decision</span>
<button id="rst" style="border:1px solid var(--line);background:transparent;color:var(--mut);border-radius:7px;padding:7px 12px;cursor:pointer;font:inherit">reset</button>
<button id="dl" disabled>Download decisions</button></div>
<script>const CARDS={js_cards};{SCRIPT}</script></body></html>'''
    open(out,"w").write(doc); return len(doc)
