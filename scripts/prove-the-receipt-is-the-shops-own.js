// The receipt is the ONE piece of Banco a customer takes home, and until 2026-09-07 it was
// carrying three things that were not the shop's:
//
//   1. "🏛️ Come find us on La Piazza" + a QR, on every receipt, whether or not the shop had
//      the module switched on. A receipt is the SHOP's paper, not ours.
//   2. That QR's image was fetched from api.qrserver.com AT PRINT TIME. A printed receipt
//      that needs the internet is a broken image box exactly when the wifi is already down.
//   3. `store_name || 'Artemis Store'` and `legal_name || 'Artemis Growing Supplies GmbH'`.
//      A shop that cloned Banco and had not filled in Settings printed ANOTHER COMPANY'S
//      LEGAL NAME on a document its customer keeps. Not a cosmetic default — a wrong company
//      on a tax document.
//
// Plus a barcode that was not one: eight hand-drawn <rect> bars encoding nothing.
//
// WHAT THIS FILE PROVES, and why each one needs a browser rather than a reading of the
// template: that the page makes NO third-party request while it loads (only the network log
// can say that), that the QR actually DECODED into pixels rather than being a broken img
// (naturalWidth), and that the print stylesheet does what it claims — measured under
// emulateMedia('print'), because the whole point of the watermark change is what happens on
// PAPER, which is the one place `isVisible()` has never been able to see. LESSON #12.
//
// NOTHING IS EVER SAVED. It opens one existing receipt read-only and never presses Refund.
//
//   NODE_PATH=/home/angel/repos/helixnet/node_modules \
//     node scripts/prove-the-receipt-is-the-shops-own.js [<transaction-uuid>]
const { chromium } = require('playwright');

const BASE = process.env.BANCO_URL || 'http://localhost:3000';
const TX = process.argv[2] || process.env.BANCO_TX;

// Hosts the receipt is allowed to talk to = its own, and nothing else. Kept as a
// PREDICATE rather than a blocklist: a blocklist only catches the third party you already
// thought of, and the fault this file exists to prevent is the NEXT one somebody adds.
const isOurs = (u) => {
  try { return new URL(u).origin === new URL(BASE).origin || u.startsWith('data:') || u.startsWith('blob:'); }
  catch (e) { return true; }
};

