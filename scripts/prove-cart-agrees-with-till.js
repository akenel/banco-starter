// The cart preview and the till must agree to the cent. "shown != charged" is the one thing
// the tier ladder exists to prevent, and Banco has TWO implementations of it — Python in
// services/pricing.py and JavaScript in base.html — so nothing but a test keeps them level.
// Compares 160 quantities across four real ladders.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
// Ask the SERVER's own pricing function, right now — do not reimplement it here and do not
// read a file someone generated earlier. Lesson 5: a script that recomputes what the server
// computes will accuse working code.
const server = JSON.parse(execFileSync('python3', ['-c', `
import sys, logging, json
sys.path.insert(0, '${process.env.BANCO_REPO || '/home/angel/repos/banco-starter'}')
logging.disable(logging.WARNING)
from decimal import Decimal
from src.services.pricing import tier_line_total
CASES = [("3 for 10", [{"min_qty":3,"unit_price":"10.00"}], "4.00", "bundle"),
         ("nested",   [{"min_qty":3,"unit_price":"10.00"},{"min_qty":10,"unit_price":"24.00"}], "4.00", "bundle"),
         ("gizeh",    [{"min_qty":1,"unit_price":"1.40"},{"min_qty":3,"unit_price":"4.00"},{"min_qty":10,"unit_price":"12.00"}], "1.40", "bundle"),
         ("3 for 5",  [{"min_qty":3,"unit_price":"5.00"}], "2.00", "bundle"),
         # PER_UNIT — the mode this suite never compared until 2026-08-21, which is the only
         # mode where the server's above-base rescue can run. Angel's OCB rows are the 4th case.
         ("pu ladder",[{"min_qty":1,"unit_price":"1.40"},{"min_qty":10,"unit_price":"1.30"},{"min_qty":50,"unit_price":"1.00"}], "1.40", "per_unit"),
         ("pu deep",  [{"min_qty":1,"unit_price":"1.50"},{"min_qty":500,"unit_price":"0.60"}], "1.50", "per_unit"),
         ("pu above", [{"min_qty":1,"unit_price":"3.50"},{"min_qty":10,"unit_price":"3.10"},{"min_qty":20,"unit_price":"2.50"}], "2.90", "per_unit"),
         ("pu OCB",   [{"min_qty":1,"unit_price":"2.00"},{"min_qty":3,"unit_price":"5.00"}], "2.00", "per_unit")]
print(json.dumps({nm: [str(tier_line_total(t, Decimal(b), q, mode=m)) for q in range(1,41)]
                  for nm, t, b, m in CASES}))
`], { encoding: 'utf8' }));
(async()=>{
  const b=await chromium.launch(); const p=await (await b.newContext()).newPage();
  await p.goto('http://localhost:3000/pos',{waitUntil:'domcontentloaded'});
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) { await p.fill('#username','ralph'); await p.fill('#password','ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**',{timeout:20000}); }
  const client = await p.evaluate(()=>{
    const CASES={"3 for 10":[[{min_qty:3,unit_price:"10.00"}],4.00,'bundle'],
                 "nested":[[{min_qty:3,unit_price:"10.00"},{min_qty:10,unit_price:"24.00"}],4.00,'bundle'],
                 "gizeh":[[{min_qty:1,unit_price:"1.40"},{min_qty:3,unit_price:"4.00"},{min_qty:10,unit_price:"12.00"}],1.40,'bundle'],
                 "3 for 5":[[{min_qty:3,unit_price:"5.00"}],2.00,'bundle'],
                 "pu ladder":[[{min_qty:1,unit_price:"1.40"},{min_qty:10,unit_price:"1.30"},{min_qty:50,unit_price:"1.00"}],1.40,'per_unit'],
                 "pu deep":[[{min_qty:1,unit_price:"1.50"},{min_qty:500,unit_price:"0.60"}],1.50,'per_unit'],
                 "pu above":[[{min_qty:1,unit_price:"3.50"},{min_qty:10,unit_price:"3.10"},{min_qty:20,unit_price:"2.50"}],2.90,'per_unit'],
                 "pu OCB":[[{min_qty:1,unit_price:"2.00"},{min_qty:3,unit_price:"5.00"}],2.00,'per_unit']};
    const out={};
    for (const k of Object.keys(CASES)) {
      const [tiers,price,mode]=CASES[k]; out[k]=[];
      for (let q=1;q<=40;q++) out[k].push(tierLineTotal({quantity:q,price,price_tiers:tiers,tier_mode:mode}).toFixed(2));
    }
    return out;
  });
  let bad=0, n=0;
  for (const k of Object.keys(server)) for (let i=0;i<40;i++){
    n++;
    if (server[k][i] !== client[k][i]) { bad++;
      if (bad<=6) console.log(`  ❌ ${k} qty ${i+1}: till ${server[k][i]} · cart ${client[k][i]}`); }
  }
  console.log(bad? `\n  ${bad} of ${n} disagree` : `\n  ✅ cart and till agree on all ${n} quantities`);

  // ── MIXED BASKETS ────────────────────────────────────────────────────────────────────
  // Pooling is implemented TWICE — allocate_pool() in Python, cartPools() in JavaScript — so
  // only a comparison keeps them level. Same shape as above: ask the server's own function.
  const mixCases = [[1,1,1],[2,1],[1,1,1,1],[2,2,1],[3,3],[1,1],[5,1,1],[1,2,3,4],[9,1]];
  const srvMix = JSON.parse(execFileSync('python3', ['-c', `
import sys, logging, json
sys.path.insert(0, '${process.env.BANCO_REPO || '/home/angel/repos/banco-starter'}')
logging.disable(logging.WARNING)
from decimal import Decimal
from src.services.pricing import allocate_pool
T = [{"min_qty": 3, "unit_price": "5.00"}]
CASES = ${JSON.stringify(mixCases)}
print(json.dumps([[str(x) for x in allocate_pool(T, Decimal("2.00"), q)] for q in CASES]))
`], { encoding: 'utf8' }));
  const cliMix = await p.evaluate((cases) => cases.map(qtys => {
    const cart = qtys.map(q => ({ quantity: q, price: 2.00, tier_mode: 'bundle',
                                  price_tiers: [{ min_qty: 3, unit_price: '5.00' }] }));
    const pools = cartPools(cart);
    return cart.map((_, i) => (i in pools ? pools[i] : tierLineTotal(cart[i])).toFixed(2));
  }), mixCases);
  let mbad = 0;
  mixCases.forEach((q, i) => {
    if (JSON.stringify(srvMix[i]) !== JSON.stringify(cliMix[i])) {
      mbad++;
      console.log(`  ❌ mix ${JSON.stringify(q)}: till ${JSON.stringify(srvMix[i])} · cart ${JSON.stringify(cliMix[i])}`);
    }
  });
  console.log(mbad ? `  ${mbad} of ${mixCases.length} mixed baskets disagree`
                   : `  ✅ cart and till agree on all ${mixCases.length} mixed baskets, line by line`);

  // ── THE HELD-ORDERS BOARD — the THIRD implementation ─────────────────────────────────
  // Found 2026-09-02 by Angel, poking at the kiosk after a test sheet. The kiosk showed a
  // customer "3× CHF 3.33 −17%" for OCB Black Slim Rolls; they added three; the cashier's
  // board quoted CHF 12.00 for a pack the shop advertises at CHF 10.00. Two francs OVER,
  // against the shop's own printed rule, on the one screen the customer never sees again.
  //
  // Cause: _kiosk_cart_payload did `price * qty` and never looked at price_tiers. This
  // suite compared the till to the cart preview and never asked the third screen — the
  // exact shape of LESSON #6, "a harness cannot see what it never constructs".
  let hbad = 0, hn = 0;
  try {
    const held = await p.evaluate(async () => {
      const tok = sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token');
      const H = { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' };
      // /products does not expose price_tiers at all — the first version of this
      // check asked it, found nothing, and printed "not checked" while a real
      // pricing bug sat in production. A discovery step that cannot find its
      // subject is a test that always passes.
      //
      // /catalog/price-check DOES list every tiered row — and on the demo stack it
      // returns ZERO, because every tiered product there is inactive. So the local
      // stack could never exercise tier pricing end to end, which is exactly why
      // this class of bug only ever showed up on the shop. BUILD THE SUBJECT: mint
      // a ZZPROBE product with a real ladder, use it, and deactivate it after.
      let list = ((await (await fetch('/api/v1/pos/catalog/price-check', { headers: H })).json()).items || [])
        .filter(x => Array.isArray(x.price_tiers) && x.price_tiers.length);
      const minted = [];
      if (!list.length) {
        const stamp = Date.now();
        const made = await (await fetch('/api/v1/pos/products', { method: 'POST', headers: H,
          body: JSON.stringify({
            name: 'ZZPROBE tier board ' + stamp, sku: 'ZZPROBE-TB-' + stamp,
            price: '4.00', tier_mode: 'bundle',
            price_tiers: [{ min_qty: 3, unit_price: '10.00' }],
            product_class: 'standard', is_active: true, stock_quantity: 99,
          }) })).json();
        if (made && made.id) {
          minted.push(made.id);
          list = [{ id: made.id, name: made.name, price: made.price,
                    price_tiers: made.price_tiers, tier_mode: made.tier_mode }];
        }
      }
      const out = [];
      for (const prod of list.slice(0, 3)) {
        const qty = Math.max(...prod.price_tiers.map(t => Number(t.min_qty)));   // reach the top rung
        const mk = await (await fetch('/api/v1/pos/kiosk/cart', { method: 'POST', headers: H,
          body: JSON.stringify({ items: [{ product_id: prod.id, qty }], source: 'proof' }) })).json();
        if (!mk || !mk.code) continue;
        const detail = await (await fetch('/api/v1/pos/carts/' + mk.code, { headers: H })).json();
        out.push({ name: prod.name, id: prod.id, qty, price: String(prod.price),
                   tiers: prod.price_tiers, mode: prod.tier_mode || 'per_unit',
                   board_total: detail.total });
      }
      // put the bench back
      for (const id of minted) {
        await fetch('/api/v1/pos/products/' + id, { method: 'PUT', headers: H,
          body: JSON.stringify({ name: 'ZZPROBE tier board (retired)', price: '4.00',
                                 is_active: false, product_class: 'standard' }) }).catch(() => {});
      }
      return out;
    });
    if (!held.length) {
      hbad++; hn++;
      console.log('  ❌ no tiered product reachable — the held-order check could not run,'
                + ' which is a FAILURE, not a shrug: it is how a real pricing bug stayed hidden');
    } else {
      const want = JSON.parse(execFileSync('python3', ['-c', `
import sys, logging, json
sys.path.insert(0, '${process.env.BANCO_REPO || '/home/angel/repos/banco-starter'}')
logging.disable(logging.WARNING)
from decimal import Decimal
from src.services.pricing import tier_line_total
CASES = json.loads(sys.stdin.read())
print(json.dumps([str(tier_line_total(c["tiers"], Decimal(c["price"]), c["qty"], mode=c["mode"]))
                  for c in CASES]))
`], { encoding: 'utf8', input: JSON.stringify(held) }));
      held.forEach((h, i) => {
        hn++;
        const flat = (Number(h.price) * h.qty).toFixed(2);
        if (h.board_total !== want[i]) {
          hbad++;
          console.log(`  ❌ held order · ${h.name} ×${h.qty}: board ${h.board_total} · till ${want[i]}`
                    + (h.board_total === flat ? '  (board is charging price × qty — the tier was dropped)' : ''));
        }
      });
      console.log(hbad ? `  ${hbad} of ${hn} held orders are priced wrong`
                       : `  ✅ the held-orders board agrees with the till on all ${hn} tiered orders`);
    }
  } catch (e) {
    // An exception here used to print a warning and pass. Two always-passing paths
    // in one check (this and the empty-discovery one) is how a live pricing bug
    // stays invisible: the suite is green and has measured nothing.
    hbad++; hn++;
    console.log('  ❌ held-order check threw — treated as a FAILURE, not a warning: ' + e.message);
  }


  // ── RING IT OUT — the HANDOFF, which is a fourth implementation nobody counted ──────
  // 2026-09-02, on the tablet: the board said CHF 10.00, Angel pressed "Ring it out", and the
  // cart it opened said CHF 12.00. The board had just been fixed; the bug had moved one screen
  // to the right. ringOut() rebuilds a till cart by hand from the board's payload, copied six
  // fields, and price_tiers/tier_mode were not among them — so _tierBest() found no ladder and
  // the cart fell back to price × qty. LESSON #2: a downstream mapper discards the very field
  // the fix upstream existed to produce.
  //
  // This check DRIVES THE REAL BUTTON. Asking the payload for its fields, or re-running the
  // mapper here, would have passed against the broken build — the mapper is the thing under
  // test, so the test may not contain a copy of it. Nothing is ever completed: reaching the
  // checkout screen writes no row. Never press Complete on a shop's books.
  let rbad = 0, rn = 0;
  try {
    const made = await p.evaluate(async () => {
      const tok = sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token');
      const H = { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' };
      const stamp = Date.now();
      const prod = await (await fetch('/api/v1/pos/products', { method: 'POST', headers: H,
        body: JSON.stringify({
          name: 'ZZPROBE ringout ' + stamp, sku: 'ZZPROBE-RO-' + stamp,
          price: '4.00', tier_mode: 'bundle',
          price_tiers: [{ min_qty: 3, unit_price: '10.00' }],
          product_class: 'standard', is_active: true, stock_quantity: 99,
        }) })).json();
      if (!prod || !prod.id) return null;
      const mk = await (await fetch('/api/v1/pos/kiosk/cart', { method: 'POST', headers: H,
        body: JSON.stringify({ items: [{ product_id: prod.id, qty: 3 }], source: 'proof' }) })).json();
      return (mk && mk.code) ? { id: prod.id, code: mk.code } : { id: prod.id, code: null };
    });
    if (!made || !made.code) {
      rbad++; rn++;
      console.log('  ❌ could not build a held order to ring out — FAILURE, not a skip:'
                + ' a discovery step that finds nothing is a test that always passes');
    } else {
      // the till's own answer for this exact ladder at qty 3
      const want = JSON.parse(execFileSync('python3', ['-c', `
import sys, logging, json
sys.path.insert(0, '${process.env.BANCO_REPO || '/home/angel/repos/banco-starter'}')
logging.disable(logging.WARNING)
from decimal import Decimal
from src.services.pricing import tier_line_total
print(json.dumps(str(tier_line_total([{"min_qty":3,"unit_price":"10.00"}], Decimal("4.00"), 3, mode="bundle"))))
`], { encoding: 'utf8' }));

      await p.goto('http://localhost:3000/pos/held-orders', { waitUntil: 'domcontentloaded' });
      const card = p.locator('.card').filter({ hasText: made.code });
      await card.first().waitFor({ timeout: 20000 });
      const boardTxt = (await card.first().innerText()).replace(/\s+/g, ' ');
      const boardNum = (boardTxt.match(/(\d+\.\d{2})/) || [])[1] || null;

      rn++;
      if (boardNum !== want) {
        rbad++;
        console.log(`  ❌ the BOARD is wrong before we even ring it: board ${boardNum} · till ${want}`);
      }

      await card.first().locator('button:has-text("Ring it out")').click();
      await p.waitForURL('**/pos/checkout**', { timeout: 20000 });
      // The number the cashier reads and says out loud. Read through a LOCATOR, not an in-page
      // loop: checkout re-renders its totals after the cart loads, and an evaluate() that is
      // still polling when that happens dies with "execution context was destroyed". A locator
      // re-resolves instead. (Same family as the waitForFunction gotcha in TESTING.md.)
      const totalLoc = p.locator('[data-i18n="checkout.total"]').locator('xpath=..').locator('span').last();
      let shown = null;
      for (let i = 0; i < 40 && shown === null; i++) {
        try {
          const m = ((await totalLoc.textContent({ timeout: 2000 })) || '').match(/(\d+\.\d{2})/);
          if (m) shown = m[1];
        } catch (e) { /* mid-render — try again */ }
        if (shown === null) await p.waitForTimeout(250);
      }

      rn++;
      if (shown !== want) {
        rbad++;
        const flat = '12.00';
        console.log(`  ❌ ring it out · board ${boardNum} → checkout ${shown} · till ${want}`
                  + (shown === flat ? '  (the handoff dropped the ladder — price × qty again)' : ''));
      }
      console.log(rbad ? `  ${rbad} of ${rn} ring-it-out checks are wrong`
                       : `  ✅ ring it out: board ${boardNum} → checkout ${shown} → till ${want}, all three agree`);

      // Put the bench back. Its own try/catch: a cleanup that fails leaves a ZZPROBE row
      // behind, which is worth SAYING, but it is not the pricing question this check asks.
      try {
      await p.evaluate(async (m) => {
        const tok = sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token');
        const H = { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' };
        sessionStorage.removeItem('pos_cart');
        sessionStorage.removeItem('pos_kiosk_cart_code');
        sessionStorage.removeItem('checkout_customer');
        await fetch('/api/v1/pos/carts/' + m.code + '/claim', { method: 'POST', headers: H, body: '{}' }).catch(() => {});
        await fetch('/api/v1/pos/products/' + m.id, { method: 'PUT', headers: H,
          body: JSON.stringify({ name: 'ZZPROBE ringout (retired)', price: '4.00',
                                 is_active: false, product_class: 'standard' }) }).catch(() => {});
      }, made);
      } catch (e) {
        console.log('  ⚠️  cleanup failed — a ZZPROBE row may still be active: ' + e.message);
      }
    }
  } catch (e) {
    rbad++; rn++;
    console.log('  ❌ ring-it-out check threw — a FAILURE, not a warning: ' + e.message);
  }

  await b.close(); process.exit((bad + mbad + hbad + rbad) ? 1 : 0);
})();
