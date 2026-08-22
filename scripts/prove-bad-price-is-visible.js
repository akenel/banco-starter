// A price that cannot mean what it says must SAY SO — on every screen, and at the moment it is
// typed.
//
// 2026-08-22. Angel rang 1 × Greengo King Size + 2 × Greengo King Size slim and the till said
// CHF 6.00 where three plain papers are 5.00. Nothing was wrong with the price: the slim pack had
// been saved with "price is for the whole pack" unticked, so it stored tier_mode 'per_unit' — an
// island that can never pool. Four live rows carried the same shape.
//
// They were not hidden. All three screens printed "3+ @ 5.00 ea", which is literally true of
// per_unit and absurd on its face — 15.00 for three, while the till charged 5.00. Nobody blinked,
// because a ladder printed in indigo reads as a deal however silly the number. So being ACCURATE
// was not enough; the screen has to be LOUD, and it has to stop pricing a row it knows is wrong.
//
// The guard-break matters more than the catch here: a warning that fires on good rows would be
// turned off within a week. A correct 3-for-5 bundle must stay silent.
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
  const p = await (await b.newContext({ viewport: { width: 1280, height: 1100 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 160)));
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  const RUN = Date.now();
  // CLEANUP IN A FINALLY. The first run of this very script threw at the shelf step and left
  // four ACTIVE probe rows behind; the next run then counted TWO bad rows and failed an
  // assertion that was correct. Three earlier provers leaked the same way. A prover that only
  // tidies up on the happy path poisons its own next run and blames the code for it.
  try {

    // ── the unit under test, as data ────────────────────────────────────────────────────────────
    //  BAD   — exactly the four live strays: 2.00, per_unit, [{1: 2.00}, {3: 5.00}]
    //  GOOD  — the 85 rows that are right: 2.00, bundle, [{3: 5.00}]        (must stay SILENT)
    //  RUNG  — a {min_qty: 1} that quietly replaces the shelf price          (amber, not red)
    //  PLAIN — no ladder at all                                             (must stay SILENT)
    const seeds = [
      ['BAD',   'ZZPROBE bad mode ' + RUN,   [{ min_qty: 1, unit_price: '2.00' }, { min_qty: 3, unit_price: '5.00' }], 'per_unit'],
      ['GOOD',  'ZZPROBE good deal ' + RUN,  [{ min_qty: 3, unit_price: '5.00' }], 'bundle'],
      ['RUNG',  'ZZPROBE one rung ' + RUN,   [{ min_qty: 1, unit_price: '1.50' }], 'per_unit'],
      ['PLAIN', 'ZZPROBE no ladder ' + RUN,  null, null],
    ];
    const ids = {}, codes = {};
    for (let i = 0; i < seeds.length; i++) {
      const [tag, name, tiers, mode] = seeds[i];
      const code = gtin('841477', 13);
      const r = await p.evaluate(async ([sku, name, code, tiers, mode]) => {
        const body = { sku, name, barcode: code, price: 2.00, stock_quantity: 1, category: 'Rolling Papers' };
        if (tiers) { body.price_tiers = tiers; body.tier_mode = mode; }
        try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true', body) }; }
        catch (e) { return { ok: false, detail: (e && e.message) || String(e) }; }
      }, [`ZZPROBE-WARN-${RUN}-${i}`, name, code, tiers, mode]);
      if (!r.ok) { console.error('seed failed:', tag, r.detail); process.exit(1); }
      ids[tag] = r.body.id; codes[tag] = code; made.push(r.body.id);
    }

    // ── 1 · the rule itself, before any screen ──────────────────────────────────────────────────
    console.log('\nthe rule (tierWarning) — catches the four, clears the eighty-five');
    const verdicts = await p.evaluate(() => ({
      bad:   tierWarning({ price: 2.00, tier_mode: 'per_unit', price_tiers: [{ min_qty: 1, unit_price: '2.00' }, { min_qty: 3, unit_price: '5.00' }] }),
      good:  tierWarning({ price: 2.00, tier_mode: 'bundle',   price_tiers: [{ min_qty: 3, unit_price: '5.00' }] }),
      roll:  tierWarning({ price: 4.00, tier_mode: 'bundle',   price_tiers: [{ min_qty: 3, unit_price: '10.00' }] }),
      real:  tierWarning({ price: 5.00, tier_mode: 'per_unit', price_tiers: [{ min_qty: 10, unit_price: '4.50' }] }),
      rung:  tierWarning({ price: 4.00, tier_mode: 'per_unit', price_tiers: [{ min_qty: 1, unit_price: '3.50' }] }),
      plain: tierWarning({ price: 2.00, tier_mode: 'per_unit', price_tiers: [] }),
      junk:  tierWarning({ price: 2.00, tier_mode: 'per_unit', price_tiers: 'not-an-array' }),
      nul:   tierWarning(null),
    }));
    ok('the mis-saved 3-for-5 is caught, loudly', verdicts.bad && verdicts.bad.level === 'error');
    ok('...and the message names the one tap', /whole pack/i.test((verdicts.bad || {}).fix || ''));
    // GUARD-BREAK. Every false positive below would train someone to ignore the real one.
    ok('a CORRECT 3-for-5 bundle says nothing', verdicts.good === null);
    ok('a CORRECT 3-for-10 roll bundle says nothing', verdicts.roll === null);
    ok('a genuine per_unit break (10+ @ 4.50) says nothing', verdicts.real === null);
    ok('no ladder, no warning', verdicts.plain === null);
    ok('a 1+ rung that undercuts the shelf price is amber, not red', verdicts.rung && verdicts.rung.level === 'warn');
    ok('a scalar price_tiers does not throw', verdicts.junk === null);
    ok('null product does not throw', verdicts.nul === null);

    // ── 2 · the catalogue row ───────────────────────────────────────────────────────────────────
    await p.goto(ROOT + '/pos/catalog');
    await p.waitForLoadState('networkidle'); await p.waitForTimeout(1200);
    await p.locator('input[placeholder*="Name"], input[type=text]').first().fill('ZZPROBE');
    await p.waitForTimeout(2500);
    console.log('\nthe catalogue row');
    const catTxt = await p.locator('body').innerText();
    ok('the bad row shows the warning', /costs MORE than one/i.test(catTxt));
    ok('...and NOT a deal chip that prices it', !/3\+\s*@\s*5\.00 ea/.test(catTxt));
    ok('the good row keeps its deal chip', /🏷️\s*3 for 5\.00/.test(catTxt));
    const badChips = await p.$$eval('.chip-bad', e => e.filter(x => x.offsetParent).length);
    ok('exactly one row is flagged red', badChips === 1);

    // ── 3 · the sweep ───────────────────────────────────────────────────────────────────────────
    console.log('\nthe sweep — the whole catalogue at once, not the row you happen to scroll past');
    const sweep = await p.evaluate(async () => {
      const r = await API.get('/api/v1/pos/catalog/price-check');
      const warned = (r.items || []).map(x => ({ n: x.name, w: tierWarning(x) })).filter(x => x.w);
      return { total: r.count, warned: warned.map(x => x.n) };
    });
    ok('the endpoint returns the catalogue\'s ladders', sweep.total >= 3);
    ok('the bad row is in the sweep', sweep.warned.some(n => /ZZPROBE bad mode/.test(n)));
    ok('the good row is NOT in the sweep', !sweep.warned.some(n => /ZZPROBE good deal/.test(n)));
    ok('the ladderless row is NOT in the sweep', !sweep.warned.some(n => /ZZPROBE no ladder/.test(n)));
    const panel = p.locator('text=/Pricing to check/i').first();
    ok('the panel is on the page', await panel.isVisible());

    // ── 4 · the editor, at the moment the mistake is made ───────────────────────────────────────
    console.log('\nthe editor — caught as it is typed, fixed in one tap');
    await p.goto(ROOT + '/pos/catalog?edit=' + ids.GOOD);
    await p.waitForLoadState('networkidle'); await p.waitForTimeout(2500);
    // Flip the good row to the wrong mode by hand — this is precisely the mis-tick under test.
    await p.locator('input[type=radio][value="per_unit"]').first().check();
    await p.waitForTimeout(400);
    // Scope to the EDITOR. The same sentence also sits in the (collapsed) sweep panel
    // higher up the page, and .first() picked that one — a test failing on working code.
    const editor = p.locator('input[type=radio][value="bundle"]').first()
                    .locator('xpath=ancestor::div[contains(@class,"space-y") or contains(@class,"modal")][1]');
    const liveWarn = editor.locator('text=/costs MORE than one/i').first();
    ok('unticking "whole pack" warns immediately', await liveWarn.isVisible());
    const fixBtn = p.locator('button[data-i18n="catalog.tiers_mode_bundle"]').first();  // button, not the radio label
    ok('a one-tap fix is offered', await fixBtn.isVisible());
    await fixBtn.click(); await p.waitForTimeout(400);
    ok('the tap clears the warning', !(await liveWarn.isVisible()));
    ok('...by ticking whole-pack, not by deleting the deal',
       await p.locator('input[type=radio][value="bundle"]').first().isChecked());

    // ── 5 · the shelf row — the screen Angel prices a shelf on ──────────────────────────────────
    console.log('\nthe shelf intake row');
    await p.goto(ROOT + '/pos/shelf-intake');
    await p.waitForLoadState('networkidle'); await p.waitForTimeout(1500);
    await p.evaluate(() => localStorage.removeItem('banco_shelf_intake_v1'));
    await p.reload({ waitUntil: 'networkidle' }); await p.waitForTimeout(1200);
    const box = p.locator('textarea').first();
    await box.fill([codes.BAD, codes.GOOD].join('\n'));
    await p.locator('button:has-text("Triage the shelf")').first().click();
    await p.waitForTimeout(6000);
    const shelfTxt = await p.locator('body').innerText();
    ok('the bad row warns on the shelf row', /costs MORE than one/i.test(shelfTxt));
    ok('...and names the tap right there', /whole pack/i.test(shelfTxt));
    ok('the good row still shows its deal', /3 for 5\.00/.test(shelfTxt));

    console.log('\npageerrors: ' + errs.length + ' ' + (errs[0] || ''));
    ok('no javascript errors', errs.length === 0);

  } finally {
    // Soft-delete, never hard: a probe row that happened to be rung in a sale cannot be
    // deleted (FK from line_items), and prove-barcode-binding.js broke the day that happened.
    // Freeing the barcode first is what lets the NEXT run re-use a code without colliding.
    for (const id of made) await p.evaluate(async (i) => {
      try { await API.put('/api/v1/pos/products/' + i + '?allow_nonstandard=true', { barcode: null }); } catch (e) {}
      try { await API.delete('/api/v1/pos/products/' + i); } catch (e) {}
    }, id).catch(() => {});
  }
  console.log('\n' + '='.repeat(52) + `\n  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
