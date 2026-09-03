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
    // Land on a settled page first. The section above finishes wherever it finishes, and
    // an evaluate() that starts while a navigation is still in flight dies with "execution
    // context was destroyed" — which then reads as a pricing failure, which it is not.
    await p.goto('http://localhost:3000/pos/dashboard', { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(1200);
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


  // ── TARGET TOTAL — the agreed price the cashier types in ──────────────────────────────
  // Angel, 2026-09-02 23:43: typed an agreed total of 100.00 and the till said 100.46.
  // Not rounding. The percentage was derived from the FULL subtotal while `totals` has
  // applied it to the ELIGIBLE portion ever since deal-priced and age-restricted lines
  // stopped discounting. Two equations, one screen.
  //
  //   subtotal 104.80 · eligible 94.80 (a 3-for-10 pack cannot discount)
  //   was: (1 - 100/104.80)*100      = 4.58%  ->  94.80 x 4.58% = 4.34  ->  100.46
  //   now: (104.80 - 100)/94.80*100  = 5.06%  ->  94.80 x 5.06% = 4.80  ->  100.00
  //
  // Driven through the REAL box: type into Target Total, read the TOTAL line. A basket
  // is built in sessionStorage the way the Edit-Cart path does it, and nothing is ever
  // completed — reaching this screen writes no row.
  let tbad = 0, tn = 0;
  try {
    const kit = await p.evaluate(async () => {
      const tok = sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token');
      const H = { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' };
      const st = Date.now();
      // Retire anything this check left behind on an earlier run, THEN create with
      // allow_duplicate=true. Without it the name-similarity guard refuses the second
      // run — correctly; it just has no opinion about a probe cleaning up after itself.
      try {
        const found = await (await fetch('/api/v1/pos/search?q=ZZPROBE%20target&limit=50', { headers: H })).json();
        for (const old of (found.items || [])) {
          await fetch('/api/v1/pos/products/' + old.id, { method: 'PUT', headers: H,
            body: JSON.stringify({ name: old.name, price: String(old.price || '1.00'),
                                   is_active: false, product_class: 'standard' }) }).catch(() => {});
        }
      } catch (e) { /* nothing to sweep */ }
      const mk = async (body) => (await (await fetch('/api/v1/pos/products?allow_duplicate=true',
        { method: 'POST', headers: H, body: JSON.stringify(body) })).json());
      const deal = await mk({ name: 'ZZPROBE target deal ' + st, sku: 'ZZPROBE-TD-' + st,
        price: '4.00', tier_mode: 'bundle', price_tiers: [{ min_qty: 3, unit_price: '10.00' }],
        product_class: 'standard', is_active: true, stock_quantity: 99 });
      const plain = await mk({ name: 'ZZPROBE target plain ' + st, sku: 'ZZPROBE-TP-' + st,
        price: '7.90', product_class: 'standard', is_active: true, stock_quantity: 99 });
      if (!deal.id || !plain.id) return { err: JSON.stringify({ deal, plain }).slice(0, 400) };
      return { deal, plain };
    });
    if (!kit || kit.err) {
      tbad++; tn++;
      console.log('  \u274c could not build the target-total basket — FAILURE, not a skip: '
                + (kit && kit.err ? kit.err : 'no response'));
    } else {
      // Angel's basket exactly: 3 of a 3-for-10 pack (never discounts) + 12 at 7.90.
      await p.evaluate((k) => {
        const cart = [
          { id: k.deal.id, product_id: k.deal.id, name: k.deal.name, quantity: 3,
            price: 4.00, price_tiers: k.deal.price_tiers, tier_mode: 'bundle', product_class: 'standard' },
          { id: k.plain.id, product_id: k.plain.id, name: k.plain.name, quantity: 12,
            price: 7.90, price_tiers: null, tier_mode: 'per_unit', product_class: 'standard' },
        ];
        sessionStorage.setItem('pos_cart', JSON.stringify({ cart, discount: 0, totals: {} }));
      }, kit);
      await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(2500);

      const totalNow = async () => {
        const loc = p.locator('[data-i18n="scan.total"]').locator('xpath=following-sibling::span[1]');
        for (let i = 0; i < 40; i++) {
          try {
            const m = ((await loc.textContent({ timeout: 2000 })) || '').match(/(\d+\.\d{2})/);
            if (m) return m[1];
          } catch (e) { /* mid-render */ }
          await p.waitForTimeout(250);
        }
        return null;
      };

      tn++;
      const sub = await totalNow();
      if (sub !== '104.80') {
        tbad++;
        console.log(`  \u274c the basket did not build: subtotal reads ${sub}, expected 104.80`
                  + ' (10.00 for the pack + 94.80) — everything below would be measuring the wrong cart');
      } else {
        await p.locator('button:has-text("Target Total")').first().click();
        await p.waitForTimeout(400);
        const box = p.locator('input[placeholder^="Max"]').first();

        await box.fill('100');
        await p.waitForTimeout(700);
        const got = await totalNow();
        tn++;
        if (got !== '100.00') {
          tbad++;
          console.log(`  \u274c target 100.00 -> till says ${got}`
                    + (got === '100.46' ? '  (percentage taken off the whole basket, applied to part of it)' : ''));
        } else {
          console.log('  \u2705 target total: typed 100.00 on a 104.80 basket with a 10.00 pack in it, got 100.00');
        }

        // A target BELOW what the basket can reach must SAY so, not land somewhere else.
        // The floor here is 10.00: the pack never discounts, whatever anyone types.
        await box.fill('5');
        await p.waitForTimeout(700);
        const err = await p.locator('p.text-red-600').first().textContent().catch(() => null);
        const low = await totalNow();
        tn++;
        if (!err || !err.trim() || low !== '104.80') {
          tbad++;
          console.log(`  \u274c an unreachable target said "${(err || '').trim()}" and left the total at ${low}`
                    + ' — it must refuse and change nothing');
        } else {
          console.log(`  \u2705 an unreachable target refuses out loud: "${err.trim()}"`);
        }
      }

      try {
        await p.evaluate(async (k) => {
          const tok = sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token');
          const H = { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' };
          sessionStorage.removeItem('pos_cart');
          for (const pr of [k.deal, k.plain]) {
            await fetch('/api/v1/pos/products/' + pr.id, { method: 'PUT', headers: H,
              body: JSON.stringify({ name: pr.name + ' (retired)', price: pr.price,
                                     is_active: false, product_class: 'standard' }) }).catch(() => {});
          }
        }, kit);
      } catch (e) { console.log('  \u26a0\ufe0f  cleanup failed — ZZPROBE rows may still be active: ' + e.message); }
    }
  } catch (e) {
    tbad++; tn++;
    console.log('  \u274c target-total check threw — a FAILURE, not a warning: ' + e.message);
  }


  // ── THE VAT LINE — the fifth implementation, and the one that ends up on a receipt ────
  // Angel photographed the tablet on 2026-09-03. Same basket, same TOTAL of CHF 10.00, and
  // the two screens disagreed about the tax inside it: the cart said CHF 0.75, checkout said
  // CHF 0.82. checkout.html's per-line VAT loop read `it.price * it.quantity` — the price
  // BEFORE the deal — while the `factor` it multiplied by had been calibrated against the
  // POOLED subtotal. So every pack deal in the basket got re-inflated by exactly the saving
  // it had just given, and the VAT line was overstated on every basket containing one.
  //
  // The BOOKS were never wrong: the server rolls up its own stored line_totals through
  // vat_resolver.split_vat, where sum(lines) IS the subtotal by construction. This was the
  // screen disagreeing with the receipt — LESSON #13.
  //
  // THE INVARIANT, and why it is stated this way: for an all-standard basket the contained
  // VAT is a pure function of the TOTAL, `total * r / (100 + r)`. Both numbers are read off
  // the screen and the rate is read from POSConfig, so nothing here re-implements the thing
  // under test (LESSON #5) — the check is that a screen agrees with its own total.
  // The basket build is asserted first: a self-consistent VAT on the WRONG total would pass.
  //
  // Note there is NO discount in the first pass. The bug did not need one — with the pack
  // priced 5.00 and read as 6.00, factor is 1 and the VAT is still wrong (0.89 vs 0.82).
  // A repro that only fires under a discount would have pointed the fix at the discount.
  let vbad = 0, vn = 0;
  try {
    await p.goto('http://localhost:3000/pos/dashboard', { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(1200);
    const vkit = await p.evaluate(async () => {
      const tok = sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token');
      const H = { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' };
      const st = Date.now();
      try {   // sweep anything an earlier run left active, so allow_duplicate is not needed twice
        const found = await (await fetch('/api/v1/pos/search?q=ZZPROBE%20vat&limit=50', { headers: H })).json();
        for (const old of (found.items || [])) {
          await fetch('/api/v1/pos/products/' + old.id, { method: 'PUT', headers: H,
            body: JSON.stringify({ name: old.name, price: String(old.price || '1.00'),
                                   is_active: false, product_class: 'standard' }) }).catch(() => {});
        }
      } catch (e) { /* nothing to sweep */ }
      const mk = async (body) => (await (await fetch('/api/v1/pos/products?allow_duplicate=true',
        { method: 'POST', headers: H, body: JSON.stringify(body) })).json());
      // Angel's exact basket: a "3 for 5.00" pack at 2.00 each, plus one plain 5.90 line.
      const deal = await mk({ name: 'ZZPROBE vat deal ' + st, sku: 'ZZPROBE-VD-' + st,
        price: '2.00', tier_mode: 'bundle', price_tiers: [{ min_qty: 3, unit_price: '5.00' }],
        product_class: 'standard', is_active: true, stock_quantity: 99 });
      const plain = await mk({ name: 'ZZPROBE vat plain ' + st, sku: 'ZZPROBE-VP-' + st,
        price: '5.90', product_class: 'standard', is_active: true, stock_quantity: 99 });
      if (!deal.id || !plain.id) return { err: JSON.stringify({ deal, plain }).slice(0, 400) };
      return { deal, plain };
    });
    if (!vkit || vkit.err) {
      vbad++; vn++;
      console.log('  ❌ could not build the VAT basket — FAILURE, not a skip: '
                + (vkit && vkit.err ? vkit.err : 'no response'));
    } else {
      await p.evaluate((k) => {
        const cart = [
          { id: k.deal.id, product_id: k.deal.id, name: k.deal.name, quantity: 3,
            price: 2.00, price_tiers: k.deal.price_tiers, tier_mode: 'bundle', product_class: 'standard' },
          { id: k.plain.id, product_id: k.plain.id, name: k.plain.name, quantity: 1,
            price: 5.90, price_tiers: null, tier_mode: 'per_unit', product_class: 'standard' },
        ];
        sessionStorage.setItem('pos_cart', JSON.stringify({ cart, discount: 0, totals: {} }));
      }, vkit);
      await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(2500);

      // Read a money figure off a locator, retrying while Alpine re-renders (the same
      // execution-context trap the ring-out check documents).
      const money = async (loc) => {
        for (let i = 0; i < 40; i++) {
          try {
            const m = ((await loc.textContent({ timeout: 2000 })) || '').match(/(\d+\.\d{2})/);
            if (m) return m[1];
          } catch (e) { /* mid-render */ }
          await p.waitForTimeout(250);
        }
        return null;
      };
      const rate = await p.evaluate(() => Number(POSConfig.vat_rate));
      const contained = (t) => (Number(t) * rate / (100 + rate)).toFixed(2);

      const scanTotal = p.locator('[data-i18n="scan.total"]').locator('xpath=following-sibling::span[1]');
      const scanVatEl = p.locator('[data-i18n="scan.total"]')
                         .locator('xpath=../following-sibling::div[1]/span[2]');
      const sTot = await money(scanTotal);
      const sVat = await money(scanVatEl);

      vn++;
      if (sTot !== '10.90') {
        vbad++;
        console.log(`  ❌ the VAT basket did not build: cart total reads ${sTot}, expected 10.90`
                  + ' (5.00 for the 3-pack + 5.90) — everything below would be measuring the wrong cart');
      } else {
        vn++;
        if (sVat !== contained(sTot)) {
          vbad++;
          console.log(`  ❌ cart screen: total ${sTot} but VAT ${sVat}, and ${rate}% of that total is ${contained(sTot)}`);
        }

        // Drive the REAL button. Reading sessionStorage or calling recalc() here would test a
        // copy of the path instead of the path (the ring-out lesson, one section up).
        await p.locator('button:has-text("Checkout")').first().click();
        await p.waitForURL('**/pos/checkout**', { timeout: 20000 });
        const coTotal = p.locator('[data-i18n="checkout.total"]').locator('xpath=..').locator('span').last();
        const coVatEl = p.locator('[data-i18n="checkout.incl_vat"]').locator('xpath=../..').locator('span').last();
        const cTot = await money(coTotal);
        const cVat = await money(coVatEl);

        vn++;
        if (cTot !== sTot) {
          vbad++;
          console.log(`  ❌ the two screens disagree on the TOTAL: cart ${sTot} · checkout ${cTot}`);
        }
        vn++;
        if (cVat !== contained(cTot)) {
          vbad++;
          console.log(`  ❌ checkout: total ${cTot} but VAT ${cVat}, and ${rate}% of that total is ${contained(cTot)}`
                    + '  (the VAT loop is reading price × qty, not the pooled line — the deal is being un-discounted)');
        }
        vn++;
        if (cVat !== sVat) {
          vbad++;
          console.log(`  ❌ the two screens disagree on the VAT inside the same total: cart ${sVat} · checkout ${cVat}`);
        }

        // Now with a discount on top, so the `factor` path is exercised too and not just the
        // factor === 1 case. The pack is deal-priced and never discounts, so the 10% lands on
        // the 5.90 line only — which is the arrangement that made the two equations diverge.
        const chip = p.locator('button:has-text("10%")').first();
        if (await chip.count()) {
          await chip.click();
          await p.waitForTimeout(800);
          const dTot = await money(coTotal);
          const dVat = await money(coVatEl);
          vn++;
          if (dTot !== '10.31') {
            vbad++;
            console.log(`  ❌ 10% off a 10.90 basket whose 5.00 pack cannot discount should be 10.31, got ${dTot}`);
          }
          vn++;
          if (dVat !== contained(dTot)) {
            vbad++;
            console.log(`  ❌ checkout, discounted: total ${dTot} but VAT ${dVat}, expected ${contained(dTot)}`);
          }
        } else {
          vn++; vbad++;
          console.log('  ❌ no 10% discount chip on checkout — the discounted half of this check could not run');
        }

        if (!vbad) console.log(`  ✅ the VAT line agrees with its own total on both screens: `
                             + `cart ${sTot}/${sVat} → checkout ${cTot}/${cVat}, at ${rate}% inclusive, with a pack deal in the basket`);
      }

      try {
        await p.evaluate(async (k) => {
          const tok = sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token');
          const H = { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' };
          sessionStorage.removeItem('pos_cart');
          for (const pr of [k.deal, k.plain]) {
            await fetch('/api/v1/pos/products/' + pr.id, { method: 'PUT', headers: H,
              body: JSON.stringify({ name: pr.name + ' (retired)', price: pr.price,
                                     is_active: false, product_class: 'standard' }) }).catch(() => {});
          }
        }, vkit);
      } catch (e) { console.log('  ⚠️  cleanup failed — ZZPROBE rows may still be active: ' + e.message); }
    }
  } catch (e) {
    vbad++; vn++;
    console.log('  ❌ VAT-line check threw — a FAILURE, not a warning: ' + e.message);
  }


  await b.close(); process.exit((bad + mbad + hbad + rbad + tbad + vbad) ? 1 : 0);
})();
