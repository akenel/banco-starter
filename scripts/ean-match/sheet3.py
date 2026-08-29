"""Round-3 sheet: side-by-side always on, no hover zigzag, title diffing, variable candidate count.

PRICE IS ON THE CARD (2026-08-28). Angel's idea, and it is the only reliable box-vs-packet tell we
have: a box costs many times what a packet costs. Measured against the 41 bindings a human confirmed
on the first papers run:

    the 4 he called CASE   ->  4.5x  15.4x  20.0x  26.7x   (the four highest ratios in the deck)
    the 37 he called RETAIL ->  0.5x .................. 2.5x

Clean separation, nothing in between. The feed's own `artikel_pro_verkaufseinheit` — the field this
replaces — got 1 of those 4 boxes right and called two CHF 2.00 packets a box (both say "32"),
because on papers it counts leaves in a booklet as often as items in a case (LESSON #2).
Re-run scripts/prove-ean-box-price.py per category; BOX is measured on papers and nowhere else.

The ratio is DISPLAYED, never acted on: it re-orders nothing, hides nothing and binds nothing.
It puts a number in front of the person who decides. (README: there is no confidence threshold,
and this is not one — it is a caption.)
"""
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

# --- the box tell ------------------------------------------------------------
# BOX is where the banner appears. It is the middle of the EMPTY BAND measured on the
# papers run: the highest confirmed retail ratio was 2.5x and the lowest confirmed case
# ratio was 4.5x, so anything in 2.5..4.5 was never observed and 3.0 splits it. It is a
# caption threshold, not a filter — crossing it hides nothing and binds nothing.
# Re-measure it per category (papers were measured; nothing else has been).
BOX = 3.0

def ratio(mine, theirs):
    """How many times our shelf price the feed charges. None whenever either side is unknown —
    an absent price must never render as 0x, which reads as a confident 'not a box'."""
    if not mine or theirs is None: return None
    try: return round(float(theirs) / float(mine), 3)
    except (TypeError, ValueError, ZeroDivisionError): return None

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
.box{display:none;margin-top:11px;padding:9px 12px;border:1px solid var(--warn);border-left:4px solid var(--warn);
     border-radius:8px;color:var(--warn);font-size:13px;font-weight:600;line-height:1.45}
.box b{font-variant-numeric:tabular-nums}
.price{margin-top:4px;font-size:13.5px;font-weight:700;font-variant-numeric:tabular-nums}
.price span{font-weight:400;color:var(--mut);font-size:12px}
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
// CUR = which alternate is loaded in the right pane. It MUST be persisted next to S.
// It was not, until 2026-08-29, and that was a silent answer-corrupter: on reload every pane
// snapped back to #1 while the verdict still read "MATCH → #2", so the picture on screen no
// longer matched the recorded decision — and the next "bind it" wrote #1 over the right answer
// because CUR had been reset to 0 by the load. Angel hit it on TAM-18963 (Kailar, 6 near
// identical candidates). Two names for one truth, and the one that renders always wins.
let CUR=JSON.parse(localStorage.getItem(K+'-cur')||'{}');
const N=CARDS.length;
function save(){try{localStorage.setItem(K,JSON.stringify(S));localStorage.setItem(K+'-ts',JSON.stringify(TS));localStorage.setItem(K+'-cur',JSON.stringify(CUR));}catch(e){}}
function show(p,j){
  CUR[p]=j; save(); const c=CARDS[p], k=c.cands[j];
  document.getElementById('bi'+p).src=k.img;
  document.getElementById('bt'+p).innerHTML=k.tdiff;
  document.getElementById('at'+p).innerHTML=k.mydiff;
  const bits=[k.brand||'—'];
  if(k.price!=null) bits.push('CHF '+k.price.toFixed(2));
  if(k.ratio!=null) bits.push(k.ratio.toFixed(1)+'× your price');
  if(k.units!=='1'&&k.units!=='?') bits.push('feed says '+k.units+'/unit');
  document.getElementById('bm'+p).textContent=bits.join('  ·  ');
  const bx=document.getElementById('bx'+p);
  if(k.ratio!=null&&k.ratio>=BOX){bx.style.display='block';
    bx.innerHTML='⚠ the feed charges <b>'+k.ratio.toFixed(1)+'×</b> what you charge. If this is your product '
      +'at all, this listing is the <b>BOX</b> and not the packet on your shelf — bind it as a <b>case</b>, '
      +'or pick another candidate.';}
  else{bx.style.display='none';}
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
  const u=e.target.closest('.undo');if(u){const p=+u.dataset.p;delete S[p];delete TS[p];show(p,0);save();render();return;}
});
document.getElementById('dl').onclick=()=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([JSON.stringify({decisions:S,stamps:TS,at:new Date().toISOString()},null,1)],{type:'application/json'}));
  a.download='ean-match-decisions-v3.json';a.click();};
