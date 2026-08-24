// A customer can join with NO name. Driven in a browser, because that is where it broke.
//
//   NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-kiosk-blank-username.js
//
// WHY THIS EXISTS. On 2026-08-22 the signup was changed so a blank username gets the shop's own
// ART-AB12 code — "nobody has to invent a name". The SERVER was fixed, the Pydantic schema was
// fixed (it had been typed `str` and rejected blank before the handler could run), and 8 unit
// tests pinned it. All green. Then on 2026-08-24 Angel opened the kiosk on his phone and the
// form said "3–30 letters" and would not submit: `submitSignup()` tested the pattern against an
// empty string with no blank check. Every layer a test could reach was correct, and the one the
// customer was standing on was not — CLAUDE.md pattern 1, ×9.
//
// A unit test could not have caught it. This has to be a browser, filling the real form.
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };

(async () => {
  const b = await chromium.launch();
  // A PHONE viewport on purpose: `source` is 'phone' when isTouch, which is the path Angel hit,
  // and it is the one that offers the bigger discount — so it is the one worth proving.
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 200)));

  // The kiosk opens in GERMAN. Switch to English first so the assertions below can quote exact
  // strings — the first version of this script looked for "Join" on a page that said
  // "Mitglied werden" and never opened the form at all.
  async function openSignup() {
    await p.goto(ROOT + '/pos/kiosk', { waitUntil: 'networkidle' });
    await p.waitForTimeout(700);
    await p.locator('button:has-text("🇬🇧")').first().click({ timeout: 5000 }).catch(() => {});
    await p.waitForTimeout(500);
    // The join button is the one wired to startSignup(); text varies by language and by
    // whether the shop is running an offer at all, so go by the handler, not the words.
    await p.locator('[\\@click="startSignup()"]').first().click({ timeout: 10000 });
    await p.waitForTimeout(700);
  }

  // SCOPE EVERY LOCATOR TO THE SIGNUP FORM. The page carries a second, always-present form —
  // the scan box — and `form input` first-matched THAT: one check failed for the wrong reason
  // and another passed vacuously by reading an empty box that was never the one under test.
  // The signup form is the only one with checkboxes (18+ and marketing).
  const signup = () => p.locator('form:has(input[type=checkbox])').first();
  const userBox = () => signup().locator('input[type=text], input:not([type])').first();

  await openSignup();
  ok('the signup form is open', await signup().isVisible().catch(() => false));

  // LEAVE THE USERNAME BLANK. Tick only 18+.
  await signup().locator('input[type=checkbox]').first().check({ timeout: 5000 });
  ok('the username box is genuinely empty', (await userBox().inputValue()) === '');

  await signup().locator('button[type=submit]').first().click();
  await p.waitForTimeout(2500);

  const body = await p.evaluate(() => document.body.innerText);
  const code = (body.match(/\bART-[0-9A-Z]{4}\b/) || [])[0];
  ok(`joining with no name succeeds and the shop assigns a code (${code || 'NONE FOUND'})`, !!code);
  ok('no "3–30 letters" error is shown', !/3\s*[–-]\s*30/.test(body));
  ok('the code is on screen for them to keep', !!code && /screenshot|Screenshot|remember|merk/i.test(body));

  // The pattern must STILL be enforced when they do type something bad — the fix must not
  // have turned the rule off, only made it conditional on there being something to judge.
  await openSignup();
  await userBox().fill('!!');
  await signup().locator('input[type=checkbox]').first().check();
  await signup().locator('button[type=submit]').first().click();
  await p.waitForTimeout(1200);
  const body2 = await p.evaluate(() => document.body.innerText);
  ok('a BAD typed username is still refused', /3\s*[–-]\s*30|letters/i.test(body2) && !/\bART-[0-9A-Z]{4}\b/.test(body2));

  ok(`no page errors (${errs.join(' | ') || 'none'})`, errs.length === 0);
  await b.close();
  console.log(`\n${fail ? '❌' : '✅'} ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})();
