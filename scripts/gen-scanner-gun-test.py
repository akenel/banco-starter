#!/usr/bin/env python3
"""Build a self-contained scanner-gun test page.

Every code carries a DIFFERENT payload naming its own size, so when the gun
fires you can read straight off the screen which sizes it actually managed —
rather than guessing. All images are embedded as data URIs: the page works
offline, from file://, on any machine, with no server and no vendored JS.
"""
import base64
import io

import barcode
import qrcode
from barcode.writer import ImageWriter

import os

# Repo-relative, and inside src/static so the APP serves it — the device you need to test
# a scanner gun on is a till or a tablet, which never has this repo on it. An absolute
# /home/angel/... path also made this script a no-op for anyone else who cloned Banco.
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "static", "scanner-gun-test.html")


def data_uri(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def qr(payload, box=10):
    q = qrcode.QRCode(box_size=box, border=2,
                      error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(payload)
    q.make(fit=True)
    return data_uri(q.make_image(fill_color="black", back_color="white").convert("RGB"))


def ean(code12):
    bc = barcode.get("ean13", code12, writer=ImageWriter())
    img = bc.render({"module_height": 15.0, "font_size": 10,
                     "text_distance": 5.0, "quiet_zone": 3.0})
    return data_uri(img), bc.get_fullcode()


def c128(payload):
    bc = barcode.get("code128", payload, writer=ImageWriter())
    img = bc.render({"module_height": 15.0, "font_size": 10,
                     "text_distance": 5.0, "quiet_zone": 3.0})
    return data_uri(img), bc.get_fullcode()


# ---- QR ladder: payload names its own size -------------------------------
QR_SIZES = [30, 25, 20, 15, 12, 10, 8]
qr_rows = "".join(
    f'<figure style="--w:{s}mm"><img src="{qr(f"QR-{s}MM")}" alt="QR {s}mm">'
    f'<figcaption><b>{s} mm</b><br><code>QR-{s}MM</code></figcaption></figure>'
    for s in QR_SIZES)

# ---- EAN-13 ladder: a distinct real code per width ------------------------
EAN_SIZES = [(60, "200000000010"), (50, "200000000020"), (40, "200000000030"),
             (34, "200000000040"), (30, "200000000050"), (25, "200000000060")]
ean_rows = ""
ean_map = []
for s, c12 in EAN_SIZES:
    uri, full = ean(c12)
    ean_map.append((s, full))
    ean_rows += (f'<figure style="--w:{s}mm"><img src="{uri}" alt="EAN {s}mm">'
                 f'<figcaption><b>{s} mm wide</b><br><code>{full}</code></figcaption></figure>')

# ---- Code128 ladder ------------------------------------------------------
C128_SIZES = [50, 40, 30, 25]
c128_rows = ""
for s in C128_SIZES:
    uri, full = c128(f"C128-{s}MM")
    c128_rows += (f'<figure style="--w:{s}mm"><img src="{uri}" alt="Code128 {s}mm">'
                  f'<figcaption><b>{s} mm wide</b><br><code>{full}</code></figcaption></figure>')

# ---- The one big QR: "does this gun do 2D at all?" ------------------------
big_qr = qr("GUN-READS-2D")

ean_legend = "".join(f"<tr><td>{s} mm</td><td><code>{f}</code></td></tr>" for s, f in ean_map)

HTML = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scanner Gun Test — Banco</title>
<style>
  :root{{ --red:#157F52; --ink:#1f2937; --mut:#6b7280; --line:#e5e7eb; --ok:#059669;
         --bg:#f6f8f7; --gold:#b0862f; --fail:#C0392B; }}
  *{{ box-sizing:border-box; }}
  body{{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:var(--ink);
        background:var(--bg); margin:0; line-height:1.5; }}
  header{{ position:sticky; top:0; z-index:10; background:#fff; border-bottom:2px solid var(--red);
          padding:12px 20px; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
  h1{{ font-size:18px; margin:0; }} h1 small{{ color:var(--mut); font-weight:500; font-size:13px;
        display:block; margin-top:2px; }}
  main{{ max-width:1000px; margin:0 auto; padding:20px 20px 80px; }}
  section{{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:16px 18px;
           margin-bottom:16px; }}
  h2{{ font-size:15px; margin:0 0 4px; }} .why{{ color:var(--mut); font-size:13px; margin:0 0 12px; }}
  code{{ font-family:ui-monospace,Menlo,monospace; font-size:12px; background:#f3f4f6;
        border:1px solid var(--line); border-radius:5px; padding:1px 5px; }}
  .ladder{{ display:flex; flex-wrap:wrap; gap:18px; align-items:flex-end; }}
  figure{{ margin:0; text-align:center; }}
  figure img{{ width:var(--w); height:auto; display:block; background:#fff; }}
  figcaption{{ font-size:11px; color:var(--mut); margin-top:5px; line-height:1.35; }}
  #cap{{ width:100%; font-family:ui-monospace,Menlo,monospace; font-size:16px; padding:11px 13px;
        border:2px solid var(--red); border-radius:9px; }}
  #log{{ margin-top:10px; font-family:ui-monospace,Menlo,monospace; font-size:13px; }}
  #log div{{ padding:4px 8px; border-bottom:1px solid var(--line); display:flex; gap:10px; }}
  #log b{{ color:var(--ok); }} #log .u{{ color:var(--gold); }}
  .safety{{ border:1px solid var(--line); border-left:4px solid var(--gold); background:#fffdf5;
           border-radius:8px; padding:10px 12px; margin:10px 0; font-size:13.5px; }}
  table{{ border-collapse:collapse; font-size:12.5px; margin-top:8px; }}
  th,td{{ border:1px solid var(--line); padding:4px 9px; text-align:left; }}
  th{{ background:#f6f8f7; }}
  .btn{{ border:1px solid var(--line); background:#fff; border-radius:8px; padding:6px 12px;
        font-size:13px; cursor:pointer; }}
  @media print{{ header,.noprint{{ display:none; }} body{{ background:#fff; }}
                section{{ border:0; page-break-inside:avoid; }} }}
</style></head>
<body>
<header><h1>🔫 Scanner Gun Test
  <small>Does it read 2D? How small can we print? · Banco sanity check</small></h1></header>
<main>

<section class="noprint">
  <h2>Scan into here</h2>
  <p class="why">Click the box so the cursor is in it, then scan any code below. The gun types like a
     keyboard — whatever it read appears here, and gets logged. <b>Each code says its own size</b>,
     so the log tells you exactly which sizes your gun can manage.</p>
  <input id="cap" placeholder="click here first, then scan…" autocomplete="off" autofocus>
  <div id="log"></div>
  <button class="btn" style="margin-top:10px" onclick="document.getElementById('log').innerHTML=''">clear log</button>
</section>

<section>
  <h2>1 · Does this gun read 2D at all?</h2>
  <p class="why">Scan the QR. If nothing happens, the gun is <b>1D laser only</b> and QR is off the table
     for that gun — no setting will change it. Expected: <code>GUN-READS-2D</code></p>
  <div class="ladder"><figure style="--w:45mm"><img src="{big_qr}" alt="big QR">
    <figcaption><b>45 mm</b> — as easy as it gets</figcaption></figure></div>
  <div class="safety"><b>If it fails here, try paper before concluding.</b> Some laser guns can't read
     glossy backlit screens at all but read printed labels fine. Print this page and retry.</div>
</section>

<section>
  <h2>2 · QR — how small can we go?</h2>
  <p class="why">Work down the ladder. The smallest one that reads reliably (try each 5×) is your floor.
     Add a safety margin — a real label is on a curved tin, under shop lighting, held at an angle.</p>
  <div class="ladder">{qr_rows}</div>
</section>

<section>
  <h2>3 · EAN-13 — the current shelf label</h2>
  <p class="why">This is what's on the labels today. The <b>34 mm</b> one is roughly what the current
     "Small" label prints, and it's the one that won't read in the shop. Find where yours gives up.</p>
  <div class="ladder">{ean_rows}</div>
  <table><tr><th>width</th><th>expected value</th></tr>{ean_legend}</table>
</section>

<section>
  <h2>4 · Code128 — for internal SKUs</h2>
  <p class="why">Used when a product has no EAN — e.g. <code>TAM-21796</code>. More compact than EAN-13
     for short payloads.</p>
  <div class="ladder">{c128_rows}</div>
</section>

<section class="noprint">
  <h2>Reading the result</h2>
  <table>
    <tr><th>What you see</th><th>What it means</th></tr>
    <tr><td>QR reads at 15 mm or smaller</td><td>✅ QR is viable for small labels — plenty of room</td></tr>
    <tr><td>QR reads only at 25 mm+</td><td>⚠️ works, but no smaller than the current barcode — little gained</td></tr>
    <tr><td>No QR reads at all, on paper either</td><td>❌ 1D-only gun. Fix the linear barcode instead: wider and taller.</td></tr>
    <tr><td>EAN-13 fails below ~40 mm</td><td>Expected. That is why the 38 mm "Small" label doesn't scan.</td></tr>
  </table>
  <div class="safety"><b>Screen ≠ paper.</b> On-screen millimetres depend on display DPI and browser zoom,
     so treat this ladder as <em>relative</em>. Once you know roughly where the floor is, print the page on
     the label roll and confirm on real media — that is the number to design against.</div>
</section>

</main>
<script>
  const cap=document.getElementById('cap'), log=document.getElementById('log');
  cap.addEventListener('keydown', e=>{{
    if(e.key!=='Enter') return;              // guns send Enter after the payload
    const v=cap.value.trim(); cap.value='';
    if(!v) return;
    const m=v.match(/^(QR|C128)-(\\d+)MM$/);
    const t=new Date().toLocaleTimeString();
    const row=document.createElement('div');
    if(m) row.innerHTML=`<span>${{t}}</span><b>✓ ${{m[1]}} @ ${{m[2]}}mm</b><code>${{v}}</code>`;
    else if(v==='GUN-READS-2D') row.innerHTML=`<span>${{t}}</span><b>✓ 2D CONFIRMED</b><code>${{v}}</code>`;
    else if(/^\\d{{13}}$/.test(v)) row.innerHTML=`<span>${{t}}</span><b>✓ EAN-13</b><code>${{v}}</code>`;
    else row.innerHTML=`<span>${{t}}</span><span class="u">? unrecognised</span><code>${{v}}</code>`;
    log.prepend(row);
  }});
  cap.focus();
  document.addEventListener('click', ()=>cap.focus());
</script>
</body></html>
"""

with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT}  ({len(HTML):,} bytes)")
