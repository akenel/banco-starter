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
 *
 * ⚠️ RUN ./scripts/rebuild.sh FIRST when you have edited a template. There is no
 *    bind mount here — templates are baked into the image, and a run against a
 *    stale container came back 51 pass / 0 fail having seen none of the change
 *    (2026-09-02). Section H0 now catches that by name, but only if you look.
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
const gaps = [];
function gap(l, d) { gaps.push(l); results.push({ r: 'GAP', l, d }); console.log(`  ⚠️  KNOWN GAP — ${l}${d ? '  — ' + d : ''}`); }
function head(t) { console.log(`\n${t}\n${'-'.repeat(t.length)}`); }

// ── login ───────────────────────────────────────────────────────────────────
// Token polling that SURVIVES A REDIRECT. The old tail — waitForURL, then
// networkidle, then ONE evaluate — raced the app: it lands on /pos/* and only
// THEN exchanges the code for a token in JavaScript, and the callback redirect
// can destroy the execution context mid-check. Roughly one run in four died at
// "login produced no token" on a login that had actually worked, and on
// 2026-09-02 that cost two false alarms in one evening — once accusing a change
// that was fine, once landing in a commit message before the run had finished.
// A harness that cries wolf is worse than no harness (LESSON #5).
async function waitForToken(p, ms = 25000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try {
      const t = await p.evaluate(() =>
        sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token'));
      if (t) return t;
    } catch (e) { /* a redirect destroyed the context — look again */ }
    await p.waitForTimeout(250);
  }
  return null;
}

