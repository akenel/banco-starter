// A search result must say which shelf it came from — and that pill must be a shortcut.
//
// WHY THIS FILE EXISTS. Angel, 2026-09-05: "we see the items for example with CBD that they
// are 18+ CBD, the two pills are excellent — but I was wondering, on that line could we add
// another pill with the category for that product. If the user searches without a category
// selected it lists a bunch of products but they don't learn where they come from."
//
// And it is Pam's request from the other end. Hers (2026-09-04) was "narrow the cats where
// only search term is applicable so cat list is shortened" — 52 categories in a picker to
// choose between the 6 that `papers` touches. The pill teaches the shelf names; tapping one
// filters to that shelf without opening the picker at all. Two doors on one feature, and
// they are checked together here because shipping either alone leaves the other half odd.
//
// THE COST IS ROW HEIGHT, AND IT IS MEASURED, NOT ASSUMED. Banco's keyboard leaves room for
// exactly ONE result row (2026-09-05, agreed with Angel). A third pill that wraps the badge
// line makes every row taller, and a taller row is how "one row visible" becomes "none".
// So this file measures the row with and without the pill and states the difference.
//
// AND THE PILL IS A BUTTON, WHICH ON THIS TILL IS A LOADED WORD. Layla, 2026-09-04: she
// searched, pressed Add, then scanned papers — and the grinder climbed to quantity 8,
// because a scanner gun is a keyboard and its ENTER re-presses whatever button holds focus.
// Every tappable thing in this list must hand focus straight back to the search box.
//
// NOTHING IS SOLD. Searches and reads. No cart, no checkout.
const { chromium } = require('playwright');

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ hasTouch: true, viewport: { width: 1440, height: 895 } });
  const p = await ctx.newPage();
  let pass = 0, fail = 0;
  const check = (ok, what, detail) => {
    if (ok) { pass++; console.log('  ✅ ' + what); }
    else { fail++; console.log('  ❌ ' + what + (detail ? '\n       ' + detail : '')); }
  };

  await p.goto('http://localhost:3000/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  const alpineReady = () => p.waitForFunction(() => {
    try { const el = document.querySelector('[x-data]'); return !!(window.Alpine && el && Alpine.$data(el)); }
    catch (e) { return false; }
  }, null, { timeout: 30000 });

  await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'load' });
  await alpineReady();
  await p.waitForTimeout(800);
  await p.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).searchMode = 'search'; });
  await p.waitForTimeout(400);

  // Rows through the SHIPPED x-for. Four shelves, one of them a long name, because a pill
  // carrying "Rolling & Filling Machines" (26 chars — the shop's longest) is the one that
  // decides whether the badge line wraps.
  const SHELVES = ['Papers & Rolling', 'Rolling & Filling Machines', 'Bongs & Pipes', 'Grinders'];
  const feed = (withCategory) => p.evaluate(({ shelves, withCategory }) => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.searchInput = 'cbd'; d.searchTotal = 366;
    d.searchResults = Array.from({ length: 12 }, (_, i) => ({
      id: 's' + i, name: 'CBD Joint Natural Rebel "Lemon Skunk" Pure 1stk Nr.' + (i + 1),
      price: 12.5 + i, sku: 'CBD-' + i, barcode: '760000000' + i,
      category: withCategory ? shelves[i % shelves.length] : null,
      // 'cbd_hemp', not 'age_restricted'. Both are 18+, but the type pill is deliberately hidden
      // for a plain age_restricted row (it would just say "18+" twice) — so that fixture
      // showed two badges and this file called it a bug. Angel's screen shows 🔞 18+ AND
      // 🌿 CBD, so the fixture has to be the class that produces both.
      product_class: 'cbd_hemp', is_age_restricted: true, stock_quantity: 1, is_active: true,
    }));
    d.matchCategories = withCategory
      ? shelves.map((s, i) => ({ name: s, count: 10 - i })) : [];
  }, { shelves: SHELVES, withCategory });

  const rowHeight = () => p.evaluate(() => {
    const rows = [...document.querySelectorAll('#search-results [data-row-snap-rows] > *')]
      .filter(e => e.getBoundingClientRect().height > 0);
    return rows.length ? Math.round(rows[0].getBoundingClientRect().height) : null;
  });

  // ── A · WHAT THE ROW SAYS ────────────────────────────────────────────────────────────────
  console.log('\n── A · the shelf is on the row ──');
  await feed(false);
  await p.waitForTimeout(900);
  const bare = await rowHeight();

  await feed(true);
  await p.waitForTimeout(900);
  const withPill = await rowHeight();

  const pill = await p.evaluate(() => {
    const row = [...document.querySelectorAll('#search-results [data-row-snap-rows] > *')]
      .find(e => e.getBoundingClientRect().height > 0);
    if (!row) return null;
    const btn = [...row.querySelectorAll('button')].find(x => /🏷️/.test(x.textContent));
    // Scope to the badge strip. The first version matched anything on the row whose text
    // said "CBD" — which includes the PRODUCT NAME, "CBD Joint Natural Rebel …" — and then
    // reported the badges as sitting on two lines. The row height (unchanged) said otherwise.
    // LESSON #5: the harness accuses working code as confidently as it reports the truth.
    const strip = row.querySelector('.flex.flex-wrap');
    const badges = strip ? [...strip.children].filter(x => x.getBoundingClientRect().height > 0) : [];
    return {
      text: btn ? btn.innerText.trim() : null,
      isButton: !!btn && btn.tagName === 'BUTTON',
      // All three on ONE line, or the badge row has wrapped and every row got taller.
      badgeTops: [...new Set(badges.map(x => Math.round(x.getBoundingClientRect().top)))].length,
      badgeCount: badges.length,
    };
  });
  check(!!pill && !!pill.text, 'the row carries a shelf pill', 'no 🏷️ pill on the row');
  check(pill && /Papers & Rolling/.test(pill.text), `it names the shelf — "${pill && pill.text}"`);
  check(pill && pill.isButton, 'and it is a button, not a label — it can be tapped');
  check(pill && pill.badgeCount >= 3, `18+, the type and the shelf all show (${pill && pill.badgeCount} badges)`);
  check(pill && pill.badgeTops === 1,
        'all three sit on ONE line — the badge row does not wrap',
        'the badges are on ' + (pill && pill.badgeTops) + ' lines, so every row in the list just got taller');
  check(withPill === bare,
        `and the row is no taller for it (${bare}px → ${withPill}px)`,
        `the row grew ${withPill - bare}px, and the keyboard leaves room for exactly one row`);

  // ── B · TAPPING IT IS THE SHORTCUT ───────────────────────────────────────────────────────
  console.log('\n── B · tapping the shelf filters to it ──');
  const tapped = await p.evaluate(async () => {
    const row = [...document.querySelectorAll('#search-results [data-row-snap-rows] > *')]
      .find(e => e.getBoundingClientRect().height > 0);
    const btn = [...row.querySelectorAll('button')].find(x => /🏷️/.test(x.textContent));
    const d = Alpine.$data(document.querySelector('[x-data]'));
    const before = d.searchCategory;
    // FOCUS IT FIRST, because a finger does. A scripted .click() leaves focus on <body>, so
    // the "focus left the button" check passed even with $el.blur() deleted — a check that
    // survives the bug it guards. Watched going red only after this line was added.
    btn.focus();
    btn.click();
    await new Promise(r => setTimeout(r, 600));
    return {
      before, after: d.searchCategory,
      // The row's own @click opens the product detail. If the pill did not stop the event,
      // a cashier reaching for a filter gets a modal instead.
      // getComputedStyle, NOT [style*="display: none"]. The attribute selector matched six
      // overlays that were already hidden before anything was clicked, so this check failed
      // on a screen that was correct. Same fault as the badge count above, same run.
      modalOpen: [...document.querySelectorAll('.fixed.inset-0')]
        .some(e => getComputedStyle(e).display !== 'none'),
      focused: document.activeElement && document.activeElement.getAttribute('x-ref'),
      focusedTag: document.activeElement && document.activeElement.tagName,
    };
  });
  check(tapped.after === 'Papers & Rolling',
        `the category filter is now "${tapped.after}"`, `it went from ${JSON.stringify(tapped.before)} to ${JSON.stringify(tapped.after)}`);
  check(!tapped.modalOpen, 'and the product detail modal did NOT open',
        'the tap fell through to the row, so reaching for a filter opens a modal');
  // NOT "did focus leave the button". That check passed with $el.blur() deleted, because
  // searchProducts() re-renders the x-for and the button stops existing — it was reporting a
  // side effect, not the fix. What a cashier needs is that the NEXT THING SHE TYPES lands in
  // the search box, so type something and look. That is also the gun: it types, and its
  // ENTER must arrive somewhere harmless (LESSON ⓛ — Layla's grinder reached quantity 8
  // because a gun's ENTER re-pressed a focused button).
  check(tapped.focused === 'searchInputBox',
        `focus is back in the search box (it is on <${(tapped.focusedTag || '?').toLowerCase()}>)`,
        'the next keystroke — or the next scan — lands nowhere');
  const typed = await p.evaluate(async () => {
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'x', bubbles: true }));
    const el = document.activeElement;
    if (el && el.tagName === 'INPUT') {
      el.value += 'x';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }
    await new Promise(r => setTimeout(r, 500));
    return Alpine.$data(document.querySelector('[x-data]')).searchInput;
  });
  check(/x$/.test(typed || ''), `and the next character typed lands in it ("${typed}")`,
        'what was typed after the tap went somewhere else');

  // ── C · THE PICKER, NARROWED ─────────────────────────────────────────────────────────────
  console.log('\n── C · the picker offers what the search touched, first ──');
  // FEED IT AGAIN FIRST. Section B taps the pill, which calls the real searchProducts(),
  // which asks the dev catalogue — six products, all in "Treats" — and replaces the fixture.
  // The first version asserted against whatever survived that, and reported "it lists 2 of
  // them, not 52" as a failure of the picker. It was a failure of the running order.
  await feed(true);
  await p.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).searchCategory = ''; });
  await p.waitForTimeout(700);
  const picker = await p.evaluate(() => {
    const sel = document.querySelector('select[x-model="searchCategory"]');
    const groups = [...sel.querySelectorAll('optgroup')].filter(g => g.offsetParent !== null || g.label);
    const first = groups[0];
    return {
      firstLabel: first ? first.label : null,
      // OPTIONs only: Alpine's x-for leaves its <template> in the optgroup, so `children`
      // is one longer than the list a person sees. Third time this has caught me today.
      firstOptions: first ? [...first.children].filter(o => o.tagName === 'OPTION')
                                               .map(o => o.textContent.trim()) : [],
      groupCount: groups.length,
      hasAllCategories: !!sel.querySelector('option[value=""]'),
    };
  });
  check(/4/.test(picker.firstLabel || ''), `the first group is the search's own shelves — "${picker.firstLabel}"`);
  check(picker.firstOptions.length === 4, `and it lists ${picker.firstOptions.length} of them, not 52`);
  check(/\(10\)/.test(picker.firstOptions.join(' ')), 'each one carries its whole-match count',
        picker.firstOptions.join(' · '));
  check(picker.groupCount > 1, 'the full list is still underneath — not a one-way door',
        'only the narrowed group exists, so a cashier cannot reach the other shelves');
  check(picker.hasAllCategories, 'and "All categories" is still the way out');

  // ── D · AND WITH NO SEARCH, NOTHING CHANGES ──────────────────────────────────────────────
  // The step whose expected result is that nothing happens.
  console.log('\n── D · no search term, no narrowing ──');
  const quiet = await p.evaluate(async () => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.searchInput = ''; d.searchResults = []; d.matchCategories = []; d.searchCategory = '';
    await new Promise(r => setTimeout(r, 500));
    const sel = document.querySelector('select[x-model="searchCategory"]');
    const groups = [...sel.querySelectorAll('optgroup')];
    // x-show on an optgroup hides it with display:none.
    const visible = groups.filter(g => getComputedStyle(g).display !== 'none');
    return { total: groups.length, visible: visible.length, firstVisible: visible.length ? visible[0].label : null };
  });
  check(quiet.visible === quiet.total - 1 || !/\(/.test(quiet.firstVisible || '('),
        'the narrowed group is hidden — the picker is the ordinary full list again',
        `first visible group is "${quiet.firstVisible}"`);

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
