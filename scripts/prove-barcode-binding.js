#!/usr/bin/env node
/**
 * prove-barcode-binding.js — does the till KEEP the code it just scanned?
 *
 * WHY THIS EXISTS
 * ---------------
 * On 2026-08-20 Angel filed six reports from the shop's own till. Three of them —
 * BL-9 ("made on the fly but only searchable by name after"), BL-12 ("create mode not
 * showing scanned results") and BL-13 — were one bug:
 *
 *   scan a packet -> not on file -> the code is held and SHOWN in the amber banner ->
 *   type a name and a price -> `createNoCodeItem()` calls `genInternalBarcode()` ANYWAY
 *   -> the row is saved under a random 2xxxxxxxxxxxx that exists on no packet anywhere.
 *
 * That packet could then never be scanned in this shop again. 4,998 of 5,446 live
 * products, 92%, only 414 findable by scanning the real thing. Felix's "too complicated,
 * too many buttons" was a scanner that misses three times in four — the buttons he hates
 * are what he gets INSTEAD of a hit.
 *
 * No test could have caught it, because there was no test. LESSONS.md said it in July
 * ("never invent an identifier that exists in the physical world") and the till kept
 * leaking for six weeks. This is the test.
 *
 * WHAT IT ASSERTS — all through the real screens, never by poking Alpine state
 *   1  a barcode miss HOLDS the code and shows it
 *   2  the create panel shows that code with an ✕ (Angel's call, 2026-08-21: show it,
 *      never bind silently — "a wrong bind looks exactly like a right one")
 *   3  creating the item saves the REAL code, not a minted one          <- the leak
 *   4  scanning that same packet again FINDS it                         <- the point
 *   5  pressing ✕ still mints, because an item with no code needs one
 *   6  a NAME typed in the catalogue search never lands in the Barcode field
 *   7  a CODE typed in the catalogue search does
 *   8  a code already on a switched-off row makes no duplicate
 *
 * ⚠️  IT WRITES PRODUCTS. It rings NO sales — nothing here reaches the Kassenbuch — but
 *     it does create catalogue rows, and it deletes its own at the end (SKU/name prefix
 *     `ZZPROBE`). It refuses to run anywhere but localhost unless you insist.
 *
 * RUN
 *   NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-barcode-binding.js
 *   (no node build in this repo on purpose — playwright is borrowed, not vendored.)
 */
'use strict';

const { execFileSync } = require('child_process');
const path = require('path');

const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
const REPO = path.resolve(__dirname, '..');
const USER = process.env.BANCO_USER || 'ralph';
const PASS = process.env.BANCO_PASS || 'ralph';

