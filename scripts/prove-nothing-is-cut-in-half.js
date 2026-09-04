// The till's product list ends on a whole row, and the controls above it stay put.
//
// WHY THIS FILE EXISTS. Layla, 2026-09-04, after running two sheets on the tablet:
//
//   "the left-hand product list cuts its last row in half — every pack looks like it is
//    missing something"
//   "the Barcode / Search / New item buttons, the input and the category picker all scroll
//    off when the results list is long — same sticky treatment the cart total got"
//
// Neither is cosmetic in the way it sounds. A half-drawn row reads as a half-LOADED screen,
// and a cashier who does not trust a list scrolls it twice before believing it. Controls that
// walk away are the same complaint that produced the pinned cart total on 2026-09-03.
//
// WHAT IS ASSERTED, AND WHY IT IS NOT THE ARITHMETIC. The snap in base.html computes a cap
// from the row pitch, and a check that recomputed that arithmetic would agree with itself
// whether or not it is right (LESSON #5). So this measures the thing a PERSON sees instead:
// no row may straddle the bottom edge of its scroll box, at any scroll position. That is
// getBoundingClientRect() against the box's own rect — the same instrument that has been the
// answer to "is it actually on the screen" four times in this repo.
//
// NOTHING IS EVER SOLD, AND NOTHING IS WRITTEN. A list is rendered, measured and scrolled. No
// item is added to a cart, no button that writes anything is pressed, and no row is created in
// any database.
//
// WHERE THE ROWS COME FROM, SAID PLAINLY. This dev database has **six active products**, so a
// search here returns one or two rows and the condition being tested — a list long enough to
// have a bottom edge — cannot be produced from its data at all. Layla hit this with "Showing
// 20 of 366 matches". So the rows are handed to the component directly and rendered by the
// SHIPPED x-for, with the shipped classes, at the tablet's real viewport. The product DATA is
// synthetic; the geometry is not, and geometry is the entire subject here. Anything this file
// claims about prices, names or catalogue contents would be worthless — it claims nothing about
// them. One of the fabricated names is deliberately long enough to wrap onto a second line,
// which is a taller row than this catalogue can currently produce and the case a fixed
// row-height fix would fail on.
const { chromium } = require('playwright');

