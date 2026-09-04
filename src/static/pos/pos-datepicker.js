/* ═══════════════════════════════════════════════════════════════════════════
   pos-datepicker.js — the month grid Banco draws itself.

   WHY THIS EXISTS. `pos-keypad.js` already killed `<input type="date">` on the
   five fields a cashier TYPES a date into, because a native date widget takes
   its format from the BROWSER'S UI locale and nothing on the page can change
   it (measured 2026-09-03: four inputs, four `lang` values, two browser
   contexts, eight identical `mm/dd/yyyy` boxes). Its own comment then said, in
   as many words, that standing rule 9 means grepping for the siblings.

   Nobody did. Layla, 2026-09-04 17:21, on Transaction History — the screen a
   cashier opens with a customer standing there asking for a receipt:

       "the same screen prints `Showing 04.09.2026` one line under a filter
        that says `09/04/2026`"

   Six survivors: Transactions From/To, Product Sales From/To, Audit From/To.
   A mask alone would have fixed the FORMAT and left the other half of the job
   undone: a filter is not a birthdate. Nobody types their way to "last
   Tuesday" — you look at a month and point at a day. Angel's call, same night:
   "mask plus the month grid".

   SO THE TWO HALVES ARE DELIBERATE, and each one covers the other's blind
   spot:
     · the MASK (pos-keypad.js, already proven) makes the box dd.mm.yyyy on
       every device, whatever the browser's locale, whether the digits come
       from Banco's pad or the folio keyboard;
     · this GRID makes the common case a single tap, and it is the only half
       that works for a person who does not know today's date offhand.

   AND IT DRAWS ON EVERY DEVICE, unlike the keypad. That is not an oversight.
   The keypad is touch-only because a laptop already has a keyboard (Angel,
   2026-09-01: "our fixes should only be for the tablet, and not change the
   desktop"). A month grid is not a keyboard substitute — the thing it replaces
   is the browser's OWN picker, which was wrong on the laptop too. Angel's
   Chromium renders that filter `09/04/2026` on the same machine this is
   written on.

   USE: wrap the input, and give it the same date box the age gate uses.

       <div class="pos-datefield">
         <input type="text" data-keypad="date" maxlength="10" inputmode="numeric"
                data-i18n-placeholder="common.date_placeholder" placeholder="dd.mm.yyyy"
                class="input-field" ...>
         <button type="button" class="pos-cal-btn" data-cal aria-label="Pick a date">📅</button>
       </div>

   The button finds its own input (the `[data-keypad=date]` inside the same
   `.pos-datefield`), so there is no id to keep in sync and nothing to forget.
   Months and weekday names come from Intl at the TENANT's locale — the same
   `_cfg('locale')` seam formatDate() uses — so an Italian till reads
   "settembre" without a single new string.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── the locale is the SHOP's, never the browser's ────────────────────────
     This is the whole bug, one layer up. `new Date().toLocaleDateString()` with
     no argument asks the BROWSER what country it is in — which is how
     cleanup.html came to print American dates on a Swiss till, and how the
     native picker got it wrong in the first place. base.html has had the seam
     since the i18n work: _cfg('locale'), tenant default de-CH. Guarded because
     this file is deferred and could in principle land before that inline
     script; a wrong month name is survivable, a TypeError on open is not. */
  function locale() {
    try {
      if (typeof _cfg === 'function') return _cfg('locale') || 'de-CH';
    } catch (e) {}
    return 'de-CH';
  }

  // i18n if it is loaded, English if it is not. Three words; a missing string
  // must never be the reason a cashier cannot close this thing.
  function say(key, fallback) {
    try {
      if (typeof window.t === 'function') {
        var s = window.t(key);
        if (s && s !== key) return s;
      }
    } catch (e) {}
    return fallback;
  }

  /* ── MONDAY IS THE FIRST DAY OF THE WEEK HERE ─────────────────────────────
     Not a preference — a Swiss calendar starts on Monday, and a grid that puts
     Sunday first is read wrong at a glance by everyone who will ever use this
     till. Intl gives us the NAMES in the tenant's language; the ORDER is ours.
     (Intl.Locale.weekInfo would answer this properly and is not in Chromium 1xx
     on the shop's tablet — checked before hardcoding.) */
  function weekdayNames() {
    var f = new Intl.DateTimeFormat(locale(), { weekday: 'short' });
    var out = [];
    // 2026-01-05 is a Monday. Any Monday would do; a literal beats arithmetic.
    for (var i = 0; i < 7; i++) {
      out.push(f.format(new Date(Date.UTC(2026, 0, 5 + i))));
    }
    return out;
  }

  function monthTitle(y, m) {
    return new Intl.DateTimeFormat(locale(), { month: 'long', year: 'numeric' })
      .format(new Date(Date.UTC(y, m, 1)));
  }

  // yyyy-mm-dd for a LOCAL calendar day. Never toISOString() — that converts to
  // UTC first, so on a CET evening "today" comes back as tomorrow, and on a
  // summer morning the day before. A date filter that is silently off by one
  // day is exactly the class of bug this whole file exists to stop.
  function isoOf(y, m, d) {
    return y + '-' + ('0' + (m + 1)).slice(-2) + '-' + ('0' + d).slice(-2);
  }
  function todayISO() {
    var n = new Date();
    return isoOf(n.getFullYear(), n.getMonth(), n.getDate());
  }

  /* `.pos-datefield` and `.pos-cal-btn` are NOT here — they are in base.html's <style>.
     They are the only two classes a TEMPLATE writes, and prove-classes-exist.js censuses
     the markup against the stylesheets: a class injected from JavaScript is invisible to
     it and gets reported as dead. Everything below is named only by this file. */
  var CSS = ''
    /* The popover. z-index 95: above the keypad (60) and the feedback bubble
       (70), below the leave guard (9999) — losing half a counted drawer to a
       calendar would be a poor trade. */
    + '.pos-cal{position:fixed;display:none;z-index:95;width:20.5rem;max-width:calc(100vw - 1rem);'
    + 'background:#fff;border:1px solid #cbd5e1;border-radius:.75rem;padding:.6rem;'
    + 'box-shadow:0 18px 44px rgba(15,23,42,.28);font-family:inherit;'
    + '-webkit-user-select:none;user-select:none}'
    + '.pos-cal.on{display:block}'
    + '.pos-cal-head{display:flex;align-items:center;gap:.25rem;margin-bottom:.5rem}'
    + '.pos-cal-title{flex:1 1 auto;text-align:center;font-weight:700;color:#0f172a;'
    + 'font-size:1rem;text-transform:capitalize}'
    + '.pos-cal-nav{width:2.2rem;height:2.2rem;border:1px solid #cbd5e1;background:#f8fafc;'
    + 'border-radius:.5rem;color:#334155;font:700 1rem/1 inherit;cursor:pointer;padding:0;'
    + 'touch-action:manipulation}'
    + '.pos-cal-nav:active{background:#c7d2fe}'
    + '.pos-cal-wk{display:grid;grid-template-columns:repeat(7,1fr);gap:2px;margin-bottom:2px}'
    + '.pos-cal-wk span{text-align:center;font-size:.7rem;font-weight:700;color:#94a3b8;'
    + 'text-transform:uppercase;padding:.15rem 0}'
    + '.pos-cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}'
    /* 44px minimum on the day cells. Layla is tapping this with a thumb, next
       to a customer, and a 32px cell is how you pick the 3rd when you meant
       the 4th. */
    + '.pos-cal-d{height:2.75rem;min-width:0;border:0;border-radius:.45rem;background:#fff;'
    + 'font:600 .95rem/1 inherit;color:#0f172a;cursor:pointer;padding:0;'
    + '-webkit-tap-highlight-color:transparent;touch-action:manipulation}'
    + '.pos-cal-d:hover{background:#eef2ff}'
    + '.pos-cal-d:active{background:#c7d2fe}'
    + '.pos-cal-d.oth{color:#cbd5e1}'
    + '.pos-cal-d.today{box-shadow:inset 0 0 0 2px #6366f1;color:#4338ca}'
    + '.pos-cal-d.sel{background:#4f46e5;color:#fff}'
    + '.pos-cal-d.sel:hover{background:#4338ca}'
    + '.pos-cal-foot{display:flex;gap:.4rem;margin-top:.55rem}'
    + '.pos-cal-f{flex:1 1 0;height:2.6rem;border:1px solid #cbd5e1;background:#f8fafc;'
    + 'border-radius:.5rem;font:600 .9rem/1 inherit;color:#334155;cursor:pointer;padding:0;'
    + 'touch-action:manipulation}'
    + '.pos-cal-f:active{background:#c7d2fe}'
    + '.pos-cal-f.prim{background:#4f46e5;border-color:#4f46e5;color:#fff}';

  var box = null;          // the popover element
  var field = null;        // the input it is currently editing
  var viewY = 0, viewM = 0;

  function build() {
    var s = document.createElement('style');
    s.textContent = CSS;
    document.head.appendChild(s);

    box = document.createElement('div');
    box.className = 'pos-cal';
    box.setAttribute('role', 'dialog');
    document.body.appendChild(box);

    // ONE delegated handler, because the grid is rebuilt on every month change
    // and per-cell listeners would leak 42 of them a tap.
    //
    // pointerdown, not click, and preventDefault on it: the field behind may be
    // focused with Banco's pad up, and on a touchscreen a `click` only arrives
    // after a 300ms-ish settle during which the pad's own outside-tap handler
    // has already fired and moved the layout under the finger. The keypad file
    // learned this the hard way ("press Create twice") — same lesson, same fix.
    box.addEventListener('pointerdown', function (e) {
      var b = e.target.closest ? e.target.closest('button') : null;
      if (!b) return;
      e.preventDefault();
      e.stopPropagation();
      if (b.dataset.nav !== undefined) { hop(+b.dataset.nav); return; }
      if (b.dataset.iso !== undefined) { pick(b.dataset.iso); return; }
      if (b.dataset.act === 'today')   { pick(todayISO()); return; }
      if (b.dataset.act === 'clear')   { pick(''); return; }
      if (b.dataset.act === 'close')   { close(); return; }
    }, true);
  }

  function hop(months) {
    var d = new Date(Date.UTC(viewY, viewM + months, 1));
    viewY = d.getUTCFullYear();
    viewM = d.getUTCMonth();
    render();
  }

  function render() {
    var sel = (typeof window.posDateToISO === 'function')
            ? window.posDateToISO(field ? field.value : '') : '';
    var today = todayISO();

    var html = '<div class="pos-cal-head">'
      + '<button type="button" class="pos-cal-nav" data-nav="-12" aria-label="-1y">&laquo;</button>'
      + '<button type="button" class="pos-cal-nav" data-nav="-1" aria-label="-1m">&lsaquo;</button>'
      + '<div class="pos-cal-title">' + esc(monthTitle(viewY, viewM)) + '</div>'
      + '<button type="button" class="pos-cal-nav" data-nav="1" aria-label="+1m">&rsaquo;</button>'
      + '<button type="button" class="pos-cal-nav" data-nav="12" aria-label="+1y">&raquo;</button>'
      + '</div><div class="pos-cal-wk">';
    weekdayNames().forEach(function (w) { html += '<span>' + esc(w) + '</span>'; });
    html += '</div><div class="pos-cal-grid">';

    // getDay() is 0=Sunday; (d+6)%7 turns it into 0=Monday, which is the column
    // the 1st of the month belongs in on a Swiss calendar.
    var first = new Date(viewY, viewM, 1);
    var lead = (first.getDay() + 6) % 7;
    var start = new Date(viewY, viewM, 1 - lead);
    // Always 42 cells — six full rows. A grid that is 5 rows in February and 6
    // in March moves the footer buttons out from under the finger between one
    // month and the next, which is the same "element vanishes mid-tap" shape
    // that cost Angel a half-built product on 2026-09-01.
    for (var i = 0; i < 42; i++) {
      var d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
      var iso = isoOf(d.getFullYear(), d.getMonth(), d.getDate());
      var cls = 'pos-cal-d';
      if (d.getMonth() !== viewM) cls += ' oth';
      if (iso === today) cls += ' today';
      if (iso === sel) cls += ' sel';
      html += '<button type="button" class="' + cls + '" data-iso="' + iso + '">'
            + d.getDate() + '</button>';
    }
    html += '</div><div class="pos-cal-foot">'
      + '<button type="button" class="pos-cal-f prim" data-act="today">'
      + esc(say('common.cal_today', 'Today')) + '</button>'
      + '<button type="button" class="pos-cal-f" data-act="clear">'
      + esc(say('common.cal_clear', 'Clear')) + '</button>'
      + '<button type="button" class="pos-cal-f" data-act="close">'
      + esc(say('common.cal_close', 'Close')) + '</button>'
      + '</div>';
    box.innerHTML = html;
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  }

  /* ── PUT IT WHERE THE FIELD IS, AND INSIDE THE RECTANGLE ──────────────────
     LESSON #12, which this repo has now paid for four times: "is it rendered"
     is not the question, "is it inside the rectangle the person is looking at"
     is — and that is getBoundingClientRect() against innerHeight. A calendar
     that opens below a filter bar near the bottom of a tablet screen is a
     calendar with its last two weeks off the glass, and the last two weeks are
     where "today" usually lives. So: below if it fits, above if it does not,
     and clamped horizontally so the right-hand From/To pair never hangs off
     the edge. */
  function place() {
    var r = field.getBoundingClientRect();
    box.style.visibility = 'hidden';
    box.classList.add('on');
    var h = box.offsetHeight, w = box.offsetWidth;
    var gap = 6;
    var top = r.bottom + gap;
    if (top + h > window.innerHeight - 8) {
      var above = r.top - gap - h;
      // If it fits nowhere (a short landscape tablet), pin it to the top of the
      // viewport rather than hanging it off the bottom: a clipped HEAD still
      // shows the days, a clipped foot shows nothing.
      top = (above >= 8) ? above : Math.max(8, window.innerHeight - h - 8);
    }
    var left = Math.min(r.left, window.innerWidth - w - 8);
    box.style.top = Math.round(top) + 'px';
    box.style.left = Math.round(Math.max(8, left)) + 'px';
    box.style.visibility = '';
  }

  function openFor(input) {
    if (!box) build();
    // Banco's own pad and this cannot both own the bottom of the screen. The
    // keypad exports close() for exactly this; calling it explicitly beats
    // relying on its outside-tap handler, which is a side effect in another
    // file and would stop being true the day that handler is rewritten.
    try { if (window.posKeypad && window.posKeypad.close) window.posKeypad.close(); } catch (e) {}
    field = input;
    var iso = (typeof window.posDateToISO === 'function') ? window.posDateToISO(input.value) : '';
    var base = iso || todayISO();
    viewY = +base.slice(0, 4);
    viewM = +base.slice(5, 7) - 1;
    render();
    place();
    box.classList.add('on');
  }

  function close() {
    if (box) box.classList.remove('on');
    field = null;
  }

  /* ── WRITING BACK: THE BOX, THEN THE MODEL, THEN THE SCREEN ───────────────
     LESSON #13 is the shape to avoid here — a value that lands in one of the
     three and not the others. So: set the text the way the mask would have
     written it, fire `input` (every Banco date field's @input handler is what
     converts dd.mm.yyyy into the ISO the model holds), then fire `change`
     (which is what the filter screens reload on — a native picker fired
     `change` on every pick, and these screens were built against that).
     Setting the model directly from here would be faster and would bypass the
     exact code the mask fields are proven on. */
  function pick(iso) {
    if (!field) return;
    var f = field;
    f.value = iso && typeof window.posISOToDate === 'function' ? window.posISOToDate(iso) : '';
    f.dispatchEvent(new Event('input', { bubbles: true }));
    f.dispatchEvent(new Event('change', { bubbles: true }));
    close();
  }

  /* ── the ways in ──────────────────────────────────────────────────────────
     Delegated from the document, so a field inside an x-show panel, a modal, or
     a template that has not rendered yet works the moment it appears — nothing
     to wire per page and nothing to re-wire after Alpine repaints. */
  document.addEventListener('pointerdown', function (e) {
    var btn = e.target.closest ? e.target.closest('[data-cal]') : null;
    if (btn) {
      var wrap = btn.closest('.pos-datefield');
      var input = wrap ? wrap.querySelector('input[data-keypad="date"]') : null;
      if (input) {
        e.preventDefault();     // do not focus the field: that would raise the pad
        e.stopPropagation();
        if (box && box.classList.contains('on') && field === input) close();
        else openFor(input);
      }
      return;
    }
    // A tap anywhere else closes it — but "anywhere else" has to be measured,
    // not assumed. This listener is on the DOCUMENT in the capture phase, so it
    // runs BEFORE the popover's own handler, on every tap, including the taps
    // that land on a day cell. contains() is what tells them apart; without it
    // this would close the calendar a beat before the day it was pointed at
    // could ever be read.
    if (box && box.classList.contains('on') && !box.contains(e.target)) close();
  }, true);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && box && box.classList.contains('on')) close();
  });

  // The popover is position:fixed and the field is not. Scrolling the page
  // would leave the calendar hanging over the middle of nowhere, pointing at a
  // filter that has moved — so it follows, and gives up if the field has left
  // the screen entirely.
  ['scroll', 'resize'].forEach(function (ev) {
    window.addEventListener(ev, function () {
      if (!box || !box.classList.contains('on') || !field) return;
      var r = field.getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) { close(); return; }
      place();
    }, true);
  });

  window.posDatePicker = { open: openFor, close: close };
  console.log('[datepicker] active — listening for [data-cal] inside .pos-datefield');
})();