// This creates and deletes rows in the products table. On the shop's box that is the
// shop's catalogue. Refuse by default; BANCO_ALLOW_CATALOG_WRITES=1 is a deliberate act.
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT) &&
    process.env.BANCO_ALLOW_CATALOG_WRITES !== '1') {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates and deletes`);
  console.error('products. If you really mean it: BANCO_ALLOW_CATALOG_WRITES=1');
  process.exit(2);
}

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  console.error('playwright not found. Set NODE_PATH to a node_modules directory that has it:');
  console.error('  NODE_PATH=/path/to/node_modules node scripts/prove-barcode-binding.js');
  process.exit(2);
}

// ---------------------------------------------------------------- reporting
let pass = 0, fail = 0;
function ok(l, d) { pass++; console.log(`  ✅ ${l}${d ? '  — ' + d : ''}`); }
function bad(l, d) { fail++; console.log(`  ❌ ${l}${d ? '  — ' + d : ''}`); }
function check(c, l, d) { (c ? ok : bad)(l, d); return !!c; }
function head(t) { console.log(`\n${t}\n${'-'.repeat(t.length)}`); }

// ---------------------------------------------------------------- database
function psql(q) {
  return execFileSync('docker', ['compose', 'exec', '-T', 'postgres', 'psql',
    '-U', process.env.POSTGRES_USER || 'helix_user',
    '-d', process.env.POSTGRES_DB || 'helix_db', '-tAc', q],
    { cwd: REPO, encoding: 'utf8' }).trim();
}
const PROBE = 'ZZPROBE';
const barcodeOf = name => psql(`select coalesce(barcode,'') from products where name='${name}'`);
const rowsNamed = name => parseInt(psql(`select count(*) from products where name='${name}'`), 10);
const isMinted = code => /^2\d{12}$/.test(code);

// A code that is on no packet in this sandbox. Digits only — a gun sends digits.
const stamp = String(Date.now()).slice(-7);
const CODE_A = '76401' + stamp;          // bound on create
const CODE_B = '76402' + stamp;          // cleared with the ✕, must mint
const CODE_C = '76403' + stamp;          // used for the catalogue prefill
const NAME_A = `${PROBE} Bound ${stamp}`;
const NAME_B = `${PROBE} Cleared ${stamp}`;

// ---------------------------------------------------------------- browser
async function newPage(b) {
  const p = await (await b.newContext({ viewport: { width: 1280, height: 1000 } })).newPage();
  p.on('dialog', async d => { await d.accept(); });
  return p;
}

async function login(p) {
  await p.goto(`${ROOT}/pos`, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('button:has-text("Login")', { timeout: 20000 });
  // The Login button is rendered before Alpine binds its handler, so a click that lands in
  // that gap does NOTHING and the whole run then dies on a bare 20s timeout looking like a
  // broken login page. Click, and click again if nothing moved. (Cost me a run.)
  const landed = () => p.waitForFunction(
    () => !!(document.querySelector('#username')
             || sessionStorage.getItem('pos_token')
             || localStorage.getItem('pos_token')),
    null, { timeout: 8000 });
  await p.click('button:has-text("Login")');
  try { await landed(); } catch (e) {
    await p.click('button:has-text("Login")');
    await landed();
  }
  if (await p.$('#username')) {
    await p.fill('#username', USER);
    await p.fill('#password', PASS);
    await p.click('#kc-login, input[type=submit]');
    await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  await p.waitForLoadState('networkidle');
  const authed = await p.evaluate(() =>
    !!(sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token')));
  if (!authed) throw new Error(`login did not produce a token: ${p.url()}`);
}

// Alpine mounts asynchronously; every read must wait for it or it throws in a way that
// reads like a broken page and is not one.
async function waitAlpine(p) {
  await p.waitForFunction(() => {
    const el = document.querySelector('[x-data]');
    if (!el || !window.Alpine) return false;
    try { return !!Alpine.$data(el); } catch (e) { return false; }
  }, null, { timeout: 20000 });
  await p.waitForTimeout(400);
}

// ?lang=en pins the language, so text locators below are stable no matter what the
// operator last picked. (base.html:1146 — url wins over localStorage.)
async function goto(p, where) {
  await p.goto(`${ROOT}${where}${where.includes('?') ? '&' : '?'}lang=en`);
  await p.waitForLoadState('networkidle');
  await waitAlpine(p);
}

const state = p => p.evaluate(() => {
  const d = Alpine.$data(document.querySelector('[x-data]'));
  return { pendingBarcode: d.pendingBarcode, searchMode: d.searchMode, cart: (d.cart || []).length,
           cartNames: (d.cart || []).map(c => c.name), formBarcode: d.form ? d.form.barcode : null };
});

// Scan a code the way a gun does: into the box, then the button.
async function scan(p, code) {
  // "Barcode" is a substring of "Find by Barcode" — take the tab, which comes first in DOM.
  await p.locator('button:has-text("Barcode")').first().click();
  await p.fill('input[x-model="barcodeInput"]', code);
  await p.click('button:has-text("Find by Barcode")');
  await p.waitForTimeout(1200);
}

async function fillNewItem(p, name, price) {
  await p.fill('input[x-model="otfName"]', name);
  await p.fill('input[x-model="otfPrice"]', String(price));
  await p.click('button:has-text("Create & add to cart")');
  await p.waitForTimeout(1800);
}

// ---------------------------------------------------------------- the run
(async () => {
  const browser = await chromium.launch();
  const p = await newPage(browser);
  try {
    await login(p);

    // ---------------------------------------------------------------------
    head('1 · a barcode miss HOLDS the code and shows it');
    await goto(p, '/pos/scan');
    await scan(p, CODE_A);
    let s = await state(p);
    check(s.pendingBarcode === CODE_A, 'the code is held', `pendingBarcode=${s.pendingBarcode}`);
    check(s.searchMode === 'catalog', 'the miss opens the department/create panel', s.searchMode);
    const bannerSeen = await p.locator(`p.font-mono:has-text("${CODE_A}")`).first().isVisible();
    check(bannerSeen, 'the code is on the screen, not just in memory');

    // ---------------------------------------------------------------------
    head('2 · the create panel shows that code, with an ✕ (Angel: show it, never bind silently)');
    const bindPanel = p.locator('div', { hasText: 'This code gets saved on the new item' }).last();
    check(await bindPanel.isVisible(), 'the "this code gets saved" panel is rendered');
    const bindText = await p.locator('p.font-mono.font-bold').first().innerText().catch(() => '');
    check(bindText.trim() === CODE_A, 'it shows THIS code', bindText.trim());
    const clearBtn = p.getByRole('button', { name: 'Clear the scanned code' });
    check(await clearBtn.isVisible(), 'the ✕ that kills a mis-scan is reachable');
    const headingCoded = await p.locator('span:has-text("with the code you scanned")').first()
      .isVisible().catch(() => false);
    check(headingCoded, 'the heading no longer claims "no barcode" when it has one');

    // ---------------------------------------------------------------------
    head('3 · creating the item saves the REAL code, not a minted one   ← THE LEAK');
    await fillNewItem(p, NAME_A, 4.5);
    const savedA = barcodeOf(NAME_A);
    check(savedA === CODE_A, 'the scanned code is on the row', `barcode=${savedA || '(none)'}`);
    check(!isMinted(savedA), 'it is NOT a minted 2xxxxxxxxxxxx', savedA);
    s = await state(p);
    check(s.pendingBarcode === '', 'the held code is consumed, not left to leak onto the next item');

    // ---------------------------------------------------------------------
    head('4 · scanning that same packet again FINDS it   ← the whole point');
    await goto(p, '/pos/scan');
    await scan(p, CODE_A);
    s = await state(p);
    check(s.pendingBarcode !== CODE_A, 'it is no longer a miss');
    check(s.cart === 1 && s.cartNames[0] === NAME_A,
      'the packet scanned straight into the cart', s.cartNames.join(', ') || '(empty cart)');

    // ---------------------------------------------------------------------
    head('5 · pressing ✕ still mints — an item with no code on it needs one');
    await goto(p, '/pos/scan');
    await scan(p, CODE_B);
    await p.getByRole('button', { name: 'Clear the scanned code' }).click();
    await p.waitForTimeout(300);
    s = await state(p);
    check(s.pendingBarcode === '', 'the ✕ drops the code');
    await fillNewItem(p, NAME_B, 2.5);
    const savedB = barcodeOf(NAME_B);
    check(isMinted(savedB), 'a code-less item still gets a minted one', savedB);
    check(savedB !== CODE_B, 'and it is not the code that was cleared', savedB);

    // ---------------------------------------------------------------------
    head('6 · a NAME typed in the catalogue search never lands in the Barcode field');
    await goto(p, '/pos/catalog');
    await p.fill('input[x-model="q"]', 'Lollipop');
    await p.waitForTimeout(900);
    await p.locator('button:has-text("New product")').first().click();
    await p.waitForTimeout(600);
    let fb = await p.inputValue('input[x-model="form.barcode"]');
    check(fb === '', 'Barcode stays empty for a name search', `barcode="${fb}"`);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(400);

    // ---------------------------------------------------------------------
    head('7 · a CODE typed in the catalogue search DOES prefill it');
    await goto(p, '/pos/catalog');
    await p.fill('input[x-model="q"]', CODE_C);
    await p.waitForTimeout(900);
    await p.locator('button:has-text("New product")').first().click();
    await p.waitForTimeout(600);
    fb = await p.inputValue('input[x-model="form.barcode"]');
    check(fb === CODE_C, 'the scanned code lands in Barcode', `barcode="${fb}"`);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(400);

    // ---------------------------------------------------------------------
    head('8 · a code already on a switched-off row makes no duplicate');
    // /products/barcode/{code} answers 400 for an inactive product (pos_router.py:2001) and
    // searchByBarcode treats every error as a miss — so a DISCONTINUED item arrives at the
    // create form looking exactly like something brand new. Minting over it would put one
    // packet on two rows: the duplicate this whole fix exists to stop.
    psql(`update products set is_active = false where name='${NAME_A}'`);
    await goto(p, '/pos/scan');
    await scan(p, CODE_A);
    s = await state(p);
    check(s.pendingBarcode === CODE_A, 'the switched-off row still reads as a miss (BL-33)');
    await fillNewItem(p, NAME_A + ' again', 4.5);
    check(rowsNamed(NAME_A + ' again') === 0, 'no second row was created for that packet');
    check(barcodeOf(NAME_A) === CODE_A, 'and the original still owns its code', barcodeOf(NAME_A));

  } catch (e) {
    bad('the run threw', e.message);
    console.error(e);
  } finally {
    // Clean up after ourselves. These are catalogue rows; leaving them would be leaving
    // my rows in Angel's catalogue, which is a mistake I have already made twice.
    // Count FIRST. `psql -tAc "delete ... returning 1"` still prints the command tag
    // ("DELETE 0"), so counting output lines reported 1 cleaned row when it had cleaned
    // none — a cleanup that lies about what it cleaned is worse than no message.
    const n = parseInt(psql(`select count(*) from products where name like '${PROBE}%'`), 10) || 0;
    psql(`delete from products where name like '${PROBE}%'`);
    console.log(`\n🧹 removed ${n} ${PROBE} row(s) from the catalogue`);
    await browser.close();
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`  ${pass} passed · ${fail} failed`);
  console.log('='.repeat(60));
  process.exit(fail ? 1 : 0);
})();
