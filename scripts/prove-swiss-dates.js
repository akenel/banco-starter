// Every date a person TYPES into Banco is dd.mm.yyyy, every time is a 24-hour clock, and
// the value recorded is the day and the hour they meant.
//
// WHY THIS FILE EXISTS. 2026-09-03, Angel photographed the tablet mid-sale: the 18+ age
// gate's Date of birth field read `mm/dd/yyyy`. On a Swiss till. A cashier under a queue
// types 03.09.2000 and records 9 March — an age-gate field in the wrong order is a
// compliance defect, not a cosmetic one, and NOTHING in the DOM says it is wrong. The
// element is `<input type="date">`; the value it holds is ISO either way. Only a picture,
// or this, can tell.
//
// MEASURED FIRST (scratchpad, same day): a native date input takes its format from the
// BROWSER'S UI LOCALE. Four inputs — inherited lang="en", lang="de-CH", lang="de",
// lang="fr-CH" — screenshotted in two browser contexts rendered eight identical boxes.
// The `lang` attribute does nothing. So these fields are Banco's own text boxes now, and
// this proves the whole round trip: what is typed, what is shown, what is stored.
//
// NOTHING IS EVER SAVED. The age gate is opened, the box is typed into, and the run ends.
// Never press Complete on a shop's books.
const { chromium } = require('playwright');

// Each page names how many Banco date boxes it MUST have. Without that number the
// "no native date input" check below passes on a 404, an error page, or a template that
// lost the field entirely — which it did on the first run of this file: /pos/customer_lookup
// (underscore) is not a route, the page came back 404, and the check reported a clean pass
// on a screen that did not exist. LESSON #5, in my own harness, within an hour of writing
// the comment about it. A count the page must MEET is what makes the absence meaningful.
const PAGES = [
  { url: '/pos/checkout',        label: 'the 18+ age gate',  boxes: 1 },
  { url: '/pos/customer-lookup', label: 'sign up a member',  boxes: 2 },
  { url: '/pos/settings',        label: 'staff card',        boxes: 2 },
];

