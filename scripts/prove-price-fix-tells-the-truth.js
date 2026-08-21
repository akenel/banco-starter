// The till's manager price-fix panel must say what the SERVER said, and must show what a
// customer will pay before anything is written.
//
// 2026-08-21. Angel, on a CHF 1.50 OCB paper, typed price 2.00 and "buy 3 for 5" with the
// "price is for the whole pack" box unticked. Unticked means per_unit — "buy 3 or more and they
// cost 5.00 EACH" — which is a price RISE, and the server refused it with a precise sentence:
//
//   Invalid price tiers: the first tier must start at min_qty 1 (the base price)
//
// The panel threw that away and printed "you may not have permission." He is the owner of the
// shop. He went hunting a rights problem that did not exist. A generic error is worse than no
// error, because it sends the person somewhere else entirely.
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
  const p = await (await b.newContext({ viewport: { width: 1150, height: 1100 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 160)));
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  const code = gtin('301048', 13);
  const prod = await p.evaluate(async ([sku, code]) => {
    try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true',
      { sku, name: 'ZZPROBE OCB Slim Virgin ' + sku, barcode: code, price: 1.50,
        stock_quantity: 5, category: 'Rolling Papers' }) }; }
    catch (e) { return { ok: false, detail: (e && e.message) || String(e) }; }
  }, ['ZZPROBE-PF-' + Date.now(), code]);
  if (!prod.ok) { console.error('seed failed:', prod.detail); process.exit(1); }
  made.push(prod.body.id);

  await p.goto(ROOT + '/pos/scan');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1500);

  // open the panel on this product, exactly as the detail modal does
  await p.evaluate((prod) => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.detailProduct = prod; d.openPriceEdit();
  }, prod.body);
  await p.waitForTimeout(600);

  console.log("\n1 · Angel's exact input: 2.00, buy 3 for 5, box UNTICKED");
  await p.evaluate(() => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.priceEdit.price = '2'; d.priceEdit.bundle = false;
    d.priceEdit.tiers = [{ min_qty: '3', unit_price: '5' }];
  });
  await p.waitForTimeout(500);
  let body = await p.locator('body').innerText();
  ok('it warns BEFORE saving that this is a price rise', /price RISE, not a deal/i.test(body));
  ok('it names the fix — tick the box', /price is for the whole pack/i.test(body) && /Tick the box/i.test(body));

  console.log('\n2 · save it anyway — the message must be the SERVER\'s');
  await p.evaluate(async () => { await Alpine.$data(document.querySelector('[x-data]')).savePriceEdit(); });
  await p.waitForTimeout(1200);
  body = await p.locator('body').innerText();
  ok('shows the real reason', /first tier must start at min_qty 1/i.test(body));
  ok('does NOT blame permissions', !/may not have permission/i.test(body));

  console.log('\n3 · tick the box — the preview shows what a customer pays');
  await p.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).priceEdit.bundle = true; });
  await p.waitForTimeout(500);
  body = await p.locator('body').innerText();
  ok('the price-rise warning clears', !/price RISE/i.test(body));
  ok('1 → 2.00', /1\s*→\s*CHF\s*2\.00/.test(body));
  ok('3 → 5.00 (the deal)', /3\s*→\s*CHF\s*5\.00/.test(body));
  ok("4 → 7.00 (Ralph's rule, not 6.67)", /4\s*→\s*CHF\s*7\.00/.test(body));

  console.log('\n4 · and now it saves');
  await p.evaluate(async () => { await Alpine.$data(document.querySelector('[x-data]')).savePriceEdit(); });
  await p.waitForTimeout(1500);
  const after = await p.evaluate(async (id) => await API.get('/api/v1/pos/products/' + id), made[0]);
  ok('price 2.00 stored', Number(after.price) === 2);
  ok('stored as a bundle', after.tier_mode === 'bundle');
  ok('3 for 5.00 stored', after.price_tiers && Number(after.price_tiers[0].unit_price) === 5);

  console.log('\npageerrors: ' + errs.length + ' ' + (errs[0] || ''));
  ok('no javascript errors', errs.length === 0);
  for (const id of made) {
    await p.evaluate(async (i) => {
      try { await API.put('/api/v1/pos/products/' + i + '?allow_nonstandard=true', { barcode: null }); } catch (e) {}
      try { await API.delete('/api/v1/pos/products/' + i); } catch (e) {}
    }, id);
  }
  console.log('\n' + '='.repeat(50));
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
