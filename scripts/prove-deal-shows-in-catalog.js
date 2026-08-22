// The deal must be readable on the CATALOG row, and a tier saved in the wrong MODE must look
// different from a right one.
//
// Angel, 2026-08-21: "I am in the catalog view and here too would be nice to show the bundle
// pricing." Third screen with the same hole — the shelf row and the bench card already showed it.
// The price was never the whole price once a product carries a deal, and on a shelf of 45 papers
// the ones MISSING a deal are the work while looking exactly like the ones that were finished.
//
// The wrong-mode case is the one that matters most: "3 for 5.00" saved as per_unit rings CORRECTLY
// at three and wrongly at four, so testing it the obvious way says it is fine.
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT) &&
    process.env.BANCO_ALLOW_CATALOG_WRITES !== '1') {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates products.`);
  process.exit(2);
}
let _s = 0;
function gtin(pre, len) {
  const need = len - 1 - pre.length;
  const u = (String(Date.now()) + String(_s++)).slice(-need).padStart(need, '0');
  const b = pre + u;
  const t = [...b].map(Number).reverse().reduce((a, x, i) => a + x * (i % 2 === 0 ? 3 : 1), 0);
  return b + String((10 - t % 10) % 10);
}
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };
const made = [];

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1200, height: 1050 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 150)));
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  const RUN = Date.now();
  const seeds = [
    ['ZZPROBE Smoking KS green ' + RUN, [{ min_qty: 3, unit_price: '5.00' }], 'bundle'],
    ['ZZPROBE Elements Zushi ' + RUN, [{ min_qty: 3, unit_price: '5.00' }], 'per_unit'],
    ['ZZPROBE Gizeh plain ' + RUN, null, null],
  ];
  for (let i = 0; i < seeds.length; i++) {
    const [name, tiers, mode] = seeds[i];
    const r = await p.evaluate(async ([sku, name, code, tiers, mode]) => {
      const body = { sku, name, barcode: code, price: 2.00, stock_quantity: 1, category: 'Rolling Papers' };
      if (tiers) { body.price_tiers = tiers; body.tier_mode = mode; }
      try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true', body) }; }
      catch (e) { return { ok: false, detail: (e && e.message) || String(e) }; }
    }, [`ZZPROBE-CAT-${RUN}-${i}`, name, gtin('841477', 13), tiers, mode]);
    if (!r.ok) { console.error('seed failed:', r.detail); process.exit(1); }
    made.push(r.body.id);
  }

  await p.goto(ROOT + '/pos/catalog');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1200);
  await p.locator('input[placeholder*="Name"], input[type=text]').first().fill('ZZPROBE');
  await p.waitForTimeout(2500);
  const t = await p.locator('body').innerText();

  console.log('\nthe catalog row must say what the deal is');
  ok('a proper bundle reads "3 for 5.00"', /🏷️\s*3 for 5\.00/.test(t));
  // REVISED 2026-08-22. This used to assert the wrong-mode row read "3+ @ 5.00 ea" — literally
  // true of per_unit, and the exact sentence that let four bad rows reach the shop unnoticed. It
  // claims 15.00 for three while the till charges 5.00, so it is not a quieter deal label, it is
  // a false one. tierWarning() now REPLACES it. The row must still look different from a good
  // one — that part of the original intent stands — it must just not look like a deal.
  ok('the SAME tier in the wrong mode no longer reads as a deal', !/🏷️\s*3\+\s*@\s*5\.00 ea/.test(t));
  ok('...it reads as a warning instead', /costs MORE than one/i.test(t));
  // Count the DEAL CHIP by its class, not by the emoji: the category badge uses 🏷️ too, so my
  // first version of this assertion counted those and failed against working code.
  const chips = await p.$$eval('.chip-deal', els => els.filter(e => e.offsetParent).map(e => e.textContent.trim()));
  ok('exactly ONE row carries a deal chip — the mis-saved one lost it', chips.length === 1);
  ok('the price is still there', /CHF\s*2\.00/.test(t));

  console.log('\npageerrors: ' + errs.length + ' ' + (errs[0] || ''));
  ok('no javascript errors', errs.length === 0);

  for (const id of made) await p.evaluate(async (i) => {
    try { await API.put('/api/v1/pos/products/' + i + '?allow_nonstandard=true', { barcode: null }); } catch (e) {}
    try { await API.delete('/api/v1/pos/products/' + i); } catch (e) {}
  }, id);
  console.log('\n' + '='.repeat(48) + `\n  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