(async () => {
  const b = await chromium.launch();
  // The tablet's real viewport — 2160x1440 at devicePixelRatio 1.5, measured off Angel's
  // own screenshot by the w-12 stepper rendering at 72 device px. The proofs used to run
  // at 1280x800, which is a screen nobody in this shop is standing in front of.
  const ctx = await b.newContext({ viewport: { width: 1440, height: 895 } });
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

  // ── A · THE HELPERS, against the days that break a naive parser ───────────────────────
  // A regex that only counts digits accepts 31.02.1990 and hands the age gate a birthday
  // nobody has. These run in the PAGE, against the shipped file — not a copy pasted here.
  console.log('\n── A · the mask and the parser ──');
  const helpers = await p.evaluate(() => {
    const out = { missing: [] };
    for (const fn of ['posDateMask', 'posDateToISO', 'posISOToDate'])
      if (typeof window[fn] !== 'function') out.missing.push(fn);
    if (out.missing.length) return out;
    out.mask = [['3', '3'], ['31', '31'], ['311', '31.1'], ['3112', '31.12'],
                ['31121990', '31.12.1990'], ['311219901', '31.12.1990'],
                ['1990-12-31', '31.12.1990'], ['31.12.1990', '31.12.1990']]
      .map(([i, w]) => [i, w, window.posDateMask(i)]);
    out.iso = [['31.12.1990', '1990-12-31'], ['01.01.2000', '2000-01-01'],
               ['29.02.2024', '2024-02-29'], ['29.02.2023', ''], ['31.02.1990', ''],
               ['00.00.0000', ''], ['3.12.1990', ''], ['31.12.1899', '']]
      .map(([i, w]) => [i, w, window.posDateToISO(i)]);
    // The digits that can never be part of a date do not appear at all. Felix typed
    // 33.33.3333 into a live member record and the Save button sat there fully green.
    out.clamp = [['33333333', '3'], ['4', ''], ['39', '3'], ['030933333', '03.09'],
                 ['0000', '0'], ['03092000', '03.09.2000']]
      .map(([i, w]) => [i, w, window.posDateMask(i)]);
    // And a birthdate is narrower than a date. Built from TODAY, never a literal —
    // a hardcoded year passes for a while and then quietly stops meaning anything.
    const yr = new Date().getUTCFullYear();
    const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
    out.birth = [['03.09.2000', '2000-09-03'],
                 [('0' + (new Date(Date.now() + 86400000).getUTCDate())).slice(-2) + '.'
                  + ('0' + (new Date(Date.now() + 86400000).getUTCMonth() + 1)).slice(-2) + '.'
                  + tomorrow.slice(0, 4), ''],
                 ['01.01.' + (yr - 130), ''], ['01.01.' + (yr - 40), (yr - 40) + '-01-01']]
      .map(([i, w]) => [i, w, window.posBirthdateISO(i)]);
    return out;
  });
  check(!helpers.missing.length, 'the date helpers are on the page',
        'missing: ' + (helpers.missing || []).join(', ') + ' — pos-keypad.js did not load');
  if (!helpers.missing.length) {
    const mbad = helpers.mask.filter(([, w, g]) => w !== g);
    check(!mbad.length, `the mask writes dd.mm.yyyy as you type (${helpers.mask.length} cases)`,
          mbad.map(([i, w, g]) => `"${i}" → "${g}", expected "${w}"`).join('\n       '));
    const ibad = helpers.iso.filter(([, w, g]) => w !== g);
    check(!ibad.length, `a day that does not exist is refused, not stored (${helpers.iso.length} cases)`,
          ibad.map(([i, w, g]) => `"${i}" → "${JSON.stringify(g)}", expected ${JSON.stringify(w)}`).join('\n       '));
    const cbad = helpers.clamp.filter(([, w, g]) => w !== g);
    check(!cbad.length, `a digit that cannot start a day, a month or a year never appears (${helpers.clamp.length} cases)`,
          cbad.map(([i, w, g]) => `typing "${i}" leaves "${g}", expected "${w}"`).join('\n       '));
    const bbad = helpers.birth.filter(([, w, g]) => w !== g);
    check(!bbad.length, `a birthdate is in the past and inside a human lifetime (${helpers.birth.length} cases)`,
          bbad.map(([i, w, g]) => `"${i}" → ${JSON.stringify(g)}, expected ${JSON.stringify(w)}`).join('\n       '));
  }

  // ── B · NO NATIVE DATE INPUT SURVIVES ON A SCREEN A CASHIER TYPES INTO ────────────────
  // The thing being prevented is a REGRESSION: `type="date"` is the natural thing to write,
  // it looks right in the source, and it is wrong on every Swiss device whose browser is
  // not set to a Swiss locale. So the assertion is about the type, not about one field.
  console.log('\n── B · no field falls back to the browser\'s locale ──');
  // Read the SERVED HTML, not the live DOM. Half of these fields sit inside a modal or an
  // x-for that has no rows yet, so a DOM sweep finds them only when something else has
  // already gone right — and reports a clean page when the field was deleted. The template
  // is what this section is about.
  for (const pg of PAGES) {
    const html = await p.evaluate(async (u) => {
      const r = await fetch(u, { credentials: 'same-origin' });
      return { status: r.status, body: await r.text() };
    }, pg.url);
    check(html.status === 200, `${pg.url} loads`,
          'status ' + html.status + ' — every check below would pass on an empty page');
    const ours = (html.body.match(/data-i18n-placeholder="common\.date_placeholder"/g) || []).length;
    check(ours === pg.boxes, `${pg.label} (${pg.url}) has its ${pg.boxes} Banco date box(es)`,
          'found ' + ours + ' — a field that vanished cannot be caught by looking for what is absent');
    const natives = (html.body.match(/<input[^>]*type="date"/g) || []);
    check(natives.length === 0, `${pg.label} (${pg.url}) has no native date input`,
          'found ' + natives.length + ': ' + natives.join(' · ').slice(0, 300)
          + ' — these render in the BROWSER\'s locale, not the shop\'s');
  }

  // ── C · TYPE A SWISS DATE INTO THE REAL BOX AND SEE WHAT GETS RECORDED ────────────────
  // The whole point. 03.09.2000 is the date that tells the two orders apart: read as
  // dd.mm it is 3 September, read as mm/dd it is 9 March. Everything else could pass
  // while still being wrong.
  console.log('\n── C · 03.09.2000 typed at the till is 3 September, not 9 March ──');
  await p.goto('http://localhost:3000/pos/customer-lookup', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1800);
  // Open the sign-up form through its own button — the panel is x-show, so the field is in
  // the DOM either way, but a box the cashier cannot reach is not a fixed box.
  const opener = p.locator('[data-i18n="customer.add_new_crack"]').first();
  check(await opener.count() > 0, 'the sign-up form has a button on it');
  if (await opener.count()) { await opener.click(); await p.waitForTimeout(700); }
  const box2 = p.locator('input[data-i18n-placeholder="common.date_placeholder"]:visible').first();
  check(await box2.count() > 0, 'the sign-up form has a Banco date box',
        'no input carrying data-i18n-placeholder="common.date_placeholder" on this page');
  if (await box2.count()) {
    // Type DIGITS, the way a person does — the dots are the mask's job, and if the mask is
    // not wired the typed string arrives as "03092000" and nothing here will accept it.
    await box2.click({ force: true });
    await box2.type('03092000', { delay: 40 });
    await p.waitForTimeout(400);
    const shown = await box2.inputValue();
    check(shown === '03.09.2000', 'typing 03092000 shows 03.09.2000',
          'the box shows "' + shown + '"');
    const stored = await p.evaluate(() => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      return (d.newCustomer && d.newCustomer.birthdate) || null;
    });
    check(stored === '2000-09-03', 'and records 2000-09-03 — September, the month that was typed',
          'recorded "' + stored + '"' + (stored === '2000-03-09' ? '  (MONTH AND DAY ARE SWAPPED)' : ''));

    // A REFUSAL MUST BE A REFUSAL. 31.02 is a day that does not exist; the box may show
    // what was typed, but nothing may reach the record.
    await box2.fill('');
    await box2.type('31021990', { delay: 30 });
    await p.waitForTimeout(300);
    const bogus = await p.evaluate(() => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      return (d.newCustomer && d.newCustomer.birthdate) || '';
    });
    check(bogus === '', '31.02.1990 is not recorded as anything',
          'recorded "' + bogus + '" for a day that does not exist');
  }

  // ── D · THE PLACEHOLDER SAYS THE ORDER, IN THE SHOP'S LANGUAGE ────────────────────────
  // "is it rendered" is not the question — a placeholder nobody can read is the same as no
  // placeholder. Read what the box actually shows, after i18n has run.
  console.log('\n── D · the box says what order it wants ──');
  const ph = await box2.count() ? await box2.getAttribute('placeholder') : null;
  check(/^(TT\.MM\.JJJJ|dd\.mm\.yyyy|jj\.mm\.aaaa|gg\.mm\.aaaa)$/.test(ph || ''),
        `the placeholder spells out the order ("${ph}")`,
        'a date box that does not say its order is a guess the cashier has to make');


  // ══ THE CLOCK ═════════════════════════════════════════════════════════════════════════
  // Added 2026-09-04, one day after the dates, because it is the SAME BUG and I did not
  // grep for it. Felix on the tablet: My Day's "Close out my day" read `09:54 AM`. A Swiss
  // shift record does not say AM.
  //
  // THIS HARNESS CANNOT SEE THE SYMPTOM. Headless Chromium renders `<input type="time">`
  // as 24-hour in en-US, de-CH and fr-CH alike — measured, three contexts, one screenshot,
  // all identical. Nothing I can write in Playwright would ever have gone red on the bug
  // that was actually on the tablet (LESSON #6: ask what your harness is structurally blind
  // to). So these sections assert the ABSENCE of the native widget and the presence of ours
  // — the shape of the fix, not the symptom, because the symptom is off-limits to me.

  // ── E · THE CLOCK HELPERS, against times that are not on any clock ────────────────────
  console.log('\n── E · the time mask and the parser ──');
  await p.goto('http://localhost:3000/pos/my-day', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1500);
  const th = await p.evaluate(() => {
    const out = { missing: [] };
    for (const fn of ['posTimeMask', 'posTimeValue'])
      if (typeof window[fn] !== 'function') out.missing.push(fn);
    if (out.missing.length) return out;
    out.mask = [['0', '0'], ['09', '09'], ['095', '09:5'], ['0954', '09:54'],
                ['09544', '09:54'], ['09:54', '09:54'], ['9:54 AM', '95:4']]
      .map(([i, w]) => [i, w, window.posTimeMask(i)]);
    out.val = [['09:54', '09:54'], ['00:00', '00:00'], ['23:59', '23:59'],
               ['24:00', ''], ['25:00', ''], ['09:74', ''], ['9:54', ''], ['', '']]
      .map(([i, w]) => [i, w, window.posTimeValue(i)]);
    return out;
  });
  check(!th.missing.length, 'the time helpers are on the page',
        'missing: ' + (th.missing || []).join(', ') + ' — pos-keypad.js did not load');
  if (!th.missing.length) {
    const bad1 = th.mask.filter(([, w, g]) => w !== g);
    check(!bad1.length, `the mask writes HH:MM as you type (${th.mask.length} cases)`,
          bad1.map(([i, w, g]) => `"${i}" -> "${g}", expected "${w}"`).join('\n       '));
    const bad2 = th.val.filter(([, w, g]) => w !== g);
    check(!bad2.length, `an hour that is not on a clock is refused, not stored (${th.val.length} cases)`,
          bad2.map(([i, w, g]) => `"${i}" -> ${JSON.stringify(g)}, expected ${JSON.stringify(w)}`).join('\n       '));
  }

  // ── F · NO NATIVE TIME INPUT ANYWHERE A PERSON TYPES ──────────────────────────────────
  // Two assertions, because either alone is a lie: the native widget must be GONE, and
  // ours must be THERE. A template that lost both fields passes the first and fails the
  // second, which is the whole reason section B grew a count on its first run.
  console.log('\n── F · no clock falls back to the browser\'s locale ──');
  const md = await p.evaluate(async () => {
    const r = await fetch('/pos/my-day', { credentials: 'same-origin' });
    return { status: r.status, body: await r.text() };
  });
  check(md.status === 200, '/pos/my-day loads',
        'status ' + md.status + ' — every check below would pass on an empty page');
  const ourTimes = (md.body.match(/window\.posTimeMask\(/g) || []).length;
  check(ourTimes >= 2, 'Close out my day has its 2 Banco time boxes',
        'found ' + ourTimes + ' — a field that vanished cannot be caught by looking for what is absent');
  const natT = (md.body.match(/<input[^>]*type="time"/g) || []);
  check(natT.length === 0, '/pos/my-day has no native time input',
        'found ' + natT.length + ': ' + natT.join(' · ').slice(0, 240));

  // The sweep, because the next one will not be on My Day. `type="date"` is deliberately
  // NOT swept: the six report range-filters still use it and are their own piece of work
  // (they are picker-driven, with preset buttons, and nobody types into them).
  const fs = require('fs'), path = require('path');
  const dir = 'src/templates/pos';
  const offenders = fs.readdirSync(dir).filter(f => f.endsWith('.html'))
    .filter(f => /<input[^>]*type="time"/.test(fs.readFileSync(path.join(dir, f), 'utf8')));
  check(offenders.length === 0, `no template under ${dir} carries a native time input`,
        'found in: ' + offenders.join(', '));

  // ── G · TYPE A TIME AT THE TILL AND SEE WHAT GETS RECORDED ────────────────────────────
  // Nothing is submitted. The form is filled and the run ends — My Day writes a shift row
  // only on its own save button, which this never touches.
  console.log('\n── G · 0954 typed at the till is 09:54, and 2530 is nothing ──');
  const box = p.locator('input[placeholder="HH:MM"]').first();
  if (!(await box.count())) {
    check(false, 'the Start time box is on the screen',
          'no input[placeholder="HH:MM"] — a check that cannot find its subject always passes');
  } else {
    await box.scrollIntoViewIfNeeded().catch(() => {});
    await box.click({ force: true }).catch(() => {});
    await box.fill(''); await box.type('0954', { delay: 40 });
    await p.waitForTimeout(250);
    const shown = await box.inputValue();
    check(shown === '09:54', 'the box shows 09:54 — colon placed as you type',
          'it shows "' + shown + '"');
    const stored = await box.evaluate(el => {
      const d = window.Alpine && Alpine.$data(el);
      return d ? d.form.start_time : null;
    });
    check(stored === '09:54', 'the shift record gets "09:54", 24-hour, no AM',
          'the model holds ' + JSON.stringify(stored));

    await box.fill(''); await box.type('2530', { delay: 40 });
    await p.waitForTimeout(250);
    const stored2 = await box.evaluate(el => {
      const d = window.Alpine && Alpine.$data(el);
      return d ? d.form.start_time : null;
    });
    check(stored2 === '', 'typing 25:30 records NOTHING rather than a time nobody worked',
          'the model holds ' + JSON.stringify(stored2) + ' — 25:30 is not an hour of any day');
  }

  // ── H · AND NO AM/PM SURVIVES AS A LITERAL IN THE SHIPPED STRINGS ─────────────────────
  // closeout.html shipped "8:00 AM" as an i18n VALUE in English and French. A grep, not a
  // render: the string is what is wrong, and it is wrong before anything draws it.
  console.log('\n── H · no AM/PM left in the strings ──');
  const i18n = fs.readFileSync('src/static/pos/pos-i18n.js', 'utf8');
  const ampm = (i18n.match(/"[^"]*\d\s?[AP]M"/g) || []);
  check(ampm.length === 0, 'no shipped string carries a 12-hour time',
        'found: ' + ampm.join(' · '));


  // ── I · AND IT CAN BE TYPED ON THE TABLET'S OWN PAD, WHICH IS THE ONLY WAY IN ────────
  // The section that should have existed yesterday. Every check above types with
  // page.type() — that is a HARDWARE KEYBOARD. This shop's tablet raises none; it has
  // Banco's pad and nothing else, which is the entire reason pos-keypad.js exists. So a
  // date field could be green on every assertion in this file and impossible to fill in
  // at the counter, and on 2026-09-03 it was: priceOk() judged the masked value against
  // the MONEY regex, and 03.09.2000 died at "03.09". Felix found it in ten minutes with
  // the pad; four sections of this file and 80 checks of prove-keypad.js did not.
  //
  // Needs its own context: the pad refuses to initialise unless the device reports touch.
  console.log('\n── I · a date and a time typed on Banco\'s own keypad ──');
  const tctx = await b.newContext({ hasTouch: true, viewport: { width: 1440, height: 895 } });
  const tp = await tctx.newPage();
  await tp.goto('http://localhost:3000/pos', { waitUntil: 'domcontentloaded' });
  if (await tp.$('button:has-text("Login")')) { await tp.click('button:has-text("Login")'); await tp.waitForTimeout(3500); }
  if (await tp.$('#username')) {
    await tp.fill('#username', 'ralph'); await tp.fill('#password', 'ralph');
    await tp.click('#kc-login, input[type=submit]'); await tp.waitForURL('**/pos/**', { timeout: 20000 });
  }

  // Taps, not clicks. The keys fire on pointerdown; HTMLElement.click() dispatches a
  // click and nothing else, so a probe that "presses" the pad that way reports every key
  // as accepted while the real pad refuses them. It cost half an hour to notice.
  async function padType(sel, digits) {
    const el = tp.locator(sel).first();
    if (!(await el.count())) return { err: 'field not found: ' + sel };
    await el.scrollIntoViewIfNeeded().catch(() => {});
    await el.tap().catch(async () => { await el.click({ force: true }); });
    await tp.waitForTimeout(700);
    if (!(await tp.evaluate(() => !!document.querySelector('.pk.on')))) return { err: 'the pad did not open' };
    await tp.locator('.pk.on [data-k="clr"]').tap().catch(() => {});
    await tp.waitForTimeout(200);
    for (const d of digits) {
      await tp.locator('.pk.on [data-k="' + d + '"]').tap().catch(() => {});
      await tp.waitForTimeout(130);
    }
    return { value: await el.inputValue() };
  }

  await tp.goto('http://localhost:3000/pos/my-day', { waitUntil: 'domcontentloaded' });
  await tp.waitForTimeout(1800);
  const rt = await padType('input[placeholder="HH:MM"]', '0954');
  check(rt.value === '09:54', 'a time typed ON THE PAD arrives whole — 0954 → 09:54',
        rt.err || 'the box reads "' + rt.value + '" — the pad refused a digit the mask had already earned');

  await tp.goto('http://localhost:3000/pos/customer-lookup', { waitUntil: 'domcontentloaded' });
  await tp.waitForTimeout(1800);
  // Its own button, the same one section C uses — the panel is x-show, so the field is in
  // the DOM either way and a probe that skips this "finds" a box no cashier can reach.
  const topener = tp.locator('[data-i18n="customer.add_new_crack"]').first();
  if (await topener.count()) { await topener.tap().catch(async () => { await topener.click(); }); await tp.waitForTimeout(800); }
  const DSEL = 'input[data-i18n-placeholder="common.date_placeholder"]:visible';
  const rd = await padType(DSEL, '03092000');
  check(rd.value === '03.09.2000', 'a birthdate typed ON THE PAD arrives whole — 03092000 → 03.09.2000',
        rd.err || 'the box reads "' + rd.value + '" — a date that cannot be finished is an age gate that cannot be used');

  // And the ceiling still holds: a stuck finger must not write a ninth digit.
  const rx = await padType(DSEL, '030920001111');
  check(rx.value === '03.09.2000', 'and it still stops at eight digits, however long the finger rests',
        rx.err || 'the box reads "' + rx.value + '"');
  await tctx.close();

  // ── J · WHAT CLAMPING CANNOT CATCH, THE BOX SAYS OUT LOUD ────────────────────────────
  // 31.02.2000 is two halves that are each legal, so no keystroke rule can stop it. The
  // parser has always refused it — silently, which is the problem: the model went empty
  // while the screen showed a date, and Save stayed green. LESSON #13 on an age record.
  //
  // "Is it rendered" is not the question. LESSON #12: it has to be inside the rectangle
  // the person is looking at, and the only thing that answers that is
  // getBoundingClientRect() against innerHeight — a refusal has already been shipped in
  // this repo at y=1372 in a 1050px viewport with isVisible() returning true throughout.
  console.log('\n── J · a date that is not a date says so, where the box is ──');
  await p.goto('http://localhost:3000/pos/customer-lookup', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1800);
  const jopen = p.locator('[data-i18n="customer.add_new_crack"]').first();
  if (await jopen.count()) { await jopen.click(); await p.waitForTimeout(700); }
  const jbox = p.locator('input[data-i18n-placeholder="common.date_placeholder"]:visible').first();
  if (!(await jbox.count())) {
    check(false, 'the sign-up date box is on the screen');
  } else {
    await jbox.click({ force: true });
    await jbox.fill(''); await jbox.type('31022000', { delay: 40 });
    await p.waitForTimeout(400);
    const r = await jbox.evaluate((el) => {
      const hint = el.parentElement && el.parentElement.querySelector('[data-bad-hint]');
      const hr = hint && !hint.hidden ? hint.getBoundingClientRect() : null;
      const fr = el.getBoundingClientRect();
      return {
        shown: el.value,
        red: el.classList.contains('pos-bad'),
        // Structural, not positional: if the warning is above the field then the pad — which
        // already guarantees the field's BOTTOM is clear — cannot reach it, on any screen at
        // any scroll position. The timing fix this replaces could not be proved either way.
        hintAboveField: !!(hr && hr.bottom <= fr.top + 1),
        hintOnScreen: !!(hr && hr.height > 0 && hr.top >= 0 && hr.bottom <= window.innerHeight),
        hintY: hr ? Math.round(hr.top) : null,
        viewport: window.innerHeight,
        text: hint ? hint.textContent.trim().slice(0, 40) : null,
      };
    });
    check(r.shown === '31.02.2000', '31.02.2000 can still be TYPED — no keystroke rule can catch it',
          'the box shows "' + r.shown + '"');
    check(r.red, 'and the box turns red', 'the box carries no .pos-bad class — it looks like any other');
    check(r.hintAboveField,
          'and the warning sits ABOVE the box, where a keypad can never slice it',
          'the hint is below the field — on a tablet the pad covers the bottom of the screen,'
          + ' and this is the position Layla found sliced in half twice');
    check(r.hintOnScreen,
          'and it says why, inside the viewport the person is looking at',
          r.hintY === null ? 'no hint element is showing at all'
            : `the hint sits at y=${r.hintY} in a ${r.viewport}px viewport — rendered, and not on the screen`);

    // And it goes away again. A warning that sticks after the fix is a warning nobody reads.
    await jbox.fill(''); await jbox.type('03092000', { delay: 40 });
    await p.waitForTimeout(400);
    const clean = await jbox.evaluate((el) => {
      const hint = el.parentElement && el.parentElement.querySelector('[data-bad-hint]');
      return { red: el.classList.contains('pos-bad'), hint: !!(hint && !hint.hidden) };
    });
    check(!clean.red && !clean.hint, 'and both clear the moment the date is a real one',
          'red=' + clean.red + ' hint=' + clean.hint);
  }

  // ── K · A DATE THAT IS ON FILE HAS TO APPEAR IN THE BOX ──────────────────────────────
  // The whole class of check this file did not have. Every other section TYPES INTO a
  // box; not one ever loaded a stored value OUT of the model and looked at the screen.
  //
  // 2026-09-04, Felix opened a member whose birthday IS on file (2000-02-02, confirmed in
  // the database) and the Date of birth box was EMPTY. Not lost — the record was perfect.
  // The x-effect that paints a stored value into the box had thrown
  // `window.posBirthdateISO is not a function` during Alpine's first pass, because
  // pos-keypad.js was DEFERRED BELOW alpine.min.js. An Alpine effect that throws on its
  // first run never registers its dependencies and therefore never runs again — dead
  // silently and permanently, for all five date fields and both time fields, from the day
  // each shipped. Four errors in the console at load; nothing on any screen.
  //
  // So this section asserts the load path AND the console, because the console was
  // shouting the answer the whole time and no proof was listening.
  console.log('\n── K · a birthdate on file appears in the box ──');
  const boot = [];
  const onErr = (e) => boot.push(String(e.message || e).slice(0, 140));
  p.on('pageerror', onErr);
  await p.goto('http://localhost:3000/pos/customer-lookup', { waitUntil: 'load' });
  await p.waitForTimeout(2200);
  p.off('pageerror', onErr);
  const helperErrs = boot.filter(m => /window\.pos[A-Za-z]* is not a function/.test(m));
  check(helperErrs.length === 0,
        'the page loads with no "window.pos… is not a function"',
        helperErrs.join(' · ') + '  — an x-effect that throws on its first pass never runs again;'
        + ' pos-keypad.js must be BEFORE alpine.min.js');

  const probe = await p.evaluate(async () => {
    const handle = 'ZZPROBE' + Date.now().toString().slice(-6);
    try {
      const r = await API.post('/api/v1/customers',
        { handle: handle, birthdate: '2000-02-02', age_confirmed: true });
      return { id: r.id, handle: r.handle };
    } catch (e) { return { err: String(e && e.message || e) }; }
  });
  if (probe.err) {
    check(false, 'a probe member with a birthdate could be created', probe.err);
  } else {
    const painted = await p.evaluate(async (id) => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      d.customer = { id: id };
      await d.editCustomer();
      await new Promise(r => setTimeout(r, 900));
      const box = [...document.querySelectorAll('input[data-keypad="date"]')]
        .find(e => e.closest('[x-show="showEditForm"]'));
      return { model: d.editForm.birthdate, box: box ? box.value : null };
    }, probe.id);
    check(painted.model === '2000-02-02', 'the edit form loads the stored birthdate',
          'editForm.birthdate is ' + JSON.stringify(painted.model) + ' — the API or the loader, not the box');
    check(painted.box === '02.02.2000',
          'and the BOX SHOWS 02.02.2000 — Swiss order, on the screen',
          'the box reads ' + JSON.stringify(painted.box)
          + ' while the record holds ' + JSON.stringify(painted.model)
          + '  — a birthdate on file that reads as blank is one a cashier will re-ask for');
    // Leave nothing behind. This runs against the dev database, but a probe row that
    // survives is a row somebody can trip over.
    await p.evaluate(async (id) => { try { await API.delete('/api/v1/customers/' + id); } catch (e) {} }, probe.id);
  }

  // Same class of check on the clock: My Day fills Start time from your login.
  await p.goto('http://localhost:3000/pos/my-day', { waitUntil: 'load' });
  await p.waitForTimeout(2000);
  const clock = await p.evaluate(async () => {
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.form.start_time = '07:45';
    await new Promise(r => setTimeout(r, 500));
    const box = document.querySelector('input[placeholder="HH:MM"]');
    return { model: d.form.start_time, box: box ? box.value : null };
  });
  check(clock.box === '07:45', 'a time set in the model appears in the time box too',
        'the box reads ' + JSON.stringify(clock.box) + ' while the model holds '
        + JSON.stringify(clock.model) + ' — the same dead-effect shape, on the clock');

  // ── L · AND A BAD DATE CANNOT BE SAVED ───────────────────────────────────────────────
  // Felix, an hour after the red box shipped: "can be saved with invalid date — so the
  // save should be greyed out IMHO." He is right, and painting alone could never do it: a
  // CSS class on an input is invisible to Alpine, so the Save button had no way to know.
  // The record saved and the birthdate silently became NULL — the one outcome nobody can
  // spot afterwards, and exactly what happened to member k2 this morning.
  //
  // So markBad() returns its verdict, the template stores it in a reactive flag, and the
  // button binds :disabled to it. This asserts the BUTTON, not the flag — a check that
  // reads the flag would pass on a binding nobody wired up.
  console.log('\n── L · a date that is not a date cannot be saved ──');
  await p.goto('http://localhost:3000/pos/customer-lookup', { waitUntil: 'load' });
  await p.waitForTimeout(2000);
  const lopen = p.locator('[data-i18n="customer.add_new_crack"]').first();
  if (await lopen.count()) { await lopen.click(); await p.waitForTimeout(700); }
  const lbox = p.locator('input[data-i18n-placeholder="common.date_placeholder"]:visible').first();
  const lbtn = p.locator('button:has-text("Create"), button[data-i18n*="create"]').first();
  if (!(await lbox.count())) {
    check(false, 'the sign-up date box is on the screen');
  } else {
    // Tick 18+ first, so the ONLY thing standing between this form and a save is the date.
    await p.evaluate(() => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      if (d.newCustomer) d.newCustomer.age_confirmed = true;
    });
    await lbox.click({ force: true });
    await lbox.fill(''); await lbox.type('31022000', { delay: 40 });
    await p.waitForTimeout(400);
    const bad = await p.evaluate(() => {
      const btns = [...document.querySelectorAll('button')]
        .filter(b => b.offsetParent !== null && /create|sign ?up|speichern|erstellen/i.test(b.textContent));
      const b = btns[0];
      return b ? { text: b.textContent.trim().slice(0, 30), disabled: b.disabled,
                   opacity: getComputedStyle(b).opacity } : null;
    });
    check(bad && bad.disabled === true,
          'with 31.02.2000 in the box, the create button is DISABLED',
          bad ? `"${bad.text}" is enabled — the record would save and the birthdate would become NULL`
              : 'no create button found — a check that cannot find its subject always passes');
    check(bad && bad.opacity !== '1', 'and it is visibly greyed, not just dead',
          bad ? 'opacity is ' + bad.opacity : '');

    // And it lets go again.
    await lbox.fill(''); await lbox.type('03092000', { delay: 40 });
    await p.waitForTimeout(400);
    const good = await p.evaluate(() => {
      const b = [...document.querySelectorAll('button')]
        .filter(x => x.offsetParent !== null && /create|sign ?up|speichern|erstellen/i.test(x.textContent))[0];
      return b ? b.disabled : null;
    });
    check(good === false, 'and a real birthdate turns it back on',
          'the button is still disabled with 03.09.2000 in the box — a gate that never opens is a broken form');
  }

  console.log('\n==========================================');
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
