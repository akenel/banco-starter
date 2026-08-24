// The "Export catalog (CSV)" BUTTON — clicked by a browser, on the screen a shop owner stands on.
//
// The endpoint is proved by scripts/prove-catalog-export.py (18 checks, 1,100 rows, the keyset
// seam, the EAN, the manager door). None of that says the button exists, is reachable, or is
// wired to the right URL — lesson 1, ×9: green on the layer you can reach says nothing about the
// layer the user stands on. Every one of those nine was code that worked and a screen that did
// not. So this drives the actual page:
//
//   * the button is VISIBLE to a manager, and absent for a cashier (the file carries cost)
//   * clicking it produces a real DOWNLOAD, with rows in it
//   * the CATEGORY filter on screen is carried into the file — pick a shelf, get that shelf
//   * the toast reports how many rows left, so "downloaded ✓" over an empty file is impossible
//
// Re-run after touching the top bar of catalog.html or /catalog/export.csv.
const { chromium } = require('playwright');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };

async function login(p, user) {
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', user); await p.fill('#password', user);
    await p.click('#kc-login, input[type=submit]');
    await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
}

(async () => {
  const dl = fs.mkdtempSync(path.join(os.tmpdir(), 'banco-export-'));
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 200)));

  console.log('\n👔 As a MANAGER (ralph) …');
  await login(p, 'ralph');
  await p.goto(ROOT + '/pos/catalog');
  await p.waitForLoadState('networkidle');
  await p.waitForTimeout(1500);

  // WAIT for it, do not merely LOOK for it. `user.isManager` arrives from an async fetch, so an
  // immediate isVisible() is a coin toss on a race — it read false here the first time, on a
  // button that was in fact fine. Waiting is not softening the check: a button that never shows
  // up still fails, it just fails for the right reason.
  const btn = p.locator('button:has-text("Export catalog")').first();
  const shown = await btn.waitFor({ state: 'visible', timeout: 15000 }).then(() => true, () => false);
  ok('the Export catalog button is on the catalog screen', shown);
  if (!shown) { console.log('\n❌ nothing else can be tested without it'); await b.close(); process.exit(1); }

  // Click it and catch the actual file the browser saves.
  const [download] = await Promise.all([
    p.waitForEvent('download', { timeout: 30000 }),
    btn.click(),
  ]);
  const name = download.suggestedFilename();
  const file = path.join(dl, name);
  await download.saveAs(file);
  const body = fs.readFileSync(file);
  const lines = body.toString('utf8').split('\r\n').filter(Boolean);
  ok(`clicking downloads a file (${name}, ${body.length} bytes)`, body.length > 0);
  ok('the filename says what it is', /^banco-catalog-.*\.csv$/.test(name));
  ok(`the file has a header + rows (${lines.length - 1} products)`, lines.length > 1);
  ok('first cell of the header is `sku`', /^﻿?"sku";/.test(lines[0]));
  ok('the header carries the barcode column', lines[0].includes('"barcode"'));

  // The toast has to say HOW MANY. A silent "✓" over an empty file looks identical to success.
  const toast = await p.locator('text=/products ✓|Produkte ✓|prodotti ✓|produits ✓/').first()
    .textContent({ timeout: 5000 }).catch(() => '');
  ok(`the toast reports the row count (${JSON.stringify(toast.trim())})`, /\d/.test(toast));

  // The filter on screen must reach the file.
  console.log('\n🔎 With a shelf picked on screen …');
  const sel = p.locator('select').first();
  const shelf = await p.evaluate(() => {
    const s = document.querySelector('select');
    const o = [...s.options].find(x => x.value && x.value.trim());
    return o ? o.value : '';
  });
  if (!shelf) {
    ok('a category is available to filter by', false);
  } else {
    await sel.selectOption(shelf);
    await p.waitForTimeout(1500);
    const [d2] = await Promise.all([
      p.waitForEvent('download', { timeout: 30000 }),
      p.locator('button:has-text("Export catalog")').first().click(),
    ]);
    const f2 = path.join(dl, 'shelf-' + d2.suggestedFilename());
    await d2.saveAs(f2);
    const rows2 = fs.readFileSync(f2, 'utf8').split('\r\n').filter(Boolean);
    const slug = shelf.toLowerCase().replace(/ /g, '-').replace(/&/g, 'and').slice(0, 24);
    ok(`the filename names the shelf (${d2.suggestedFilename()} for "${shelf}")`,
       d2.suggestedFilename().includes(slug));
    ok(`the shelf file is a subset of the whole catalog (${rows2.length - 1} of ${lines.length - 1})`,
       rows2.length > 0 && rows2.length <= lines.length);
  }

  ok(`no page errors (${errs.join(' | ') || 'none'})`, errs.length === 0);

  console.log('\n💰 As a CASHIER (pam) — cost is not hers to take …');
  const p2 = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  await login(p2, 'pam');
  await p2.goto(ROOT + '/pos/catalog');
  await p2.waitForLoadState('networkidle');
  // Wait for the CASHIER'S OWN banner first ("editing … requires a manager"). Without it,
  // "the button is hidden" is true of a page that simply has not rendered yet — the check
  // would pass on a blank screen, which is the emptiest kind of green there is.
  const noticed = await p2.locator('text=/require|requires a|manager/i').first()
    .waitFor({ state: 'visible', timeout: 15000 }).then(() => true, () => false);
  ok('the cashier page has rendered (the manager-role notice is up)', noticed);
  const cashierSees = await p2.locator('button:has-text("Export catalog")').first()
    .isVisible().catch(() => false);
  ok('the button is HIDDEN from a cashier', noticed && !cashierSees);

  await b.close();
  fs.rmSync(dl, { recursive: true, force: true });
  console.log(`\n${fail ? '❌' : '✅'} ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})();
