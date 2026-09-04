// Every class our templates ask for actually does something.
//
// WHY THIS FILE EXISTS. src/static/pos/tailwind.css is a pre-built, frozen file with no
// config, no build step and no safelist — the deliberate "no node build in this repo" call.
// So a class written in a template that is not in that file does NOTHING, silently, and the
// markup reads as if it works. There is no error, no warning, no visual hint.
//
// 2026-09-04 a census found 131 of them. Not cosmetics: `left-1/2` + `-translate-x-1/2`
// that did not centre, four z-index utilities that never applied, kiosk modal scrims that
// did not darken, ~15 guest-facing text colours — and `from-cyan-700`, which is why Felix's
// tablet showed the shop's own name in white on near-white for two days. `min-h-[44px]` bit
// the same way on 2026-09-03 and was treated as a one-off.
//
// WHAT IT ASSERTS, and the two kinds are different on purpose:
//   plain utilities  — inject an element, and require the class to CHANGE at least one
//                      computed property against an identical bare element. A rule that
//                      exists but is overridden to nothing still fails.
//   variants/markers — `hover:`, `sm:`, `group-hover:` cannot be measured from a static
//                      element, so for those the assertion is that a matching selector is
//                      in the CSSOM. Weaker, and stated as such rather than pretended.
//
// It reads the TEMPLATES, not a list. A class added tomorrow is covered tomorrow.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TPL = 'src/templates/pos';
// Classes with no declarations by design. Keep this list short and say why for each.
const SINGLE_WORD = new Set(`block inline flex grid hidden contents table absolute relative fixed sticky static italic underline truncate uppercase lowercase capitalize group container isolate invisible visible rounded border shadow ring transform transition resize sr-only antialiased`.split(/\s+/));

const MARKERS = new Set([
  'group',   // Tailwind reads it only as the ancestor in `.group:hover .group-hover\\:x`
  'sheet',   // postcard.html styles that link with `.toolbar a`, by TAG — no rule needed
]);

function pageStyles(txt) {
  return (txt.match(/<style[\s\S]*?<\/style>/g) || []).join('');
}

