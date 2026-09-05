// Banco's own keyboard must not sit on top of the answer the box just produced.
//
// WHY THIS FILE EXISTS. Layla, 2026-09-03, on the tablet, typing `cbd` into Find Product:
// "Showing 20 of 366 matches" and one and a half rows. You had to put the keyboard away to
// see what you had searched for. It was carried for three days as "needs a re-run with the
// folio off" — twice retested with the folio keyboard attached, which means Banco's own pad
// never appeared, and the pad is the entire subject of the test.
//
// MEASURED 2026-09-05 at the tablet's 1440x895, before any fix: pad lid y=651, the one and
// only result row 522..680. ZERO whole rows above the pad, and the pad's top edge ran
// through `CHF 9.45` — the single thing on that row a cashier is reading out loud. The
// screenshot is what settled it; the numbers alone had been reported as "1 row visible"
// for days.
//
// TWO THINGS WERE WRONG, and they fail differently, so both are checked here:
//
//   1. data-row-snap knew about the stylesheet's max-height and nothing about the keyboard.
//      It snapped the list to a whole row against a 384px cap and the pad then sliced
//      through it anyway. A cap that does not know about every obstruction is half a cap.
//   2. The pad's "is the field visible" check had grown from the field, to the field plus
//      its warning, and stopped there. A search box's REASON TO EXIST is the list below it.
//      LESSON #12, sixth turn, one notch finer each time.
//
// ONE row above the pad, deliberately, not the list: twenty rows cannot fit above a 244px
// keyboard, and asking for them would scroll the box being typed into off the top. One whole
// row is the difference between "it found something" and "it found nothing"; the rest is
// what the list's own scrollbar is for.
//
// NOTHING IS EVER SOLD. This types into a search box and reads geometry. No cart, no
// checkout, no payment button.
const { chromium } = require('playwright');

const VIEW = { width: 1440, height: 895 };   // the shop tablet's real viewport

