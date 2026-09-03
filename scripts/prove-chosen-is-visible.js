// You can SEE which one you picked, and you can READ it.
//
// 2026-09-03, from a photograph of the tablet: the SELECTED payment tile showed a card
// emoji, a green border, and NO LABEL. "Visa/MC" was in the markup, was rendered, was
// correct — and was invisible. `.card { background-color:#fff }` is declared AFTER
// tailwind.css in the same <head>, both are single-class rules, so on equal specificity
// source order decided: `bg-green-600` lost, `text-white` (which `.card` does not declare)
// won, and the label was painted white on white.
//
// EVERY DOM ASSERTION PASSES ON THAT BUG. The element exists, it has text, it is visible
// by every definition Playwright offers, its class list contains both `bg-green-600` and
// `text-white`. The only thing that disagrees is a person looking at it. So this measures
// the two colours a person's eye actually receives — `getComputedStyle().color` against the
// background PAINTED BEHIND IT, walking up through transparent ancestors the way the screen
// composites — and applies the WCAG contrast ratio.
//
// A census on the day found EIGHT controls with this shape, and the payment tile was not
// the worst: dine-in / takeaway is the VAT RATE selector, 8.1% against 2.6%.
//
// Nothing is ever completed. Selecting a payment method writes no row.
const { chromium } = require('playwright');

// Contrast floor. 3.0 is WCAG AA for large text; these are 16-20px bold labels on a till
// at arm's length, and the bug this file exists for scored 1.0 — identical colours.
const FLOOR = 3.0;

