// ============================================================================
// prove-the-shift-row-closes — the attendance row must close on logout even when
// the access token is already dead, because that is the logout that actually happens.
//
// WHY THIS EXISTS (2026-09-19). Four attendance rows on the live shop were still
// ACTIVE days after the fact, one since 17 September. There is no "End Shift" button:
// `shift/end` is fired inside AuthHelper.logout() as a best-effort call using whatever
// access token is in hand. The access token lives FIVE MINUTES. So on the one logout
// that matters — the one that happens because the session timed out — it posted a dead
// token, took a 401, and `.catch(() => {})` ate it.
//
// It worked on every layer I could reach. A probe logs in and logs straight out with a
// token seconds old, and that path is perfect. LESSON #1, again: ask what the person is
// actually doing when they need it. She is going home at 19:00 having last touched the
// till at 17:46.
//
// THE DISCRIMINATOR. Test A stales the access token and keeps the refresh token, which is
// exactly the shape of a real end-of-day logout, and then asks the DATABASE whether the row
// closed. Verified both ways by reverting logout() and rebuilding (LESSON #4 — if you did
// not watch it fail, you do not know it works):
//
//     reverted →  ❌ order seen: ["end"]          ❌ ACTIVE rows still open: 1
//     fixed    →  ✅ refresh before end            ✅ no ACTIVE session left
//
// Test B is the control: an ordinary logout with a live token must STILL close the row, and
// it passes on BOTH versions. That is not padding — it is the reason this bug lived for
// months. The easy path was always perfect, so nothing anybody ran could see the hard one.
//
// Do NOT assert on the shift/end HTTP status here. Two attempts at it came back empty:
// logout redirects to Keycloak the instant the close is away, and the navigation tears down
// both the response listener and the route handler. The row is the outcome; ask for that.
//
//   NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-the-shift-row-closes.js
// ============================================================================
const { chromium } = require('playwright');
const { execSync } = require('child_process');

