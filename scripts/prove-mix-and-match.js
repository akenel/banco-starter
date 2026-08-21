/*
 * MIX AND MATCH — three different King Size papers must ring as one "3 for 5.00".
 *
 * 2026-08-21. Angel: "if they buy 2 Gizeh rolls and 1 other roll, at checkout they would end up
 * paying 12 — this is a nasty issue and affects all the papers, rolls and others with tier
 * pricing." A customer does not buy three of one paper; they buy a Smoking, a Raw and an OCB.
 *
 * His own rule became the design: "if the paper has tier pricing then they can mix." The deal
 * terms ARE the group — no roll list, no paper list, nothing to maintain, and a roll can never
 * pool with a paper because 10.00 ≠ 5.00.
 *
 * ⚠️  THIS SCRIPT RINGS REAL COMPLETED SALES. A completed transaction is a line in the
 *     Kassenbuch. Never point it at the shop's books. Guarded behind BANCO_ALLOW_FAKE_SALES=1
 *     and refuses any host that is not localhost.
 *
 * RUN
 *   BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=<dir with playwright> node scripts/prove-mix-and-match.js
 */
'use strict';
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT)) {
  console.error(`REFUSING: ${ROOT} is not localhost. This script rings completed sales.`);
  process.exit(2);
}
if (process.env.BANCO_ALLOW_FAKE_SALES !== '1') {
  console.log(require('fs').readFileSync(__filename, 'utf8').split('*/')[0]);
  console.error("REFUSING: set BANCO_ALLOW_FAKE_SALES=1 to run. Never on a shop's live books.");
  process.exit(2);
}
let _s = 0;
function gtin(pre, len) {
  const n = len - 1 - pre.length;
  const u = (String(Date.now()) + String(_s++)).slice(-n).padStart(n, '0');
  const b = pre + u;
  const t = [...b].map(Number).reverse().reduce((a, x, i) => a + x * (i % 2 === 0 ? 3 : 1), 0);
  return b + String((10 - t % 10) % 10);
}
let pass = 0, fail = 0;
const ok = (n, c, extra) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n + (extra ? '  ' + extra : ''))); };
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
  // three PAPERS on "3 for 5.00", two ROLLS on "3 for 10.00" — the rolls prove pools stay apart
  const seed = async (i, name, price, deal) => {
    const code = gtin('841477', 13);
    const r = await p.evaluate(async ([sku, name, code, price, deal]) => {
      try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true',
        { sku, name, barcode: code, price, stock_quantity: 50, category: 'Rolling Papers',
          price_tiers: [{ min_qty: 3, unit_price: deal }], tier_mode: 'bundle' }) }; }
      catch (e) { return { ok: false, detail: (e && e.message) || String(e) }; }
    }, [`ZZPROBE-MM-${RUN}-${i}`, `${name} ${RUN}`, code, price, deal]);
    if (!r.ok) { console.error('seed failed:', r.detail); process.exit(1); }
    made.push(r.body.id);
    return { code, id: r.body.id };
  };
  const P1 = await seed(0, 'ZZPROBE Smoking KS green', 2.00, '5.00');
  const P2 = await seed(1, 'ZZPROBE Raw KS brown',     2.00, '5.00');
  const P3 = await seed(2, 'ZZPROBE OCB KS Bamboo',    2.00, '5.00');
  const R1 = await seed(3, 'ZZPROBE Smoking Rolls red', 4.00, '10.00');
  const R2 = await seed(4, 'ZZPROBE Raw Rolls slim',    4.00, '10.00');

  // Ring a REAL sale of the given products and return what the drawer took.
  const sell = async (items) => {
    return await p.evaluate(async (items) => {
      const lines = items.map(([id, qty]) => ({ product_id: id, quantity: qty }));
      // client_uuid is the idempotency key — a fresh one per basket, or the server adopts the
      // FIRST sale again and every assertion after the first would read a stale total.
      const uuid = crypto.randomUUID();
      const sale = await API.post('/api/v1/pos/sales', {
        client_uuid: uuid, lines, payment_method: 'cash', amount_tendered: 500,
      });
      // Read the LINES back from the transaction, not from the create response — the receipt,
      // the VAT split and the Kassenbuch are all per line, so a pooled price that only exists as
      // a basket total would be untraceable on paper. (The create response carries no lines.)
      const full = await API.get('/api/v1/pos/transactions/' + sale.id);
      const rows = full.line_items || full.lines || full.items || [];
      return { total: Number(sale.total), id: sale.id,
               lines: rows.map(l => Number(l.line_total)) };
    }, items);
  };

  console.log('\n① three DIFFERENT papers — the basket that started this');
  let s = await sell([[P1.id, 1], [P2.id, 1], [P3.id, 1]]);
  ok('the drawer takes 5.00, not 6.00', s.total === 5, `got ${s.total}`);
  ok('the money is split across all three lines, summing exactly',
     s.lines.length === 3 && Math.abs(s.lines.reduce((a, x) => a + x, 0) - 5) < 0.005,
     JSON.stringify(s.lines));

  console.log('\n② two of one paper + one of another');
  s = await sell([[P1.id, 2], [P2.id, 1]]);
  ok('still 5.00', s.total === 5, `got ${s.total}`);

  console.log("\n③ FOUR mixed papers — Ralph's rule across the mix");
  s = await sell([[P1.id, 2], [P2.id, 1], [P3.id, 1]]);
  ok('5.00 + 2.00 = 7.00', s.total === 7, `got ${s.total}`);

  console.log('\n④ two papers only — no deal yet');
  s = await sell([[P1.id, 1], [P2.id, 1]]);
  ok('4.00, the deal has not been reached', s.total === 4, `got ${s.total}`);

  console.log('\n⑤ ROLLS and PAPERS in one basket must NOT pool together');
  s = await sell([[P1.id, 1], [P2.id, 1], [P3.id, 1], [R1.id, 1], [R2.id, 1]]);
  ok('papers 5.00 + two rolls at 4.00 = 13.00', s.total === 13, `got ${s.total}`);

  console.log('\n⑥ three rolls, mixed');
  s = await sell([[R1.id, 2], [R2.id, 1]]);
  ok('10.00', s.total === 10, `got ${s.total}`);

  console.log('\n⑦ a single paper is untouched');
  s = await sell([[P1.id, 1]]);
  ok('2.00', s.total === 2, `got ${s.total}`);

  console.log('\npageerrors: ' + errs.length + ' ' + (errs[0] || ''));
  ok('no javascript errors', errs.length === 0);

  for (const id of made) await p.evaluate(async (i) => {
    try { await API.put('/api/v1/pos/products/' + i + '?allow_nonstandard=true', { barcode: null }); } catch (e) {}
    try { await API.delete('/api/v1/pos/products/' + i); } catch (e) {}
  }, id);
  console.log(`(cleanup: ${made.length} fixture row(s) deactivated; the test SALES remain, as sales must)`);
  console.log('\n' + '='.repeat(52) + `\n  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
