// "3 for 10" on 46 rolls, one tap a row — and the tap must write what a shopkeeper MEANT.
//
// 2026-08-21, Angel, before straightening every roll in the shop: "if you give me the EANs I could
// quickly go through them via the shelf intake and fix them all manually so each roll is 4 CHF even,
// and I could set the 3 packs for 10 tier pricing." The price was already two taps; the deal was six.
//
// The assertion that matters most is the LAST one: the deal must be stored as tier_mode 'bundle'.
// Five products on that shelf carry "3 for 5.00" written as per_unit, and they only ring correctly
// because the pricing service rescues them at the till. This must not add a sixth.
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
  const p = await (await b.newContext({ viewport: { width: 1250, height: 1100 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 160)));
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  const RUN = Date.now();
  const codes = [gtin('716165', 13), gtin('841477', 13), gtin('803275', 13)];
  const names = ['ZZPROBE Raw Rolls Classic', 'ZZPROBE Smoking Rolls organic', 'ZZPROBE RS Rolls Blau'];
  for (let i = 0; i < 3; i++) {
    const r = await p.evaluate(async ([sku, name, code]) => {
      try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true',
        { sku, name, barcode: code, price: 3.20, stock_quantity: 1, category: 'Unsorted' }) }; }
      catch (e) { return { ok: false, detail: (e && e.message) || String(e) }; }
    }, [`ZZPROBE-DEAL-${RUN}-${i}`, `${names[i]} ${RUN}`, codes[i]]);
    if (!r.ok) { console.error('seed failed:', r.detail); process.exit(1); }
    made.push(r.body.id);
  }

  await p.goto(ROOT + '/pos/shelf-intake');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1000);
  await p.evaluate(() => localStorage.removeItem('banco_shelf_intake_v1'));
  await p.reload(); await p.waitForTimeout(1200);
  await p.locator('textarea').first().fill(codes.join('\n'));
  await p.locator('button:has-text("Triage the shelf")').click();
  await p.waitForTimeout(3500);

  console.log('\n1 · the rule is off until you set it');
  ok('no apply button before a rule exists',
     !(await p.locator('button:has-text("🏷️ Apply")').first().isVisible().catch(() => false)));

  console.log('\n2 · set it once for the whole shelf');
  await p.locator('button:has-text("Set one rule for this whole shelf")').click();
  await p.waitForTimeout(400);
  await p.evaluate(() => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.dealPrice = '4.00'; d.dealQty = '3'; d.dealTotal = '10.00';
  });
  await p.waitForTimeout(500);
  ok('an apply button appears on the rows',
     await p.locator('button:has-text("🏷️ Apply")').first().isVisible());

  console.log('\n3 · a deal that is not a discount is called out');
  await p.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).dealTotal = '12.00'; });
  await p.waitForTimeout(400);
  ok('3 × 4.00 = 12.00 is flagged as no discount',
     /is not a discount/i.test(await p.locator('body').innerText()));
  await p.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).dealTotal = '10.00'; });
  await p.waitForTimeout(400);

  console.log('\n4 · one tap does the whole row');
  await p.locator('button:has-text("🏷️ Apply")').first().click();
  await p.waitForTimeout(2500);
  const after = await p.evaluate(async (id) => {
    const r = await API.get('/api/v1/pos/products/' + id);
    return { price: r.price, tiers: r.price_tiers, mode: r.tier_mode };
  }, made[0]);
  ok('the price is 4.00', Number(after.price) === 4);
  ok('the deal is stored as 3 for 10.00',
     Array.isArray(after.tiers) && after.tiers.length === 1 &&
     Number(after.tiers[0].min_qty) === 3 && Number(after.tiers[0].unit_price) === 10);
  ok('stored as BUNDLE, not per_unit — say what a shopkeeper means', after.mode === 'bundle');

  console.log('\n5 · and the till charges what it says');
  const rung = await p.evaluate(async (id) => {
    const r = await API.get('/api/v1/pos/products/' + id); return r;
  }, made[0]);
  ok('reads back consistently', Number(rung.price) === 4 && rung.tier_mode === 'bundle');
  ok('the row shows it applied', /✓ Done/.test(await p.locator('body').innerText()));

  console.log('\n6 · the untouched rows are untouched');
  const other = await p.evaluate(async (id) => await API.get('/api/v1/pos/products/' + id), made[1]);
  ok('a row you did not tap keeps its old price', Number(other.price) === 3.2);
  ok('and has no deal', !other.price_tiers || other.price_tiers.length === 0);

  console.log('\npageerrors: ' + errs.length + ' ' + (errs[0] || ''));
  ok('no javascript errors', errs.length === 0);

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
