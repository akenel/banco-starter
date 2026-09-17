#!/usr/bin/env node
/**
 * prove-a-qr-is-not-a-barcode.js
 *
 * WHY THIS EXISTS
 * ---------------
 * 2026-09-17, at the counter. A packet sitting by the till had no barcode stripe
 * anywhere on it — only a QR. Angel scanned the QR "like a silly cashier might
 * do", and Banco bound `https://vqr.vc/BiWfnR9bv` to AlpenBreeze as its barcode.
 *
 * It got in because the format guard SAW it and gave the WRONG REASON: a URL has
 * letters, so it read as a lot number and offered "use it anyway" — and a cashier
 * told the code is probably a batch number, looking at a packet with no other code
 * on it, will quite reasonably press that button. (LESSON #12: a wrong reason is
 * worse than none.)
 *
 * WHAT IT ASSERTS
 *   A  a URL is REFUSED on the catalogue create, the sentence is on screen, INSIDE
 *      the viewport, and there is NO way past it — no override button.
 *   B  the JaJa Noir packet (`2024VL099B`) is still objected to AND still has its
 *      override. That packet cost an hour in August; this guard must not take it
 *      back. This is the assertion that makes the first one safe.
 *   C  at the TILL, a scanned QR does not stop the sale: the item lands in the
 *      cart, the code is not saved, and the toast says which of those happened.
 *      The old catch showed "link failed" and left the cart EMPTY, because
 *      addToCart sat after the bind inside the same try.
 *
 * It creates nothing: A and B are both refusals, and C links to a product that
 * already exists and never commits a sale.
 *
 * RUN  NODE_PATH=<dir with playwright> node scripts/prove-a-qr-is-not-a-barcode.js
 */
'use strict';
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
const USER = process.env.BANCO_USER || 'ralph', PASS = process.env.BANCO_PASS || 'ralph';
let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) { console.error('playwright not found — set NODE_PATH'); process.exit(2); }

let pass = 0, fail = 0;
const ok  = (l, d) => { pass++; console.log(`  ✅ ${l}${d ? '  — ' + d : ''}`); };
const bad = (l, d) => { fail++; console.log(`  ❌ ${l}${d ? '  — ' + d : ''}`); };
const check = (c, l, d) => { (c ? ok : bad)(l, d); return !!c; };
const head = t => console.log(`\n${t}\n${'-'.repeat(t.length)}`);

async function login(p) {
  await p.goto(`${ROOT}/pos`, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('button:has-text("Login")', { timeout: 20000 });
  await p.click('button:has-text("Login")');
  await p.waitForSelector('#username', { timeout: 12000 }).catch(() => null);
  if (await p.$('#username')) {
    await p.fill('#username', USER); await p.fill('#password', PASS);
    await p.click('#kc-login, input[type=submit]');
    await p.waitForURL('**/pos/**', { timeout: 20000 }).catch(() => null);
  }
  for (let i = 0; i < 60; i++) {
    const t = await p.evaluate(() => sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token')).catch(() => null);
    if (t) return;
    await p.waitForTimeout(250);
  }
  throw new Error('login produced no token');
}
const alpine = p => p.waitForFunction(() => {
  const el = document.querySelector('[x-data]');
  try { return !!(el && window.Alpine && Alpine.$data(el)); } catch (e) { return false; }
}, null, { timeout: 20000 }).catch(() => {});

/** THE BOX ITSELF, NOT "SOMETHING ON THE PAGE CONTAINS THE WORD".
 *  The first cut of this searched every div for the text and PASSED by matching a
 *  wrapper whose textContent was the entire modal — a green tick over a refusal it
 *  had never actually found (LESSON #5, in a harness written the same hour as the
 *  fix). Named selector, and the rectangle measured against the viewport, because
 *  isVisible() means "in the DOM and not display:none" and returned TRUE for a
 *  refusal sitting 322px below the fold on 2026-08-28. */
const refusalBox = (p, sel) => p.evaluate((s) => {
  const el = document.querySelector(s);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { text: (el.textContent || '').replace(/\s+/g, ' ').trim(),
           top: Math.round(r.top), h: Math.round(r.height),
           inView: r.height > 0 && r.top >= 0 && r.top < window.innerHeight };
}, sel);

/** A toast is its own element and fades; find it by its own text, in the viewport. */
const toastText = (p, re) => p.evaluate((src) => {
  const rx = new RegExp(src, 'i');
  for (const el of document.querySelectorAll('div,span,p')) {
    if (el.children.length > 1) continue;
    const t = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || !rx.test(t)) continue;
    const r = el.getBoundingClientRect();
    if (r.height > 0 && r.top >= 0 && r.top < window.innerHeight) return t.slice(0, 220);
  }
  return null;
}, re.source || re);

/** IS THE OVERRIDE BUTTON ACTUALLY OFFERED. `page.$('button:has-text(...)')`
 *  finds it either way — it lives in the DOM inside an x-show block that is merely
 *  display:none — so asking that way says "yes" on both screens and means nothing.
 *  The question is whether a finger can hit it, which is a rectangle. */
const overrideOffered = (p) => p.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    if (!/That IS the code on the packet/i.test(b.textContent || '')) continue;
    const r = b.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return true;
  }
  return false;
});

