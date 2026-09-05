// When the till window stops filling the screen, the screen must SAY SO.
//
// WHY THIS FILE EXISTS. Layla, 2026-09-04 21:29, looking at a strip of till and a field
// of desktop wallpaper: "i will reboot to resolve this issue — only thing a cashier could
// do." The ⛶ button that fixes it in one tap was on her screen the entire time.
//
// Angel hit the same thing on 2026-09-05, used the toggle, and named the real problem:
// "maybe the user gets stuck in that mode and doesn't realize what they're doing."
//
// A title bar is a drag handle on a touchscreen, and it cannot be removed without also
// removing the system bar — battery, wifi — which is the trade written into
// banco-till.service and deliberately kept. What CAN be fixed is the silence afterwards.
//
// WHAT THIS REPLACED. A GNOME Shell extension that snapped the window back. Built,
// loaded, reported State: ACTIVE — and did nothing at all, because it matched wm_class
// "chromium" and a window launched with --app= is called something else entirely. Angel
// found that by dragging a window; no check could have. It was then removed on purpose,
// not because it was broken: custom code inside the compositor on a machine that takes
// money, silently undoing anything deliberate, fixing a symptom while teaching nobody
// anything. This lives in our own code where a proof can hold it to account.
//
// ⚠️ THE SCREEN IS SIMULATED, AND IT HAS TO BE. Playwright reports
// screen.availWidth === innerWidth, so "a window smaller than its screen" cannot occur
// there naturally. Sections B and D stub screen.availWidth / screenX to make the window
// smaller than the display — which is the exact real condition, not a proxy for it.
// Section A runs UNSTUBBED, so the quiet case is proved against the browser's own truth
// and the stub is not doing all the work.
const { chromium } = require('playwright');

const APP = 'http://localhost:3000/pos';

(async () => {
  const b = await chromium.launch();
  let pass = 0, fail = 0;
  const check = (ok, what, detail) => {
    if (ok) { pass++; console.log('  ✅ ' + what); }
    else { fail++; console.log('  ❌ ' + what + (detail ? '\n       ' + detail : '')); }
  };

  const login = async (p) => {
    await p.goto(APP, { waitUntil: 'domcontentloaded' });
    if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
    if (await p.$('#username')) {
      await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
      await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
    }
    await p.waitForTimeout(1200);
  };
  const state = (p) => p.evaluate(() => {
    const n = document.getElementById('fs-nudge');
    const t = document.getElementById('fs-toggle');
    const vis = el => !!el && !el.hidden && getComputedStyle(el).display !== 'none';
    return {
      nudgeExists: !!n, nudgeVisible: vis(n), nudgeText: n ? n.textContent.trim() : null,
      toggleVisible: vis(t),
      innerWidth: window.innerWidth, availWidth: screen.availWidth, screenX: window.screenX,
    };
  });

  // ── A · THE QUIET CASE, UNSTUBBED ────────────────────────────────────────────────────
  // The window fills the screen, so the till says nothing. This is the step whose expected
  // result is that NOTHING happens, and it runs against the browser's real numbers.
  console.log('\n── A · a window that fills the screen says nothing ──');
  {
    const ctx = await b.newContext({ hasTouch: true, viewport: { width: 1440, height: 895 } });
    const p = await ctx.newPage();
    await login(p);
    await p.waitForTimeout(2600);              // longer than the 2s poll
    const s = await state(p);
    check(s.nudgeExists, 'the nudge is in the page');
    check(s.toggleVisible, 'the ⛶ toggle is showing (touch device)');
    check(s.innerWidth === s.availWidth, `and the window really does fill it (${s.innerWidth} of ${s.availWidth}) — unstubbed`);
    check(!s.nudgeVisible, 'the nudge stays HIDDEN', 'it is nagging about a window that is fine');
    await ctx.close();
  }

  // ── B · SQUEEZED: NARROWER THAN THE SCREEN ───────────────────────────────────────────
  console.log('\n── B · dragged off maximised — narrower than the screen ──');
  {
    const ctx = await b.newContext({ hasTouch: true, viewport: { width: 1000, height: 800 } });
    const p = await ctx.newPage();
    // A 1920-wide display behind a 1000-wide window: exactly what GNOME leaves behind
    // when a maximised window is dragged.
    await p.addInitScript(() => Object.defineProperty(screen, 'availWidth', { get: () => 1920 }));
    await login(p);
    await p.waitForTimeout(2600);
    const s = await state(p);
    check(s.innerWidth < s.availWidth, `the window is ${s.innerWidth} on a ${s.availWidth} screen`);
    check(s.nudgeVisible, 'the till SAYS SO — the nudge appears',
          'the window is two-thirds of the screen and nothing on it mentions the fix');
    check(/fill the screen/i.test(s.nudgeText || ''), `and it names the remedy — "${s.nudgeText}"`);

    // Tapping the sentence must do the same thing as tapping the icon. A cashier reading
    // "tap ⛶" while holding somebody's change should not have to find a second target.
    const fired = await p.evaluate(async () => {
      let called = 0;
      const el = document.documentElement;
      el.requestFullscreen = function () { called++; return Promise.resolve(); };
      document.getElementById('fs-nudge').click();
      await new Promise(r => setTimeout(r, 300));
      return called;
    });
    check(fired === 1, 'and tapping the sentence itself asks for full screen',
          `requestFullscreen called ${fired} times`);
    await ctx.close();
  }

  // ── C · SHOVED PAST THE EDGE, SAME WIDTH ─────────────────────────────────────────────
  // The other way a window goes wrong, and the one a resize event never reports: full
  // width, dragged so its right-hand side is off the glass. Angel's original symptom.
  console.log('\n── C · full width, but pushed off the edge ──');
  {
    const ctx = await b.newContext({ hasTouch: true, viewport: { width: 1440, height: 895 } });
    const p = await ctx.newPage();
    await p.addInitScript(() => {
      Object.defineProperty(screen, 'availWidth', { get: () => 1440 });
      Object.defineProperty(window, 'screenX', { get: () => 700 });   // half of it off the right
    });
    await login(p);
    await p.waitForTimeout(2600);
    const s = await state(p);
    check(s.innerWidth === s.availWidth, `the window is full width (${s.innerWidth}) — a resize event would never fire`);
    check(s.nudgeVisible, 'and the nudge appears anyway, because it also watches WHERE the window is',
          'only the width is being checked, so a dragged window goes unnoticed — which is the exact bug');
    await ctx.close();
  }

  // ── D · NOT ON A MACHINE WITH A WINDOW MANAGER YOU ALREADY KNOW ──────────────────────
  // The same gate the keypad and the toggle use. A laptop has a window manager the person
  // knows; nagging them about it is noise.
  console.log('\n── D · a non-touch machine is left alone ──');
  {
    const ctx = await b.newContext({ viewport: { width: 1000, height: 800 } });   // no hasTouch
    const p = await ctx.newPage();
    await p.addInitScript(() => Object.defineProperty(screen, 'availWidth', { get: () => 1920 }));
    await login(p);
    await p.waitForTimeout(2600);
    const s = await state(p);
    check(!s.toggleVisible, 'the ⛶ toggle stays hidden on a non-touch machine');
    check(!s.nudgeVisible, 'and so does the nudge, on a window that IS squeezed',
          'a laptop user is being nagged about a window manager they already know');
    await ctx.close();
  }

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
