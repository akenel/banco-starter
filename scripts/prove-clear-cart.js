// "Clear cart" has to clear the cart — including the copy the page restores itself from.
//
//   NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-clear-cart.js
//
// Angel, at a live till, 2026-08-24: "clear the cart does not work anymore ... i cleared twice
// and when i go back to cart the last item is still there even though i want to start fresh."
//
// He was right, and "twice" is the tell. `confirmClearCart()` emptied `this.cart` in memory and
// removed `pos_sale_uuid`, but never `pos_cart` — and scan.html RESTORES the cart from `pos_cart`
// on every load, for the Edit-Cart round trip. So clearing worked on screen, the stale copy sat
// in sessionStorage, and the next navigation resurrected it. Clearing a second time could not
// help: it never touched the thing being restored from.
//
// A unit test cannot see this. It only appears when you LEAVE the page and come back, and only
// after a trip to Checkout, because that is what writes `pos_cart` in the first place. That is
// two navigations and a storage layer — a browser, or nothing.
//
// The second assertion is the one Angel did NOT report: clearing must also drop
// `checkout_customer`, or the last customer's member card — and their age answer — stays attached
// to the next person's sale.
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  p.on('dialog', d => d.accept());

  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'felix'); await p.fill('#password', 'felix');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }

  await p.goto(ROOT + '/pos/scan', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1500);

  // Put a line in the cart the way the till does, then plant the two session keys the real
  // Checkout round trip leaves behind. Planting them directly is deliberate: it is exactly the
  // state the app itself creates, and it keeps the proof from depending on which products this
  // particular database happens to hold.
  await p.evaluate(() => {
    const el = document.querySelector('[x-data]');
    const d = el._x_dataStack[0];
    d.cart = [{ id: 'probe', product_id: 'probe', name: 'ZZPROBE Clear Cart', price: 2, quantity: 1, line_total: 2 }];
    sessionStorage.setItem('pos_cart', JSON.stringify({ cart: d.cart, discount: 0, totals: {}, transactionId: null }));
    sessionStorage.setItem('checkout_customer', JSON.stringify({ id: 'probe-member', handle: 'ART-PROBE', is_of_age: true }));
  });
  await p.waitForTimeout(400);
  ok('a cart and an attached member are in play', await p.evaluate(() =>
    !!sessionStorage.getItem('pos_cart') && !!sessionStorage.getItem('checkout_customer')));

  // Clear it, through the real modal.
  await p.locator('button:has-text("Clear")').first().click();
  await p.waitForTimeout(600);
  await p.locator('button:has-text("Clear it"), button:has-text("Clear")').last().click();
  await p.waitForTimeout(900);
  ok('the cart looks empty on screen', await p.evaluate(() =>
    (document.querySelector('[x-data]')._x_dataStack[0].cart || []).length === 0));

  // THE ACTUAL BUG: leave, come back. Before the fix the line returns here.
  await p.goto(ROOT + '/pos/dashboard', { waitUntil: 'networkidle' });
  await p.waitForTimeout(800);
  await p.goto(ROOT + '/pos/scan', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1800);
  const back = await p.evaluate(() => (document.querySelector('[x-data]')._x_dataStack[0].cart || []).length);
  ok(`the cart is STILL empty after leaving and coming back (found ${back} line(s))`, back === 0);
  ok('no "cart restored" toast', !/restored|wiederhergestellt|ripristinat|restauré/i.test(
    await p.evaluate(() => document.body.innerText)));

  // The half Angel did not report.
  ok('the stored cart is gone from sessionStorage',
     await p.evaluate(() => !sessionStorage.getItem('pos_cart')));
  ok('the attached member is detached, so the next sale cannot inherit their age',
     await p.evaluate(() => !sessionStorage.getItem('checkout_customer')));

  await b.close();
  console.log(`\n${fail ? '❌' : '✅'} ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})();