async function tryCreate(p, barcode, tag) {
  await p.goto(`${ROOT}/pos/catalog?lang=en`, { waitUntil: 'domcontentloaded' });
  await alpine(p);
  await p.waitForTimeout(1200);
  await p.locator('button:has-text("New product")').first().click();
  await p.waitForTimeout(800);
  await p.evaluate(([bc, t]) => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.form.name = 'ZZPROBE ' + t + ' ' + Date.now();
    d.form.price = '2.50';
    d.form.barcode = bc;
  }, [barcode, tag]);
  await p.waitForTimeout(300);
  await p.locator('button.btn-success:visible', { hasText: 'Create product' }).first().click();
  await p.waitForTimeout(1800);
}

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1100, height: 1000 } })).newPage();
  try {
    await login(p);

    head('A · a scanned QR is refused, and says so where the button is');
    await tryCreate(p, 'https://vqr.vc/BiWfnR9bv', 'QR trap');
    const box = await refusalBox(p, '[x-show="saveError"]');
    check(box && box.h > 0 && /WEB LINK/i.test(box.text),
          'the refusal names a WEB LINK, in its own box',
          box ? box.text.slice(0, 110) : 'the saveError box is not on the page');
    check(box && box.inView, 'and it is INSIDE the viewport, not below the fold',
          box ? `top ${box.top}px · height ${box.h}px` : '');
    check(/blank/i.test((box && box.text) || ''), 'and it says what to do instead',
          'leave the barcode blank — there is no stripe on the packet to go and find');
    check(await overrideOffered(p) === false,
          'there is NO way past it',
          'a shop may need an odd code; no shop has ever needed https:// as one');
    check(await p.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).modalOpen === true),
          'the form is still open, so nothing was saved behind the refusal');

    head('B · and the JaJa Noir packet still saves — the guard this must not take back');
    await tryCreate(p, '2024VL099B', 'JaJa lot');
    const lotBox = await refusalBox(p, '[x-show="codeObjection"]');
    check(lotBox && lotBox.h > 0 && /LOT or BATCH/i.test(lotBox.text),
          'the lot-number objection still fires, in its own box',
          lotBox ? lotBox.text.slice(0, 100) : 'the codeObjection box is not on the page');
    check(await overrideOffered(p) === true,
          'and it STILL offers the way past — a real button, with a rectangle',
          '2024VL099B is a real printed code — one hour was lost to this packet in August');

    head('C · at the till, a scanned QR does not stop the sale');
    await p.goto(`${ROOT}/pos/scan?lang=en`, { waitUntil: 'domcontentloaded' });
    await alpine(p);
    await p.waitForTimeout(1200);
    const res = await p.evaluate(async () => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      const r = await API.get('/api/v1/pos/products?limit=1&is_active=true');
      const prod = (r.items || r.products || r)[0];
      if (!prod) return { err: 'no product to link to' };
      const before = (d.cart || []).length;
      d.lazyBarcode = 'https://vqr.vc/BiWfnR9bv';
      d.lazyQty = 1;
      await d.linkToExisting(prod);
      await new Promise(r2 => setTimeout(r2, 600));
      return { before, after: (d.cart || []).length, name: prod.name, id: prod.id };
    });
    if (res.err) { bad('could not reach a product to link to', res.err); }
    else {
      check(res.after === res.before + 1, 'the item still goes in the cart',
            `cart ${res.before} -> ${res.after} · "${res.name}" — it used to stay empty`);
      const toast = await toastText(p, /WEB LINK|not saved/);
      check(toast !== null, 'and the toast says the code was NOT saved',
            toast ? toast.slice(0, 130) : 'no readable toast — it used to say only "link failed"');
      const bound = await p.evaluate(async (id) => {
        const fresh = await API.get(`/api/v1/pos/products/${id}`);
        return fresh.barcode || '';
      }, res.id);
      check(!/^https?:/i.test(bound), 'and the product did NOT take the link as its code',
            `barcode is now "${bound}"`);
    }
  } catch (e) {
    bad('the run itself', e.message);
  } finally { await b.close(); }

  console.log('\n' + '='.repeat(66));
  console.log(`  ${pass} pass · ${fail} fail`);
  console.log('='.repeat(66) + '\n');
  process.exit(fail ? 1 : 0);
})();
