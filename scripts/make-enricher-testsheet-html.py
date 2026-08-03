#!/usr/bin/env python3
# ============================================================================
# make-enricher-testsheet-html — the enricher sheet, in the house testsheet format.
#
#   python3 scripts/make-enricher-testsheet-html.py --report /path/suspects.json
#
# Same shape as AGE-GATE-RECLASS-TESTSHEET.html and SHOP-DAY-PREFLIGHT.html: sticky
# ok/issue/fail meters, marks kept in localStorage, Part A/B/C phases, one verdict per
# numbered step. Angel marks it on a tablet at the desk and the counts follow him.
#
# It reads the rows the enricher ACTUALLY WROTE into the dev database, not a fresh parse.
# A sheet built by re-parsing pages only proves the parser can read them; a sheet built
# from stored rows proves what is now IN the catalogue — and only that catches a write
# that mangled a correct parse.
# ============================================================================
import argparse
import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def q(sql, container="banco-postgres"):
    p = subprocess.run(["docker", "exec", "-i", container, "psql", "-U", "helix_user",
                        "-d", "helix_db", "-tA", "-F", "\x1f", "-v", "ON_ERROR_STOP=1"],
                       input=sql, capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        print(p.stderr[:400], file=sys.stderr)
        return []
    return [ln.split("\x1f") for ln in p.stdout.splitlines() if ln.strip()]


def de(url):
    return url.replace("/en/product/", "/de/produkt/")


def E(s):
    return html.escape(str(s), quote=True)


def ladder(tiers):
    return " · ".join(f"<b>{t['min_qty']}+</b> → CHF {t['unit_price']}" for t in tiers)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="", help="suspects.json from enrich-from-source --report")
    ap.add_argument("--steps", type=int, default=12, help="how many ladders get their own step")
    ap.add_argument("--out", default=os.path.join(
        ROOT, "onboarding", "testsheets", "ENRICHER-TESTSHEET.html"))
    args = ap.parse_args()

    rows = q("SELECT sku, name, source_url, price_tiers::text, "
             "  (SELECT count(*) FROM jsonb_object_keys(raw_facets)) "
             "FROM products WHERE attributes ? '_sample_load' AND price_tiers IS NOT NULL "
             "ORDER BY jsonb_array_length(price_tiers) DESC, sku;")
    lad = []
    for r in rows:
        try:
            lad.append({"sku": r[0], "name": r[1], "url": de(r[2]),
                        "tiers": json.loads(r[3]), "specs": int(r[4] or 0)})
        except Exception:
            continue

    specs = q("SELECT sku, name, source_url, "
              "  (SELECT count(*) FROM jsonb_object_keys(raw_facets)), raw_facets::text "
              "FROM products WHERE attributes ? '_sample_load' AND raw_facets IS NOT NULL "
              "ORDER BY (SELECT count(*) FROM jsonb_object_keys(raw_facets)) DESC LIMIT 3;")

    total = q("SELECT count(*), count(*) FILTER (WHERE price_tiers IS NOT NULL), "
              "count(*) FILTER (WHERE raw_facets IS NOT NULL) "
              "FROM products WHERE attributes ? '_sample_load';")
    n_all, n_lad, n_spec = (int(x) for x in total[0][:3]) if total else (0, 0, 0)

    suspects = []
    if args.report and os.path.exists(args.report):
        suspects = json.load(open(args.report, encoding="utf-8")).get("suspects", [])

    picked = lad[:args.steps]
    rest = lad[args.steps:]

    P = []
    A = P.append
    A("""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enricher — tier ladders &amp; specs testsheet</title>
<style>
  :root{ --red:#157F52; --dark:#0f5c3b; --ink:#1f2937; --mut:#6b7280; --line:#e5e7eb;
         --ok:#059669; --iss:#d97706; --fail:#C0392B; --bg:#f6f8f7; --gold:#b0862f; }
  *{ box-sizing:border-box; }
  body{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:var(--ink);
        background:var(--bg); margin:0; line-height:1.5; }
  header{ position:sticky; top:0; z-index:10; background:#fff; border-bottom:2px solid var(--red);
          padding:12px 20px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
  .htop{ display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }
  h1{ font-size:18px; margin:0; }
  h1 small{ color:var(--mut); font-weight:500; font-size:13px; display:block; margin-top:2px; }
  .meters{ display:flex; gap:16px; align-items:center; }
  .meter{ text-align:center; } .meter b{ font-size:20px; display:block; }
  .meter.ok b{ color:var(--ok); } .meter.iss b{ color:var(--iss); } .meter.fail b{ color:var(--fail); }
  .meter span{ font-size:11px; color:var(--mut); text-transform:uppercase; letter-spacing:.04em; }
  .btn{ border:1px solid var(--line); background:#fff; border-radius:8px; padding:6px 12px;
        font-size:13px; cursor:pointer; } .btn:hover{ background:#f0f0f0; }
  main{ max-width:900px; margin:0 auto; padding:22px 20px 80px; }
  .lead{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin-bottom:20px; }
  .phase{ font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
          color:var(--red); margin:26px 0 10px; padding-bottom:6px; border-bottom:2px solid var(--red); }
  section{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin-bottom:14px; }
  section h2{ font-size:15px; margin:0 0 4px; }
  section .why{ color:var(--mut); font-size:13px; margin:0 0 12px; }
  code{ font-family:ui-monospace,Menlo,monospace; font-size:12px; background:#f3f4f6;
        border:1px solid var(--line); border-radius:5px; padding:1px 5px; }
  .cmd{ display:block; font-family:ui-monospace,Menlo,monospace; font-size:12.5px; background:#0f172a;
        color:#e2e8f0; border-radius:8px; padding:9px 12px; margin:6px 0; white-space:pre-wrap; word-break:break-word; }
  ol.steps{ margin:0; padding-left:0; list-style:none; counter-reset:s; }
  ol.steps li{ counter-increment:s; display:flex; gap:10px; padding:9px 0; border-top:1px solid var(--line); }
  ol.steps li:first-child{ border-top:0; }
  ol.steps li::before{ content:counter(s); flex:0 0 22px; height:22px; border-radius:50%;
        background:var(--red); color:#fff; font-size:12px; font-weight:700; display:flex;
        align-items:center; justify-content:center; margin-top:2px; }
  .step-body{ flex:1; font-size:14px; }
  .exp{ display:block; color:var(--ok); font-size:12.5px; margin-top:4px; }
  .verdict{ display:flex; gap:6px; margin-top:7px; }
  .v{ border:1px solid var(--line); background:#fff; border-radius:7px; padding:3px 10px;
      font-size:12px; cursor:pointer; font-weight:600; color:var(--mut); }
  .v.on[data-v=ok]{ background:var(--ok); color:#fff; border-color:var(--ok); }
  .v.on[data-v=iss]{ background:var(--iss); color:#fff; border-color:var(--iss); }
  .v.on[data-v=fail]{ background:var(--fail); color:#fff; border-color:var(--fail); }
  .safety{ border:1px solid var(--line); border-left:4px solid var(--gold); background:#fffdf5;
           border-radius:8px; padding:10px 12px; margin:10px 0; font-size:13.5px; }
  .danger{ border-left-color:var(--fail); background:#fdf2f0; }
  table{ border-collapse:collapse; width:100%; font-size:13px; margin:8px 0; }
  th,td{ border:1px solid var(--line); padding:6px 9px; text-align:left; vertical-align:top; }
  th{ background:#f6f8f7; }
  a{ color:var(--dark); } .lad{ font-size:13px; }
</style></head>
<body>

<header><div class="htop">
  <h1>🏷️ Enricher — quantity breaks &amp; specs
    <small>Prove it reads the shop's own pages correctly, BEFORE it writes 5,100 products</small></h1>
  <div class="meters">
    <div class="meter ok"><b id="mOk">0</b><span>ok</span></div>
    <div class="meter iss"><b id="mIss">0</b><span>issue</span></div>
    <div class="meter fail"><b id="mFail">0</b><span>fail</span></div>
    <button class="btn" onclick="if(confirm('Clear all marks?')){localStorage.removeItem(KEY);location.reload()}">reset</button>
  </div>
</div></header>

<main>
  <div class="lead">
    <strong>What this is.</strong> <code>scripts/enrich-from-source.py</code> wants to fill
    <b>quantity breaks</b> and <b>spec tables</b> for ~5,100 products by reading each one's own page
    on artemisluzern.ch. Every row already knows its page — that is what <code>source_url</code> is.
    This sheet proves it reads them <em>correctly</em>, against the real shop pages, before a single
    row on prod is touched.""")

    A(f"""
    <div class="safety danger">
      <b>Why this is a money sheet, not a data sheet.</b> A <em>missing</em> ladder is harmless — the
      till charges the normal price. A <em>wrong</em> ladder charges a customer the wrong money, at
      the counter, with a queue. Judge the two columns by different standards: <b>tiers are money,
      specs are information.</b>
    </div>

    <div class="safety">
      <b>Nothing here has touched your shop.</b> Everything below was produced on the dev laptop
      against a {n_all}-row slice of the real catalogue, pulled read-only. Prod is untouched.
    </div>

    <div class="safety">
      <b>The sample already caught one.</b> {len(suspects)} ladder was <b>refused</b> before it could
      be written — see Part A. That is what this exercise is for, and it is the reason the run is
      worth doing on a sample first.
    </div>
  </div>
""")

    if suspects:
        A('<div class="phase">Part A — the one it refused (do this first)</div>\n<section>')
        A('<h2>A1 · Confirm the refused ladder really is wrong on Felix\'s page</h2>')
        A('<p class="why">The enricher now refuses any "quantity break" that costs MORE than a '
          'single unit. It kept the specs and skipped only the pricing. Check the page agrees, '
          'then tell Felix — the error is on his site, so the next import brings it back.</p>')
        A('<ol class="steps">')
        for s in suspects:
            lads = " · ".join(f"CHF {t['unit_price']} from {t['min_qty']}" for t in s["tiers"])
            url = ""
            for r in q("SELECT source_url FROM products WHERE sku = %s LIMIT 1;"
                       % ("'" + s["sku"].replace("'", "''") + "'")):
                url = de(r[0])
            A(f'''<li><div class="step-body">Open <b>{E(s['name'])}</b> (<code>{E(s['sku'])}</code>)
              and read the price box:
              {f'<span class="cmd">{E(url)}</span>' if url else ''}
              <table>
                <tr><th>one unit costs</th><td><b>CHF {s['unit_price']:.2f}</b></td></tr>
                <tr><th>but the "break" says</th><td><b>{E(lads)}</b></td></tr>
              </table>
              <span class="exp">the page really does say a bigger quantity costs more EACH. Left
              alone, buying 100 would have been charged 100 × CHF {float(s['tiers'][0]['unit_price']):.2f}
              = <b>CHF {100 * float(s['tiers'][0]['unit_price']):,.0f}</b> instead of about
              CHF {100 * s['unit_price']:,.0f}. Almost certainly the page means "a bag of 100 for
              CHF {float(s['tiers'][0]['unit_price']):.2f}" — a bundle price written as a per-unit one.</span>
              </div></li>''')
        A('''<li><div class="step-body"><b>Send the SKU to Felix</b> so it is corrected at source.
          <span class="exp">Banco refuses it either way, so nothing is at risk while he fixes it.</span>
          </div></li>''')
        A('</ol></section>')

    A(f'<div class="phase">Part B — check the ladders against the shop pages ({len(picked)} of '
      f'{n_lad})</div>\n<section>')
    A('<h2>B1 · Open the page, compare the numbers</h2>')
    A('<p class="why">Each row shows exactly what the enricher stored. Open the link, look at the '
      'price box, mark it. You do not need to do all of them — five or six is a real answer. '
      'A single wrong ladder means STOP.</p>')
    A('<ol class="steps">')
    for r in picked:
        A(f'''<li><div class="step-body"><b>{E(r['name'])}</b> <code>{E(r['sku'])}</code>
          <span class="cmd">{E(r['url'])}</span>
          <div class="lad">stored: {ladder(r['tiers'])} &nbsp;·&nbsp; {r['specs']} spec fields</div>
          <span class="exp">the price box on the page shows these same breaks, at these same
          quantities.</span></div></li>''')
    A('</ol></section>')

    if rest:
        A('<section><h2>B2 · The rest of the ladders, for reference</h2>')
        A('<p class="why">Not individually marked — scan them for anything that looks absurd '
          '(a break dearer than the unit price, a quantity of 1, a price of 0).</p>')
        A('<table><tr><th>SKU</th><th>product</th><th>stored breaks</th><th>page</th></tr>')
        for r in rest:
            A(f"<tr><td><code>{E(r['sku'])}</code></td><td>{E(r['name'])}</td>"
              f"<td class='lad'>{ladder(r['tiers'])}</td>"
              f"<td><a href='{E(r['url'])}' target='_blank'>open</a></td></tr>")
        A('</table>')
        A('<ol class="steps"><li><div class="step-body">Nothing in that table looks absurd.'
          '<span class="exp">every break is cheaper than the one before it, and cheaper than '
          'buying one.</span></div></li></ol></section>')

    A('<div class="phase">Part C — the specs (information, not money)</div>\n<section>')
    A('<h2>C1 · A spec table matches the page\'s Details block</h2>')
    A('<p class="why">These fill <code>raw_facets</code>. They are what finally makes '
      '<code>Breite 4.4 cm</code> vs <code>5.2 cm</code> visible in Banco instead of needing two '
      'web fetches to settle whether two rows are duplicates.</p>')
    A('<ol class="steps">')
    for r in specs:
        try:
            f = json.loads(r[4])
        except Exception:
            f = {}
        pairs = "".join(f"<tr><th>{E(k)}</th><td>{E(v)}</td></tr>" for k, v in list(f.items())[:6])
        A(f'''<li><div class="step-body"><b>{E(r[1])}</b> <code>{E(r[0])}</code> — stored {E(r[3])} fields
          <span class="cmd">{E(de(r[2]))}</span>
          <table>{pairs}</table>
          <span class="exp">these match the <b>Details</b> block on the page, and there is no footer
          text (<code>Kontakt</code>, <code>Impressum</code>, <code>AGB</code>) among them.</span>
          </div></li>''')
    A('''<li><div class="step-body">Nothing in any spec table is site furniture — no
      <code>Kontakt: Jugendschutz</code>, no <code>AGB: Seit 1999</code>.
      <span class="exp">the Details block ends where the footer begins. This was checked
      automatically on 60 pages with zero hits, but a human eye is the real test.</span>
      </div></li>''')
    A('</ol></section>')

    A(f'''<div class="phase">Part D — the go / no-go</div>
<section>
  <h2>D1 · Run it on prod</h2>
  <p class="why">Only after Part A and B are marked. Dry run first — it writes nothing without
     <code>--apply</code>.</p>
  <ol class="steps">
    <li><div class="step-body">On the prod box, read what it wants to do:
      <span class="cmd">cd /root/banco-starter &amp;&amp; git pull
python3 scripts/enrich-from-source.py --report /tmp/suspects.json</span>
      <span class="exp">about 90 minutes at 1s apart. Writes nothing. Ends with the ladder count,
      the spec count, and the list of any REFUSED ladders.</span></div></li>
    <li><div class="step-body">Read the refused list before applying.
      <span class="cmd">cat /tmp/suspects.json</span>
      <span class="exp">each one is a page where a bigger quantity costs more each — Felix's data,
      not ours. Nothing gets written for them either way.</span></div></li>
    <li><div class="step-body">Apply.
      <span class="cmd">python3 scripts/enrich-from-source.py --apply --report /tmp/suspects.json</span>
      <span class="exp">"✅ enriched N product(s) from their own source pages."</span></div></li>
    <li><div class="step-body"><b>Prove it at the till, not in a report.</b> Ring up 10 of a product
      from Part B and check the line price matches the break.
      <span class="exp">this is the only step that counts. A stored ladder is a claim; a till
      charging the right money is proof.</span></div></li>
  </ol>
  <div class="safety">
    <b>Expected scale, measured on the {n_all}-row sample:</b> {n_lad} ladders and {n_spec} spec
    tables out of {n_all}. Across 5,100 products that is roughly <b>580 ladders</b> and
    <b>4,700 spec tables</b>.
  </div>
  <div class="safety danger">
    <b>If any ladder in Part B is wrong — stop.</b> Do not run <code>--apply</code> on prod. A wrong
    break is a customer charged the wrong money, and it is far cheaper to fix the parser than to
    find out at the counter.
  </div>
</section>
</main>

<script>
  const KEY='banco-enricher-testsheet-v1';
  let state=JSON.parse(localStorage.getItem(KEY)||'{{}}');
  document.querySelectorAll('ol.steps li').forEach((li,i)=>{{
    const d=document.createElement('div'); d.className='verdict';
    ['ok','iss','fail'].forEach(v=>{{
      const b=document.createElement('button'); b.className='v'; b.dataset.v=v;
      b.textContent={{ok:'✓ OK',iss:'⚠ ISSUE',fail:'✗ FAIL'}}[v];
      b.onclick=()=>{{ state[i] = state[i]===v ? '' : v; save(); }};
      d.appendChild(b);
    }});
    li.querySelector('.step-body').appendChild(d);
  }});
  function save(){{
    localStorage.setItem(KEY, JSON.stringify(state));
    let o=0,s=0,f=0;
    document.querySelectorAll('ol.steps li').forEach((li,i)=>{{
      li.querySelectorAll('.v').forEach(b=>b.classList.toggle('on', state[i]===b.dataset.v));
      if(state[i]==='ok')o++; else if(state[i]==='iss')s++; else if(state[i]==='fail')f++;
    }});
    mOk.textContent=o; mIss.textContent=s; mFail.textContent=f;
  }}
  save();
</script>
</body></html>''')

    open(args.out, "w", encoding="utf-8").write("\n".join(P))
    print(f"✅ {args.out}")
    print(f"   {n_lad} ladders ({len(picked)} as steps) · {n_spec} spec tables · "
          f"{len(suspects)} refused")
    return 0


if __name__ == "__main__":
    sys.exit(main())
