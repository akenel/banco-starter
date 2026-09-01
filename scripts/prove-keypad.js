#!/usr/bin/env node
/**
 * prove-keypad.js — the on-screen keypad, in a real browser, with a real touchscreen.
 *
 * WHY THIS EXISTS
 * ---------------
 * On 2026-09-01 the keypad was deployed to the till and did nothing, for an hour,
 * with no error anywhere. It was wired to the wrong two fields — `lazyName`, the
 * form you reach after a SCANNED barcode misses, instead of `otfName`, the
 * on-the-fly form a cashier actually opens. Both are on scan.html, forty lines
 * apart, and to a grep they look the same. The screen tells them apart: one says
 * "Product name", the other says "Item name", and Angel had been saying "Item
 * name" since his first message.
 *
 * Nothing in the repo could have caught it. So: this.
 *
 * WHAT IT ASSERTS
 *   A  the keypad script is ALIVE on every screen a cashier can reach
 *      (it can switch itself off on a device it thinks has no touchscreen —
 *       the single most dangerous line in it)
 *   B  no DO-NOT-TOUCH field has been given a keypad. The scanner gun types into
 *      those as a hardware keyboard, and shelf-intake takes a scan OR typing.
 *      A pad there does not break the gun; it throws a keyboard over half the
 *      screen on every scan.
 *   C  on NEW ITEM — the screen this all started on — Item name opens LETTERS,
 *      Price opens DIGITS, the keys reach Alpine's model, the caret is honoured,
 *      and a third rappen is refused.
 *   D  coverage: how many fields are wired, and how many are not. Reported, not
 *      failed — it is a progress number, not a defect.
 *
 * ⚠️ WHAT IT CANNOT SEE. It runs here, in a simulated touch context, not on the
 *    counter tablet. It proves WIRING — is the field marked, does the right pad
 *    open, does the value land. It cannot prove how anything FEELS, and it cannot
 *    see GNOME. That stays a human on the tablet, once — not sixty-five times.
 *    (LESSON #6: ask what your harness is structurally blind to.)
 *
 * It rings NO sales, writes NO rows and touches no money. Safe against any box.
 *
 * RUN
 *   NODE_PATH=<dir with playwright> node scripts/prove-keypad.js
 *   NODE_PATH=... node scripts/prove-keypad.js --save   # write the baseline
 *   BANCO_URL=https://banco.wolfhold.app NODE_PATH=... node scripts/prove-keypad.js
 */
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
const USER = process.env.BANCO_USER || 'ralph';
const PASS = process.env.BANCO_PASS || 'ralph';
const REPO = path.resolve(__dirname, '..');
const SAVE = process.argv.includes('--save');

// The screens a cashier reaches. Manager/admin screens wait their turn.
const SCREENS = [
  '/pos/scan', '/pos/checkout', '/pos/customer-lookup',
  '/pos/shelf-intake', '/pos/my-day', '/pos/selftest',
];

let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  console.error('playwright not found. Point NODE_PATH at a node_modules that has it:');
  console.error('  NODE_PATH=/path/to/node_modules node scripts/prove-keypad.js');
  process.exit(2);
}

let pass = 0, fail = 0;
const results = [];
function ok(l, d)  { pass++; results.push({ r: 'PASS', l, d }); console.log(`  ✅ ${l}${d ? '  — ' + d : ''}`); }
function bad(l, d) { fail++; results.push({ r: 'FAIL', l, d }); console.log(`  ❌ ${l}${d ? '  — ' + d : ''}`); }
function check(c, l, d) { (c ? ok : bad)(c ? l : l, d); return !!c; }
function head(t) { console.log(`\n${t}\n${'-'.repeat(t.length)}`); }

