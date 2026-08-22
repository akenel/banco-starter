// The till must say WHY a line costs what it costs.
//
// 2026-08-22. Twice in one day Angel sent me a screenshot of a cart asking "is this my pricing
// issue?" — once because a pack was saved per_unit and could not pool, once because he had picked
// papers that were not all on the same deal. Both times the arithmetic was right and the screen
// showed only numbers. Numbers cannot say why.
//
// He could send me a screenshot. Layla and Mark cannot.
//
// The load-bearing case is 'apart': a line sitting NEXT TO an identical deal and priced alone,
// because one checkbox on its product record was unticked. That is the shape that cost the day,
// and it is the one a cashier has no way to diagnose from a total.
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT) &&
    process.env.BANCO_ALLOW_CATALOG_WRITES !== '1') {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates products.`);
  process.exit(2);
}
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1280, height: 1100 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 160)));
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }

  // No products created and no sale rung: dealInfo() reads a cart and nothing else.
  // Baskets are built INSIDE the page: dealInfo() and cartDeals() live in base.html's script
  // scope, so the cart has to be assembled where they can see it.
  const R = await p.evaluate(() => {
    const KS    = (n, q) => ({ name: n, quantity: q, price: 2.00, tier_mode: 'bundle',
                               price_tiers: [{ min_qty: 3, unit_price: '5.00' }] });
    const ROLL  = (n, q) => ({ name: n, quantity: q, price: 4.00, tier_mode: 'bundle',
                               price_tiers: [{ min_qty: 3, unit_price: '10.00' }] });
    const STRAY = (n, q) => ({ name: n, quantity: q, price: 2.00, tier_mode: 'per_unit',
                               price_tiers: [{ min_qty: 1, unit_price: '2.00' }, { min_qty: 3, unit_price: '5.00' }] });
    const PLAIN = (n, q) => ({ name: n, quantity: q, price: 3.50, tier_mode: 'per_unit', price_tiers: [] });
    const carts = {
      angel:    [KS('Smoking Red', 1), KS('Smoking Green', 1), KS('Greengo slim', 1)],
      twoShort: [KS('Smoking Red', 1), KS('Smoking Green', 1)],
      four:     [KS('a', 1), KS('b', 1), KS('c', 1), KS('d', 1)],
      stray:    [KS('Smoking Red', 1), KS('Smoking Green', 1), STRAY('OCB Slim', 1)],
      mixed:    [KS('a', 1), KS('b', 1), KS('c', 1), ROLL('r1', 1), ROLL('r2', 1), ROLL('r3', 1)],
      lonely:   [STRAY('OCB Slim', 2)],
      plain:    [PLAIN('Lighter', 3)],
      giveaway: [Object.assign(KS('free', 1), { is_giveaway: true })],
      solo:     [KS('Smoking Red', 4)],
    };
    const out = {};
    for (const k of Object.keys(carts)) {
      const c = carts[k];
      out[k] = { info: c.map((_, i) => dealInfo(c, i)), deals: cartDeals(c),
                 sum: Math.round(c.reduce((a, _, i) => a + cartLineTotal(c, i), 0) * 100) / 100 };
    }
    return out;
  });

  const txt = o => (o && o.text) || '';
  const nud = o => (o && o.nudge) || '';

  console.log("\nAngel's basket — three different papers, the one that rang 6.00");
  ok('it now rings 5.00', R.angel.sum === 5.00);
  ok('every line says it is in the deal', R.angel.info.every(o => o && o.state === 'pooled'));
  ok('...and names the deal', /3\s.*\s5\.00/.test(txt(R.angel.info[0])));
  ok('...and says how many are in it', /3/.test(txt(R.angel.info[0])));
  ok('the basket lists the group once', R.angel.deals.length === 1);
  ok('...with every member named', R.angel.deals[0].names.length === 3
       && R.angel.deals[0].names.includes('Greengo slim'));
  ok('...and what it saved', R.angel.deals[0].saved === 1.00);

  console.log('\ntwo papers — one short');
  ok('it says the deal is not reached', R.twoShort.info.every(o => o && o.state === 'near'));
  ok('...and what one more is worth', /\+1/.test(nud(R.twoShort.info[0])));
  ok('...naming the actual saving', /1\.00/.test(nud(R.twoShort.info[0])));
  ok('no group is claimed yet', R.twoShort.deals.length === 0);

  console.log("\nfour papers — Ralph's rule, and no false promise");
  ok('it rings 7.00', R.four.sum === 7.00);
  ok('the lines are pooled', R.four.info.every(o => o && o.state === 'pooled'));
  ok('no nudge — there is no rung above 3 to reach', R.four.info.every(o => !nud(o)));

  console.log('\nTHE ONE THAT COST THE DAY — a per_unit stray beside an identical deal');
  ok('the two eligible papers are grouped but one short',
     R.stray.info[0].state === 'near' && R.stray.info[1].state === 'near');
  ok('...and the till offers the missing one', /\+1/.test(nud(R.stray.info[0])));
  ok('the stray is called out as APART', R.stray.info[2] && R.stray.info[2].state === 'apart');
  ok('...and says why: priced per unit', /per unit/i.test(txt(R.stray.info[2])));
  ok('the basket total is honestly 6.00, not 5.00', R.stray.sum === 6.00);

  console.log('\ntwo deals at once — they must not be merged');
  ok('two separate groups', R.mixed.deals.length === 2);
  ok('papers group is 3 for 5.00', R.mixed.deals.some(d => /3\s.*\s5\.00/.test(d.label) && d.qty === 3));
  ok('rolls group is 3 for 10.00', R.mixed.deals.some(d => /3\s.*\s10\.00/.test(d.label) && d.qty === 3));
  ok('the basket rings 15.00', R.mixed.sum === 15.00);

  console.log('\nsilence where silence is right');
  // GUARD-BREAK. A till that comments on every line is a till nobody reads.
  ok('a lone per_unit ladder with no twin says nothing', R.lonely.info[0] === null);
  ok('a plain product with no ladder says nothing', R.plain.info[0] === null);
  ok('a giveaway line says nothing', R.giveaway.info[0] === null);
  ok('a giveaway is not counted as a deal', R.giveaway.deals.length === 0);

  console.log('\none product, four of it — the deal applies without a partner');
  ok('it says the deal is on', R.solo.info[0] && R.solo.info[0].state === 'solo');
  ok('...counting all four', /4/.test(txt(R.solo.info[0])));
  ok('it rings 7.00', R.solo.sum === 7.00);

  console.log('\nthe words reach the screen');
  await p.goto(ROOT + '/pos/scan'); await p.waitForLoadState('networkidle'); await p.waitForTimeout(1500);
  await p.evaluate(() => {
    const KS = (n) => ({ id: 'x' + n, name: n, quantity: 1, price: 2.00, tier_mode: 'bundle',
                         price_tiers: [{ min_qty: 3, unit_price: '5.00' }] });
    const STRAY = (n) => ({ id: 'y' + n, name: n, quantity: 1, price: 2.00, tier_mode: 'per_unit',
                            price_tiers: [{ min_qty: 1, unit_price: '2.00' }, { min_qty: 3, unit_price: '5.00' }] });
    const el = document.querySelector('[x-data]');
    const d = Alpine.$data(el);
    // Three papers so the deal actually fires, plus the stray standing outside it.
    d.cart = [KS('Smoking Red'), KS('Smoking Green'), KS('Greengo slim'), STRAY('OCB Slim')];
  });
  await p.waitForTimeout(900);
  const screen = await p.locator('body').innerText();
  ok('the deal is named on screen', /3\s.*\s5\.00/.test(screen));
  ok('the basket summary is on screen', /Deals in this basket/i.test(screen));
  ok('the stray is called out on screen', /not in the deal/i.test(screen));
  ok('...in red', await p.locator('.text-red-600', { hasText: /not in the deal/i }).first().isVisible());
  await p.screenshot({ path: '/tmp/deal-explained.png' });

  console.log('\npageerrors: ' + errs.length + ' ' + (errs[0] || ''));
  ok('no javascript errors', errs.length === 0);
  console.log('\n' + '='.repeat(52) + `\n  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