(async () => {
  const b = await chromium.launch();
  // The tablet's real viewport: 2160x1440 at devicePixelRatio 1.5, measured off Angel's
  // own screenshot by the w-12 stepper rendering at 72 device px.
  const p = await (await b.newContext({ viewport: { width: 1440, height: 895 } })).newPage();
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

  // Installed into the page once and reused: the compositing rule the eye follows.
  const INSTALL = () => {
    const lum = (c) => {
      const [r, g, bl] = c.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
      return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
    };
    const parse = (s) => {
      const m = String(s).match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const n = m[1].split(',').map(x => parseFloat(x));
      return { rgb: n.slice(0, 3), a: n.length > 3 ? n[3] : 1 };
    };
    // THE BACKGROUND A PERSON SEES is not the element's own background-color — a
    // transparent element shows whatever is behind it. Walk up until something opaque
    // paints, exactly as the screen composites, or the measurement is fiction.
    window.__paintedBg = (el) => {
      for (let n = el; n; n = n.parentElement) {
        const c = parse(getComputedStyle(n).backgroundColor);
        if (c && c.a > 0.95) return c.rgb;
      }
      return [255, 255, 255];
    };
    window.__contrast = (el) => {
      const fg = parse(getComputedStyle(el).color);
      if (!fg) return null;
      const bg = window.__paintedBg(el);
      const l1 = lum(fg.rgb), l2 = lum(bg);
      return { ratio: (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05),
               fg: fg.rgb, bg };
    };
  };

  // ── The controls, and how to reach the state where the bug shows ─────────────────────
  // Each is CLICKED, not toggled through Alpine: the class binding is the thing under test,
  // so the test may not contain a copy of it.
  const SUITES = [
    { url: '/pos/checkout', label: 'payment method',
      // A basket is needed for checkout to render; nothing is ever completed.
      pre: async () => {
        await p.evaluate(() => sessionStorage.setItem('pos_cart', JSON.stringify({
          cart: [{ id: 'zz', product_id: 'zz', name: 'ZZPROBE contrast', quantity: 1,
                   price: 5.00, price_tiers: null, tier_mode: 'per_unit', product_class: 'cafe_food' }],
          discount: 0, totals: {} })));
      },
      controls: [
        ['💵 Cash',   'button:has-text("Cash")'],
        ['💳 card',   'button:has-text("Visa")'],
        ['🏦 Debit',  'button:has-text("Debit")'],
        ['📱 TWINT',  'button:has-text("TWINT")'],
      ] },
    { url: '/pos/checkout', label: 'the VAT rate selector',
      pre: async () => {
        await p.evaluate(() => sessionStorage.setItem('pos_cart', JSON.stringify({
          cart: [{ id: 'zz', product_id: 'zz', name: 'ZZPROBE contrast', quantity: 1,
                   price: 5.00, price_tiers: null, tier_mode: 'per_unit', product_class: 'cafe_food' }],
          discount: 0, totals: {} })));
      },
      controls: [
        ['🍽️ Dine in',  'button:has-text("Dine in")'],
        ['🥡 Takeaway', 'button:has-text("Takeaway")'],
      ] },
    { url: '/pos/reorder', label: 'Order Book reason',
      post: async () => {
        // The form lives behind the "add a line" panel.
        await p.evaluate(() => {
          const d = window.Alpine && Alpine.$data(document.querySelector('[x-data]'));
          if (d && 'newOpen' in d) d.newOpen = true;
        });
        await p.waitForTimeout(500);
      },
      controls: [
        ['🔁 Restock',        'button:has-text("Restock")'],
        ['🙋 Customer order', 'button:has-text("Customer order")'],
      ] },
  ];

  for (const suite of SUITES) {
    console.log(`\n── ${suite.label} (${suite.url}) ──`);
    // Land somewhere stable FIRST, then set up, then navigate. The first cut did the
    // reverse and /pos/checkout with an empty cart bounced to /pos/scan — so the basket
    // was written on the wrong page, the reload came back to the wrong page, and four
    // checks reported "the control is on the screen: no". A setup step that runs after
    // the redirect it exists to prevent is not a setup step.
    await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(800);
    if (suite.pre) await suite.pre();
    await p.goto('http://localhost:3000' + suite.url, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(1800);
    if (suite.post) { await suite.post(); await p.waitForTimeout(500); }
    await p.evaluate(INSTALL);

    for (const [name, sel] of suite.controls) {
      const btn = p.locator(sel).first();
      if (!(await btn.count())) {
        check(false, `${name} — the control is on the screen`,
              `no element matched ${sel} — a check that cannot find its subject always passes`);
        continue;
      }
      await btn.scrollIntoViewIfNeeded().catch(() => {});
      await btn.click({ force: true }).catch(() => {});
      await p.waitForTimeout(350);
      await p.evaluate(INSTALL);

      const r = await btn.evaluate((el) => {
        // Measure the LABEL, not the button: the emoji has its own colour, and a button
        // whose text sits in a child <p> is where the white-on-white actually happened.
        const texts = [...el.querySelectorAll('p, span')]
          // Strip variation selectors and ZWJ before deciding "is this only an emoji" —
          // "🍽️" is U+1F37D U+FE0F, and FE0F is not Extended_Pictographic, so the first
          // cut measured the emoji span and reported it as the label.
          .filter(n => {
            const t = n.textContent.replace(/[\uFE0E\uFE0F\u200D]/g, '').trim();
            return t && !/^\p{Extended_Pictographic}+$/u.test(t);
          });
        const target = texts[0] || el;
        const c = window.__contrast(target);
        return c && { ...c, text: target.textContent.trim().slice(0, 40),
                      chosen: el.className.includes('is-chosen') };
      });
      if (!r) { check(false, `${name} — could not read its colours`); continue; }
      const rgb = (a) => `rgb(${a.map(Math.round).join(',')})`;
      check(r.ratio >= FLOOR,
            `${name} — its label is readable once chosen  (contrast ${r.ratio.toFixed(1)}:1)`,
            `"${r.text}" is ${rgb(r.fg)} on ${rgb(r.bg)} — ratio ${r.ratio.toFixed(2)}, floor ${FLOOR}`
            + (r.ratio < 1.1 ? '  · THE SAME COLOUR AS ITS BACKGROUND — the label is invisible' : ''));
    }

    // AND you can tell it apart from the ones you did not pick. A control whose chosen
    // state paints the same as its neighbours is unreadable in a different way.
    if (suite.controls.length > 1) {
      const bgs = await p.evaluate((sels) => sels.map(s => {
        const el = [...document.querySelectorAll('button')]
          .find(b => b.textContent.includes(s));
        return el ? getComputedStyle(el).backgroundColor : null;
      }), suite.controls.map(c => c[0].replace(/^\S+\s/, '')));
      const distinct = new Set(bgs.filter(Boolean)).size;
      check(distinct > 1, `${suite.label} — the chosen one looks different from the rest`,
            'every control paints ' + bgs[0] + ' — nothing on screen says which is selected');
    }
  }

  await p.evaluate(() => sessionStorage.removeItem('pos_cart'));
  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