document.getElementById('rst').onclick=()=>{if(confirm('Clear all?')){S={};TS={};CUR={};localStorage.removeItem(K);localStorage.removeItem(K+'-ts');localStorage.removeItem(K+'-cur');CARDS.forEach(c=>show(c.i,0));render();}};
CARDS.forEach(c=>show(c.i, CUR[c.i] ?? (typeof S[c.i]==='number' ? S[c.i] : 0))); render();
"""

def build(cards, out, title, intro, sections, run_id='v3'):
    body=[]
    for c in cards:
        if c["i"] in sections: body.append(f'<div class="sec">{sections[c["i"]]}</div>')
        for k in c["cands"]:
            md,td = diff_html(c["name"], k["title"]); k["mydiff"], k["tdiff"] = md, td
        def cap(j, k):
            # the price sits under every thumbnail, so the box in the line-up is visible
            # BEFORE you click it — that was the whole point of putting price on the card
            p = k.get("price")
            return f'{j+1}' if p is None else f'{j+1} · {p:g}'
        alts="".join(
            f'<button class="al" data-p="{c["i"]}" data-j="{j}"><img src="{b64(k["img"])}" alt="">'
            f'<div class="cap">{cap(j,k)}</div></button>' for j,k in enumerate(c["cands"]))
        brands=[k.get("brand","") for k in c["cands"]]
        dup={b for b in brands if b and brands.count(b)>1}
        flag='<div class="flag">⚠ two candidates share a brand — the difference is in the <u style="color:var(--diff)">red words</u>, not the picture</div>' if dup else ""
        weak='<div class="flag">⚠ nothing here scored well. Expect no match.</div>' if c["cands"][0]["cls"]=="w" else ""
        mine=(f'CHF {c["price"]:.2f} <span>your till price</span>' if c.get("price") is not None
              else '<span>no price on file</span>')
        body.append(f'''
<section class="card" id="p{c["i"]}">
  <header><span class="n">{c["i"]+1}/{len(cards)}</span><span>{html.escape(c["cat"])}</span>
    <span class="conf w" id="cf{c["i"]}">—</span><span class="verdict" id="v{c["i"]}">—</span></header>
  <div class="duo">
    <div class="pane"><div class="lbl">your product · {html.escape(c["sku"])}</div>
      <img src="{b64(c["img"])}" alt=""><div class="ttl" id="at{c["i"]}"></div>
      <div class="price">{mine}</div></div>
    <div class="pane"><div class="lbl">FourTwenty candidate</div>
      <img id="bi{c["i"]}" alt=""><div class="ttl" id="bt{c["i"]}"></div>
      <div class="meta" id="bm{c["i"]}"></div></div>
  </div>
  <div class="alts"><span class="hdr">other guesses:</span>{alts}</div>
  <div class="box" id="bx{c["i"]}"></div>
  {flag}{weak}
  <div class="redo">↺ changed your mind? click any option again — nothing is locked</div>
  <div class="acts"><button class="yes" data-p="{c["i"]}">✓ Same product — bind it</button>
    <button class="no" data-p="{c["i"]}">✗ No match</button>
    <button class="hm" data-p="{c["i"]}">Can't tell</button><button class="undo" data-p="{c["i"]}">↺ clear</button></div>
</section>''')
    js=json.dumps([{"i":c["i"],"name":c["name"],
        "cands":[{"img":b64(k["img"]),"tdiff":k["tdiff"],"mydiff":k["mydiff"],
                  "brand":k.get("brand",""),"units":k["units"],"conf":k["conf"],"cls":k["cls"],
                  "price":k.get("price"),"ratio":ratio(c.get("price"), k.get("price"))}
                 for k in c["cands"]]} for c in cards])
    doc=f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{STYLE}</style></head><body><div class="wrap"><h1>{html.escape(title)}</h1>
<p class="lede">{intro}</p>{"".join(body)}</div>
<div class="bar"><span>reviewed <b id="prog">0</b></span><span>median <b id="spd">—</b>/decision</span>
<button id="rst" style="border:1px solid var(--line);background:transparent;color:var(--mut);border-radius:7px;padding:7px 12px;cursor:pointer;font:inherit">reset</button>
<button id="dl" disabled>Download decisions</button></div>
<script>const RUN={run_id!r};const BOX={BOX};const CARDS={js};{SCRIPT}</script></body></html>'''
    open(out,"w").write(doc); return len(doc)