(async () => {
  if (!TX) {
    console.log('usage: node scripts/prove-the-receipt-is-the-shops-own.js <transaction-uuid>');
    console.log('  (any completed sale — it is opened read-only)');
    process.exit(2);
  }
  const b = await chromium.launch();
  // The tablet's real viewport, same as the other proofs — a screen someone stands in front of.
  const ctx = await b.newContext({ viewport: { width: 1440, height: 895 } });
  const p = await ctx.newPage();
  let pass = 0, fail = 0;
  // The detail prints on a PASS too, on purpose. A row of green ticks cannot tell you
  // whether the check was looking at the right element — LESSON #5, where a date assertion
  // went green while reading a different box. Printing the number it measured is what makes
  // a pass readable: "the QR prints at least 15mm — 76px" can be argued with; "✅" cannot.
  const check = (ok, what, detail) => {
    const d = detail ? '\n       ' + detail : '';
    if (ok) { pass++; console.log('  ✅ ' + what + d); }
    else { fail++; console.log('  ❌ ' + what + d); }
  };

  // The Keycloak hop occasionally times out — measured 1 run in 8 — and it has nothing to do
  // with the receipt. Uncaught it exits on a stack trace that reads exactly like the receipt
  // being broken, which is the worst thing a proof can do: report a fault in the subject when
  // the fault is in the fixture. Say which one it is.
  try {
    await p.goto(BASE + '/pos', { waitUntil: 'domcontentloaded' });
    if (await p.$('button:has-text("Login")')) {
      await p.click('button:has-text("Login")');
      // WAIT FOR THE BOX, not for a number. The other prove-*.js files sleep 3500ms here and
      // then check for #username; when Keycloak took longer than that the login simply did not
      // happen, the run carried on signed-out, and the guard above caught it 3 times in 6.
      // A fixed sleep is a coin toss with extra steps.
      await p.waitForSelector('#username', { timeout: 20000 });
    }
    if (await p.$('#username')) {
      await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
      await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
    }
  } catch (e) {
    console.log('\n⚠️  could not sign in — this says NOTHING about the receipt. Run it again.');
    console.log('    ' + (e.message || e).split('\n')[0]);
    await b.close(); process.exit(2);
  }

  // ── A · the receipt, and every byte it asks the network for ──────────────────────────
  console.log('\n── A · what the page fetches while it loads ──');
  const foreign = [];
  p.on('request', r => { if (!isOurs(r.url())) foreign.push(r.url()); });
  await p.goto(`${BASE}/pos/receipt/${TX}`, { waitUntil: 'networkidle' });

  // THE PAGE MUST HAVE LOADED BEFORE ANYTHING BELOW IS ALLOWED TO MEAN ANYTHING.
  // Caught this file doing the very thing it exists to catch: the Keycloak hop failed on one
  // run in eight, the receipt rendered signed-out and EMPTY, and "no other company's legal
  // name" went green — on a page with no name on it at all. A check that passes hardest when
  // there is nothing to check is the shape in LESSON #5. So: the shop's own name has to be on
  // the sheet first, and if it is not, this exits saying so rather than reporting a clean run.
  try {
    await p.waitForFunction(() => {
      const h = document.querySelector('.receipt-page h1');
      return h && h.textContent.trim().length > 0;
    }, null, { timeout: 15000 });
  } catch (e) {
    console.log('\n⚠️  the receipt rendered EMPTY — not signed in, or the API did not answer.');
    console.log('    This says NOTHING about the receipt itself. Run it again.');
    await b.close(); process.exit(2);
  }
  await p.waitForTimeout(600);   // let the loyalty/member fetch settle too

  check(foreign.length === 0,
        'the receipt makes NO third-party request — it prints with the wifi down',
        foreign.length ? foreign.slice(0, 5).join('\n       ')
                       : 'every request stayed on ' + new URL(BASE).origin);

  // ── B · whose paper is this ─────────────────────────────────────────────────────────
  console.log('\n── B · whose name is on it ──');
  const seen = await p.evaluate(() => {
    const el = document.querySelector('.receipt-page');
    return { text: el ? el.innerText : '', title: document.title };
  });
  // textContent, NOT innerHTML: the source carries these words in the COMMENTS that explain
  // why they were removed, and grepping the markup would fail on its own documentation.
  check(!/La Piazza/i.test(seen.text), 'no La Piazza on the receipt',
        seen.text.split('\n').filter(Boolean).slice(0, 3).join(' / '));
  check(!/Artemis Growing Supplies/i.test(seen.text),
        "no other company's legal name", seen.text.slice(0, 120));
  check(/Artemis/.test(seen.title) && !/HelixPOS/.test(seen.title),
        'the page title names the SHOP, not the vendor — it is the print header', seen.title);
  // A UID full of X's is what the seed ships with a TODO on it. It was printing on 2026-09-07:
  // a fabricated tax identifier on a document a customer keeps and a bookkeeper may file.
  check(!/X{3}/.test(seen.text),
        'no placeholder tax identifier on the sheet',
        (seen.text.match(/[^\n]*X{3}[^\n]*/) || ['none'])[0]);

  // ── C · the QR: ours, drawn here, and actually decoded ───────────────────────────────
  console.log('\n── C · the QR ──');
  const qr = await p.evaluate(() => {
    const i = document.querySelector('img.receipt-qr');
    if (!i) return null;
    return { src: i.getAttribute('src').slice(0, 32), nw: i.naturalWidth, alt: i.alt };
  });
  check(!!qr, 'the QR block is on the page');
  if (qr) {
    check(qr.src.startsWith('data:image/png'), 'the QR is a data URI, not a remote fetch', qr.src);
    check(qr.nw > 0, 'the QR image actually DECODED — not a broken box',
          'naturalWidth ' + qr.nw + 'px');
    check(!!qr.alt && !/piazza/i.test(qr.alt), "the QR's alt names the shop's own address", qr.alt);
  }
  const host = await p.evaluate(() => {
    const el = [...document.querySelectorAll('.receipt-page p')].find(
      e => /^[a-z0-9.-]+\.[a-z]{2,}(\/|$)/i.test(e.textContent.trim()));
    return el ? el.textContent.trim() : '';
  });
  check(!!host, 'the address is printed as text under the QR, for anyone who will not scan', host);

  // ── C2 · THE SHEET ON SCREEN, which is where it is read a hundred times for every once
  //         it is printed. The `p-2 sm:p-8` in the markup is on the wrapper OUTSIDE the white
  //         card — the grey gap AROUND the paper — so the card itself had no padding and every
  //         line from "Receipt #" down through TOTAL ran flush to its edge. Angel, off the
  //         deployed build: "the text basically touches the edge … on the screen it looks
  //         wrong". Measured against the CARD, not the viewport: that is the edge he means.
  console.log('\n── C2 · the sheet on screen ──');
  const gaps = await p.evaluate(() => {
    const card = document.querySelector('.receipt-page').getBoundingClientRect();
    const vis = s => [...document.querySelectorAll(s)].find(x => x.getBoundingClientRect().width > 0);
    const o = {};
    const a = vis('.receipt-page .grid p');   if (a) o.receiptNo = Math.round(a.getBoundingClientRect().left - card.left);
    const h = vis('.receipt-page thead th');  if (h) o.itemHead  = Math.round(h.getBoundingClientRect().left - card.left);
    const t = document.querySelector('.receipt-page .text-2xl span');
    if (t) o.total = Math.round(t.getBoundingClientRect().left - card.left);
    const r = [...document.querySelectorAll('.receipt-page .text-2xl span')].pop();
    if (r) o.totalRight = Math.round(card.right - r.getBoundingClientRect().right);
    return o;
  });
  const worst = Math.min(...Object.values(gaps));
  check(worst >= 16, 'nothing on screen runs flush to the edge of the sheet',
        Object.entries(gaps).map(([k, v]) => k + ' ' + v + 'px').join(' · '));

  // ── D · ON PAPER. The one thing only print media can answer ──────────────────────────
  console.log('\n── D · under print media ──');
  await p.emulateMedia({ media: 'print' });
  // WAIT FOR THE IMAGES TO BE IMAGES. This measured 0px tall on one run and 56px on the next,
  // for the same page and the same logo: `width:auto` on an <img> that has not decoded yet has
  // no height, and the geometry read below happened to land in that window. A check that
  // reports a fault on a good page is as useless as one that misses a bad one (LESSON #5), so
  // the wait is on the CONDITION rather than on a longer sleep, which only moves the odds.
  await p.waitForFunction(() => [...document.querySelectorAll('.receipt-page img')]
      .every(i => i.complete && i.naturalWidth > 0), null, { timeout: 10000 });
  await p.waitForTimeout(300);
  const paper = await p.evaluate(() => {
    const g = s => { const e = document.querySelector(s); return e ? e.getBoundingClientRect() : null; };
    const wm = document.querySelector('.watermark');
    return {
      watermark: wm ? getComputedStyle(wm).display : 'absent',
      qr: g('img.receipt-qr'),
      logo: g('img.receipt-logo'),
      fakeBars: document.querySelectorAll('.receipt-page svg rect').length,
    };
  });
  check(paper.watermark === 'none' || paper.watermark === 'absent',
        'the PAID watermark does not print', 'display: ' + paper.watermark);
  check(paper.fakeBars === 0, 'the fake barcode is gone', paper.fakeBars + ' <rect> bars in the receipt');
  // 20mm at 96dpi ≈ 75.6 CSS px. The floor is 15mm (~57px): _qr_data_uri is measured
  // readable to 10mm on both of the shop's guns, and a customer's phone is worse than a gun.
  check(paper.qr && paper.qr.width >= 57,
        'the QR prints at least 15mm wide', paper.qr ? paper.qr.width.toFixed(0) + 'px' : 'no QR');
  // 34px was the old blanket cap that made it a smudge; the floor is comfortably above it.
  check(paper.logo && paper.logo.height >= 70,
        "the shop's logo is not squeezed to a smudge",
        paper.logo ? paper.logo.height.toFixed(0) + 'px tall' : 'no logo set in Settings');

  // ── D2 · THE PAGE BOX ITSELF. Angel, off the first real print: "there are no margins so
  //         text is full left or full right — is that normal". It was not: `@page margin: 0`
  //         put the totals hard against the paper edge, inside the 4-6mm dead border almost
  //         every office printer refuses to image. Read through the CSSOM, not by grepping the
  //         template — this is the rule the BROWSER resolved from the file it was served.
  const page = await p.evaluate(() => {
    for (const sheet of document.styleSheets) {
      let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
      for (const r of rules) {
        if (r.constructor.name === 'CSSMediaRule' && /print/.test(r.conditionText || ''))
          for (const q of r.cssRules) if (q.constructor.name === 'CSSPageRule')
            return { margin: q.style.margin || q.style.marginTop, size: q.style.getPropertyValue('size') };
        if (r.constructor.name === 'CSSPageRule')
          return { margin: r.style.margin || r.style.marginTop, size: r.style.getPropertyValue('size') };
      }
    }
    return null;
  });
  check(page && page.margin && !/^0\b/.test(page.margin),
        'the printed page has a margin — nothing sits on the paper edge',
        page ? `@page { size: ${page.size}; margin: ${page.margin} }` : 'no @page rule found');

  // Nothing of the APP may print under the receipt. `.app-content` is grey (#f9fafb) and
  // min-height:100vh, so it painted a slab across the bottom third of the first real PDF.
  const below = await p.evaluate(() => {
    const rp = document.querySelector('.receipt-page').getBoundingClientRect(); const out = [];
    document.querySelectorAll('*').forEach(el => {
      const cs = getComputedStyle(el), r = el.getBoundingClientRect();
      if (cs.display === 'none' || r.height < 20) return;
      const bg = cs.backgroundColor;
      if (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent' || bg === 'rgb(255, 255, 255)') return;
      if (r.bottom > rp.bottom - 2) out.push(el.tagName + '.' + (el.className || '').toString().slice(0, 40) + ' ' + bg);
    });
    return out;
  });
  check(below.length === 0, 'no app chrome paints below the receipt',
        below.length ? below.slice(0, 3).join(' · ') : 'the sheet ends where the receipt ends');

  // ── THE ROWS MUST MULTIPLY OUT, AND THE COLUMN MUST CLOSE ──────────────────────────────
  // 2026-09-10. A customer holding this sheet does the only check available to them: quantity
  // times price, and does the bottom line follow. Until today a pack deal printed
  // "3 × CHF 2.00 = CHF 5.14" — right to the cent and impossible to verify, because the deal
  // had been divided back into a per-unit rate and there is no discount column on a receipt.
  // Read under PRINT media on purpose: paper is the layer no fix reaches afterwards.
  const sheet = await p.evaluate(() => {
    const money = (s) => parseFloat(String(s).replace(/[^\d.,-]/g, '').replace(',', '.'));
    const rows = [...document.querySelectorAll('table tbody tr')].map(tr => {
      const c = [...tr.querySelectorAll('td')].map(td => td.innerText.trim());
      return c.length >= 4 ? { qty: parseInt(c[1], 10), unit: money(c[2]), total: money(c[3]) } : null;
    }).filter(r => r && isFinite(r.qty) && isFinite(r.unit) && isFinite(r.total));
    const label = (re) => {
      const el = [...document.querySelectorAll('div')].find(d => re.test(d.innerText) && d.children.length === 2);
      return el ? money(el.children[1].innerText) : null;
    };
    return { rows, sub: label(/Subtotal|Zwischensumme|Sous-total|Subtotale/i),
             total: label(/^\s*(TOTAL|TOTALE)\s*:/i) };
  });
  const offenders = sheet.rows.filter(r => Math.abs(r.qty * r.unit - r.total) >= 0.005);
  check(sheet.rows.length > 0 && offenders.length === 0,
        'every row multiplies out: quantity × price = the line',
        offenders.length
          ? offenders.map(r => `${r.qty} × ${r.unit.toFixed(2)} ≠ ${r.total.toFixed(2)}`).join(' · ')
          : `${sheet.rows.length} rows, checked on PAPER`);
  const rowSum = sheet.rows.reduce((s, r) => s + r.qty * r.unit, 0);
  check(sheet.sub !== null && Math.abs(rowSum - sheet.sub) < 0.02,
        'the rows add up to the subtotal printed under them',
        `rows ${rowSum.toFixed(2)} · subtotal ${sheet.sub}`);

  const shot = 'onboarding/evidence/receipt-print-' + new Date().toISOString().slice(0, 10) + '.png';
  await p.screenshot({ path: shot, fullPage: true });
  console.log('\n  📸 ' + shot + '  (print media — this is the paper)');
  // A screenshot under emulateMedia is close to paper; a PDF through the print pipeline IS
  // the paper, @page box and all. NOTE: never call emulateMedia('screen') before pdf() —
  // it renders the app shell, nav bars and all, and looks convincingly like a receipt.
  await p.emulateMedia({ media: null });
  const pdf = 'onboarding/evidence/receipt-a4.pdf';
  await p.pdf({ path: pdf, preferCSSPageSize: true, printBackground: true });
  console.log('  📄 ' + pdf + '  (A4, straight through the print pipeline)');

  console.log(`\n${fail ? '❌' : '✅'}  ${pass} pass · ${fail} fail`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
