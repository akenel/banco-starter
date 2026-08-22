#!/usr/bin/env node
/**
 * prove-webcam-button-shows.js — 2026-08-22
 *
 * WHY THIS EXISTS
 * Angel put a USB webcam on the X1 Tablet (Debian + Chromium). It worked in GNOME
 * instantly. In Banco, "✨ Snap & fill" opened a FILE PICKER and the "📷 Webcam"
 * button was nowhere — on the one machine in the shop that had just grown a camera.
 *
 * Cause: pos-scanner.js split the world into phone-or-laptop on `maxTouchPoints`.
 * A Linux tablet is BOTH — a touchscreen AND a desktop browser that ignores the
 * file input's `capture` attribute. So it got the phone branch's attribute (a no-op)
 * and the phone branch's hidden button, and had no live-camera path at all.
 *
 * The axis that matters is the OS, not the glass: only a phone has a native camera
 * app worth handing off to.
 *
 * WHAT THIS PROVES:   the four device shapes resolve posShowWebcam()/posCaptureAttr()
 *                     correctly, including the two that were wrong before.
 * WHAT IT DOES NOT:   that the BUTTON RENDERS. `x-show` is Alpine, in a browser, on a
 *                     screen. Per LESSONS #7 that is a human's job or Playwright's —
 *                     never a script reading a template. Angel verifies on the tablet.
 *
 * GUARD-BREAK: run against git HEAD~ (pre-fix) and cases 1 and 4 MUST go red.
 *   node scripts/prove-webcam-button-shows.js --src <(git show HEAD~1:src/static/pos-scanner.js)
 */
const fs = require('fs'), vm = require('vm'), path = require('path');

const argIdx = process.argv.indexOf('--src');
const SRC = argIdx > -1 ? process.argv[argIdx + 1]
                        : path.join(__dirname, '..', 'src', 'static', 'pos-scanner.js');
const src = fs.readFileSync(SRC, 'utf8');

// name, userAgent, maxTouchPoints, has getUserMedia, expected
const CASES = [
  ['X1 Tablet · Debian · Chromium + USB webcam  ← the one that was broken',
   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/138 Safari/537.36', 10, true,
   { webcam: true, capture: false }],
  ['Android phone — the shop camera, must NOT regress',
   'Mozilla/5.0 (Linux; Android 14; Fairphone) Chrome/138 Mobile Safari/537.36', 5, true,
   { webcam: false, capture: 'environment' }],
  ['ProBook laptop, no touchscreen',
   'Mozilla/5.0 (X11; Linux x86_64) Chrome/138 Safari/537.36', 0, true,
   { webcam: true, capture: false }],
  ['Browser with NO getUserMedia — offer nothing, do not dead-end',
   'Mozilla/5.0 (X11; Linux x86_64) Chrome/138 Safari/537.36', 10, false,
   { webcam: false, capture: false }],
];

function fakeDoc() {
  const set = new Set();
  return {
    _classes: set,
    createElement: () => ({ style: {}, appendChild() {} }),
    body: { appendChild() {} },
    documentElement: {
      classList: {
        add: (c) => set.add(c),
        remove: (c) => set.delete(c),
        contains: (c) => set.has(c),
        toggle: (c, on) => (on ? set.add(c) : set.delete(c)),
      },
    },
  };
}

let fail = 0;
for (const [name, ua, touch, gum, want] of CASES) {
  const ctx = {
    navigator: { userAgent: ua, maxTouchPoints: touch, mediaDevices: gum ? { getUserMedia() {} } : undefined },
    document: fakeDoc(),
  };
  ctx.window = ctx; ctx.globalThis = ctx;
  vm.createContext(ctx);
  try { vm.runInContext(src, ctx); } catch (e) { /* DOM-dependent tail, irrelevant here */ }

  const showFn = ctx.window.posShowWebcam
    || (() => !ctx.window.posIsTouchDevice());               // pre-fix shape, for the guard-break
  const got = { webcam: showFn(), capture: ctx.window.posCaptureAttr() };
  const ok = got.webcam === want.webcam && got.capture === want.capture;
  if (!ok) fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`);
  console.log(`        webcam button ${got.webcam} (want ${want.webcam})` +
              `   capture=${JSON.stringify(got.capture)} (want ${JSON.stringify(want.capture)})`);
}
// ── PART 2: is a camera actually attached? ───────────────────────────────────────
// posShowWebcam() only says the BROWSER can open cameras. The Win 10 tablet has a
// touchscreen, a desktop browser and no camera — it passed part 1 and still must not
// show the button. That is what .banco-has-camera decides.
const CAM_CASES = [
  ['USB webcam attached  ← the X1 with Angel\'s webcam',
   [{ kind: 'videoinput' }, { kind: 'audioinput' }], true],
  ['No camera at all     ← the shop Win 10 tablet',
   [{ kind: 'audioinput' }], false],
  ['enumerateDevices throws — cannot tell, must NOT hide a real camera',
   'throw', true],
  ['enumerateDevices missing entirely (ancient browser)',
   null, true],
];

(async () => {
  for (const [name, devices, want] of CAM_CASES) {
    const md = { getUserMedia() {} };
    if (devices === 'throw') md.enumerateDevices = async () => { throw new Error('nope'); };
    else if (devices !== null) md.enumerateDevices = async () => devices;

    const ctx = {
      navigator: { userAgent: 'Mozilla/5.0 (X11; Linux x86_64) Chrome/138', maxTouchPoints: 10, mediaDevices: md },
      document: fakeDoc(),
    };
    ctx.window = ctx; ctx.globalThis = ctx;
    vm.createContext(ctx);
    try { vm.runInContext(src, ctx); } catch (e) { /* DOM tail */ }

    if (!ctx.window.posRefreshCameraPresence) {
      console.log(`FAIL  ${name}\n        posRefreshCameraPresence missing (pre-fix source?)`);
      fail++; continue;
    }
    await ctx.window.posRefreshCameraPresence();
    const shown = ctx.document.documentElement.classList.contains('banco-has-camera');
    const ok = shown === want;
    if (!ok) fail++;
    console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`);
    console.log(`        button shown ${shown} (want ${want})`);
  }

  const total = CASES.length + CAM_CASES.length;
  console.log(fail ? `\n${fail} FAILED` : `\nall ${total} pass`);
  process.exit(fail ? 1 : 0);
})();
