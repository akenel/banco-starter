// The discount row on Checkout must say what the customer is being charged.
//
// WHY THIS FILE EXISTS. Layla, 2026-09-04, on the tablet: "Target Total sets 15.25% and
// None / 5% / 10% / 15% / Custom shows nothing selected. A cashier cannot tell what the
// customer is being charged."
//
// Two faults stacked, and the first one is the interesting one. A discount that arrives from
// the cart screen's TARGET TOTAL is almost never a round number — 15.25% is what "make it
// CHF 40.00" works out to — so it matched no preset, and with only equality tests in the
// markup the whole row rendered unselected. A control showing nothing selected reads as NO
// DISCOUNT, which is the opposite of the truth, in front of a customer who is waiting to hear
// the number.
//
// The second: the tests were `discount === 5` — STRICT — against a value that has been
// through parseFloat, sessionStorage and a text input on its way to this screen. A "5" out of
// storage would have failed to light the 5% chip too, and nothing would have said so.
//
// NOTHING IS EVER SOLD. The cart is built through the API, the checkout screen is opened and
// read, and the run ends. Complete is never pressed — a completed transaction is a line in the
// Kassenbuch and cannot be taken back out. The cart is emptied at the end.
const { chromium } = require('playwright');

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 895 } });   // the tablet's real one
  const p = await ctx.newPage();
  let pass = 0, fail = 0;
  const check = (ok, what, detail) => {
    if (ok) { pass++; console.log('  ✅ ' + what); }
    else { fail++; console.log('  ❌ ' + what + (detail ? '\n       ' + detail : '')); }
  };

  await p.goto('http://localhost:3000/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }

  // ── A · THE CASE THAT BROKE: A DISCOUNT NO BUTTON REPRESENTS ─────────────────────────────
  // Built the way the cashier builds it — a basket, then Target Total on the CART screen, then
  // walk to Checkout. The percentage is never typed; it is derived, and that is the point.
  console.log('\n── A · a Target Total discount, carried to Checkout ──');
  await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'load' });
  await p.waitForTimeout(2200);

  // A basket with a price that divides badly on purpose. Whatever the shop's first product
  // costs, "knock it to a round total" lands on a fractional percentage nearly every time.
  const built = await p.evaluate(async () => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    const r = await API.get('/api/v1/pos/products?limit=1&is_active=true');
    const list = Array.isArray(r) ? r : (r.items || r.products || []);
    if (!list.length) return { err: 'no products in the catalogue to put in a basket' };
    const prod = list[0];
    d.cart = [];
    d.addToCart ? d.addToCart(prod) : d.cart.push({ ...prod, quantity: 1 });
    await new Promise(r => setTimeout(r, 400));
    return { name: prod.name, price: prod.price, subtotal: d.totals && d.totals.subtotal };
  });
  check(!built.err, 'a basket with one line in it', built.err);

  if (!built.err) {
    // Target Total → a percentage nobody would type.
    const derived = await p.evaluate(async () => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      const sub = Number(d.totals.subtotal);
      // Aim a few rappen off a round figure so the percentage cannot land on 5/10/15.
      const target = (Math.floor(sub * 0.85 * 20) / 20 - 0.03).toFixed(2);
      d.discountMode = 'target';
      d.targetTotal = target;
      d.calculateDiscountFromTarget();
      await new Promise(r => setTimeout(r, 300));
      d.cartData = d.cartData || {};
      return { subtotal: sub, target: target, discount: d.discount };
    });
    const pctOf = Number(derived.discount);
    check(pctOf > 0 && ![0, 5, 10, 15].includes(pctOf),
          `Target Total CHF ${derived.target} on CHF ${derived.subtotal} works out at ${derived.discount}% — a figure no button carries`,
          'it came out at ' + derived.discount + '%, which is one of the presets — this run proves nothing');

    // Carry it over with the till's OWN handoff. Hand-building the sessionStorage payload was
    // the first version and it was wrong in the way that matters: it wrote a `discount` onto an
    // object with no `cart` in it, checkout's recalculateTotals() threw on undefined.reduce,
    // and the run reported a null breakdown. A probe that constructs its own input tests the
    // probe. goToCheckout() is the button the cashier presses.
    await p.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).goToCheckout());
    await p.waitForURL('**/pos/checkout', { timeout: 15000 });
    await p.waitForTimeout(2200);

    const row = await p.evaluate(() => {
      const btns = [...document.querySelectorAll('button')].filter(b => b.offsetParent !== null);
      const chip = t => btns.find(b => (b.textContent || '').trim().startsWith(t));
      const lit = b => !!b && /ring-2/.test(b.className);
      const d = Alpine.$data(document.querySelector('[x-data]'));
      // The custom chip is the one that opens the modal; find it by its handler, not its text,
      // because its text is the thing under test.
      const custom = btns.find(b => (b.getAttribute('@click') || b.getAttribute('x-on:click') || '') === 'customDiscount()')
                  || btns.find(b => /bg-blue-(100|300)/.test(b.className));
      return {
        model: d.discount,
        anyLit: btns.some(b => /ring-2/.test(b.className) && /bg-(gray|green|yellow|blue)-300/.test(b.className)),
        // innerText, NEVER textContent. textContent returns the hidden span too, so the
        // button read "Custom\n25%" and the check failed on a screen that was correct —
        // the harness reading something no human can see. LESSON #12, from the other side.
        customText: custom ? custom.innerText.trim() : null,
        customLit: lit(custom),
        noneLit: lit(chip('None')),
        breakdown: (document.body.innerText.match(/Discount \(([\d.]+)%\)/) || [])[1] || null,
      };
    });

    check(row.anyLit, 'something in the discount row is lit up',
          'every chip is unselected while a ' + pctOf + '% discount is being applied —'
          + ' a row that shows nothing selected reads as NO discount');
    check(row.customLit, 'and it is the Custom chip',
          'Custom is not the lit one; the row says ' + JSON.stringify(row.customText));
    check(!row.noneLit, 'and None is NOT lit',
          '"None" is highlighted while ' + pctOf + '% is coming off the price');
    check(row.customText === String(pctOf) + '%' || row.customText === pctOf.toFixed(2) + '%',
          `the chip carries the actual figure — it reads "${row.customText}"`,
          'it reads ' + JSON.stringify(row.customText) + ' while ' + pctOf + '% is applied');
    // The number on the button and the number on the price breakdown are two renderings of one
    // fact, and two renderings of one fact is how a screen ends up arguing with itself.
    check(row.breakdown && Math.abs(Number(row.breakdown) - pctOf) < 0.005,
          `and the price breakdown below says the same figure (${row.breakdown}%)`,
          'the chip says ' + row.customText + ' and the breakdown says ' + row.breakdown + '%');
  }

  // ── B · A PRESET STILL LIGHTS ITS OWN BUTTON ─────────────────────────────────────────────
  // The other half. Making Custom work is worth nothing if it stole the highlight from the
  // presets, and this is the path a cashier takes twenty times a day.
  console.log('\n── B · the presets still light, including as a STRING out of storage ──');
  for (const preset of [5, 10, 15, 0]) {
    const r = await p.evaluate(async (pc) => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      d.applyDiscount(pc);
      await new Promise(r => setTimeout(r, 250));
      const btns = [...document.querySelectorAll('button')].filter(b => b.offsetParent !== null);
      const label = pc === 0 ? 'None' : pc + '%';
      const own = btns.find(b => (b.textContent || '').trim() === label);
      return { lit: !!own && /ring-2/.test(own.className), found: !!own,
               others: btns.filter(b => /ring-2/.test(b.className)).length };
    }, preset);
    check(r.found && r.lit && r.others === 1,
          `${preset === 0 ? 'None' : preset + '%'} lights its own button, and only it`,
          r.found ? `lit=${r.lit}, and ${r.others} chips are highlighted at once` : 'no such button on screen');
  }

  // THE STRING CASE. sessionStorage and the till's own percent box both hand this screen a
  // string; `discount === 5` is false for "5" and the chip would go dark with the discount
  // fully applied. Nothing on the screen would say so — which is why it is worth a check
  // rather than an assumption.
  const str = await p.evaluate(async () => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.discount = '10';                       // exactly what comes back out of storage
    await new Promise(r => setTimeout(r, 250));
    const own = [...document.querySelectorAll('button')].find(b => (b.textContent || '').trim() === '10%');
    return { lit: !!own && /ring-2/.test(own.className) };
  });
  check(str.lit, 'and a discount that arrives as the STRING "10" lights the 10% chip too',
        'the chip is dark while 10% is applied — `discount === 10` is false for "10"');

  // ── C · AND THE CEILING LINE ONLY SPEAKS WHEN THERE IS A CEILING ─────────────────────────
  // Same report: "Your max discount: 100%" is developer copy on a cashier's screen. An owner
  // has no cap, so the line was announcing the absence of a limit.
  console.log('\n── C · "Your max discount: 100%" is gone ──');
  const cap = await p.evaluate(async () => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    const out = {};
    d.maxDiscount = 100;
    await new Promise(r => setTimeout(r, 250));
    out.at100 = document.body.innerText;
    d.maxDiscount = 15;
    await new Promise(r => setTimeout(r, 250));
    out.at15 = document.body.innerText;
    return out;
  });
  check(!/100%/.test(cap.at100.split('\n').filter(l => /max|give up to/i.test(l)).join(' ')),
        'an owner with no cap is told nothing about a ceiling',
        'the screen still says: ' + cap.at100.split('\n').filter(l => /max|give up to/i.test(l)).join(' · '));
  check(/give up to 15%|15%/.test(cap.at15.split('\n').filter(l => /give up to/i.test(l)).join(' ')),
        'and a cashier who HAS a ceiling is told what it is, in words',
        'the capped screen says: ' + JSON.stringify(cap.at15.split('\n').filter(l => /give up to|max/i.test(l))));
  check(!/Your max discount/i.test(cap.at15),
        'and the developer wording is gone',
        '"Your max discount:" is still on the screen');

  // ── PUT THE SHOP BACK ────────────────────────────────────────────────────────────────────
  // No sale was rung. Empty the basket so nothing is left sitting in a cashier's cart.
  await p.evaluate(() => { try { sessionStorage.removeItem('pos_cart'); } catch (e) {} });

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
