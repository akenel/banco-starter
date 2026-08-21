// One product, two barcodes, both scanned onto the same shelf. Fix the price on one twin and
// BOTH must redraw.
//
// Angel, 2026-08-21, working a live shelf: "sometimes I change the price, save it, and it shows
// the old price… but I think it actually has the new price — minor bug IMHO." He was right about
// the data and generous about the bug. His screenshot had `716165286707 · ITEM-0088` at CHF 3.00
// and `42239512 · ITEM-0088` still at ⚑ 999.99 — the same SKU, the same product, one row updated.
//
// Cause was mine, from the recheck added that morning: .find() returns the FIRST row with that
// product_id and updated only it. A product legitimately carrying two barcodes appears on this
// list twice, which is correct — he scanned two packets.
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT) &&
    process.env.BANCO_ALLOW_CATALOG_WRITES !== '1') {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates products.`);
  process.exit(2);
}
let _seq = 0;
function gtin(prefix, length) {
  const need = length - 1 - prefix.length;
  const uniq = (String(Date.now()) + String(_seq++)).slice(-need).padStart(need, '0');
  const body = prefix + uniq;
  const total = [...body].map(Number).reverse().reduce((a, x, i) => a + x * (i % 2 === 0 ? 3 : 1), 0);
  return body + String((10 - total % 10) % 10);
}
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };
const made = [];

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1200, height: 1100 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 160)));
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }

  const RUN = Date.now();
  const primary = gtin('716165', 13);
  const alias   = gtin('422395', 13);

  const prod = await p.evaluate(async ([sku, code]) => {
    try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true',
      { sku, name: 'ZZPROBE Gizeh Filter Tips Regular ' + sku, barcode: code,
        price: 999.99, stock_quantity: 1, category: 'Unsorted' }) }; }
    catch (e) { return { ok: false, detail: (e && e.message) || String(e) }; }
  }, ['ZZPROBE-TWIN-' + RUN, primary]);
  if (!prod.ok) { console.error('seed failed:', prod.detail); process.exit(1); }
  made.push(prod.body.id);

  const aliased = await p.evaluate(async ([id, code]) => {
    try { return { ok: true, body: await API.post(`/api/v1/pos/products/${id}/barcodes`, { barcode: code }) }; }
    catch (e) { return { ok: false, detail: (e && e.message) || String(e) }; }
  }, [prod.body.id, alias]);
  ok('a second barcode can be bound to one product', aliased.ok === true);

  await p.goto(ROOT + '/pos/shelf-intake');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1000);
  await p.evaluate(() => localStorage.removeItem('banco_shelf_intake_v1'));
  await p.reload(); await p.waitForTimeout(1200);
  await p.locator('textarea').first().fill(primary + '\n' + alias);
  await p.locator('button:has-text("Triage the shelf")').click();
  await p.waitForTimeout(3500);

  const rows = () => p.evaluate(() => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    return (d.result.known || []).map(k => ({ barcode: k.barcode, price: k.price, pid: k.product_id }));
  });

  console.log('\n1 · both scanned codes land as their own row');
  let r = await rows();
  ok('two rows on the shelf', r.length === 2);
  ok('both point at ONE product', r.length === 2 && r[0].pid === r[1].pid);
  ok('each keeps the code it was scanned as',
     r.some(x => x.barcode === primary) && r.some(x => x.barcode === alias));

  console.log('\n2 · the list says so, instead of looking like a duplicate');
  const body = await p.locator('body').innerText();
  ok('the twin badge is on the row', /same product as 1 other row/i.test(body));

  console.log('\n3 · THE BUG: fix one twin, both must redraw');
  await p.evaluate(async () => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    const k = d.unfinishedKnown()[0];
    d.startPrice(k); k.newPrice = '3.00';
    await d.savePrice(k);
  });
  await p.waitForTimeout(2500);
  r = await rows();
  ok('the row you edited shows 3.00', r.length === 2 && Number(r[0].price) === 3);
  ok('THE TWIN shows 3.00 too — not the old 999.99',
     r.length === 2 && r.every(x => Number(x.price) === 3));
  ok('neither row had its scanned barcode rewritten',
     r.some(x => x.barcode === primary) && r.some(x => x.barcode === alias));

  console.log('\npageerrors: ' + errs.length + ' ' + (errs[0] || ''));
  ok('no javascript errors (duplicate x-for keys would show here)', errs.length === 0);

  for (const id of made) {
    await p.evaluate(async (i) => {
      try { await API.put('/api/v1/pos/products/' + i + '?allow_nonstandard=true', { barcode: null }); } catch (e) {}
      try { await API.delete('/api/v1/pos/products/' + i); } catch (e) {}
    }, id);
  }
  console.log(`(cleanup: ${made.length} fixture row(s) deactivated)`);
  console.log('\n' + '='.repeat(50));
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