async function loginOnce(p) {
  await p.goto(`${ROOT}/pos`, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('button:has-text("Login")', { timeout: 20000 });
  await p.click('button:has-text("Login")');
  // waitForSelector, NOT waitForFunction: clicking Login navigates CROSS-ORIGIN to
  // Keycloak, which destroys the context a polled function runs in, so it times out
  // even though the form arrived. A selector wait survives the navigation. An
  // existing SSO session skips the form entirely, so a miss here is not a failure.
  await p.waitForSelector('#username', { timeout: 12000 }).catch(() => null);
  if (await p.$('#username')) {
    await p.fill('#username', USER);
    await p.fill('#password', PASS);
    await p.click('#kc-login, input[type=submit]');
    await p.waitForURL('**/pos/**', { timeout: 20000 }).catch(() => null);
  }
  return await waitForToken(p);
}

async function login(p) {
  if (await loginOnce(p)) return;
  // One retry, because the Login button renders BEFORE Alpine binds its handler and
  // a click that lands in that gap does nothing at all.
  if (await loginOnce(p)) return;
  throw new Error(`login produced no token: ${p.url()}`);
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

      // A date belongs to the BROWSER. Chromium draws a tappable calendar and needs
      // no keyboard of any kind, so a pad there would replace a working widget with
      // a worse one. There are 12 in the POS; the one that matters is
      // checkout.html:501, ageForm.birthdate — the 18+ date of birth, which is a
      // compliance record, not a preference.
      const dates = await p.evaluate(() =>
        [...document.querySelectorAll('input[type="date"][data-keypad]')]
          .map(el => el.getAttribute('x-model') || el.id || '?'));
      check(dates.length === 0, `${s} — dates left to the browser's calendar`,
            dates.length ? 'WIRED BY MISTAKE: ' + dates.join(', ') : 'none wired');
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

      // THE FOLIO CASE. Angel, 2026-09-01: "somebody thinks, oh, I'll just snap on
      // the keyboard and start using the keyboard." The pad sets inputmode="none",
      // which suppresses a SOFT keyboard and has no authority over a real one — but
      // that is a claim until something types. keyboard.type() sends real key events,
      // the same ones the folio and the scanner gun produce.
      await p.click(nameSel);
      await p.waitForTimeout(200);
      await p.$eval(nameSel, el => { el.value = ''; el.dispatchEvent(new Event('input', { bubbles: true })); });
      await p.keyboard.type('Grüne Tips');
      await p.waitForTimeout(200);
      const typed = await p.$eval(nameSel, el => el.value);
      const typedModel = await p.evaluate(() =>
        String(Alpine.$data(document.querySelector('[x-data]')).otfName));
      check(typed === 'Grüne Tips', 'a REAL keyboard still types into a keypad field',
            `box reads "${typed}" — the folio, and the scanner gun, both send these events`);
      check(typedModel === 'Grüne Tips', 'and Alpine received what the real keyboard typed');

      // B2, found by Angel with the folio attached: our pad filters as you tap, so
      // "999.ab" is impossible from the pad and trivial from a real keyboard. The
      // fields were type="number" — policed by the browser for free — until I made
      // them type="text" so the caret would work. A scanner gun is a real keyboard
      // too, so this is not a rare case.
      await p.click(priceSel);
      await p.waitForTimeout(150);
      await p.$eval(priceSel, el => { el.value = ''; el.dispatchEvent(new Event('input', { bubbles: true })); });
      await p.keyboard.type('999.ab');
      await p.waitForTimeout(200);
      const junk = await p.$eval(priceSel, el => el.value);
      const junkModel = await p.evaluate(() =>
        String(Alpine.$data(document.querySelector('[x-data]')).otfPrice));
      check(junk === '999.', 'a REAL keyboard cannot type letters into a price', `box reads "${junk}"`);
      check(junkModel === '999.', 'and Alpine never saw the letters either', `otfPrice = "${junkModel}"`);

      await p.$eval(priceSel, el => { el.value = ''; el.dispatchEvent(new Event('input', { bubbles: true })); });
      await p.keyboard.type('12.5099');
      await p.waitForTimeout(200);
      const rappen = await p.$eval(priceSel, el => el.value);
      check(rappen === '12.50', 'and it cannot type a third rappen either', `"${rappen}"`);

      // Angel, mid-retest: "I could type 5555555, which is just crazy."
      await p.$eval(priceSel, el => { el.value = ''; el.dispatchEvent(new Event('input', { bubbles: true })); });
      await p.keyboard.type('5555555');
      await p.waitForTimeout(150);
      const capped = await p.$eval(priceSel, el => el.value);
      check(capped === '55555', 'a price stops at CHF 99999.99', `"${capped}"`);

      // OK MUST NOT NAVIGATE. The key fires on pointerdown and the pad closes
      // instantly; a finger held a moment longer is then over the bottom nav,
      // and the click that follows the release lands on Customers — taking a
      // half-built product with it. Reproduced the way a slow thumb does it:
      // press, pause, release, and let the click fall where the finger is.
      await p.click(priceSel);
      await p.waitForTimeout(200);
      const urlBefore = p.url();
      const okBox = await p.evaluate(() => {
        const b = document.querySelector('#pk-num [data-k="done"]');
        const r = b.getBoundingClientRect();
        return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
      });
      // What IS assertable: the hazard itself. If someone later moves the pad clear
      // of the nav this goes red, and that is the day the guard can be deleted.
      const hazard = await p.evaluate(() => {
        const ok = document.querySelector('#pk-num [data-k="done"]');
        const r = ok.getBoundingClientRect();
        const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2);
        document.querySelectorAll('.pk').forEach(el => el.classList.remove('on'));
        const under = document.elementFromPoint(x, y);
        const a = under && under.closest('a');
        document.querySelector('#pk-num').classList.add('on');
        return a ? a.getAttribute('href') : null;
      });
      // INVERTED 2026-09-02. This used to assert that OK sat ON TOP of a nav link,
      // to justify the guard. Angel's step C4: "if the number pad had the OK at
      // the top right you would not have the bottom line problem" — so OK moved
      // to a top strip and the overlap is gone. Removing the hazard beats racing
      // it, and the guard below stays as belt and braces.
      check(hazard === null, 'OK is NOT sitting on top of the bottom nav',
            hazard ? `under OK: ${hazard} — the overlap is back` : 'nothing under OK');

      const guarded = await p.evaluate(() => {
        const b = document.querySelector('#pk-num [data-k="done"]');
        b.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
        const nav = document.querySelector('.app-bottomnav');
        return nav ? getComputedStyle(nav).pointerEvents : 'no nav';
      });
      check(guarded === 'none', 'and closing makes that nav link inert', `pointer-events: ${guarded}`);

      // ⚠️ THE BUG ITSELF IS NOT ASSERTABLE HERE, and pretending otherwise is worse
      // than admitting it. Angel hit this with a fingertip held a moment too long;
      // Playwright's mouse.down/up in a desktop context does NOT reproduce it,
      // because preventDefault on pointerdown suppresses the synthetic click that a
      // real touchscreen still delivers. Verified: reverting shutSafely() left this
      // suite fully GREEN. Only a finger on the tablet can confirm the fix.
      gap('holding OK on a real touchscreen', 'mouse events cannot reproduce it — human check, retest sheet');
      await p.waitForTimeout(500);

      // "Press Create twice — once to get in focus and a second time to save."
      // Same family: closing the pad reclaimed its reserved space, the page
      // reflowed, and the button moved out from under the finger. Assert the
      // geometry holds still across a close.
      await p.click(priceSel);
      // SETTLE FIRST. On prod this failed at 828 -> 766 and the pad was innocent:
      // typing into Item name fires searchOwnedForOtf() on a 400ms debounce, and
      // against a 5,479-product catalogue the results land BETWEEN the two
      // measurements and push the button up. A demo catalogue returns nothing, so
      // the same code was green locally and red on the shop — the harness
      // accusing working code, which is LESSON #5's whole shape.
      await p.waitForTimeout(900);
      // And measure the SAME element twice. Re-finding "the first visible button
      // whose text matches create|add|save" can return a different button after a
      // reflow, which is a moving ruler, not a moving button.
      // :has-text() is a Playwright locator and NOT valid CSS inside evaluate().
      await p.evaluate(() => {
        const b = [...document.querySelectorAll('button')]
          .find(x => /create|add|save/i.test(x.textContent || '') && x.offsetParent !== null);
        if (b) b.setAttribute('data-pk-ruler', '1');
      });
      const btnTop = () => p.evaluate(() => {
        const b = document.querySelector('[data-pk-ruler]');
        return b ? Math.round(b.getBoundingClientRect().top) : null;
      });
      const before2 = await btnTop();
      await tapKey(p, 'done');
      await p.waitForTimeout(120);          // inside the click window
      const after2 = await btnTop();
      check(before2 !== null && before2 === after2,
            'the page does NOT jump while a tap is completing',
            `button top ${before2} -> ${after2}`);
      await p.evaluate(() => {
        const b = document.querySelector('[data-pk-ruler]');
        if (b) b.removeAttribute('data-pk-ruler');
      });
    }

    // ── E ─────────────────────────────────────────────────────────────────
    // Angel, 2026-09-01, on his phone: "in landscape it's usable, actually not
    // bad, but in portrait the keyboard is extremely small." That is a real
    // observation and a feeling — so measure it, and it stops being a feeling.
    //
    // The floor is 44px, which is Apple's HIG minimum tap target and the number
    // base.html already cites in its own phone-sizing block. Under that, a thumb
    // hits two keys. A pad taller than ~45% of the screen is the other failure:
    // the field you are typing INTO stops being visible, which is LESSON #12.
    //
    // The TABLET is the machine in the shop, so it asserts. The phone reports —
    // nobody has decided to support it yet, and a red test for an undecided
    // question is noise.
    head('E · does it fit the hand? (tablet asserts · phone reports)');
    const FORMS = [
      { name: 'tablet landscape', w: 1280, h: 800,  assert: true  },
      { name: 'tablet portrait',  w: 800,  h: 1280, assert: true  },
      { name: 'phone landscape',  w: 844,  h: 390,  assert: false },
      { name: 'phone portrait',   w: 390,  h: 844,  assert: false },
    ];
    for (const f of FORMS) {
      await p.setViewportSize({ width: f.w, height: f.h });
      await p.goto(`${ROOT}/pos/scan`, { waitUntil: 'domcontentloaded' });
      await waitAlpine(p);
      await p.evaluate(() => {
        const d = Alpine.$data(document.querySelector('[x-data]'));
        d.searchMode = 'catalog'; d.deptOpen = false;
      });
      await p.waitForTimeout(250);
      // BOTH pads, because they are not the same shape and Angel's report drew the
      // distinction precisely: "the keyboard is extremely small. Number pad is
      // basically usable." The number pad is 3 keys across; the letters are 11.
      // Measuring only the digits said phone-portrait was fine, which is the
      // opposite of what he felt — the harness was answering a question nobody
      // asked (LESSON #5).
      for (const pad of [
        { id: '#pk-num', kind: 'digits',  sel: 'input[data-keypad="decimal"][x-model="otfPrice"]' },
        { id: '#pk-abc', kind: 'letters', sel: 'input[data-keypad="text"][x-model="otfName"]' },
      ]) {
      const sel = pad.sel;
      if (!(await p.$(sel))) { continue; }
      await p.click(sel);
      await p.waitForTimeout(250);

      const m = await p.evaluate(([sel, padId]) => {
        const pad = document.querySelector(padId);
        if (!pad || !pad.classList.contains('on')) return null;
        const keys = [...pad.querySelectorAll('.pk-k')].map(k => k.getBoundingClientRect());
        const field = document.querySelector(sel).getBoundingClientRect();
        return {
          padH:  Math.round(pad.getBoundingClientRect().height),
          keyH:  Math.round(Math.min(...keys.map(r => r.height))),
          keyW:  Math.round(Math.min(...keys.map(r => r.width))),
          // is the box you are typing into still ON SCREEN, above the pad?
          fieldVisible: field.top >= 0 && field.bottom <= (window.innerHeight - pad.getBoundingClientRect().height) + 2,
          vh: window.innerHeight,
        };
      }, [sel, pad.id]);

      const who = `${f.name} · ${pad.kind}`;
      if (!m) { bad(`${who} — the pad did not open`); continue; }
      const pct = Math.round((m.padH / m.vh) * 100);
      const detail = `pad ${m.padH}px (${pct}% of ${m.vh}) · smallest key ${m.keyW}×${m.keyH}px`;
      if (f.assert) {
        check(m.keyW >= 32 && m.keyH >= 44, `${who} — keys are thumb-sized`, detail);
        check(pct <= 45,     `${who} — pad leaves the screen usable (≤45%)`, detail);
        check(m.fieldVisible, `${who} — the field is still visible above the pad`);
      } else {
        console.log(`  ℹ️  ${who} — ${detail}` +
                    `${m.keyW < 32 ? '  ⚠️ keys narrower than a fingertip' : ''}` +
                    `${pct > 45 ? '  ⚠️ pad over 45% of the screen' : ''}`);
        results.push({ r: 'INFO', l: who, d: detail });
      }
      }
    }
    await p.setViewportSize({ width: 1280, height: 1000 });

    // ── G ─────────────────────────────────────────────────────────────────
    // Angel's call after running the sheet on his own phone: "the mobile phone
    // keypad should be left alone and native. Our fixes should only be for the
    // tablet." The measurements agreed — 28px keys in portrait, 91% of the screen
    // in landscape. iOS and Android raise a good keyboard by themselves; the
    // Debian tablet is the one that does not.
    head('G · a phone keeps its own keyboard');
    {
      const phone = await b.newContext({
        hasTouch: true, isMobile: true, viewport: { width: 390, height: 844 },
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) ' +
                   'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
      });
      const pp = await phone.newPage();
      // /pos/selftest has no login gate on purpose, which also keeps this check
      // clear of the Keycloak redirect race.
      await pp.goto(`${ROOT}/pos/selftest`, { waitUntil: 'domcontentloaded' });
      await pp.waitForTimeout(1200);
      const live = await pp.evaluate(() => typeof window.posKeypad === 'object');
      const pads = await pp.evaluate(() => document.querySelectorAll('.pk').length);
      check(!live, 'iPhone — our keypad stays OUT of the way', `posKeypad=${typeof live}, pads drawn=${pads}`);
      await phone.close();
    }

    // ── F ─────────────────────────────────────────────────────────────────
    // Angel, 2026-09-01: "we have to test it in portrait AND landscape, for both
    // the mobile and the tablet... some of these screens, it might screw up."
    // Right, and section E only measures the KEYPAD. This measures the SCREEN.
    //
    // The check is horizontal overflow, which is the classic tell that a layout
    // has broken: the body is wider than the window, so the page scrolls sideways
    // and something is off the edge where nobody will look for it. base.html's own
    // rule is that wide content scrolls INSIDE its own container, never the page.
    head('F · do the screens survive being turned sideways?');
    for (const f of [
      { name: 'tablet landscape', w: 1280, h: 800  },
      { name: 'tablet portrait',  w: 800,  h: 1280 },
      { name: 'phone portrait',   w: 390,  h: 844  },
    ]) {
      await p.setViewportSize({ width: f.w, height: f.h });
      const broken = [];
      for (const s of SCREENS) {
        await p.goto(`${ROOT}${s}`, { waitUntil: 'domcontentloaded' });
        await waitAlpine(p);
        const over = await p.evaluate(() => {
          const d = document.documentElement;
          const slop = d.scrollWidth - window.innerWidth;
          if (slop <= 2) return null;
          // Name the widest offender, or the report is just a number to argue with.
          let worst = null, max = 0;
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            if (r.width > 0 && r.right > window.innerWidth + 2 && r.right > max) {
              max = r.right;
              worst = (el.tagName.toLowerCase()
                    + (el.id ? '#' + el.id : '')
                    + (el.className && typeof el.className === 'string'
                        ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''));
            }
          }
          return { slop, worst };
        });
        if (over) broken.push(`${s} (+${over.slop}px: ${over.worst})`);
      }
      check(broken.length === 0, `${f.name} — no screen scrolls sideways`,
            broken.length ? broken.join('  ·  ') : `${SCREENS.length} screens clean`);
    }
    await p.setViewportSize({ width: 1280, height: 1000 });

    // ── D ─────────────────────────────────────────────────────────────────
    // ─────────────────────────────────────────────────────────────────────────
    head('H · the 31 demo-path fields — New Sale · Shelf Intake · Checkout');
    // Added 2026-09-02, and H0 exists because of a mistake made ten minutes before
    // it: templates are BAKED INTO THE IMAGE here, there is no bind mount, and a
    // proof run against a container built before the edit came back 51/0 having
    // seen none of it. A green from a harness that cannot see the change is
    // LESSON #5 wearing a clean shirt.
    // customer_lookup joined on 2026-09-02: Angel's D4 failed there, not on the
    // demo path — "create a member" is a thing a manager does and nothing on that
    // screen had a keyboard.
    const DEMO = ['scan.html', 'shelf_intake.html', 'checkout.html', 'customer_lookup.html'];
    const disk = {};
    for (const f of DEMO) {
      disk[f] = fs.readFileSync(path.join(REPO, 'src', 'templates', 'pos', f), 'utf8');
    }

    // H0 · is the box we are testing actually running the code on disk?
    //      Counting occurrences was the naive version and it lied twice: base.html
    //      mentions data-keypad in a comment (served 24 vs disk 22), and before
    //      that the fetch used location.href, which sections F and G had moved.
    //      So name the fields instead — a miss says WHICH one is missing.
    const servedSrc = await p.evaluate(u => fetch(u, { credentials: 'same-origin' }).then(r => r.text()), `${ROOT}/pos/scan`);
    const wantModels = [...disk['scan.html'].matchAll(/<input\b[^>]*>/g)]
      .map(m => m[0]).filter(t => /data-keypad="/.test(t))
      .map(t => (/x-model[^=]*="([^"]+)"/.exec(t) || [, null])[1]).filter(Boolean);
    const missing = wantModels.filter(mdl => {
      const re = new RegExp('<input\\b[^>]*x-model[^=]*="' + mdl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '"[^>]*>');
      const tag = re.exec(servedSrc);
      return !tag || !/data-keypad="/.test(tag[0]);
    });
    check(missing.length === 0, 'the SERVER is running the scan.html on disk',
          missing.length ? `not served with a keypad: ${missing.join(', ')} — templates are BAKED INTO THE IMAGE here, run ./scripts/rebuild.sh before believing anything below`
                         : `all ${wantModels.length} wired fields on /pos/scan are the ones on disk`);

    // The static half. These read the templates, because the question is about
    // markup that a page has to be deep inside a flow to render at all — a modal,
    // a manager's price fix, an x-for row that needs a cart with something in it.
    const TAG = /<(?:input|textarea)\b[^>]*>/g;
    let badType = [], badKind = [], noMode = [], stillNumberModel = [], wired = 0;
    for (const f of DEMO) {
      for (const tag of disk[f].match(TAG) || []) {
        const kd = /data-keypad="([^"]*)"/.exec(tag);
        if (!kd) continue;
        wired++;
        const kind = kd[1];
        const where = `${f} ${(/x-model[^=]*="([^"]+)"/.exec(tag) || [, '?'])[1]}`;
        if (!['text', 'decimal', 'numeric'].includes(kind)) badKind.push(`${where}="${kind}"`);
        if (/type="number"/.test(tag)) badType.push(where);
        if (kind !== 'text' && !/inputmode="/.test(tag)) noMode.push(where);
        if (kind === 'decimal' && /x-model\.number/.test(tag)) stillNumberModel.push(where);
      }
    }
    check(badKind.length === 0, 'every data-keypad names a pad that exists', badKind.join(', ') || 'text · decimal · numeric');
    check(badType.length === 0, 'no wired field is still type="number"',
          badType.join(', ') || 'a number input has no selectionStart — the caret cannot be placed in one');
    check(noMode.length === 0, 'every number box still declares inputmode',
          noMode.join(', ') || 'the type carried the phone keyboard; inputmode carries it now');
    check(stillNumberModel.length === 0, 'no decimal box kept x-model.number',
          stillNumberModel.join(', ') || 'it re-parses "12." to 12 and eats the point mid-keystroke');

    // H5 · the sanitisers, run in the BROWSER, from the file the server shipped —
    // not from a node eval of a regex I copied out by hand.
    const san = await p.evaluate(() => {
      if (typeof window.posMoneyOnly !== 'function') return null;
      const m = window.posMoneyOnly, i = window.posIntOnly;
      return {
        money: [['999.ab', '999.'], ['12.5099', '12.50'], ['5555555', '55555'], ['abc', '']]
          .map(([a, b]) => m(a) === b).every(Boolean),
        int: [['12a3', '123'], ['1.5', '15'], ['007', '7'], ['999999', '99999']]
          .map(([a, b]) => i(a) === b).every(Boolean),
        identity: m.toString().indexOf('return v') === -1,
      };
    });
    check(san && san.identity, 'the REAL sanitisers loaded, not the identity fallback',
          san ? '' : 'window.posMoneyOnly is missing entirely');
    check(san && san.money, 'a money box refuses letters, a third rappen and CHF 5,555,555');
    check(san && san.int,   'a quantity box refuses a decimal point, a minus and a leading zero');

    // H6 · a real keyboard fires `change` when it is done with a field. The cart
    // quantity box binds :value + @change, so without this it types on the glass
    // and never reaches the cart — right on screen, wrong in the basket.
    const changed = await (async () => {
      await p.evaluate(() => {
        window.__pkChange = 0; window.__pkChange2 = 0;
        const mk = (id, n) => {
          const el = document.createElement('input');
          el.id = id; el.setAttribute('data-keypad', 'numeric');
          el.style.cssText = `position:fixed;top:${n * 40}px;left:0;z-index:99999`;
          el.addEventListener('change', () => { window['__pkChange' + (n || '')]++; });
          document.body.appendChild(el);
        };
        mk('pk-probe', 0);
        // A SECOND box, because moving to the next field is the other way out and
        // it is the one that was broken: open() reassigned `active` without ever
        // closing what it was leaving. A one-probe test cannot see that door.
        mk('pk-probe2', 2);
      });
      await p.click('#pk-probe');
      await p.waitForTimeout(250);
      const padWas = await whichPad(p);
      await tapKey(p, '6');
      const dot = await tapKey(p, '.');            // a numeric pad has no decimal point
      await p.waitForTimeout(150);
      const typed = await p.$eval('#pk-probe', el => el.value);
      await tapKey(p, 'done');
      await p.waitForTimeout(200);
      const n = await p.evaluate(() => window.__pkChange);

      // …and now the field-to-field door: type in probe 2, tap into probe 1, and
      // probe 2 must have fired exactly once WITHOUT anyone pressing DONE.
      await p.evaluate(() => { window.__pkChange = 0; window.__pkChange2 = 0; });
      await p.click('#pk-probe2');
      await p.waitForTimeout(250);
      await tapKey(p, '5');
      await p.waitForTimeout(120);
      await p.click('#pk-probe');
      await p.waitForTimeout(250);
      const across = await p.evaluate(() => window.__pkChange2);
      await tapKey(p, 'done');
      await p.waitForTimeout(200);

      await p.evaluate(() => {
        for (const id of ['pk-probe', 'pk-probe2']) {
          const e = document.getElementById(id); if (e) e.remove();
        }
      });
      return { padWas, typed, n, dot, across };
    })();
    check(changed.padWas === 'decimal', 'data-keypad="numeric" opens the NUMBER pad');
    check(changed.typed === '6', 'a numeric box refuses the decimal point ON THE PAD',
          `box reads "${changed.typed}"`);
    check(changed.n === 1, 'closing the pad fires ONE change event',
          `fired ${changed.n}× — @change handlers finalise on this`);
    check(changed.across === 1, 'moving to the NEXT box also fires change on the one you left',
          changed.across === 1
            ? 'no DONE needed — a real keyboard fires change on blur, and this is a blur'
            : `fired ${changed.across}× — the Qty box would keep its old value until DONE`);

    // H7 · THE PAD COVERING THE BOX — the real screen this time.
    // Angel, step C2 (twice): the pad still covered the price box in the manager
    // price-fix panel. Three earlier attempts at this test were deleted because
    // each passed with the fix REVERTED — they aimed at synthetic panels or at
    // fields that already worked. This one opens the actual panel: it lives in
    // the product-detail modal, which is `fixed inset-0` wrapping a
    // `max-h-[90vh] overflow-y-auto` body, and that is the whole reason padding
    // .app-content never helped.
    //
    // No writes: setting detailProduct and priceEditOpen only opens a modal.
    // user.isManager is forced because this is a LAYOUT question, not a
    // permission one — the permission is tested elsewhere.
    await p.setViewportSize({ width: 1280, height: 800 });
    await p.goto(`${ROOT}/pos/scan`, { waitUntil: 'domcontentloaded' });
    await waitAlpine(p);
    const panel = await p.evaluate(() => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      d.user = Object.assign({}, d.user, { isManager: true });
      d.detailProduct = { id: -1, name: 'ZZTEST layout probe', price: '2.00',
                          product_class: 'general', price_tiers: [], barcode: '0000000000000' };
      d.priceEdit = { price: '2.00', tiers: [] };
      d.priceEditOpen = true;
      return true;
    }).catch(() => false);
    if (panel) {
      await p.waitForTimeout(400);
      const sel = 'input[data-keypad="decimal"][x-model="priceEdit.price"]';
      const there = await p.$(sel);
      check(!!there, 'the manager price-fix box is reachable and wired');
      if (there) {
        // preventScroll is the honest substitute for a click here: p.click() auto-scrolls
        // the element into view, which is the very thing this check is measuring. But the
        // pad now waits for a real human gesture before opening (so that a screen which
        // autofocuses its search box does not come up half-covered), and a bare focus()
        // is not one. So send the pointerdown a finger would send, then focus without
        // scrolling — a tap, minus the part that would rig the measurement.
        await p.evaluate(s => {
          const el = document.querySelector(s);
          el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
          el.focus({ preventScroll: true });
        }, sel);
        await p.waitForTimeout(900);
        const m = await p.evaluate(s => {
          const pad = document.querySelector('#pk-num.on');
          const el = document.querySelector(s);
          if (!pad) return null;
          return { bottom: Math.round(el.getBoundingClientRect().bottom),
                   padTop: Math.round(window.innerHeight - pad.offsetHeight) };
        }, sel);
        check(m && m.bottom <= m.padTop,
              'the manager price-fix box is ABOVE the pad, not under it',
              m ? `field bottom ${m.bottom}, pad top ${m.padTop}` : 'no pad opened');
        await tapKey(p, 'done');
        await p.waitForTimeout(250);
      }
      await p.evaluate(() => {
        const d = Alpine.$data(document.querySelector('[x-data]'));
        d.priceEditOpen = false; d.detailProduct = null;
      });
    } else {
      gap('the manager price-fix panel', 'could not be opened in this build');
    }

    // H8 · the guard that keeps a held finger off the bottom nav must hand the
    // screen back as soon as the FINGER LIFTS, not after a fixed 400ms. A guess
    // at how long a finger rests is wrong for somebody in both directions.
    const guard = await (async () => {
      await p.evaluate(() => {
        const el = document.createElement('input');
        el.id = 'pk-probe3'; el.setAttribute('data-keypad', 'text');
        el.style.cssText = 'position:fixed;top:0;left:0;z-index:99999';
        document.body.appendChild(el);
      });
      await p.click('#pk-probe3');
      await p.waitForTimeout(250);
      const navSel = '.app-bottomnav';
      const read = () => p.evaluate(sel => {
        const n = document.querySelector(sel);
        return n ? getComputedStyle(n).pointerEvents : 'no-nav';
      }, navSel);
      await tapKey(p, 'done');                    // pointerdown + pointerup on OK
      await p.waitForTimeout(50);
      const during = await read();                // the click has not landed yet
      await p.waitForTimeout(260);
      const after = await read();                 // finger long gone
      await p.evaluate(() => { const e = document.getElementById('pk-probe3'); if (e) e.remove(); });
      return { during, after };
    })();
    check(guard.during === 'none' || guard.during === 'no-nav',
          'the nav is inert while the closing tap is still landing',
          `pointer-events: ${guard.during} at 50ms`);
    check(guard.after === 'auto' || guard.after === 'no-nav',
          'and comes back once the finger has gone — not on a fixed 400ms timer',
          `pointer-events: ${guard.after} at 310ms — dead time is the press, plus 120ms for the click`);

    // H9 · what is actually wired, counted from the templates rather than claimed.
    console.log(`  ℹ️  ${wired} boxes wired across ${DEMO.length} screens`);
    results.push({ r: 'INFO', l: 'demo path wired', d: String(wired) });

    // ─────────────────────────────────────────────────────────────────────────
    head('I · a half-counted drawer cannot leave quietly');
    // Angel, 2026-09-02: "they fill in half the coin counts and BAMM they get
    // thrown out." Ten minutes of counting lives nowhere but that screen.
    // No writes: this types into boxes and never submits.
    await p.goto(`${ROOT}/pos/shift`, { waitUntil: 'domcontentloaded' });
    await waitAlpine(p);
    const shiftReady = await p.evaluate(() => {
      try {
        const d = Alpine.$data(document.querySelector('[x-data]'));
        return !!(d && d.openCounts);
      } catch (e) { return false; }
    });
    if (!shiftReady) {
      gap('the drawer guard', 'the shift screen did not load for this user');
    } else {
      // clean first: leaving with nothing typed must NOT nag
      const cleanAsks = await p.evaluate(() => {
        window.posGo(location.pathname + '#probe');   // same document: no real navigation
        const el = document.getElementById('pos-leave-guard');
        return !!(el && el.style.display === 'flex');
      });
      check(cleanAsks === false, 'an untouched drawer screen lets you leave without a word',
            'a guard that nags when nothing is at stake is a guard people learn to dismiss');

      await p.goto(`${ROOT}/pos/shift`, { waitUntil: 'domcontentloaded' });
      await waitAlpine(p);
      const dirtyAsks = await p.evaluate(() => {
        const d = Alpine.$data(document.querySelector('[x-data]'));
        const k = Object.keys(d.openCounts)[0];
        d.openCounts[k] = 14;                       // fourteen notes counted in
        window.posGo('/pos/dashboard');
        const el = document.getElementById('pos-leave-guard');
        return {
          shown: !!(el && el.style.display === 'flex'),
          says: el ? (el.querySelector('#pos-leave-what') || {}).textContent || '' : '',
          here: location.pathname,
        };
      });
      check(dirtyAsks.shown, 'a counted drawer stops you on the way out',
            dirtyAsks.shown ? 'the modal is up' : 'it navigated away with the count');
      check(/14/.test(dirtyAsks.says), 'and it says what is at stake, with the number',
            `"${dirtyAsks.says.slice(0, 90)}"`);
      check(dirtyAsks.here === '/pos/shift', 'and it has not navigated yet', dirtyAsks.here);

      const stayed = await p.evaluate(() => {
        document.getElementById('pos-leave-stay').click();
        const el = document.getElementById('pos-leave-guard');
        return { hidden: el.style.display === 'none', here: location.pathname };
      });
      check(stayed.hidden && stayed.here === '/pos/shift',
            'Stay and finish puts you back where you were', stayed.here);

      // AND IT MUST SHUT UP ONCE THE WORK IS FILED. Angel hit this within minutes
      // of the guard shipping: on the shift REPORT, drawer already closed, he
      // pressed 🏠 and was told he was about to lose a count that was already
      // saved. The counts stay in state after a close; nothing is at stake.
      const afterFiling = await p.evaluate(() => {
        const d = Alpine.$data(document.querySelector('[x-data]'));
        d.mode = 'report';                      // the drawer is closed and filed
        window.posGo(location.pathname + '#probe2');  // same document: no real navigation
        const el = document.getElementById('pos-leave-guard');
        return !!(el && el.style.display === 'flex');
      });
      check(afterFiling === false, 'and it says NOTHING once the drawer is filed',
            afterFiling ? 'it nagged about a count that is already saved'
                        : 'a guard that fires over saved work teaches people to click through it');
    }

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

    // J RUNS LAST, AFTER THE COUNT, and that is deliberate. The coverage line
    // above counts the boxes on whatever /pos/scan looks like at that moment,
    // and the sections before it have opened panels that reveal more of them.
    // Putting this section ahead of it navigated to /pos/catalog and turned a
    // steady "31 of 33" into "16 of 19" — then "19 of 23" once I navigated back,
    // because a freshly loaded page is not the same page either. The number was
    // never wrong about what it counted; it was wrong about what it SAID it
    // counted. Move the new work, not the measurement (LESSON #5).
    // ── J · the edit modal, with the pad open ────────────────────────────────
    // Angel, on the tablet 2026-09-02, steps B4/B5/B7: "the overlap in landscape
    // makes it tough to add a second tier", "it works but very clunky", "the
    // screen gets messed up when the keypads pop up". Two of my own fixes were
    // fighting each other inside this one modal:
    //
    //   1. the panel is sized max-h-[92vh] — measured against the VIEWPORT, so
    //      lifting the overlay above the pad left a 966px panel in a 696px box.
    //      items-center split the overflow: 135px above y=0, which nothing can
    //      scroll to, and 135px behind the pad.
    //   2. padding the scroller by the pad's height — right for a page, wrong
    //      for a panel already lifted clear of the pad, and it drags a
    //      `sticky; bottom: 0` footer up into the middle of the form, because
    //      sticky resolves that 0 against the scroller's CONTENT box.
    //
    // Both are geometry, and geometry is the thing a template review cannot see
    // (LESSON #7) and a green isVisible() will lie about (LESSON #12). So this
    // section MEASURES RECTANGLES.
    head('J · the manager edit modal keeps its shape when the pad opens');
    {
      await p.goto(`${ROOT}/pos/catalog`, { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(2500);
      const editBtn = p.locator('button.cat-edit:visible').first();
      if (!(await editBtn.count())) {
        bad('could not open the edit modal', 'no visible Edit button — this check measured nothing');
      } else {
        await editBtn.click();
        await p.waitForTimeout(1200);
        const add = p.locator('button:has-text("Add break")').first();
        if (await add.count()) { await add.click(); await p.waitForTimeout(400); }
        const box = p.locator('[data-keypad="decimal"]').last();
        await box.click();
        await p.waitForTimeout(900);

        const g = await p.evaluate(() => {
          const vis = e => e && e.getBoundingClientRect().height > 10;
          const r = e => { const b = e.getBoundingClientRect();
            return { top: Math.round(b.top), bottom: Math.round(b.bottom) }; };
          const pad = [...document.querySelectorAll('div')].find(e =>
            e.offsetHeight > 200 && getComputedStyle(e).position === 'fixed'
            && Math.abs(e.getBoundingClientRect().bottom - window.innerHeight) < 2
            && e.querySelector('button'));
          const overlay = [...document.querySelectorAll('.fixed.inset-0')]
            .filter(e => e.getBoundingClientRect().height > 100).pop();
          const panel = overlay && overlay.firstElementChild;
          const bars = [...document.querySelectorAll('.modal-actions')].filter(vis);
          const bar = bars[bars.length - 1];
          const f = document.activeElement;
          return {
            vh: window.innerHeight,
            padTop: pad ? Math.round(pad.getBoundingClientRect().top) : null,
            panel: panel ? r(panel) : null,
            bar: bar ? r(bar) : null,
            field: (f && f.hasAttribute && f.hasAttribute('data-keypad')) ? r(f) : null,
          };
        });

        if (g.padTop === null || !g.panel || !g.field) {
          bad('could not measure the edit modal',
              `padTop=${g.padTop} panel=${!!g.panel} field=${!!g.field} — measured nothing`);
        } else {
          // 1. NOTHING ABOVE THE TOP OF THE SCREEN. This is the half nobody
          //    notices: content scrolled off y=0 has no scrollbar to bring it back.
          check(g.panel.top >= -1,
                'the modal does not hang off the top of the screen',
                `panel top ${g.panel.top} (was -135 before the cap)`);
          // 2. NOTHING BEHIND THE PAD.
          check(g.panel.bottom <= g.padTop + 1,
                'the modal ends above the pad',
                `panel bottom ${g.panel.bottom} · pad top ${g.padTop}`);
          // 3. THE BOX THE FINGER IS IN IS READABLE — not merely rendered.
          const ceiling = g.bar ? Math.min(g.bar.top, g.padTop) : g.padTop;
          check(g.field.bottom <= ceiling + 1,
                'the focused box is above the pad AND above the action bar',
                `field bottom ${g.field.bottom} · lowest readable ${ceiling}`);
          // 4. THE ACTION BAR SITS AT THE BOTTOM, NOT ACROSS THE FORM. This is
          //    the one that goes red on the padding bug: it landed at 225 in a
          //    panel running 8..688.
          if (g.bar) {
            check(g.bar.bottom >= g.panel.bottom - 24,
                  'the Save/Discontinue bar rides the bottom of the panel',
                  `bar ${g.bar.top}..${g.bar.bottom} · panel ends ${g.panel.bottom}`);
          } else {
            bad('no action bar found in the edit modal', 'cannot tell whether it covers the form');
          }
        }
        await p.keyboard.press('Escape').catch(() => {});
        await p.waitForTimeout(300);
      }
    }

    // ── K · no dropdown hides its own text ──────────────────────────────────
    // Angel, 2026-09-02: "the supplier selection does not show the supplier
    // name, it's always blank." It was not the data — prod held supplier_code
    // 'FTW' and FTW is an active supplier — and it was not a race. The picker
    // carried `.input-field h-10`: a 40px border-box with 16px of padding top
    // and bottom, leaving FOUR pixels for a 27px line. A <select> clips its
    // selected text to the content box, so it painted nothing.
    //
    // The Qty box beside it carries the same two classes and shows its number,
    // because an <input> does not clip that way. That is why this looked like a
    // data problem — and why only SELECTs are judged here; flagging inputs on
    // the same rule would fail on boxes that render perfectly.
    //
    // It reproduced on my machine from the first try. I missed it through five
    // probes because every one of them asked the DOM, which answered
    // selectedIndex=1 and the right option text, all the way through. Only the
    // screenshot disagreed. LESSON #12: being in the DOM is not being on screen.
    head('K · no dropdown is too short to show what it has selected');
    {
      const SCREENS = ['/pos/reorder', '/pos/catalog', '/pos/shelf-intake', '/pos/checkout'];
      let squashed = 0, looked = 0;
      for (const url of SCREENS) {
        await p.goto(`${ROOT}${url}`, { waitUntil: 'domcontentloaded' }).catch(() => null);
        await p.waitForTimeout(2200);
        const found = await p.evaluate(() => {
          const out = [];
          for (const el of document.querySelectorAll('select')) {
            const r = el.getBoundingClientRect();
            if (r.height < 1 || r.width < 1) continue;
            const cs = getComputedStyle(el);
            if (cs.visibility === 'hidden' || cs.display === 'none') continue;
            let lh = parseFloat(cs.lineHeight);
            if (!isFinite(lh)) lh = parseFloat(cs.fontSize) * 1.2;
            const inner = r.height
              - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom)
              - parseFloat(cs.borderTopWidth) - parseFloat(cs.borderBottomWidth);
            out.push({ cls: (el.className || '').toString().slice(0, 44),
                       inner: Math.round(inner), lh: Math.round(lh), ok: inner + 0.5 >= lh });
          }
          return out;
        });
        looked += found.length;
        for (const f of found) {
          if (!f.ok) {
            squashed++;
            console.log(`  ❌ ${url} — a dropdown has ${f.inner}px for a ${f.lh}px line`
                      + `  · class="${f.cls}"`);
          }
        }
      }
      check(squashed === 0 && looked > 0,
            'every dropdown has room for one line of its own text',
            looked === 0 ? 'NO dropdowns found on any screen — this check measured nothing'
                         : `${looked} dropdowns across ${SCREENS.length} screens`);
    }

    // ---- L · a box is the size its markup asks for -------------------------
    // Companion to K, and the same root cause seen from the other side.
    // tailwind.css is linked at the top of pos/base.html; `.input-field` is
    // declared in the <style> block BELOW it. Both are one class, so on equal
    // specificity SOURCE ORDER decided every fight, and `.input-field` won every
    // property it declares — width, padding, font-size. Six boxes across the POS
    // asked for a small width and rendered full width, with the class still
    // sitting in the markup looking like it worked.
    //
    // The worst was the Order Book's per-line Qty: `w-16` (64px) rendering at
    // 790px, which wrapped a one-line row onto THREE and cost a third of the
    // visible list on a counter tablet. Angel had already reported it in words
    // — "the order book's Qty box asks for w-16 and renders full width" — and it
    // sat there because nothing measured it. Fixed 2026-09-03 by moving width
    // into `:where(.input-field)` (zero specificity) and adding `.input-compact`
    // for the small boxes, whose padding would otherwise eat them.
    //
    // L2 is the trap that fix opens: a 64px box carrying `.input-field`'s 1.25rem
    // side padding has ~20px of content for a four-digit quantity. Narrow WITHOUT
    // `input-compact` is a bug even though every width now measures correct.
    head('L · every sized box renders the width its markup asks for');
    {
      const SCREENS = ['/pos/reorder', '/pos/receiving', '/pos/suppliers',
                       '/pos/checkout', '/pos/shelf-intake', '/pos/catalog'];
      let wrong = 0, squeezed = 0, looked = 0;
      for (const url of SCREENS) {
        await p.goto(`${ROOT}${url}`, { waitUntil: 'domcontentloaded' }).catch(() => null);
        await p.waitForTimeout(2200);
        // Two of the six live in the edit-product modal (the price-tier row), so
        // this check is blind to them unless it opens the thing first.
        if (url === '/pos/catalog') {
          const edit = p.locator('button.cat-edit').first();
          if (await edit.count()) {
            await edit.click().catch(() => null);
            await p.waitForTimeout(1500);
            const add = p.locator('button:has-text("Add break")').first();
            if (await add.count()) { await add.click().catch(() => null); await p.waitForTimeout(600); }
          }
        }
        const found = await p.evaluate(() => {
          // Tailwind's scale in px at a 16px root. Only fixed widths — a
          // fraction or `w-full` is relative and has nothing to compare against.
          const SCALE = { 'w-12': 48, 'w-14': 56, 'w-16': 64, 'w-20': 80, 'w-24': 96,
                          'w-28': 112, 'w-32': 128, 'w-36': 144, 'w-40': 160 };
          const out = [];
          for (const el of document.querySelectorAll('.input-field')) {
            const r = el.getBoundingClientRect();
            if (r.width < 1 || r.height < 1) continue;
            const cs = getComputedStyle(el);
            if (cs.visibility === 'hidden' || cs.display === 'none') continue;
            const cls = (el.className || '').toString();
            const asked = cls.split(/\s+/).find(c => SCALE[c]) || null;
            out.push({ asked, want: asked ? SCALE[asked] : null,
                       got: Math.round(r.width),
                       compact: /(^|\s)input-compact(\s|$)/.test(cls),
                       cls: cls.slice(0, 46) });
          }
          return out;
        });
        for (const f of found) {
          looked++;
          if (f.asked && Math.abs(f.got - f.want) > 6) {
            wrong++;
            console.log(`  \u274c ${url} \u2014 asked ${f.asked} (${f.want}px), rendered ${f.got}px`
                      + `  \u00b7 class="${f.cls}"`);
          }
          if (f.got < 120 && !f.compact) {
            squeezed++;
            console.log(`  \u274c ${url} \u2014 ${f.got}px wide with full padding and no`
                      + ` input-compact  \u00b7 class="${f.cls}"`);
          }
        }
      }
      check(wrong === 0 && looked > 0,
            'a width utility on an input is honoured, not silently ignored',
            looked === 0 ? 'NO .input-field found on any screen \u2014 this measured nothing'
                         : `${looked} boxes across ${SCREENS.length} screens`);
      check(squeezed === 0,
            'no narrow box is left with the full-width padding that would eat it',
            'a box under 120px needs .input-compact');
    }


  } catch (e) {
    bad('the run itself', e.message);
  } finally {
    await b.close();
  }

  console.log('\n' + '='.repeat(74));
  console.log(`  ${pass} pass · ${fail} fail${gaps.length ? ' · ' + gaps.length + ' known gap' + (gaps.length > 1 ? 's' : '') : ''}`);
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