async function login(p) {
  await p.goto(`${ROOT}/pos`, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('button:has-text("Login")', { timeout: 20000 });
  await p.click('button:has-text("Login")');
  // waitForFunction is WRONG here and it is wrong in the older proofs too: clicking
  // Login navigates CROSS-ORIGIN to Keycloak on :8090, which destroys the execution
  // context the function is being polled in, so it times out even though the form
  // arrived. Waiting on a selector survives the navigation.
  await p.waitForSelector('#username', { timeout: 20000 }).catch(() => null);
  if (await p.$('#username')) {
    await p.fill('#username', USER);
    await p.fill('#password', PASS);
    await p.click('#kc-login, input[type=submit]');
    await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  await p.waitForLoadState('networkidle');
  const authed = await p.evaluate(() =>
    !!(sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token')));
  if (!authed) throw new Error(`login produced no token: ${p.url()}`);
}

// Alpine mounts asynchronously; evaluate() before it is ready reads as a broken page.
async function waitAlpine(p) {
  await p.waitForFunction(() => {
    const el = document.querySelector('[x-data]');
    if (!el || !window.Alpine) return false;
    try { return !!Alpine.$data(el); } catch (e) { return false; }
  }, null, { timeout: 20000 }).catch(() => {});
  await p.waitForTimeout(300);
}

/** Which pad is on screen right now: 'decimal' | 'text' | null. */
function whichPad(p) {
  return p.evaluate(() => {
    const n = document.querySelector('#pk-num'), a = document.querySelector('#pk-abc');
    const on = el => el && el.classList.contains('on') && el.offsetHeight > 0;
    if (on(n)) return 'decimal';
    if (on(a)) return 'text';
    return null;
  });
}
const tapKey = (p, k) => p.evaluate(k => {
  const b = document.querySelector(`.pk.on [data-k="${k}"]`);
  if (!b) return false;
  b.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
  b.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }));
  return true;
}, k);

async function main() {
  console.log('='.repeat(74));
  console.log(`prove-keypad.js  —  ${ROOT}  —  simulated touchscreen`);
  console.log('='.repeat(74));

  const b = await chromium.launch({ headless: process.env.BANCO_HEADED !== '1' });
  // hasTouch is the whole point: without it maxTouchPoints is 0, posIsTouchDevice()
  // returns false and the script switches itself off — which is exactly the failure
  // mode a test running on a laptop would otherwise never see.
  const ctx = await b.newContext({ hasTouch: true, viewport: { width: 1280, height: 1000 } });
  const p = await ctx.newPage();

  try {
    await login(p);
    console.log(`logged in as ${USER}\n`);

    // ── A ─────────────────────────────────────────────────────────────────
    head('A · the keypad script is alive on every cashier screen');
    for (const s of SCREENS) {
      await p.goto(`${ROOT}${s}`, { waitUntil: 'domcontentloaded' });
      await waitAlpine(p);
      const alive = await p.evaluate(() => typeof window.posKeypad === 'object');
      const touch = await p.evaluate(() => navigator.maxTouchPoints);
      check(alive, `${s} — script active`, `maxTouchPoints=${touch}`);
    }

    // ── B ─────────────────────────────────────────────────────────────────
    head('B · no scanner field has been given a keypad');
    for (const s of SCREENS) {
      await p.goto(`${ROOT}${s}`, { waitUntil: 'domcontentloaded' });
      await waitAlpine(p);
      const offenders = await p.evaluate(() => {
        const SCANNER = /barcode|scan|sku|\bean\b|\bcode\b|gtin|upc/i;
        return [...document.querySelectorAll('input[data-keypad]')]
          .filter(el => SCANNER.test([el.id, el.name, el.placeholder,
                                      el.getAttribute('x-model') || ''].join(' ')))
          .map(el => el.id || el.getAttribute('x-model') || el.placeholder || '?');
      });
      check(offenders.length === 0, `${s} — scanner fields left alone`,
            offenders.length ? 'WIRED BY MISTAKE: ' + offenders.join(', ') : 'none wired');
    }

    // ── C ─────────────────────────────────────────────────────────────────
    head('C · NEW ITEM — the screen this started on');
    await p.goto(`${ROOT}/pos/scan`, { waitUntil: 'domcontentloaded' });
    await waitAlpine(p);
    // The on-the-fly form shows when searchMode==='catalog' and no department is open
    // (scan.html:265). Driving Alpine directly keeps this about the KEYPAD and not
    // about however the operator happened to arrive at the form.
    await p.evaluate(() => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      d.searchMode = 'catalog'; d.deptOpen = false;
    });
    await p.waitForTimeout(300);

    const nameSel  = 'input[data-keypad="text"][x-model="otfName"]';
    const priceSel = 'input[data-keypad="decimal"][x-model="otfPrice"]';

    const hasName  = await p.$(nameSel);
    const hasPrice = await p.$(priceSel);
    check(!!hasName,  'Item name is marked data-keypad="text"');
    check(!!hasPrice, 'Price (CHF) is marked data-keypad="decimal"');

    if (hasName && hasPrice) {
      await p.click(nameSel);
      await p.waitForTimeout(250);
      check(await whichPad(p) === 'text', 'tapping Item name opens the LETTER pad',
            'the field a cashier types a product name into');

      await p.click(priceSel);
      await p.waitForTimeout(250);
      check(await whichPad(p) === 'decimal', 'tapping Price opens the NUMBER pad');

      // Alpine's x-model listens for `input`. Setting .value alone leaves the box
      // showing a price the model never received — the screen and the truth
      // disagreeing, and the screen is what a person believes (LESSON #13).
      for (const k of ['1', '2', '.', '5', '0']) await tapKey(p, k);
      await p.waitForTimeout(200);
      const shown = await p.$eval(priceSel, el => el.value);
      const model = await p.evaluate(() =>
        String(Alpine.$data(document.querySelector('[x-data]')).otfPrice));
      check(shown === '12.50', 'the pad types 12.50 into the box', `box reads "${shown}"`);
      check(model === '12.50', 'and Alpine RECEIVED it', `otfPrice = "${model}"`);

      await tapKey(p, '9');
      await p.waitForTimeout(150);
      const third = await p.$eval(priceSel, el => el.value);
      check(third === '12.50', 'a third rappen is refused', `still "${third}"`);

      // The caret is the truth: v2 appended every key to the end, so correcting one
      // letter cost the whole word.
      await p.$eval(priceSel, el => el.setSelectionRange(2, 2));
      await tapKey(p, '3');
      await p.waitForTimeout(150);
      const caret = await p.$eval(priceSel, el => el.value);
      check(caret === '123.50', 'a key lands AT THE CARET, not at the end', `"${caret}"`);
    }

    // ── D ─────────────────────────────────────────────────────────────────
    head('D · coverage (reported, not failed — this is a progress number)');
    const cov = await p.evaluate(() => {
      const all = [...document.querySelectorAll('input, textarea')].filter(el => {
        const t = (el.type || 'text').toLowerCase();
        return !['hidden','checkbox','radio','file','date','submit','button'].includes(t);
      });
      return { total: all.length, wired: all.filter(el => el.hasAttribute('data-keypad')).length };
    });
    console.log(`  /pos/scan — ${cov.wired} of ${cov.total} typable inputs wired`);
    results.push({ r: 'INFO', l: 'coverage /pos/scan', d: `${cov.wired}/${cov.total}` });

  } catch (e) {
    bad('the run itself', e.message);
  } finally {
    await b.close();
  }

  console.log('\n' + '='.repeat(74));
  console.log(`  ${pass} pass · ${fail} fail`);
  console.log('='.repeat(74) + '\n');

  if (SAVE) {
    const dest = path.join(REPO, 'docs', 'keypad-baseline.json');
    fs.writeFileSync(dest, JSON.stringify(
      { at: new Date().toISOString(), url: ROOT, pass, fail, results }, null, 2));
    console.log(`  baseline written: ${path.relative(REPO, dest)}\n`);
  }
  process.exit(fail ? 1 : 0);
}

main();
