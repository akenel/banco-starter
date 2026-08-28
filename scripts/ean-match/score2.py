#!/usr/bin/env python3
"""Score round 2.  usage: python3 score2.py ~/Downloads/ean-match-decisions-v2.json"""
import json, os, re, sys
SP=os.path.dirname(os.path.abspath(__file__))
def n(g):
    g=re.sub(r"\D","",g or ""); return g.lstrip("0") or g
d=json.load(open(sys.argv[1] if len(sys.argv)>1 else os.path.expanduser("~/Downloads/ean-match-decisions-v2.json")))
T={t["i"]:t for t in json.load(open(SP+"/truth2.json"))}
D=d["decisions"]
right=dis=missed=unavail=cr=fp=unsure=0
b_match=b_none=b_unsure=0; mut_right=mut_wrong=0
lines=[]
for k,v in D.items():
    t=T[int(k)]
    if not t["scored"]:
        if isinstance(v,int):
            b_match+=1; lines.append(f"  {int(k)+1:>2}. [{t['cat']:<8}] {t['name'][:40]:<40} matched -> {t['cand_titles'][v][:36]}  (gtin {t['cand_gtins'][v]})")
        elif v=="skip": b_unsure+=1
        else: b_none+=1
        continue
    g=[n(x) for x in t["cand_gtins"]]; true=n(t["true_ean"]); shown=true in g
    if isinstance(v,int) and t["cand_mutual"][v]:
        (mut_right if g[v]==true else mut_wrong).__int__
        if g[v]==true: mut_right+=1
        else: mut_wrong+=1
    if t["has_twin"]:
        if isinstance(v,int):
            if g[v]==true: right+=1; tag="CORRECT"
            else: dis+=1; tag=f"DISAGREE -> {t['cand_titles'][v][:32]}"
        elif v=="skip": unsure+=1; tag="unsure"
        elif shown: missed+=1; tag="MISSED (was on screen)"
        else: unavail+=1; tag="ranker never showed it"
    else:
        if isinstance(v,int): fp+=1; tag=f"FALSE POSITIVE -> {t['cand_titles'][v][:32]}"
        elif v=="skip": unsure+=1; tag="unsure"
        else: cr+=1; tag="correct rejection"
    lines.append(f"  {int(k)+1:>2}. [{t['cat']:<8}] {t['name'][:40]:<40} {tag}")
print("\n".join(sorted(lines, key=lambda s:int(s.split('.')[0]))))
real=sum(1 for t in T.values() if t["has_twin"]); dn=sum(1 for t in T.values() if t["scored"] and not t["has_twin"])
print(f"""
PART 1 — SCORED
  real cases ({real})   exact {right} · different gtin {dis} · missed on screen {missed} · never shown {unavail}
  decoys ({dn})        correct rejection {cr} · FALSE POSITIVE {fp}
  unsure               {unsure}
  BOTH AGREE badge     right {mut_right} · wrong {mut_wrong}

PART 2 — GRINDERS & BONGS (no ground truth)
  you found a match    {b_match}
  no match found       {b_none}
  couldn't tell        {b_unsure}""")
ts=sorted(int(x) for x in d.get("stamps",{}).values())
gaps=[(ts[i]-ts[i-1])/1000 for i in range(1,len(ts))]
gaps=[g for g in gaps if 0<g<180]
if gaps:
    gaps.sort(); m=gaps[len(gaps)//2]
    print(f"\n  median {m:.0f}s per decision  ->  5,061 products ≈ {5061*m/3600:.1f} hours")
if real: print(f"\n  BOTTOM LINE: {right}/{real} exact ({right/real:.0%}), {fp} false positive(s) of {dn} decoys")