(async () => {
  const b = await chromium.launch();
  // hasTouch is not decoration: the pad refuses to exist on a machine with no touch
  // (`[keypad] STOPPED — not a touch device`), so without it this file measures a screen
  // that has no keyboard on it and passes every assertion for the wrong reason.
  const ctx = await b.newContext({ hasTouch: true, viewport: VIEW });
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
  await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'load' });
  await alpineReady();
  await p.waitForTimeout(800);

  // The geometry, read the way a person reads it. A row is only "showing" where the card's
  // own scroll box lets it show; a row clipped away at 639 is not on the screen at all, and
  // counting its bounding rect against the pad would accuse a correct screen.
  // Alpine wires the screen up after `load`; every measurement below is meaningless
  // until it has. Wrapped because $data() THROWS on an element it has not reached yet,
  // and a throw inside waitForFunction ends the run instead of retrying.
  async function alpineReady() {
    await p.waitForFunction(() => {
      try {
        const el = document.querySelector('[x-data]');
        return !!(window.Alpine && el && Alpine.$data(el));
      } catch (e) { return false; }
    }, null, { timeout: 30000 });
  }

  const geometry = () => p.evaluate(() => {
    const lid = [...document.querySelectorAll('.pk')]
      .map(e => e.getBoundingClientRect()).filter(r => r.height > 0)
      .reduce((m, r) => Math.min(m, r.top), window.innerHeight);
    const card = document.getElementById('search-results');
    if (!card || card.getBoundingClientRect().height === 0) return { card: null, lid };
    const cr = card.getBoundingClientRect();
    const rows = [...card.querySelectorAll('[data-row-snap-rows] > *')]
      .filter(e => e.getBoundingClientRect().height > 0);
    const seen = rows.map(r => {
      const b = r.getBoundingClientRect();
      const top = Math.max(b.top, cr.top), bot = Math.min(b.bottom, cr.bottom, lid);
      return { h: b.height, shown: Math.max(0, bot - top) };
    });
    return {
      lid: Math.round(lid),
      card: { top: Math.round(cr.top), bottom: Math.round(cr.bottom), maxH: card.style.maxHeight || '',
              scrolls: card.scrollHeight > card.clientHeight + 1 },
      rows: rows.length,
      whole: seen.filter(s => s.shown >= s.h - 0.5).length,
      // The bug, stated as a number: a row that is neither fully shown nor fully hidden.
      sliced: seen.filter(s => s.shown > 0.5 && s.shown < s.h - 0.5).length,
      firstRowText: rows.length ? rows[0].innerText.replace(/\s+/g, ' ').trim().slice(0, 60) : null,
      priceVisible: (() => {
        if (!rows.length) return null;
        const price = [...rows[0].querySelectorAll('*')].find(e => /CHF\s*[\d.]/.test(e.textContent) && e.children.length === 0);
        if (!price) return null;
        const b = price.getBoundingClientRect();
        return b.top >= cr.top - 0.5 && b.bottom <= Math.min(cr.bottom, lid) + 0.5;
      })(),
    };
  });

  const openPadOnSearch = async () => {
    await p.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).searchMode = 'search'; });
    await p.waitForTimeout(400);
    await p.click('input[x-ref="searchInputBox"]');
    await p.waitForTimeout(900);
  };
  // Rows pushed through the SHIPPED x-for, AFTER the pad is already up — which is the real
  // sequence and the one that was broken: you tap the box, the keyboard comes, and THEN the
  // server answers. open() checks the field at +140ms and +480ms; the answer is later than
  // both. The dev catalogue holds 6 active products, so 20 of them have to be made.
  const answer = (n) => p.evaluate((count) => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.searchInput = 'cbd'; d.searchTotal = 366;
    d.searchResults = Array.from({ length: count }, (_, i) => ({
      id: 'syn' + i, name: 'CBD Blüten Sorte ' + (i + 1), price: 12.5 + i,
      sku: 'CBD-' + i, barcode: '760000000' + i, category: 'CBD', stock_quantity: 1, is_active: true,
    }));
  }, n);

  // ── A · THE PAD IS UP AND THE FIRST ANSWER IS WHOLE ──────────────────────────────────────
  console.log('\n── A · twenty matches arrive while the keyboard is already up ──');
  await openPadOnSearch();
  const padUp = await p.evaluate(() =>
    [...document.querySelectorAll('.pk')].some(e => e.getBoundingClientRect().height > 0));
  check(padUp, "Banco's own letter pad is on the screen");
  await answer(20);
  await p.waitForTimeout(1800);
  let g = await geometry();

  check(!!g.card, 'the results card is on the screen', 'no #search-results — the fixture did not render');
  check(g.rows === 20, `all twenty rows are in the list (${g.rows})`);
  check(g.sliced === 0, 'NOT ONE row is cut in half by the keyboard',
        `${g.sliced} row(s) are part-shown — this is Layla's "one and a half rows"`);
  check(g.whole >= 1, `at least one whole row is readable with the pad up (${g.whole})`,
        'every row is either under the keyboard or sliced — you must dismiss the pad to see what you searched for');
  check(g.card && g.card.bottom <= g.lid + 0.5,
        `the list ends above the keyboard (card bottom ${g.card && g.card.bottom} · pad lid ${g.lid})`,
        'the card runs under the pad');
  check(g.priceVisible === true, `and the PRICE on that row is readable — "${g.firstRowText}"`,
        'the price is the half that is under the keyboard, which is the half being read to the customer');
  check(g.card && g.card.scrolls, 'the other nineteen are reachable — the list scrolls',
        'the list was shortened without becoming scrollable, which loses rows instead of parking them');

  // ── B · AND ONE REAL RESULT FROM THE SHOP'S OWN CATALOGUE ────────────────────────────────
  // Synthetic rows prove the geometry; they cannot prove the search wires up. This types on
  // the pad's own keys, the way a finger does, and reads whatever the catalogue returns.
  console.log("\n── B · the same thing, typed on the pad, against the real catalogue ──");
  await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'load' });
  await alpineReady();
  await p.waitForTimeout(800);
  await openPadOnSearch();
  for (const ch of 'cbd') {
    const k = await p.$(`#pk-abc .pk-k[data-k="${ch}"]`);
    if (k) await k.click(); else await p.keyboard.type(ch);
    await p.waitForTimeout(160);
  }
  await p.waitForTimeout(1800);
  g = await geometry();
  check(!!g.card && g.rows > 0, `the catalogue answered (${g.rows} row(s))`, 'no results — nothing to be buried, so this run proves nothing');
  check(g.sliced === 0, 'no row is cut in half by the keyboard', `${g.sliced} row(s) part-shown`);
  check(g.whole >= 1, `a whole row is readable — "${g.firstRowText}"`, 'the answer is under the keyboard');
  check(g.priceVisible === true, 'including its price');
  await p.screenshot({ path: '/tmp/pad-does-not-bury.png' });
  console.log('     (screenshot: /tmp/pad-does-not-bury.png — LESSON #12, only a picture settles it)');

  // ── C · AND PUTTING THE KEYBOARD AWAY GIVES THE LIST BACK ────────────────────────────────
  // The cap has to be temporary. A list permanently shortened to one row would be a worse
  // bug than the one being fixed, and it would look like a fix in every check above.
  console.log('\n── C · closing the pad returns the full list ──');
  const before = (await geometry()).card;
  await p.evaluate(() => window.posKeypad.close());
  await p.waitForTimeout(700);
  await answer(20);
  await p.waitForTimeout(1200);
  const after = await geometry();
  check(after.lid === VIEW.height, 'the keyboard is gone', 'a pad is still on screen');
  check(after.card.bottom > before.bottom,
        `the list is taller again (${before.bottom} → ${after.card.bottom})`,
        'the pad-sized cap outlived the pad');
  check(after.sliced === 0, 'and it still ends on a whole row — the 2026-09-04 fix is intact',
        `${after.sliced} row(s) sliced by the card's own bottom edge`);
  check(after.whole >= 2, `more than one row shows with the keyboard away (${after.whole})`);

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