// THE OUTCOME, not the wire. Two attempts to read the shift/end STATUS in the browser came
// back empty — logout redirects to Keycloak the instant the close is away, and the
// navigation tears down both the response listener and the route handler. The status was
// never the question anyway. The question is whether the row closed, so ask the database.
function activeRows(who) {
  const sql = `SELECT count(*) FROM shift_sessions WHERE username='${who}' AND status='ACTIVE';`;
  const out = execSync(
    `docker exec -i banco-postgres psql -U helix_user -d helix_db -At -c "${sql}"`,
    { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] });
  return parseInt(out.trim(), 10);
}
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT)) {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script logs users in and out.`);
  process.exit(2);
}
let pass = 0, fail = 0;
const ok = (n, c, extra) => {
  c ? (pass++, console.log('  ✅ ' + n))
    : (fail++, console.log('  ❌ ' + n + (extra ? '  → ' + extra : '')));
};

// Two harness faults were fixed in here, and both of them ACCUSED WORKING CODE (LESSON #5).
//  1. It waited on the URL. waitForURL('**/pos/**') resolves at /pos/callback, which is
//     BEFORE the token is written — so the fixed sleep after it was a race. Wait for the
//     TOKEN, which is the thing the next step actually needs.
//  2. It assumed one attempt. This script logs the same user out through Keycloak's logout
//     endpoint and then straight back in on the next run; that leaves the landing page in
//     its "Stuck on already logged in?" state and the callback comes back with no code, so
//     the second attempt lands on /pos with no token. Retry, and say so when it happens.
async function login(p, who) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(400);
    if (await p.$('button:has-text("Login")')) {
      await p.click('button:has-text("Login")');
      await p.waitForTimeout(3500);
    }
    if (await p.$('#username')) {
      await p.fill('#username', who);
      await p.fill('#password', who);
      await p.click('#kc-login, input[type=submit]');
    }
    try {
      await p.waitForFunction(() => !!sessionStorage.getItem('pos_token'), null,
                              { timeout: 15000, polling: 200 });
    } catch (e) { /* reported below */ }
    if (await p.evaluate(() => sessionStorage.getItem('pos_token'))) {
      if (attempt > 1) console.log(`     ↳ (logged in on attempt ${attempt})`);
      return true;
    }
  }
  console.log('     ↳ url:', p.url());
  console.log('     ↳ body:', (await p.evaluate(() => document.body.innerText)).slice(0, 140).replace(/\n/g, ' | '));
  return false;
}

// Watch the wire, not the DOM: the only question is what the server did.
// `seq` records ORDER, which is the structural thing the fix changes and the one signal
// that does not depend on timing. A token-state assertion here proved flaky — a dashboard
// fetch 401s on the staled token and the API helper silently renews it, so "is the token
// still stale?" measures the dashboard, not logout(). Order cannot be faked that way.
function watchWire(p) {
  const w = { seq: [], endStatuses: [] };
  p.on('request', r => {
    const u = r.url();
    if (u.includes('/pos/refresh')) w.seq.push('refresh');
    else if (u.includes('/api/v1/pos/shift/end')) w.seq.push('end');
  });
  p.on('response', r => {
    if (r.url().includes('/api/v1/pos/shift/end')) w.endStatuses.push(r.status());
  });
  return w;
}

async function clickLogout(p) {
  // The dashboard guards logout with confirm(). Playwright auto-DISMISSES dialogs, which
  // would cancel the very thing under test, so accept it explicitly and drive the real
  // button — not AuthHelper.logout() directly. What is being proven is the path a cashier
  // takes at the end of her day.
  p.once('dialog', d => d.accept().catch(() => {}));
  const btn = await p.$('button[data-i18n="dashboard.logout"]');
  if (!btn) return false;
  await btn.click();
  await p.waitForTimeout(4000);   // logout awaits refresh + close, bounded at 1.5s each
  return true;
}

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 1000 } });
  const p = await ctx.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message.slice(0, 160)));

  try {
    // CLEAN FIRST, and this one is earned. Ten runs of this script left stuck ACTIVE rows
    // behind; login REUSES an existing ACTIVE row rather than opening a new one, so one
    // stuck row from an earlier run made the CONTROL fail and I spent a while reading it as
    // a regression. `prove-bad-price-is-visible.js` carries the same warning in its own
    // words: a prover that does not tidy up poisons its next run and blames the code.
    try {
      execSync(`docker exec -i banco-postgres psql -U helix_user -d helix_db -q -c ` +
               `"DELETE FROM shift_sessions WHERE username IN ('ralph','pam');"`,
               { stdio: 'ignore' });
    } catch (e) { console.log('  ⚠️  could not pre-clean shift_sessions:', e.message.slice(0, 80)); }

    // ---- TEST A — the real end-of-day: access token dead, session still good ----
    console.log('\nA · logout with a STALE access token (the one that was losing the row)');
    ok('logged in as ralph', await login(p, 'ralph'));

    const hadRefresh = await p.evaluate(() => !!sessionStorage.getItem('pos_refresh'));
    ok('a refresh token is present to renew with', hadRefresh);

    // ⚠️ THE ENVIRONMENT HAS TO BE CONTROLLED, AND THIS TOOK THREE TRIES (LESSON #5 ×3).
    //  1st: stale the token, click logout, assert 200. PASSED against the reverted code —
    //       the ~45s notification poller had renewed the token while I waited.
    //  2nd: freeze the timers, then assert the token is still stale at click time. Flaky —
    //       it measured the dashboard, not logout().
    //  3rd: assert the ORDER, refresh-before-end. ALSO PASSED against the reverted code,
    //       because the dashboard's own API call 401s on the staled token and the API
    //       helper renews REACTIVELY, before logout is ever pressed. refresh→end happens
    //       either way, so the assertion could not tell the versions apart.
    //
    // The app is simply very good at healing itself, and every one of those healers had to
    // be shut off before the question could even be asked. So: abort every POS API call
    // EXCEPT the shift close. An aborted fetch is a network error, which the API helper
    // treats as 'transient' and does NOT renew on — so after this, the only thing in the
    // whole page that can call /pos/refresh is logout() itself. That is the frozen tab.
    //
    // The shift/end status is captured INSIDE the route handler, not from a response event.
    // logout() redirects to Keycloak the moment the close is away, and the page navigating
    // kills the response listener — so `statuses seen: []` even on a perfectly good 200.
    // Fetching it here settles the status before the navigation can eat it.
    const endStatus = [];
    await p.route('**/api/v1/pos/**', async route => {
      if (!route.request().url().includes('/shift/end')) return route.abort();
      try {
        const resp = await route.fetch();
        endStatus.push(resp.status());
        await route.fulfill({ response: resp });
      } catch (e) { await route.abort(); }
    });
    await p.waitForTimeout(500);

    // Stale the ACCESS token only. Structurally a JWT so nothing chokes parsing it; the
    // signature is nonsense, so the server rejects it exactly as an expired one.
    await p.evaluate(() => {
      const dead = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.' +
                   btoa(JSON.stringify({ exp: 1, sub: 'dead' })).replace(/=/g, '') + '.dead';
      sessionStorage.setItem('pos_token', dead);
      try { localStorage.setItem('pos_token', dead); } catch (e) {}
    });
    await p.waitForTimeout(1500);
    const stillStale = await p.evaluate(() => (sessionStorage.getItem('pos_token') || '').endsWith('.dead'));
    ok('nothing but logout can renew now (token still stale at click time)', stillStale,
       'something healed it — the test cannot tell the two versions apart');

    const wA = watchWire(p);
    wA.seq.length = 0;                       // only what happens from the click onward
    ok('logout button found and pressed', await clickLogout(p));
    ok('the till POSTed shift/end at all', wA.seq.includes('end'),
       'no request seen — logout never reached the close');
    // THE DISCRIMINATOR: logout renews BEFORE it closes. Reverted code goes straight to
    // 'end' and takes a 401; fixed code emits 'refresh' then 'end'.
    const iR = wA.seq.indexOf('refresh'), iE = wA.seq.indexOf('end');
    ok('logout renewed the token BEFORE closing the row', iR !== -1 && iE !== -1 && iR < iE,
       'order seen: ' + JSON.stringify(wA.seq));
    ok('THE ROW CLOSED — no ACTIVE session left for ralph', activeRows('ralph') === 0,
       'ACTIVE rows still open: ' + activeRows('ralph'));

    // ---- TEST B — the control: a perfectly ordinary logout must still work ----
    console.log('\nB · control — ordinary logout, live token (must not regress)');
    const p2 = await ctx.newPage();
    p2.on('pageerror', e => errs.push(e.message.slice(0, 160)));
    ok('logged in as pam', await login(p2, 'pam'));
    const wB = watchWire(p2);
    ok('logout button found and pressed', await clickLogout(p2));
    ok('THE ROW CLOSED — no ACTIVE session left for pam', activeRows('pam') === 0,
       'ACTIVE rows still open: ' + activeRows('pam'));

    console.log('\nC · the page did not throw while doing it');
    ok('no uncaught page errors', errs.length === 0, errs.join(' | '));
  } finally {
    await b.close();
  }

  console.log(`\n${pass} pass · ${fail} fail`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('HARNESS FAULT:', e); process.exit(3); });
