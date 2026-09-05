/* ═══════════════════════════════════════════════════════════════════════════
   pos-keypad.js — the keypad Banco draws itself.

   WHY THIS EXISTS. On the counter tablet (ThinkPad X1, Debian 13 + GNOME 48,
   Chromium kiosk) NO browser will raise the system on-screen keyboard. Measured
   2026-09-01 by elimination: GNOME raises it correctly for its own apps and for
   GDM, and refuses for Chromium AND Firefox — including on a blank HTML file
   with three plain inputs and none of our code on it. Ruled out along the way:
   `screen-keyboard-enabled true` (keep it, it is what makes GNOME's half work),
   a session restart, the folio detached, a full system + Chromium update, and
   `--ozone-platform=wayland --enable-wayland-ime --wayland-text-input-version=3`.
   The cashier had to swipe the keyboard up by hand on every single field.

   So we stop asking the operating system. A keypad we draw needs nothing from
   it and behaves the same on Debian, on an iPad, or on whatever hardware turns
   up next — which is the actual requirement, since the shop's tablet is not a
   decision that has been made once and for all.

   ALSO MEASURED, and it killed the obvious fix: on this stack `inputmode` is
   IGNORED and `type` is what picks the keyboard. Adding `inputmode` to the ~290
   inputs that lack it — the plan before this was tested — would have changed
   nothing on the machine the cashier stands at. See WORKLIST ⑳.

   USE: put data-keypad="decimal", "numeric", "date", "time" or "text" on an
   input. That is all. The four digit kinds draw the same number pad and
   differ only in what they will let you type: money, whole numbers, eight
   digits behind a dd.mm.yyyy mask, four behind HH:MM.
        Touch devices only — a laptop with a real keyboard never sees it.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── the policing a box needs once it stops being type="number" ───────────
     Swapping type="number" → type="text" is what makes the caret work at all
     (a number input has no selectionStart, and setSelectionRange throws on
     it) — but the BROWSER'S OWN POLICING LEAVES WITH THE TYPE, and a scanner
     gun is a real keyboard that can fire anything into a focused field. The
     keypad's priceOk() only guards keys pressed on the KEYPAD; these guard
     every other door.

     Defined ABOVE the touch gate on purpose: a laptop never draws a pad and
     still needs the policing. One implementation, used from every template —
     scan.html's proven priceOnly() delegates here rather than keeping a
     second copy of the same regexes. Deliberately NOT handling "12,50" today:
     that is a behaviour change to a field Angel has already signed off, and it
     goes in on its own, with its own assertion. See WORKLIST ⑳. */
  function moneyOnly(v) {
    return String(v == null ? '' : v)
      .replace(/[^0-9.]/g, '')            // letters, spaces, a gun's stray SHIFT
      .replace(/(\..*)\./g, '$1')         // one decimal point, not three
      .replace(/^(\d*\.\d{2}).*$/, '$1')  // two rappen, no more
      .replace(/^(\d{5})\d+/, '$1');      // CHF 99999.99 ceiling, same as the pad
  }
  function intOnly(v) {
    return String(v == null ? '' : v)
      .replace(/[^0-9]/g, '')             // a quantity has no point and no minus
      .replace(/^(\d{5})\d+/, '$1')
      .replace(/^0+(\d)/, '$1');          // no 007 crates
  }
  /* ── SWISS DATES, AND WHY THE NATIVE WIDGET COULD NOT DO IT ─────────────────
     2026-09-03, on the tablet: the 18+ age gate's Date of birth field rendered
     `mm/dd/yyyy`. On a Swiss till. A cashier under a queue types 03.09.2000 and
     records 9 March — an age-gate field in the wrong order is a compliance
     defect, not a cosmetic one.

     MEASURED before fixing, because the obvious answer is wrong: a native
     `<input type="date">` takes its format from the BROWSER'S UI LOCALE, and
     nothing on the page can change it. Screenshotted four inputs — inherited
     `lang="en"`, `lang="de-CH"`, `lang="de"`, `lang="fr-CH"` — in two browser
     contexts, and all eight rendered IDENTICALLY. The `lang` attribute does
     nothing here. Setting Chromium's --lang would fix Angel's tablet and no
     other device; a Swiss till must read dd.mm.yyyy on whatever someone opens
     it with.

     AND the tablet made it worse: this shop's tablet raises no system keyboard
     (that is why this file exists), and `type="date"` carries no data-keypad —
     so the ONE field where a cashier must type a birthdate had no way to type
     at all, only a calendar to spin back forty years. As a text box with
     data-keypad="decimal" it gets Banco's own pad.

     The MODEL still holds ISO `yyyy-mm-dd`, so nothing downstream changes. */
  /* ── AND THE DIGITS THAT CANNOT BE PART OF ANY DATE NEVER GO IN ────────────
     2026-09-04, Felix, having just watched the box accept 33.33.3333 with the
     Save button sitting there fully green: "the year 4 digit allows any number
     — we need to block this, nobody is 99 years old coming into this shop and
     year 3333 is obviously false."

     Worse than he knew: the PARSER already refused it, so the model held '' —
     the birthdate would have saved as NOTHING while the screen showed a date.
     LESSON #13, the stored copy and the screen disagreeing, on an age record.

     So the mask refuses the digit at the door. No day begins 4–9; nothing
     follows a 3 but 0 or 1; no month begins 2–9; nobody was born in year 3xxx.
     A digit that cannot be part of any date simply does not appear, which is
     the same silence the 8-digit ceiling already uses and which Felix accepted
     there. What clamping CANNOT catch — 31.02.2000, two halves that are each
     legal — is what markBad() below paints red. */
  function clampDateDigits(d) {
    var out = '';
    for (var i = 0; i < d.length && out.length < 8; i++) {
      var c = d.charAt(i), n = +c, k = out.length;
      if (k === 0 && n > 3) continue;                            // no day starts 4-9
      if (k === 1 && out.charAt(0) === '3' && n > 1) continue;   // 32..39
      if (k === 1 && out.charAt(0) === '0' && n === 0) continue; // day 00
      if (k === 2 && n > 1) continue;                            // no month starts 2-9
      if (k === 3 && out.charAt(2) === '1' && n > 2) continue;   // month 13..19
      if (k === 3 && out.charAt(2) === '0' && n === 0) continue; // month 00
      if (k === 4 && n !== 1 && n !== 2) continue;               // year 1xxx or 2xxx
      out += c;
    }
    return out;
  }

  function dateMask(v) {
    var s = String(v == null ? '' : v);
    // A pasted ISO date is a real thing a person does (copied out of a record).
    // Catch it BEFORE stripping punctuation, or 1990-12-31 masks to "19.90.1231".
    var iso = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (iso) return iso[3] + '.' + iso[2] + '.' + iso[1];
    var d = clampDateDigits(s.replace(/[^0-9]/g, '')).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '.' + d.slice(2);
    return d.slice(0, 2) + '.' + d.slice(2, 4) + '.' + d.slice(4);
  }
  // dd.mm.yyyy -> yyyy-mm-dd, or '' if it is not a REAL day. The round-trip through
  // Date is what rejects 31.02.1990 and 00.00.0000 — a regex that only counts digits
  // would hand the server a birthdate nobody has, and the age gate would believe it.
  function dateToISO(v) {
    var m = String(v == null ? '' : v).match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
    if (!m) return '';
    var dd = +m[1], mm = +m[2], yy = +m[3];
    if (mm < 1 || mm > 12 || dd < 1 || dd > 31 || yy < 1900 || yy > 2200) return '';
    var d = new Date(Date.UTC(yy, mm - 1, dd));
    if (d.getUTCFullYear() !== yy || d.getUTCMonth() !== mm - 1 || d.getUTCDate() !== dd) return '';
    return m[3] + '-' + m[2] + '-' + m[1];
  }
  function isoToDate(v) {
    var m = String(v == null ? '' : v).match(/^(\d{4})-(\d{2})-(\d{2})/);
    return m ? (m[3] + '.' + m[2] + '.' + m[1]) : '';
  }

  /* ── AND THE SAME THING WITH THE CLOCK, ONE DAY LATER ──────────────────────
     2026-09-04, Felix on the tablet: My Day's "Close out my day" showed Start
     time `09:54 AM` and Finish time `--:-- --`. Switzerland runs a 24-hour
     clock; a shift record that says AM is the wrong document.

     Identical mechanism to the dates above, and I did not go looking for it
     when I fixed those — standing rule 9 says one bad `type="date"` means grep
     for its siblings, and `type="time"` is the sibling. A native time widget
     takes its format from the BROWSER'S UI LOCALE and nothing on the page can
     change it. Banco's OWN clock was already correct: formatTime() runs on the
     tenant regime's locale (a CH tenant -> de-CH), which is why the top bar
     read 10:11 in the very same screenshot. Only the two native widgets
     disagreed, and they are the two a person types into.

     AND NO PROOF OF MINE COULD HAVE FOUND IT. Headless Chromium renders
     type="time" as 24-hour in en-US, de-CH and fr-CH alike — measured, three
     browser contexts, one screenshot, all identical. The harness is blind to
     this by construction (LESSON #6), so the assertion that guards it is the
     ABSENCE of the native widget, exactly as it is for dates.

     The MODEL still holds "HH:MM" — the same string the server already gets,
     so nothing downstream changes. */
  function timeMask(v) {
    var d = String(v == null ? '' : v).replace(/[^0-9]/g, '').slice(0, 4);
    if (d.length <= 2) return d;
    return d.slice(0, 2) + ':' + d.slice(2);
  }
  // "HH:MM" -> "HH:MM", or '' if it is not an hour of an actual day. 25:00 and
  // 09:74 are four digits in the right shape and no time at all; a shift that
  // starts at 25:00 is a payroll row nobody can explain.
  function timeValue(v) {
    var m = String(v == null ? '' : v).match(/^(\d{2}):(\d{2})$/);
    if (!m) return '';
    if (+m[1] > 23 || +m[2] > 59) return '';
    return m[1] + ':' + m[2];
  }

  /* ── A BIRTHDATE IS A DATE IN THE PAST, OF SOMEBODY WHO COULD WALK IN ──────
     dateToISO() answers "is this a real day". This answers the question the
     18+ gate is actually asking. 1900..2200 was the old range and 2200 is a
     birth year for nobody; a card issued to a 130-year-old is a typo, not a
     customer. Kept separate from dateToISO on purpose — not every date field
     in Banco is a birthday, and a rule that fits this one would be wrong on a
     delivery date. */
  function birthdateISO(v) {
    var iso = dateToISO(v);
    if (!iso) return '';
    var today = new Date().toISOString().slice(0, 10);
    if (iso > today) return '';                              // nobody is born tomorrow
    if (+iso.slice(0, 4) < new Date().getUTCFullYear() - 120) return '';
    return iso;
  }

  /* ── AND WHEN IT IS STILL WRONG, THE BOX SAYS SO WHERE THE BOX IS ──────────
     Felix, twice in one morning: "no warning". Clamping stops the impossible
     digit; this catches what gets past it — 31.02.2000 is two halves that are
     each perfectly legal. Only fires once the box is FULL (8 digits, or 4 for
     a time), so nobody is shouted at halfway through typing.

     Plain DOM, deliberately: these five boxes live in five different Alpine
     components, and threading a reactive flag through each is more moving
     parts than a class toggle. It also behaves identically whether the digits
     came from Banco's pad or the folio keyboard, which is exactly the split
     that hid the last bug. */
  // RETURNS the verdict as well as painting it. 2026-09-04, Felix, an hour after the
  // red box shipped: "can be saved with invalid date — so the save should be greyed out
  // IMHO." He is right, and painting alone could never do that: a class on an element is
  // invisible to Alpine, so the Save button had no way to know. The caller stores what
  // comes back in a reactive flag and binds :disabled to it — the paint says WHY, the
  // flag stops the press.
  function markBad(el, ok, need) {
    if (!el) return false;
    var digits = String(el.value == null ? '' : el.value).replace(/[^0-9]/g, '').length;
    var bad = !ok && digits >= (need || 8);
    el.classList.toggle('pos-bad', bad);
    // Look one level further out than the box's own parent. A date field wrapped in
    // `.pos-datefield` (the calendar button needs a positioning context — see
    // pos-datepicker.js) has a parent that contains the input and nothing else, so a
    // hint written as its SIBLING in the original markup would silently stop being
    // found and the red warning would never appear. Nothing depends on that today;
    // the whole point is that adding a hint to a date box must not be a trap.
    var scope = el.parentElement;
    if (scope && scope.classList.contains('pos-datefield') && scope.parentElement) {
      scope = scope.parentElement;
    }
    var hint = scope && scope.querySelector('[data-bad-hint]');
    if (hint) hint.hidden = !bad;

    /* AND IF THAT JUST MADE THE FIELD TALLER, CHECK IT STILL FITS. Layla, 2026-09-04,
       second run: the warning was STILL sliced by the top of the pad on the tablet, on a
       build where I had "fixed" exactly that.

       revealBottom() was right and useless. ensureAbovePad() runs 140ms and 480ms after the
       pad OPENS — and the hint does not exist then. It appears seconds later, when the
       fourth digit makes the value invalid, and nothing re-measured. My own check passed
       because that page happened to be scrolled so the hint fitted anyway: the assertion
       was true and proved nothing, which is the fault I have written up five times this
       week and just committed again.

       The moment the content grows IS the moment to re-check. */
    if (bad && hint && active === el && padOpen()) {
      var pad = (kind === 'decimal' || kind === 'numeric' || kind === 'date' || kind === 'time') ? num : abc;
      if (pad) setTimeout(function () { ensureAbovePad(el, pad); }, 60);
    }
    return bad;
  }

  window.posMoneyOnly = moneyOnly;
  window.posIntOnly   = intOnly;
  window.posDateMask  = dateMask;
  window.posDateToISO = dateToISO;
  window.posISOToDate = isoToDate;
  window.posBirthdateISO = birthdateISO;
  window.posMarkBad = markBad;
  window.posTimeMask  = timeMask;
  window.posTimeValue = timeValue;

  // A touchscreen is the right axis HERE — this is a layout decision, which is
  // exactly what posIsTouchDevice() says it is for. (It is NOT a proxy for "is a
  // phone"; misusing it that way is what hid the camera button on this very
  // tablet on 2026-08-22.) Falls back if pos-scanner.js has not loaded.
  var isTouch = (typeof window.posIsTouchDevice === 'function')
              ? window.posIsTouchDevice()
              : ((navigator.maxTouchPoints || 0) > 0);

  // A PHONE IS NOT THE PROBLEM WE ARE SOLVING. Angel, 2026-09-01, after running
  // the sheet on his own phone: "the mobile phone keypad should be left alone and
  // native — they generally work fine. If we put ours in then we need to maintain
  // it. Our fixes should only be for the tablet, and not change the desktop or
  // the mobile versions."
  //
  // He is right, and the measurements agree: on a phone in portrait our letter
  // keys are 28px wide — under half a fingertip — and in landscape the pad eats
  // 91% of the screen. iOS and Android raise a perfectly good keyboard on their
  // own; the Debian tablet is the machine that does not, and it is the only one
  // this exists for. Every OS job we take over is a job we maintain forever.
  //
  // The axis is the OS, not the glass — the same distinction posIsMobileOS() was
  // written for on 2026-08-22, when treating any touchscreen as a phone hid the
  // camera button on this very tablet.
  var isPhone = (typeof window.posIsMobileOS === 'function')
              ? window.posIsMobileOS()
              : /Mobi|Android|iPhone|iPod/i.test(navigator.userAgent || '');
  // Beacons. Added 2026-09-01 because this script failed SILENTLY on the counter
  // tablet — no error, no pad, nothing in the console to say it had even run.
  // A feature that can switch itself off must say so out loud. Grep '[keypad]'.
  console.log('[keypad] gate: isTouch=' + isTouch + ' isPhone=' + isPhone
            + ' maxTouchPoints=' + navigator.maxTouchPoints
            + ' posIsTouchDevice=' + (typeof window.posIsTouchDevice));
  if (!isTouch) { console.log('[keypad] STOPPED — not a touch device'); return; }
  if (isPhone)  { console.log('[keypad] STOPPED — phone: its own keyboard is better'); return; }

  var CSS = ''
    + '.pk{position:fixed;left:0;right:0;bottom:0;display:none;background:#e5e7eb;'
    + 'border-top:1px solid #cbd5e1;padding:.5rem;'
    + 'padding-bottom:calc(.5rem + env(safe-area-inset-bottom));'
    + 'box-shadow:0 -4px 16px rgba(0,0,0,.12);z-index:60;'
    + '-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}'
    + '.pk.on{display:block}'
    + '.pk-row{display:flex;gap:.4rem;margin-bottom:.4rem}'
    + '.pk-row:last-child{margin-bottom:0}'
    + '.pk-k{flex:1 1 0;min-width:0;height:54px;font:600 1.25rem/1 inherit;'
    + 'border:1px solid #9ca3af;background:#fff;border-radius:.5rem;color:#111827;'
    + '-webkit-tap-highlight-color:transparent;touch-action:manipulation;cursor:pointer;'
    + 'padding:0;-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}'
    + '.pk-k:active{background:#c7d2fe}'
    + '.pk-wide{flex:2 1 0}.pk-space{flex:5 1 0}'
    // OK lives at the TOP now — Angel's idea, step C4, and it beats every guard
    // we wrote for the old position: "if the number pad had the OK at the top
    // right then you would not have the bottom line problem." The OK key used to
    // sit directly over the app's bottom nav (measured: OK centre y=761, nav
    // 747-800 at 1280x800), so a finger held a beat too long landed on Customers.
    // Moving it removes the overlap instead of racing it.
    + '.pk-top{display:flex;gap:.4rem;margin-bottom:.5rem;align-items:center}'
    + '.pk-top .pk-k{height:44px}'
    + '.pk-gap{flex:1 1 0}'
    + '.pk-util{background:#d1d5db;font-size:1rem}'
    + '.pk-del{background:#fee2e2;color:#b91c1c}'
    + '.pk-done{background:#4f46e5;color:#fff;border-color:#4f46e5;font-size:1rem}'
    + '.pk-lock{background:#4f46e5;color:#fff;border-color:#4f46e5}'
    + '#pk-num .pk-k{height:62px;font-size:1.5rem;font-weight:700}'
    + '#pk-num .pk-done,#pk-num .pk-util{font-size:1.05rem}';

  var LETTERS = [
    ['q','w','e','r','t','z','u','i','o','p','ü'],
    ['a','s','d','f','g','h','j','k','l','ö','ä'],
    ['y','x','c','v','b','n','m','-','&']
  ];
  var SYMBOLS = [
    ['1','2','3','4','5','6','7','8','9','0'],
    ['/','(',')','%','+','.',',',"'",'"','!'],
    ['#','*','@','§','?',':',';','_','&']
  ];

  var num = null, abc = null, active = null, kind = null;
  var shift = false, caps = false, symbols = false, shiftAt = 0;

  function esc(c) {
    return c.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  }
  function up() { return (shift || caps) && !symbols; }

  function build() {
    var s = document.createElement('style');
    s.textContent = CSS;
    document.head.appendChild(s);

    num = document.createElement('div');
    num.className = 'pk'; num.id = 'pk-num';
    num.innerHTML =
        '<div class="pk-top"><button class="pk-k pk-util" data-k="clr">C</button>'
      + '<span class="pk-gap"></span>'
      + '<button class="pk-k pk-done pk-wide" data-k="done">OK</button></div>'
      + row(['7','8','9']) + row(['4','5','6']) + row(['1','2','3'])
      + '<div class="pk-row">'
      + key('.', '.') + key('0', '0')
      + '<button class="pk-k pk-del" data-k="del">⌫</button></div>';

    abc = document.createElement('div');
    abc.className = 'pk'; abc.id = 'pk-abc';

    document.body.appendChild(num);
    document.body.appendChild(abc);
    [num, abc].forEach(wire);
    drawLetters();
  }
  function key(k, label) { return '<button class="pk-k" data-k="' + esc(k) + '">' + esc(label) + '</button>'; }
  function row(ks) {
    return '<div class="pk-row">' + ks.map(function (k) { return key(k, k); }).join('') + '</div>';
  }

  function drawLetters() {
    var rows = symbols ? SYMBOLS : LETTERS, html = '';
    rows.forEach(function (r, i) {
      html += '<div class="pk-row">';
      if (i === 2 && !symbols) {
        html += '<button class="pk-k pk-util' + (caps ? ' pk-lock' : '') + '" data-k="shift">'
              + (caps ? '⇪' : '⇧') + '</button>';
      }
      r.forEach(function (c) { html += key(c, up() ? c.toUpperCase() : c); });
      if (i === 2) html += '<button class="pk-k pk-del" data-k="del">⌫</button>';
      html += '</div>';
    });
    abc.innerHTML =
        '<div class="pk-top">'
      + '<button class="pk-k pk-util" data-k="mode">' + (symbols ? 'abc' : '123') + '</button>'
      + '<button class="pk-k pk-space" data-k=" ">space</button>'
      + '<button class="pk-k pk-done pk-wide" data-k="done">OK</button></div>'
      + html;
  }

  /* ── open / close ─────────────────────────────────────────────────────── */
  function scroller() {
    return document.querySelector('.app-content') || document.scrollingElement || document.body;
  }

  // THE BOX MIGHT NOT BE ON THE PAGE AT ALL. Angel, step C2, 2026-09-02: the pad
  // still covered the price box in the manager price-fix panel — and that panel
  // lives inside the product-detail MODAL, which is `fixed inset-0 flex
  // items-center` wrapping a `max-h-[90vh] overflow-y-auto` body. So:
  //   · reserving space on .app-content does nothing — the modal is not in it;
  //   · the window cannot scroll — the overlay is fixed;
  //   · scrolling the modal's own body moves the CONTENT, while the modal's
  //     bottom edge stays exactly where it was, under the pad.
  // The only thing that helps is making the overlay itself shorter, so its
  // centring re-centres what is left in the space above the pad.
  var lifted = null;
  function liftFixedOverlay(el, padH) {
    var n = el.parentElement;
    while (n && n !== document.body) {
      var st = getComputedStyle(n);
      if (st.position === 'fixed' && n.getBoundingClientRect().height > window.innerHeight * 0.7) {
        lifted = { el: n, bottom: n.style.bottom, panels: [] };
        n.style.bottom = padH + 'px';
        // AND CAP THE PANEL INSIDE IT. Shrinking the overlay is only half the job:
        // the modal panel is sized `max-h-[92vh]`, which is measured against the
        // VIEWPORT and knows nothing about the pad. Measured on the catalog edit
        // modal, 2026-09-02, tablet in landscape (viewport 1050, pad 354):
        //
        //     overlay   0..696   correctly lifted
        //     panel  -135..831   still 966px tall — 92vh
        //
        // The overlay centres what does not fit, so the overflow is split in two:
        // 135px above y=0, which NOTHING can scroll to because it is off the top
        // of the screen, and 135px under the pad. Angel, on this exact modal:
        // "the screen gets messed up when the keypads pop up", and on the tier
        // rows, "the overlap makes it tough to add a second tier".
        //
        // So re-cap any child that is taller than the space now available. The
        // panel already has overflow-y:auto, so a shorter box scrolls the same
        // content — every field stays reachable and the sticky action strip
        // lands just above the pad instead of across the middle of the form.
        var avail = n.getBoundingClientRect().height;
        for (var i = 0; i < n.children.length; i++) {
          var c = n.children[i];
          if (!c || c.nodeType !== 1) continue;
          if (c.getBoundingClientRect().height > avail - 8) {
            lifted.panels.push({ el: c, maxHeight: c.style.maxHeight });
            c.style.maxHeight = Math.max(160, avail - 16) + 'px';
          }
        }
        console.log('[keypad] lifted a fixed overlay by ' + padH + 'px, capped '
                  + lifted.panels.length + ' panel(s) to ' + Math.max(160, avail - 16) + 'px');
        return;
      }
      n = n.parentElement;
    }
  }
  function dropFixedOverlay() {
    if (!lifted) return;
    lifted.el.style.bottom = lifted.bottom;
    for (var i = 0; i < lifted.panels.length; i++) {
      lifted.panels[i].el.style.maxHeight = lifted.panels[i].maxHeight;
    }
    lifted = null;
  }

  /**
   * The lowest y a field may reach and still be READABLE. Normally the top of the
   * pad — but a modal can pin its own bar to the bottom of its scroll box, and a
   * field scrolled to just above the pad then sits behind THAT instead. On the
   * catalog edit modal the Save/Discontinue/Delete strip is `position: sticky;
   * bottom: 0`, and it measured 368..453 with the focused box at 316..379: the
   * box was above the pad, and its bottom half was still unreadable. LESSON #12 —
   * "is it rendered" is not the question, "is it inside the rectangle the person
   * is looking at" is.
   *
   * A sticky HEADER is not an obstruction here (it computes `bottom: auto`), and
   * a bar the field itself lives inside is not one either.
   */
  function readableBottom(el, padTop) {
    var lowest = padTop;
    var n = el.parentElement;
    while (n && n !== document.body) {
      for (var i = 0; i < n.children.length; i++) {
        var c = n.children[i];
        if (!c || c.nodeType !== 1 || c === el || c.contains(el)) continue;
        var cs = getComputedStyle(c);
        if (cs.position !== 'sticky' && cs.position !== 'fixed') continue;
        if (cs.bottom === 'auto') continue;          // top-pinned header — not in the way
        var b = c.getBoundingClientRect();
        if (b.height < 8 || b.bottom < 8) continue;  // hidden or collapsed
        if (b.top < lowest) lowest = b.top;
      }
      n = n.parentElement;
    }
    return lowest;
  }

  /** The nearest thing that can actually scroll — the modal body, not the page. */
  function scrollerFor(el) {
    var n = el.parentElement;
    while (n && n !== document.body) {
      var st = getComputedStyle(n);
      if (/(auto|scroll)/.test(st.overflowY) && n.scrollHeight > n.clientHeight + 1) return n;
      n = n.parentElement;
    }
    return scroller();
  }
  function open(el, k) {
    if (!num) build();
    // MOVING TO THE NEXT BOX IS ALSO LEAVING THIS ONE. A real keyboard fires
    // `change` on blur, and a tap into the next field IS a blur — so the third
    // door needs the same line shut() has. Angel, 2026-09-02, on the tablet:
    // changed Qty to 5, tapped across to Target total, and price × qty stayed
    // at 1 until he pressed DONE. DONE always worked; this is the other way out.
    if (active && active !== el) {
      active.dispatchEvent(new Event('change', { bubbles: true }));
    }
    active = el; kind = k;
    // Set here, never in the template: if this script fails to load, the field
    // must fall back to behaving exactly as it did before, not to having no
    // keyboard at all. (On an iPad this is also what stops the OS keyboard
    // appearing UNDER our own pad.)
    el.setAttribute('inputmode', 'none');
    var pad = (k === 'decimal' || k === 'numeric' || k === 'date' || k === 'time') ? num : abc;
    num.classList.toggle('on', pad === num);
    abc.classList.toggle('on', pad === abc);
    // THE RED CHAT BUBBLE SITS ON THE PAD. Twice off the tablet: on 2026-09-03 it
    // covered the `n` key of the letter pad, and on 2026-09-04 the `0` key of the
    // number pad — in the CATALOG PRICE editor, which is the worst place on the
    // whole till to lose a digit. Nothing to do with the missing classes I
    // predicted it would be: the feedback button is position:fixed at bottom:104px
    // with z-index:70, and the pad is z-index:60. It was ALWAYS going to sit on
    // top, on every screen, for every field.
    // A person mid-keystroke is not filing feedback. Mark the document while the
    // pad is up and let base.html take the button out of the way.
    document.documentElement.classList.add('pk-open');
    console.log('[keypad] open kind=' + k + ' padHeight=' + pad.offsetHeight
              + ' padZ=' + (getComputedStyle(pad).zIndex));
    // LESSON #12 — being in the DOM is not being on the screen. Clear the pad's
    // height out of the scroll area AND put the field the finger is in on screen.
    dropFixedOverlay();
    liftFixedOverlay(el, pad.offsetHeight);
    var sc = scrollerFor(el);
    // ONE MECHANISM OR THE OTHER, NEVER BOTH. Padding the scroller by the pad's
    // height is how a PAGE makes room for the pad. A modal that we just lifted is
    // already entirely above the pad, so the padding buys nothing there — and it
    // actively breaks the panel, because a `position: sticky; bottom: 0` footer
    // resolves its 0 against the scroller's CONTENT box, not its padding box.
    // Measured on the catalog edit modal, 2026-09-02:
    //
    //     panel padding-box bottom  688
    //     padding-bottom            378   <- added here
    //     sticky strip lands at     688 - 378 - 85 = 225
    //
    // which is the middle of the form. That is the green Save bar lying across
    // the Class/Supplier fields in Angel's screenshots — "the overlap makes it
    // tough to add a second tier", "it works but very clunky". Both fixes were
    // mine; applying them together is what produced the mess.
    if (!lifted) {
      sc.style.paddingBottom = (pad.offsetHeight + 24) + 'px';
    } else if (sc.style.paddingBottom) {
      sc.style.paddingBottom = '';
    }
    setTimeout(function () {
      try { el.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) {}
    }, 60);
    // AND THEN CHECK IT ACTUALLY WORKED. Angel, 2026-09-02, step B4: inside the
    // manager price-fix panel the pad covered the box — "you have to press OK to
    // see what you typed." scrollIntoView() scrolls the NEAREST scrollable
    // ancestor, which in a nested panel is the panel, and moving the field to the
    // middle of a panel that is itself under the pad achieves nothing.
    // So measure, then correct. Being scrolled is not being visible (LESSON #12).
    // The lid just moved, so every list that snaps to a whole row has to be measured
    // again against it — and again after the scroll settles, because the scroll moves
    // the box and therefore how much room is left above the pad.
    setTimeout(function () { ensureAbovePad(el, pad); resnap(); }, 140);
    setTimeout(function () { ensureAbovePad(el, pad); resnap(); }, 480);   // after the smooth scroll settles
  }

  function resnap() { if (window.posRowSnap) window.posRowSnap(); }

  /* THE FIELD IS NOT THE ONLY THING THAT HAS TO BE VISIBLE. Layla, 2026-09-04, typing
     25:25 into Finish time: the box went red exactly as designed and the line under it —
     "That is not a time on the clock." — was sliced in half by the top edge of the pad.
     She asked for the warning to be "pulled up a little higher so it is fully readable".

     The warning was in the right place. What was wrong is that this function measured the
     INPUT's bottom edge and nothing else, so it scrolled the box clear of the pad and left
     the explanation underneath it. LESSON #12 for the fifth time, one notch finer each
     time: it is not "is the field on screen", it is "is everything the field needs to say
     on screen". Any box with a hint beneath it is covered by this, not just the clock. */
  function revealBottom(el) {
    var bottom = el.getBoundingClientRect().bottom;
    var host = el.parentElement;
    var hint = host && host.querySelector('[data-bad-hint]');
    if (hint && !hint.hidden) {
      var hb = hint.getBoundingClientRect();
      if (hb.height > 0 && hb.bottom > bottom) bottom = hb.bottom;
    }
    /* AND A SEARCH BOX'S ANSWER IS PART OF WHAT IT HAS TO SAY. Layla, 2026-09-03:
       typing `cbd` into Find Product showed "Showing 20 of 366 matches" and one and a
       half rows — you had to put the keyboard away to see what you had searched for.
       The sixth turn of LESSON #12, and each one has been the same correction one notch
       finer: the field, then the field's warning, now the field's RESULT. A box whose
       whole purpose is to produce a list below it is not "visible" while the list is
       under the pad.
       ONE row, deliberately, not the list. Twenty rows cannot fit above the keyboard and
       asking for them would scroll the field itself off the top; one whole row is the
       difference between "it found something" and "it found nothing", and the rest is
       what the list's own scrollbar is for — data-row-snap caps it to whole rows against
       the same lid. Opt in with data-reveals="<selector>" on the input. */
    var sel = el.getAttribute('data-reveals');
    if (sel) {
      var box = document.querySelector(sel);
      var wrap = box && box.querySelector('[data-row-snap-rows]');
      // THE FIRST CHILD IS NOT THE FIRST ROW. Alpine's x-for leaves its own <template>
      // in the DOM and inserts the rows after it, so `> *` hands back a zero-height
      // element and this whole check quietly did nothing — measured: need computed as
      // negative, ensureAbovePad returned before it even logged. data-row-snap has
      // filtered on height since it was written; so does this now.
      var row = null, kids = wrap ? wrap.children : [];
      for (var i = 0; i < kids.length && !row; i++) {
        if (kids[i].getBoundingClientRect().height > 0) row = kids[i];
      }
      if (row) {
        var rb = row.getBoundingClientRect();
        if (rb.bottom > bottom) bottom = rb.bottom;
      }
    }
    return bottom;
  }

  /** Is the box — and whatever it needs to say — above the pad? If not, scroll until it is. */
  function ensureAbovePad(el, pad) {
    if (active !== el) return;
    var padTop = readableBottom(el, window.innerHeight - pad.offsetHeight);
    var need = Math.round(revealBottom(el) - (padTop - 12));
    if (need <= 0) return;
    /* AND NEVER SO FAR THAT THE BOX BEING TYPED INTO LEAVES THE TOP OF THE SCREEN.
       Angel's tablet, 2026-09-05 10:23, as pam: the first match for `cbd` is
       "CBD Joint Natural Rebel \"Lemon Skunk\" Pure 1stk" — a name that WRAPS TO TWO
       LINES, which makes that row tall enough that scrolling all of it clear of the
       keyboard would have taken the search box with it. Asking for the answer must not
       cost the question: a cashier typing into a field that has scrolled off the top is
       a worse screen than one whose bottom row is short. Where the row cannot fit, we
       take what headroom there is and the list's own scrollbar carries the rest.

       ⚠️ UNEXERCISED, and said so rather than implied. I could not build a case that makes
       this clamp bind: four-line names at 1440x895 and again at 1440x620 both leave the
       field on screen, because the Find Product card above it runs out of scroll first. So
       it is a rail, not a proven fix — LESSON #4 says a guard you have not watched go red
       is a guess. It stays because it is three lines and obviously correct in the direction
       it acts; if it ever fires on the tablet, that screen is the missing test case. */
    var headroom = Math.round(el.getBoundingClientRect().top - 8);
    if (headroom < 0) headroom = 0;
    if (need > headroom) need = headroom;
    if (need <= 0) return;
    // Walk out from the field and spend the overlap on whatever can absorb it —
    // the panel first, then its parents, then the window.
    var n = el.parentElement;
    while (n && need > 0) {
      var st = getComputedStyle(n);
      var scrolls = /(auto|scroll)/.test(st.overflowY) && n.scrollHeight > n.clientHeight + 1;
      if (scrolls) {
        var room = n.scrollHeight - n.clientHeight - n.scrollTop;
        var take = Math.min(need, room);
        if (take > 0) { n.scrollTop += take; need -= take; }
      }
      n = n.parentElement;
    }
    if (need > 0) { try { window.scrollBy(0, need); } catch (e) {} }
    var after = Math.round(revealBottom(el));
    console.log('[keypad] ensureAbovePad readableBottom=' + Math.round(padTop)
              + ' fieldBottom=' + after + (after <= padTop ? ' ok' : ' STILL COVERED'));
  }
  function padOpen() {
    return !!((num && num.classList.contains('on')) || (abc && abc.classList.contains('on')));
  }

  function shut() {
    // A REAL KEYBOARD FIRES change WHEN THE FIELD IS DONE WITH. Ours has to as
    // well, or every field that finalises on @change silently never finalises.
    // Found 2026-09-02 wiring the cart quantity box on scan.html: it binds
    // :value + @change="setQuantity(...)", so typing 6 on the pad and pressing
    // OK left "6" on the glass and the old quantity in the cart — right on the
    // screen, wrong in the basket, which is LESSON #13's exact shape. Fired on
    // close, not per keystroke: @change means "finished", not "typing".
    var leaving = active;
    if (active) { active.dispatchEvent(new Event('change', { bubbles: true })); }
    active = null;
    if (num) num.classList.remove('on');
    if (abc) abc.classList.remove('on');
    document.documentElement.classList.remove('pk-open');
    // HOLD THE LAYOUT STILL FOR A MOMENT. Angel, 2026-09-01: "I scroll to the
    // bottom and press Create twice — once to get in focus and a second time to
    // get it to save." Same cause as the OK-navigates bug and I missed it the
    // first time. Reclaiming the pad's reserved space REFLOWS the page, so the
    // button under the finger moves between pointerdown and the click, and the
    // first tap lands on nothing. Give the click time to finish, then tidy up —
    // and only if a pad has not opened again in the meantime.
    var sc = leaving ? scrollerFor(leaving) : scroller();
    resnap();                       // the lid is gone — the lists get their full cap back
    setTimeout(function () {
      if (!padOpen()) { sc.style.paddingBottom = ''; dropFixedOverlay(); resnap(); }
    }, 350);
  }

  // ── OK MUST NOT NAVIGATE. Angel, 2026-09-01, mid-retest ─────────────────
  // "I've held the OK a split second too long and guess what, I'm hitting the
  //  Customers button. Everything I was creating is basically gone."
  //
  // OK sits at the bottom of the pad, directly over the app's bottom nav. The
  // key fires on POINTERDOWN, the pad closes immediately, and the finger is then
  // over Customers with nothing in between — so the click that follows the
  // release lands on the nav and the half-built product is gone. A quick tap
  // outruns it; a slightly held one does not. Classic element-vanishes-from-
  // under-the-finger, and the cost is a cashier's work in front of a customer.
  //
  // So closing swallows the one click that follows it. 400ms is long enough for
  // a slow release and far too short to eat a deliberate second tap.
  // MEASURED on the till, 1280x800: the OK key's centre is at y=761 and the app's
  // bottom nav spans 747-800, so document.elementFromPoint under OK returns
  // <a href="/pos/customer-lookup">. The overlap is real and not incidental —
  // both are pinned to the bottom of the screen by design.
  //
  // Two layers, because they fail differently: the swallow stops the click that
  // has ALREADY been generated, and the dead nav means that even a click nobody
  // swallowed lands on something inert. Neither can contradict the other — they
  // are the same 400ms window, and after it both simply stop applying.
  // 2026-09-02, Angel on the till: "about a 3/4 second press is fine, but if you
  // lay the finger for 2 seconds you hit the bottom menu bar and get flipped into
  // Customers or My Day." The 400ms was a GUESS at how long a finger rests, and
  // any guess is wrong for somebody — lengthen it and a deliberate tap on the nav
  // dies for a second instead, which is the same annoyance pointed the other way.
  //
  // So stop timing and follow the gesture. The click we must eat belongs to the
  // press that closed the pad; it ends at that press's pointerup. Anything that
  // starts LATER is a new, deliberate tap and must go straight through, however
  // few milliseconds later it comes. Dead time is now exactly the length of the
  // finger press — 2 seconds or 20 — and zero afterwards.
  function shutSafely() {
    var nav = document.querySelector('.app-bottomnav');
    var done = false;
    var swallow = function (e) { e.stopPropagation(); e.preventDefault(); };
    var release = function () {
      if (done) return;
      done = true;
      document.removeEventListener('click', swallow, true);
      document.removeEventListener('pointerup', onUp, true);
      if (nav) nav.style.pointerEvents = '';
    };
    // The click follows pointerup, but not reliably in the same task — releasing
    // at pointerup+0ms could hand the screen back BEFORE the click arrived, which
    // is worse than the timer it replaced. A short tail closes that race: a human
    // cannot deliberately tap again inside 120ms, so nothing real is ever eaten.
    var onUp = function () { setTimeout(release, 120); };

    document.addEventListener('click', swallow, true);
    document.addEventListener('pointerup', onUp, true);
    if (nav) nav.style.pointerEvents = 'none';
    // Safety net only: a pointerup that never arrives (the finger leaves the
    // digitiser sideways, a cancelled gesture) must not leave the nav dead.
    setTimeout(release, 1500);
    shut();
  }

  /* ── the caret is the truth ───────────────────────────────────────────── */
  function caret(f) {
    try { return [f.selectionStart, f.selectionEnd]; }
    catch (e) { return [f.value.length, f.value.length]; }
  }
  function place(f, pos) { try { f.setSelectionRange(pos, pos); } catch (e) {} }

  // Alpine's x-model listens for `input`. Setting .value alone leaves the box
  // showing a price the model never received — LESSON #13, the stored copy and
  // the screen disagreeing, and the screen is what you believe.
  function commit(f) { f.dispatchEvent(new Event('input', { bubbles: true })); }

  function insert(f, text) {
    var c = caret(f), s = c[0], e = c[1], v = f.value;
    if (s === null) { s = e = v.length; }
    f.value = v.slice(0, s) + text + v.slice(e);
    place(f, s + text.length);
    commit(f);
  }
  function backspace(f) {
    var c = caret(f), s = c[0], e = c[1], v = f.value;
    if (s === null) { s = e = v.length; }
    if (s !== e) { f.value = v.slice(0, s) + v.slice(e); place(f, s); commit(f); return; }
    if (s === 0) return;
    f.value = v.slice(0, s - 1) + v.slice(e);
    place(f, s - 1);
    commit(f);
  }
  // Judge what the box WOULD read, not the key pressed — a digit typed into the
  // middle can otherwise still produce 12.5.0.
  // Angel, same session: "I could type 5555555, which is just crazy. There is
  // nothing that sells for over ten thousand in this shop. It should have
  // stopped me." Five digits before the point — CHF 99999.99 — is far past
  // anything a headshop sells and still refuses a stuck finger. The server keeps
  // its own ceiling; this one only has to stop the fat-finger case at the glass.
  function priceOk(f, text) {
    var c = caret(f), s = c[0], e = c[1], v = f.value;
    if (s === null) { s = e = v.length; }
    return /^\d{0,5}(\.\d{0,2})?$/.test(v.slice(0, s) + text + v.slice(e));
  }

  /* ── A MASKED BOX IS NOT A PRICE, AND priceOk() JUDGED IT AS ONE ───────────
     2026-09-04, Felix on the tablet: "when I use the soft numeric keypad I can
     only type in 3 numbers and the last minute is blocked, but if I press the
     hard keyboard the last digit is entered."

     He is describing priceOk(). It tests the string the box WOULD read against
     /^\d{0,5}(\.\d{0,2})?$/ — the right rule for money and nonsense for a box
     whose own mask puts punctuation in. Typing 0954 into a time box goes
     0 → 09 → "09:5" (the mask inserted the colon) → and the fourth digit is
     judged as "09:54", which has a colon in it, so the pad silently refuses it.

     THE DATE FIELDS HAVE IT WORSE and had it since yesterday: 03.09.2000 dies
     at "03.09" — six digits refused — so a birthdate could NEVER be completed
     on the only input method this tablet has. I proved those fields with
     page.type(), which is the hardware keyboard. Felix passed them with the
     folio attached. Neither of us used the pad that exists BECAUSE the tablet
     raises no keyboard. LESSON #1: the layer I could reach was not the layer
     he stands on.

     So the pad now polices by KIND. Money keeps the money rule; a masked box is
     judged on the only thing that is really bounded about it — how many DIGITS
     it holds, whatever the mask does with them in between. */
  function digitsOk(f, text, max) {
    var c = caret(f), s = c[0], e = c[1], v = f.value;
    if (s === null) { s = e = v.length; }
    return (v.slice(0, s) + text + v.slice(e)).replace(/[^0-9]/g, '').length <= max;
  }

  function press(k) {
    if (!active) return;
    if (k === 'done') { shutSafely(); return; }
    if (k === 'clr')  { active.value = ''; place(active, 0); commit(active); return; }
    if (k === 'del')  { backspace(active); return; }
    if (k === 'mode') { symbols = !symbols; shift = false; drawLetters(); return; }
    if (k === 'shift') {
      var now = Date.now();
      if (!caps && shift && now - shiftAt < 400) { caps = true; shift = false; }
      else if (caps) { caps = false; shift = false; }
      else { shift = true; shiftAt = now; }
      drawLetters();
      return;
    }
    if (kind === 'date' || kind === 'time') {
      if (!/^[0-9]$/.test(k)) return;                   // the mask writes the . and the :
      if (!digitsOk(active, k, kind === 'date' ? 8 : 4)) return;
      insert(active, k);
      return;
    }
    if (kind === 'decimal' || kind === 'numeric') {
      if (k === '.') {
        if (kind === 'numeric') return;                 // whole numbers only
        if (active.value === '') { insert(active, '0.'); return; }
      }
      if (!/^[0-9.]$/.test(k)) return;
      if (!priceOk(active, k)) return;
      insert(active, k);
      return;
    }
    insert(active, up() ? k.toUpperCase() : k);
    if (shift && !caps) { shift = false; drawLetters(); }
  }

  /* ── hold to repeat, and never the browser's own long-press menu ───────── */
  var holdTimer = null, repeatTimer = null;
  function stopHold() { clearTimeout(holdTimer); clearInterval(repeatTimer); holdTimer = repeatTimer = null; }

  function wire(pad) {
    // pointerdown + preventDefault keeps the INPUT focused; without it the field
    // blurs on every tap and the caret is lost, so every key lands at the end.
    pad.addEventListener('pointerdown', function (e) {
      var b = e.target.closest('[data-k]');
      if (!b) return;
      e.preventDefault();
      var k = b.getAttribute('data-k');
      press(k);
      if (k === 'del') {
        stopHold();
        holdTimer = setTimeout(function () {
          repeatTimer = setInterval(function () { press(k); }, 60);
        }, 400);
      }
    });
    pad.addEventListener('pointerup', stopHold);
    pad.addEventListener('pointercancel', stopHold);
    pad.addEventListener('pointerleave', stopHold);
    pad.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  }

  /* ── attachment: one delegated listener, so it works for fields Alpine
        reveals later just as well as for ones present at load ────────────── */
  function target(e) {
    var el = e.target;
    // textarea too — Edit member's "📝 Staff notes" is one, and a box with no
    // keyboard is a box nobody fills in.
    return (el && el.matches && el.matches('input[data-keypad], textarea[data-keypad]')) ? el : null;
  }
  // A PAGE THAT LANDS THE CARET SOMEWHERE IS NOT A PERSON ASKING FOR A KEYBOARD.
  // Screens autofocus their main box so a scan or the first keystroke just lands
  // (Angel: "it makes scanning painless and straight forward"). If that focus
  // opened the pad, every one of those screens would come up with half of itself
  // covered before anyone had touched anything. So the pad waits for a real
  // human gesture; the caret is already in the box either way, which is all a
  // barcode gun needs. Tap the box and the pad comes up exactly as before.
  var userHasActed = false;
  ['pointerdown', 'keydown'].forEach(function (ev) {
    document.addEventListener(ev, function () { userHasActed = true; }, true);
  });

  document.addEventListener('focusin', function (e) {
    var el = target(e);
    console.log('[keypad] focusin on <' + (e.target.tagName || '?').toLowerCase()
              + '> data-keypad=' + (e.target.getAttribute ? e.target.getAttribute('data-keypad') : 'n/a')
              + ' -> ' + (el ? (userHasActed ? 'MINE' : 'MINE, but nobody has touched the page yet') : 'not mine'));
    if (el && userHasActed) open(el, el.getAttribute('data-keypad'));
    else if (active && e.target !== active) shut();   // focus went somewhere else
  });
  document.addEventListener('click', function (e) {
    var el = target(e);
    if (el) open(el, el.getAttribute('data-keypad'));
  });

  document.addEventListener('pointerdown', function (e) {
    if (!active) return;
    var t = e.target;
    if (t && t.closest && (t.closest('.pk') || t.closest('input[data-keypad], textarea[data-keypad]'))) return;
    console.log('[keypad] tap outside — closing');
    shut();
  }, true);

  /* THE ANSWER ARRIVES AFTER THE KEYBOARD DOES. open() checks the field is clear of the
     pad at +140ms and +480ms; the search results come back from the server later than
     that, and land under the pad with nothing left to notice. So the row-snap sweep —
     which already runs on every DOM change — tells the pad to look again. Cheap: with
     nothing covered, ensureAbovePad measures and returns. */
  function recheck() {
    if (!active) return;
    var pad = (kind === 'decimal' || kind === 'numeric' || kind === 'date' || kind === 'time') ? num : abc;
    if (pad) ensureAbovePad(active, pad);
  }

  window.posKeypad = { close: shut, recheck: recheck };
  console.log('[keypad] active — listening for focus on [data-keypad]');
})();