// The same two sources the generator reads: literal class="" attributes, AND Jinja
// {% set %} string literals — login.html picks its gradient per environment that way, so
// `from-cyan-700` never appears in any class="" and a census that skips it reports the
// page clean.
function census() {
  const base = pageStyles(fs.readFileSync(path.join(TPL, 'base.html'), 'utf8'));
  const found = new Map();
  for (const f of fs.readdirSync(TPL).filter(x => x.endsWith('.html'))) {
    const txt = fs.readFileSync(path.join(TPL, f), 'utf8');
    const own = pageStyles(txt);
    const segs = [];
    for (const m of txt.matchAll(/(?<![-:\w])class="([^"]*)"/g)) {
      if (m[1].includes('{{') || m[1].includes('{%')) continue;
      segs.push(m[1]);
    }
    // Alpine bindings. `:class="x ? 'bg-rose-50' : 'bg-white'"` names real classes that
    // must exist, and a census reading only literal class="" attributes never sees them —
    // which is how bg-rose-50, space-y-2, pl-1 and eight others stayed dead through the
    // first pass of this very check.
    // …but the same attribute holds comparison operands — :class="method === 'cash' ? …"
    // — so a token only counts as a utility if it carries a separator or is one of the
    // handful of single-word ones. Without that, `cash`, `visa` and `twint` arrive as
    // classes and the check demands CSS for them.
    for (const m of txt.matchAll(/:class="([^"]*)"/g)) {
      for (const lit of m[1].matchAll(/'([^']*)'/g)) {
        const toks = lit[1].split(/\s+/).filter(Boolean);
        if (toks.length && toks.every(t2 =>
              /^-?[a-z][-a-z0-9:/[\]().!#%,]*$/.test(t2) &&
              (/[-:/[]/.test(t2) || SINGLE_WORD.has(t2)))) segs.push(lit[1]);
      }
    }
    for (const m of txt.matchAll(/{%-?\s*set\s+\w+\s*=\s*'([^']*)'/g)) {
      const toks = m[1].split(/\s+/).filter(Boolean);
      if (toks.length && toks.every(t => /^-?[a-z][-a-z0-9:/[\]().!#%,]*$/.test(t))) segs.push(m[1]);
    }
    for (const seg of segs) {
      for (const c of seg.split(/\s+/)) {
        if (!c || !/^[-a-z0-9:/[\]().!#%,]+$/i.test(c)) continue;
        // A class defined in the page's OWN <style> (or base's) is that page's business.
        // Selector boundary, not substring: `.bg-rose-50` is a substring of `.bg-rose-500`.
        const esc = '.' + c.replace(/([.[\]()/:!#%,*])/g, '\\$1');
        const pat = new RegExp(esc.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?![0-9A-Za-z_\\-\\\\])');
        if (pat.test(base) || pat.test(own)) continue;
        if (!found.has(c)) found.set(c, new Set());
        found.get(c).add(f);
      }
    }
  }
  return found;
}

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1440, height: 895 } })).newPage();
  let pass = 0, fail = 0;
  const check = (ok, what, detail) => {
    if (ok) { pass++; console.log('  ✅ ' + what); }
    else { fail++; console.log('  ❌ ' + what + (detail ? '\n       ' + detail : '')); }
  };

  await p.goto('http://localhost:3000/pos', { waitUntil: 'load' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  await p.goto('http://localhost:3000/pos/scan', { waitUntil: 'load' });
  await p.waitForTimeout(1500);

  const used = census();
  const classes = [...used.keys()].sort();
  console.log(`\n── ${classes.length} distinct classes used across the POS templates ──`);
  check(classes.length > 500, 'the census found a real population',
        `only ${classes.length} — a scanner that reads nothing passes everything`);

  const VARIANT = /^(hover|focus|active|disabled|group-hover|focus-visible|peer-checked|first|last|odd|even|print|sm|md|lg|xl|2xl):/;
  const plain = classes.filter(c => !VARIANT.test(c) && !MARKERS.has(c));
  const variants = classes.filter(c => VARIANT.test(c));

  // ── plain utilities: does the class CHANGE what the browser paints? ──────────────────
  const dead = await p.evaluate((list) => {
    const host = document.createElement('div');
    host.style.cssText = 'position:absolute;left:-9999px;top:0;width:200px;height:200px';
    document.body.appendChild(host);

    // THE PROBE NEEDS SOMETHING TO OVERRIDE. A bare <div> is already display:block with
    // zero margin and no border, so `block`, `m-0` and `border-0` change nothing on it and
    // the first version of this check called eleven perfectly good utilities dead. Give the
    // probe a deliberately odd baseline and every utility has a value to replace.
    //
    // :where() is the right tool HERE and was the wrong tool for the base classes on
    // 2026-09-03 — same zero specificity, opposite requirement. This baseline MUST lose to
    // everything; a base class must not.
    const style = document.createElement('style');
    style.textContent = ':where(.__probe){' + [
      // NOT absolute: an absolutely positioned box is blockified, so display:inline
      // computes to block and `.block` read as a class that does nothing.
      'position:relative', 'display:inline', 'margin:7px', 'padding:7px',
      'border:3px solid rgb(1,2,3)', 'background-color:rgb(1,2,3)',
      'background-image:linear-gradient(rgb(1,2,3),rgb(1,2,3))', 'color:rgb(1,2,3)',
      'font-weight:900', 'font-size:7px', 'line-height:7px', 'letter-spacing:7px',
      'width:77px', 'height:77px', 'min-width:77px', 'max-width:77px',
      'min-height:77px', 'max-height:77px',
      'top:7px', 'left:7px', 'right:7px', 'bottom:7px', 'z-index:7',
      'opacity:.77', 'border-radius:7px', 'cursor:crosshair', 'list-style-type:square',
      'text-decoration-line:overline', 'gap:7px', 'column-gap:7px', 'row-gap:7px',
      'accent-color:rgb(1,2,3)', 'overflow:scroll', 'transform:translate(7px,7px)',
      'grid-column:span 7/span 7', 'flex:7 7 7px', 'text-align:justify',
      'white-space:pre-wrap', 'vertical-align:super', 'box-shadow:0 0 7px rgb(1,2,3)',
      'text-transform:uppercase', 'font-style:italic', 'text-overflow:clip',
    ].join(';') + '}';
    document.head.appendChild(style);
    const kids = (el) => { for (let i = 0; i < 2; i++) el.appendChild(document.createElement('span')); };

    // TWO baselines, because one can never do it. A bare <div> catches everything that adds
    // (h-10 on an auto height); the odd probe catches everything that REMOVES or resets
    // (m-0, border-0, block on an inline). Measured against only the odd one, every h-* in
    // the file read as dead — its min/max-height clamped the result. A class is dead only
    // when it moves NEITHER.
    const plainBare = document.createElement('div');
    kids(plainBare);
    host.appendChild(plainBare);
    const bare = document.createElement('div');
    bare.className = '__probe';
    kids(bare);
    host.appendChild(bare);
    // Tailwind's preflight sets --tw-translate-x, --tw-scale-x and friends on `*`, so
    // "this custom property is non-empty" is true of EVERY element on the page. The
    // baseline has to carry them too, or the fallback below absolves every dead class
    // and the whole check reports a clean run on a stylesheet that is missing 133 rules.
    // It did exactly that on the first red test.
    const TW_VARS = ['--tw-gradient-from', '--tw-gradient-to', '--tw-gradient-stops',
                     '--tw-translate-x', '--tw-translate-y', '--tw-scale-x', '--tw-scale-y',
                     '--tw-ring-color', '--tw-bg-opacity', '--tw-text-opacity',
                     '--tw-border-opacity'];
    const snap = (el) => {
      const cs = getComputedStyle(el), o = {};
      for (let i = 0; i < cs.length; i++) o[cs[i]] = cs.getPropertyValue(cs[i]);
      for (const v of TW_VARS) o[v] = cs.getPropertyValue(v);
      return o;
    };
    const baseline = snap(bare);
    const baselinePlain = snap(plainBare);
    const out = [];
    const differs = (el, base) => {
      const cs = getComputedStyle(el);
      for (let i = 0; i < cs.length; i++) {
        if (cs.getPropertyValue(cs[i]) !== base[cs[i]]) return true;
      }
      // Custom properties do not appear in the enumeration above, so check them by name —
      // against the baseline VALUE, never against emptiness. Tailwind's preflight sets
      // --tw-translate-x and friends on `*`, so "non-empty" is true of every element and
      // absolved every dead class on the first red run.
      for (const v of TW_VARS) if (cs.getPropertyValue(v) !== base[v]) return true;
      return false;
    };
    for (const c of list) {
      const el = document.createElement('div');
      el.className = '__probe ' + c;
      kids(el);                       // divide-* needs siblings to draw a line between
      host.appendChild(el);
      const el2 = document.createElement('div');
      el2.className = c;
      kids(el2);
      host.appendChild(el2);
      let changed = differs(el, baseline) || differs(el2, baselinePlain);
      // placeholder-* paints a pseudo-element that a <div> does not have. Probe an input.
      if (!changed && c.startsWith('placeholder-')) {
        const i1 = document.createElement('input'), i2 = document.createElement('input');
        i2.className = c;
        host.appendChild(i1); host.appendChild(i2);
        const a = getComputedStyle(i2, '::placeholder'), bl = getComputedStyle(i1, '::placeholder');
        for (const prop of ['color', 'opacity', 'font-size']) {
          if (a.getPropertyValue(prop) !== bl.getPropertyValue(prop)) { changed = true; break; }
        }
        host.removeChild(i1); host.removeChild(i2);
      }
      // divide-* paints on the CHILDREN, never on the element itself.
      if (!changed && (c.startsWith('divide-') || c.startsWith('space-'))) {
        const k = el.children[1], kb = bare.children[1];
        const a = getComputedStyle(k), bl = getComputedStyle(kb);
        for (const prop of ['border-top-width', 'border-top-color', 'border-left-width',
                            'border-left-color', 'margin-top', 'margin-left']) {
          if (a.getPropertyValue(prop) !== bl.getPropertyValue(prop)) { changed = true; break; }
        }
      }
      if (!changed) out.push(c);
      host.removeChild(el);
      host.removeChild(el2);
    }
    document.head.removeChild(style);
    document.body.removeChild(host);
    return out;
  }, plain);

  // A class that changes nothing is not automatically a bug. `divide-gray-200` sets
  // border-color to the very grey Tailwind's preflight already defaults to — present,
  // correct, and invisible. The FAILURE is a class with no rule anywhere, so a no-visual
  // result is only damning when the CSSOM has no selector for it either.
  const reallyDead = await p.evaluate((list) => {
    const sels = [];
    for (const sheet of document.styleSheets) {
      let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
      const walk = (rs) => { for (const r of rs) {
        if (r.selectorText) sels.push(r.selectorText);
        if (r.cssRules) walk(r.cssRules);
      } };
      walk(rules);
    }
    const blob = sels.join('\n');
    return list.filter(c => !blob.includes('.' + c.replace(/([.[\]()/:!#%,*])/g, '\\$1')));
  }, dead);

  check(reallyDead.length === 0,
        `every one of the ${plain.length} plain utilities is defined and does something`,
        reallyDead.length
          ? reallyDead.map(c => `  ${c}  (${[...used.get(c)].join(', ')})`).join('\n       ')
            + `\n       ${reallyDead.length} classes are written in the markup and have NO RULE ANYWHERE.`
            + '\n       Run: python3 scripts/make-css-addendum.py'
          : (dead.length ? `${dead.length} paint nothing but ARE defined (a value equal to the default) — fine` : ''));

  // ── variants: a matching selector has to be in the CSSOM ─────────────────────────────
  const noRule = await p.evaluate((list) => {
    const sels = [];
    for (const sheet of document.styleSheets) {
      let rules;
      try { rules = sheet.cssRules; } catch (e) { continue; }   // cross-origin
      const walk = (rs) => { for (const r of rs) {
        if (r.selectorText) sels.push(r.selectorText);
        if (r.cssRules) walk(r.cssRules);
      } };
      walk(rules);
    }
    const blob = sels.join('\n');
    return list.filter(c => !blob.includes('.' + c.replace(/([.[\]()/:!#%,*])/g, '\\$1')));
  }, variants);

  check(noRule.length === 0,
        `every one of the ${variants.length} variant utilities has a rule in the stylesheet`,
        noRule.map(c => '  ' + c).join('\n       '));

  // ── and the login page's palette, per environment ────────────────────────────────────
  // Five branches, and only ONE of them runs on any given box. `from-cyan-700` was missing
  // for UAT alone, so a dev machine and prod were both fine and the shop's tablet was not.
  console.log('\n── the login gradient, on every environment ──');
  const login = fs.readFileSync(path.join(TPL, 'login.html'), 'utf8');
  const palettes = [...login.matchAll(/{%-?\s*set\s+_bg\s*=\s*'([^']*)'/g)].map(m => m[1]);
  check(palettes.length >= 5, `login.html declares ${palettes.length} environment palettes`,
        'expected at least 5 — prod, staging, uat, sandbox, local');
  const broken = await p.evaluate((pals) => {
    const out = [];
    for (const cls of pals) {
      const el = document.createElement('div');
      el.className = 'bg-gradient-to-br ' + cls;
      el.style.cssText = 'position:absolute;left:-9999px;width:100px;height:100px';
      document.body.appendChild(el);
      const bg = getComputedStyle(el).backgroundImage;
      document.body.removeChild(el);
      // "Is it a gradient" is NOT the question, and asking only that shipped a broken one
      // to prod on 2026-09-04: a lone `from-*` in a stylesheet loading after tailwind.css
      // clobbers the three-stop --tw-gradient-stops that `via-*` had already set, and the
      // UAT login computed to `linear-gradient(to right bottom, rgb(14,116,144),
      // rgba(14,116,144,0))` — cyan fading to nothing. A gradient. Not the one designed.
      //
      // So count the STOPS and require one per from-/via-/to- class the markup asked for,
      // and refuse a fully transparent final stop when a `to-` was named.
      const want = cls.split(/\s+/).filter(c => /^(from|via|to)-/.test(c)).length;
      const stops = (bg.match(/rgba?\([^)]*\)/g) || []);
      const lastTransparent = stops.length > 0 && /,\s*0\s*\)$/.test(stops[stops.length - 1]);
      if (!bg || bg === 'none' || !bg.includes('gradient')) out.push({ cls, bg, why: 'no gradient at all' });
      else if (stops.length < want) out.push({ cls, bg, why: `${stops.length} colour stops, the markup names ${want}` });
      else if (lastTransparent && /(^|\s)to-/.test(cls)) out.push({ cls, bg, why: 'the last stop is fully transparent, but a to- colour was named' });
    }
    return out;
  }, palettes);
  check(broken.length === 0, 'every environment paints an actual gradient behind the login card',
        broken.map(x => `  "${x.cls}" — ${x.why}\n         computes to ${x.bg}`).join('\n       '));

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