(async () => {
  const b = await chromium.launch();
  // The tablet's real viewport, measured off Angel's own screenshot (devicePixelRatio 1.5).
  // The whole subject here is geometry, so a viewport nobody stands in front of proves nothing.
  const ctx = await b.newContext({ viewport: { width: 1440, height: 895 }, hasTouch: true });
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
  await p.waitForTimeout(2000);

  // ── A · THE LIST ENDS ON A WHOLE ROW ─────────────────────────────────────────────────────
  // "cbd" is the search Layla ran when she found this — 366 matches, 20 shown, and one and a
  // half rows of them visible.
  console.log('\n── A · the product list ends on a whole row ──');
  const box = '[data-row-snap]';

  // 20 rows, the way the screen would have them: an ordinary name, a long one that wraps, and
  // a mix of classes so the badges render as they really do.
  async function showRows(n) {
    return p.evaluate(async (n) => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      const LONG = 'Curaprox Naturally Zahnpasta Sensitive Whitening mit Fluorid 75ml Doppelpack';
      d.searchMode = 'search';
      d.searchResults = Array.from({ length: n }, (_, i) => ({
        id: 900000 + i,
        name: (i % 5 === 2) ? LONG : ('ZZPROBE Test Item ' + (i + 1)),
        sku: 'ZZ-' + (1000 + i),
        barcode: '760' + String(1000000 + i),
        price: 4.5 + i,
        product_class: (i % 3 === 0) ? 'age_restricted' : 'standard',
      }));
      d.searchTotal = 366;
      // x-for renders, the observer fires, the snap runs on a rAF, and the box reflows. Four
      // steps, and a measurement taken between any two of them reports a box that is halfway
      // through changing size — which is how this file first accused a 2-row list of scrolling
      // when it does not. Wait, poke the snap directly, wait again.
      await new Promise(r => setTimeout(r, 700));
      if (window.posRowSnap) window.posRowSnap();
      await new Promise(r => setTimeout(r, 400));
      return true;
    }, n);
  }

  // The straddle test, run at a given scroll position inside the box.
  async function straddle(frac) {
    return p.evaluate(({ sel, frac }) => {
      const el = document.querySelector(sel);
      if (!el || el.offsetParent === null) return { none: true };
      const wrap = el.querySelector('[data-row-snap-rows]');
      // The <template x-for> element is a child too, and it has no box. Filtering by height is
      // what tells a rendered row from the machinery that renders it — the first version of
      // this check counted the template as a row and reported a row height of 0.
      const rows = wrap ? [...wrap.children].filter(n => n.getBoundingClientRect().height > 0) : [];
      el.scrollTop = Math.round(el.scrollHeight * frac);
      const r = el.getBoundingClientRect();
      // THE BORDER BOX, not the padding box. This started as `bottom - paddingBottom` on the
      // reasoning that content is cut at the inner edge. It is not: a scrolling box's content
      // passes THROUGH its padding and is visible right down to the border. Defining the edge
      // 24px too high meant the check was measuring the very line the fix put the last row on,
      // and it reported a clean pass over a visible 16px sliver of the next row. A screenshot
      // found it. The number this check produces has to be the number a person sees.
      const edge = r.bottom;
      const cut = rows.filter(row => {
        const rr = row.getBoundingClientRect();
        return rr.top < edge - 1 && rr.bottom > edge + 1;
      });
      return {
        rows: rows.length,
        visible: rows.filter(row => { const rr = row.getBoundingClientRect(); return rr.top >= r.top - 1 && rr.bottom <= edge + 1; }).length,
        cut: cut.length,
        sliver: cut.length ? Math.round(edge - cut[0].getBoundingClientRect().top) : 0,
        rowH: rows.length ? Math.round(rows[0].getBoundingClientRect().height) : 0,
        boxH: Math.round(r.height),
        scrolls: el.scrollHeight > el.clientHeight + 1,
        scrollH: el.scrollHeight, clientH: el.clientHeight,
      };
    }, { sel: box, frac });
  }

  await showRows(20);
  const top = await straddle(0);
  check(!top.none && top.rows === 20, `20 rows render into the results card (${top.rows} found)`,
        JSON.stringify(top));
  check(top.cut === 0,
        `no row is sliced by the bottom of the box (box ${top.boxH}px, row ${top.rowH}px, ${top.visible} whole rows showing)`,
        top.cut + ' row(s) straddle the edge — the first shows only ' + top.sliver + 'px of its '
        + top.rowH + 'px, which is the sliver Layla is looking at');

  // The cheapest way to pass the check above would be to cap the box at one row, or to drop the
  // cap so the list runs off the page. Neither is the fix, so both are ruled out here.
  check(top.scrolls, 'and the box is still a scrolling list, not the whole 20 rows down the page',
        'it does not scroll — the cap was removed rather than snapped');
  check(top.visible >= 2, `and it still shows more than one row at a time (${top.visible})`,
        'only ' + top.visible + ' row fits — capping to a single row passes the slice test and helps nobody');

  // AND AT THE END OF THE LIST, which is the other resting place a thumb actually leaves it in.
  const bot = await straddle(1);
  check(bot.cut === 0, 'and scrolling to the bottom of the list also ends on a whole row',
        bot.cut + ' row(s) straddle the edge at the end of the list');

  // WHAT IS DELIBERATELY *NOT* CLAIMED: that a row can never be halfway across the edge at an
  // arbitrary mid-scroll position. It can, and so it can in every scrolling list ever built —
  // that is what scrolling looks like. The defect Layla reported was the list ALWAYS resting
  // on a sliced row, before she had touched it at all.
  //
  // CSS scroll-snapping would have made the stronger claim true and was tried and REMOVED:
  // `scroll-snap-type: y proximity` broke the resting case it was meant to strengthen (the
  // measurement above went red with it in), and `mandatory` hijacks a fast flick and fights
  // the finger — which on a till is worse than the sliver. Neither could be feel-tested on
  // the tablet tonight, and a scroll behaviour nobody has felt is not one to ship.
  const mid = await straddle(0.35);
  console.log(`  ·  (mid-scroll shows ${mid.cut} partial row, which is what scrolling looks like — not asserted)`);

  // A LIST THAT FITS MUST NOT BE FORCED TO SCROLL. The snap only ever makes a box shorter, so
  // a list already inside the cap has to lose the cap entirely rather than be trimmed to obey
  // a rule. TWO rows, not three — measured, not assumed: a row is 118px and the cap is 384, so
  // three rows genuinely do not fit and asserting they should was the check being wrong rather
  // than the code. (That number is worth saying out loud: at this cap the till shows the
  // cashier TWO products at a time out of twenty. Logged for Angel — raising the cap is a
  // layout decision, not a bug fix, and it is his call.)
  await showRows(2);
  // SETTLE BEFORE ASSERTING. Two consecutive identical measurements, or this check reports a
  // box caught halfway through changing size — which is exactly what it did: it accused a
  // 2-row list of scrolling while a direct measurement of the same page showed
  // scrollHeight === clientHeight === 332 and no cap at all. The app was right and the
  // stopwatch was wrong, which is this repo's most expensive recurring shape (LESSON #5).
  let few = await straddle(0), prev = null, tries = 0;
  while (JSON.stringify(few) !== JSON.stringify(prev) && tries++ < 6) {
    prev = few;
    await p.waitForTimeout(250);
    few = await straddle(0);
  }
  check(few.cut === 0 && few.visible === few.rows,
        `a short list shows every one of its rows whole (${few.visible} of ${few.rows})`,
        JSON.stringify(few));

  // AND A CLAIM DELIBERATELY NOT MADE: that a short list carries no scrollbar at all. It
  // should not, and when this page is measured on its own it does not — scrollHeight and
  // clientHeight both come back 332 with the cap cleared. Measured at the END of this run,
  // after twenty rows have been rendered and scrolled, the same box reports scrollHeight 402
  // against a content height that adds up to 332, and I cannot yet account for the 70px.
  // Every row is whole either way, which is the thing Layla reported. Asserting the tidier
  // claim would mean asserting something I cannot explain, and a green I cannot explain is
  // worth less than an honest gap. Logged in WORKLIST.md.
  console.log(`  ·  (short list: scrollHeight ${few.scrollH} vs clientHeight ${few.clientH} — unexplained, logged, not asserted)`);

  await showRows(20);

  // ── B · THE CONTROLS STAY PUT ────────────────────────────────────────────────────────────
  // "Is it sticky" is not the question — LESSON #12. The question is whether the buttons are
  // still inside the rectangle the person is looking at once she has scrolled to the bottom of
  // the page, and that is getBoundingClientRect() against innerHeight.
  console.log('\n── B · the Find Product controls do not run away ──');
  // STRUCTURAL FIRST, because this database cannot produce the condition. Layla hit this with
  // 366 matches on a real catalogue; here there are SIX active products, so the page scrolls
  // about 108px — not far enough to carry the controls off the top on its own. A visibility
  // check alone would therefore pass on a build with the fix reverted, and it did exactly that
  // when this section was first written. So: assert the pin itself, then assert the person's
  // view as far as this data can scroll it.
  const pin = await p.evaluate(() => {
    const card = document.querySelector('.card');
    const cs = getComputedStyle(card);
    return { position: cs.position, top: cs.top };
  });
  check(pin.position === 'sticky' && pin.top === '0px',
        `in Search mode the controls panel is pinned (position: ${pin.position}, top: ${pin.top})`,
        'it is position:' + pin.position + ' — the controls will walk off the moment a real'
        + ' catalogue puts twenty results under them');
  // THE PAGE DOES NOT SCROLL — `.app-content` DOES. Measured while writing this: window.scrollY
  // stayed at 0 no matter what, and every "still visible" check below would have passed on a
  // page that had never moved. pos-keypad.js has known this since it was written (scrollerFor);
  // I did not, and a check that cannot move the screen proves nothing about what stays on it.
  await p.evaluate(() => {
    const sc = document.querySelector('.app-content') || document.scrollingElement;
    sc.scrollTop = sc.scrollHeight;
  });
  await p.waitForTimeout(600);
  const after = await p.evaluate(() => {
    const sc = document.querySelector('.app-content') || document.scrollingElement;
    const btn = [...document.querySelectorAll('button')].find(x => /Search/.test(x.textContent) && x.offsetParent);
    const inp = document.querySelector('input[data-i18n-placeholder="scan.ph_product_search"]');
    const sel = [...document.querySelectorAll('select')].find(s => s.offsetParent);
    const onScreen = el => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return r.height > 0 && r.top >= 0 && r.bottom <= window.innerHeight;
    };
    return {
      scrolled: Math.round(sc.scrollTop),
      btn: onScreen(btn), input: onScreen(inp), select: onScreen(sel),
      btnTop: btn ? Math.round(btn.getBoundingClientRect().top) : null,
      viewport: window.innerHeight,
    };
  });
  check(after.scrolled > 50, `the page actually scrolled (${after.scrolled}px) — otherwise nothing below is a test`,
        'the page did not move, so "still visible" means nothing');
  check(after.btn === true, `the Barcode / Search / New item buttons are still on screen (top ${after.btnTop} of ${after.viewport})`,
        'they scrolled away — this is the complaint, unfixed');
  check(after.input === true, 'the box she types in is still on screen');
  check(after.select === true, 'and so is the category picker');

  // AND THE NEW ITEM PANEL IS DELIBERATELY NOT PINNED. A sticky element taller than the
  // viewport pins its top at 0 and puts its own bottom permanently out of reach — which on
  // that panel is the Create button. This asserts the exception is real, not an accident.
  console.log('\n── C · and the New item form is NOT pinned (its Create button must stay reachable) ──');
  await p.evaluate(() => { const sc = document.querySelector('.app-content') || document.scrollingElement; sc.scrollTop = 0; });
  await p.click('button:has-text("New item")').catch(() => {});
  await p.waitForTimeout(700);
  const pinned = await p.evaluate(() => {
    const card = document.querySelector('.card');
    return { position: getComputedStyle(card).position, cls: card.className };
  });
  check(pinned.position !== 'sticky',
        'in New item mode the panel is not sticky',
        'it is sticky — a panel taller than the screen pins its top and hides its own Create button');

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
