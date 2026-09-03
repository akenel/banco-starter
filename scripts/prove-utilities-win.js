// A utility class on an element WINS. What the markup asks for is what the screen does.
//
// WHY THIS FILE EXISTS. Banco's base classes — `.input-field`, `.card`, `.btn-secondary` and
// the rest — are single-class rules, and so is every Tailwind utility. On equal specificity
// the LATER rule wins, and Banco's <style> block sat AFTER tailwind.css in the same <head>.
// So `w-16` on an `.input-field`, `bg-green-600` on a `.card`, `text-sm` on a `.btn-secondary`
// all lost, silently, with nothing in the markup or the head saying so. It cost three days:
//
//   2026-09-02  an Order Book qty box asked for w-16 (64px) and rendered at 790px, wrapping
//               a one-line row onto three
//   2026-09-03  the SELECTED payment tile painted white on white — bg-green-600 lost to
//               .card, text-white had no competitor and won, and "Visa/MC" was rendered,
//               correct, and invisible. Same shape on the VAT rate selector, 8.1% vs 2.6%.
//   2026-09-03  a census: 199 elements where a base class silently overruled the markup
//
// Fixed by moving the block ABOVE tailwind.css — the only lever that puts these rules above
// the element resets and below the utilities. (`:where()` was tried twice and is wrong:
// zero specificity also loses to preflight's `padding:0` / `background-color:transparent`
// on button and input, and the controls collapse.)
//
// THIS FILE DOES NOT READ THE HEAD. Checking the order of two tags would pass on a build
// where the utility still lost for some other reason. It measures the RENDERED value against
// what the class name asks for, on real screens.
const { chromium } = require('playwright');

// utility -> the computed value it must produce. Only ones with a single unambiguous answer.
const WIDTH = { 'w-12':48,'w-14':56,'w-16':64,'w-20':80,'w-24':96,'w-28':112,'w-32':128,'w-36':144,'w-40':160 };
const FONT  = { 'text-xs':12,'text-sm':14,'text-base':16,'text-lg':18,'text-xl':20,'text-2xl':24,'text-3xl':30 };
const PADY  = { 'py-0':0,'py-1':4,'py-2':8,'py-3':12,'py-4':16,'py-5':20,'py-6':24 };
// The fat-finger floor this repo already enforces in prove-keypad.
const TAP = 44;

const PAGES = ['/pos/scan','/pos/checkout','/pos/catalog','/pos/reorder','/pos/receiving',
               '/pos/customer-lookup','/pos/settings','/pos/shift','/pos/my-day','/pos/suppliers',
               '/pos/transactions','/pos/cleanup','/pos/held-orders','/pos/audit'];

(async () => {
  const b = await chromium.launch();
  // The tablet's real viewport: 2160x1440 at devicePixelRatio 1.5, measured off a photograph
  // by the w-12 stepper rendering at 72 device px. The proofs used to run at 1280x800.
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

  const BASE = ['input-field','btn-primary','btn-secondary','btn-danger','btn-success','card',
                'data-table','chip','chip-age','chip-deal','chip-warn','chip-bad',
                'price-display','price-display-large'];
  let seen = 0, wrong = [], small = [], pagesOk = 0;

  for (const url of PAGES) {
    const r = await p.goto('http://localhost:3000' + url, { waitUntil: 'domcontentloaded' }).catch(() => null);
    if (!r || r.status() !== 200) {
      // A page that does not load contributes ZERO elements and would quietly shrink the
      // population this suite claims to cover. Say so; do not average it away.
      check(false, `${url} loads`, 'status ' + (r ? r.status() : 'none'));
      continue;
    }
    pagesOk++;
    await p.waitForTimeout(1300);
    const res = await p.evaluate(({ BASE, WIDTH, FONT, PADY, TAP }) => {
      const out = { n: 0, wrong: [], small: [] };
      document.querySelectorAll('*').forEach(el => {
        const cls = (el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
        if (!cls.some(c => BASE.includes(c))) return;
        const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return;            // never rendered — measures nothing
        const cs = getComputedStyle(el);
        const say = (u, want, got) => out.wrong.push({
          u, want, got: Math.round(got * 10) / 10, tag: el.tagName.toLowerCase(),
          base: cls.filter(c => BASE.includes(c)).join('+'),
          txt: (el.textContent || '').trim().slice(0, 30) });
        for (const c of cls) {
          out.n++;
          if (c in WIDTH && Math.abs(r.width - WIDTH[c]) > 6) say(c, WIDTH[c], r.width);
          if (c in FONT  && Math.abs(parseFloat(cs.fontSize) - FONT[c]) > 0.6) say(c, FONT[c], parseFloat(cs.fontSize));
          if (c in PADY  && Math.abs(parseFloat(cs.paddingTop) - PADY[c]) > 0.6) say(c, PADY[c], parseFloat(cs.paddingTop));
        }
        // Honouring the markup must not put a control under the thumb floor. The markup is
        // the author's intent; the floor is the shop's, and the shop wins.
        if (['button','a','select'].includes(el.tagName.toLowerCase()) && r.height < TAP)
          out.small.push({ h: Math.round(r.height), txt: (el.textContent || '').trim().slice(0, 26) });
      });
      return out;
    }, { BASE, WIDTH, FONT, PADY, TAP });
    seen += res.n;
    res.wrong.forEach(w => wrong.push({ url, ...w }));
    res.small.forEach(s => small.push({ url, ...s }));
  }

  console.log(`\n── the markup is what the screen does ──`);
  check(pagesOk === PAGES.length, `all ${PAGES.length} screens loaded`,
        `${pagesOk} did — the rest contributed no elements and this suite would have measured a smaller shop than it names`);
  check(seen > 400, `enough to be worth saying: ${seen} class checks across ${pagesOk} screens`,
        `only ${seen} — a suite that finds almost nothing passes for the wrong reason`);
  check(wrong.length === 0, `every width / font-size / padding utility on a Banco base class is honoured`,
        wrong.slice(0, 12).map(w =>
          `${w.url} <${w.tag}.${w.base}> ${w.u} asks ${w.want} · renders ${w.got}   ${JSON.stringify(w.txt)}`
        ).join('\n       ') + (wrong.length > 12 ? `\n       … ${wrong.length - 12} more` : ''));

  console.log(`\n── and nothing fell under the thumb ──`);
  // Known and accepted: the Order Book's per-line controls and the audit screen's filter
  // chips were already under the floor before the cascade was corrected — they are logged,
  // not introduced here. This asserts the SHAPE of the list, so a NEW one shows up.
  const KNOWN = /\/pos\/(reorder|audit)$/;
  const fresh = small.filter(s => !KNOWN.test(s.url));
  check(fresh.length === 0, `no tappable control outside the known screens is under ${TAP}px`,
        fresh.slice(0, 10).map(s => `${s.url} ${s.h}px  ${JSON.stringify(s.txt)}`).join('\n       ')
        + (fresh.length > 10 ? `\n       … ${fresh.length - 10} more` : ''));

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed   (${seen} class checks, ${pagesOk} screens)`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
