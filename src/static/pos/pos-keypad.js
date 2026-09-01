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

  // A touchscreen is the right axis HERE — this is a layout decision, which is
  // exactly what posIsTouchDevice() says it is for. (It is NOT a proxy for "is a
  // phone"; misusing it that way is what hid the camera button on this very
  // tablet on 2026-08-22.) Falls back if pos-scanner.js has not loaded.
  var isTouch = (typeof window.posIsTouchDevice === 'function')
              ? window.posIsTouchDevice()
              : ((navigator.maxTouchPoints || 0) > 0);
  // Beacons. Added 2026-09-01 because this script failed SILENTLY on the counter
  // tablet — no error, no pad, nothing in the console to say it had even run.
  // A feature that can switch itself off must say so out loud. Grep '[keypad]'.
  console.log('[keypad] gate: isTouch=' + isTouch
            + ' maxTouchPoints=' + navigator.maxTouchPoints
            + ' posIsTouchDevice=' + (typeof window.posIsTouchDevice));
  if (!isTouch) { console.log('[keypad] STOPPED — not a touch device'); return; }

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
  function shut() {
    active = null;
    if (num) num.classList.remove('on');
    if (abc) abc.classList.remove('on');
    scroller().style.paddingBottom = '';
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
  function priceOk(f, text) {
    var c = caret(f), s = c[0], e = c[1], v = f.value;
    if (s === null) { s = e = v.length; }
    return /^\d*(\.\d{0,2})?$/.test(v.slice(0, s) + text + v.slice(e));
  }

  function press(k) {
    if (!active) return;
    if (k === 'done') { shut(); return; }
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
