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

   USE: put data-keypad="decimal" or data-keypad="text" on an input. That is all.
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
  window.posMoneyOnly = moneyOnly;
  window.posIntOnly   = intOnly;

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
        row(['7','8','9']) + row(['4','5','6']) + row(['1','2','3'])
      + '<div class="pk-row">'
      + key('.', '.') + key('0', '0')
      + '<button class="pk-k pk-del" data-k="del">⌫</button></div>'
      + '<div class="pk-row"><button class="pk-k pk-util" data-k="clr">C</button>'
      + '<button class="pk-k pk-done pk-wide" data-k="done">OK</button></div>';

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
    html += '<div class="pk-row">'
          + '<button class="pk-k pk-util" data-k="mode">' + (symbols ? 'abc' : '123') + '</button>'
          + '<button class="pk-k pk-space" data-k=" ">space</button>'
          + '<button class="pk-k pk-done pk-wide" data-k="done">OK</button></div>';
    abc.innerHTML = html;
  }

  /* ── open / close ─────────────────────────────────────────────────────── */
  function scroller() {
    return document.querySelector('.app-content') || document.scrollingElement || document.body;
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
    var pad = (k === 'decimal' || k === 'numeric') ? num : abc;
    num.classList.toggle('on', pad === num);
    abc.classList.toggle('on', pad === abc);
    console.log('[keypad] open kind=' + k + ' padHeight=' + pad.offsetHeight
              + ' padZ=' + (getComputedStyle(pad).zIndex));
    // LESSON #12 — being in the DOM is not being on the screen. Clear the pad's
    // height out of the scroll area AND put the field the finger is in on screen.
    var sc = scroller();
    sc.style.paddingBottom = (pad.offsetHeight + 24) + 'px';
    setTimeout(function () {
      try { el.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) {}
    }, 60);
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
    if (active) { active.dispatchEvent(new Event('change', { bubbles: true })); }
    active = null;
    if (num) num.classList.remove('on');
    if (abc) abc.classList.remove('on');
    // HOLD THE LAYOUT STILL FOR A MOMENT. Angel, 2026-09-01: "I scroll to the
    // bottom and press Create twice — once to get in focus and a second time to
    // get it to save." Same cause as the OK-navigates bug and I missed it the
    // first time. Reclaiming the pad's reserved space REFLOWS the page, so the
    // button under the finger moves between pointerdown and the click, and the
    // first tap lands on nothing. Give the click time to finish, then tidy up —
    // and only if a pad has not opened again in the meantime.
    var sc = scroller();
    setTimeout(function () { if (!padOpen()) sc.style.paddingBottom = ''; }, 350);
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
  function shutSafely() {
    var swallow = function (e) { e.stopPropagation(); e.preventDefault(); };
    document.addEventListener('click', swallow, true);
    var nav = document.querySelector('.app-bottomnav');
    if (nav) nav.style.pointerEvents = 'none';
    setTimeout(function () {
      document.removeEventListener('click', swallow, true);
      if (nav) nav.style.pointerEvents = '';
    }, 400);
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
    return (el && el.matches && el.matches('input[data-keypad]')) ? el : null;
  }
  document.addEventListener('focusin', function (e) {
    var el = target(e);
    console.log('[keypad] focusin on <' + (e.target.tagName || '?').toLowerCase()
              + '> data-keypad=' + (e.target.getAttribute ? e.target.getAttribute('data-keypad') : 'n/a')
              + ' -> ' + (el ? 'MINE' : 'not mine'));
    if (el) open(el, el.getAttribute('data-keypad'));
    else if (active && e.target !== active) shut();   // focus went somewhere else
  });
  document.addEventListener('click', function (e) {
    var el = target(e);
    if (el) open(el, el.getAttribute('data-keypad'));
  });

  window.posKeypad = { close: shut };
  console.log('[keypad] active — listening for focus on [data-keypad]');
})();
