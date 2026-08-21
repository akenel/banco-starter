// Proves Banco refuses to bind something that is not a product barcode.
//
// Born from the live shop on 2026-08-21: Angel scanned a JaJa Noir packet and Banco bound
// `2024VL099B` — the LOT NUMBER printed beside the real EAN. His gun reads Code-128 as happily
// as EAN-13, and a packet carries several stripes. Nothing said a word, and that row could never
// have scanned again: the next box carries a different lot number.
//
// Measured on the live catalogue before the guard was written: 5,412 of 5,413 bound codes pass
// the GTIN check digit, and the one that doesn't is the row above. The blast radius of this
// guard is exactly the bug it exists to catch.
//
// Creates and deletes ZZPROBE rows; refuses to run off localhost without an explicit opt-in.
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT) &&
    process.env.BANCO_ALLOW_CATALOG_WRITES !== '1') {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates products.`);
  console.error('Set BANCO_ALLOW_CATALOG_WRITES=1 if you really mean it.');
  process.exit(2);
}
// Barcodes must be UNIQUE PER RUN. Banco's delete is a SOFT delete by design (a row that has
// sold cannot leave the books), so a deactivated fixture keeps its barcode and the next run
// collides with it on the unique index. The first cut of this script used fixed codes, passed
// once, and then reported 6 failures on the second run — which for a few minutes looked like
// the guard breaking. Generate a fresh valid GTIN each time instead.
let seq = 0;
function gtin(prefix, length) {
  // The unique part goes at the END. My first version built prefix+timestamp and then sliced
  // from the FRONT, which threw the fast-changing digits away — the 8-digit case produced the
  // literal same code on every run and collided with its own leftovers. It failed about one run
  // in three, which is the worst kind of prover: green often enough to be believed.
  const need = length - 1 - prefix.length;
  if (need < 1) throw new Error('prefix too long for length ' + length);
  const uniq = (String(Date.now()) + String(seq++)).slice(-need).padStart(need, '0');
  const body = prefix + uniq;
  const total = [...body].map(Number).reverse()
    .reduce((a, x, i) => a + x * (i % 2 === 0 ? 3 : 1), 0);
  return body + String((10 - total % 10) % 10);
}
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };
const made = [];

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext()).newPage();
  await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) {
    await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**', { timeout: 20000 });
  }

  // Record EVERY row that gets created, including from calls that were supposed to fail —
  // when the guard is reverted on purpose those calls succeed, and the first version of this
  // script leaked them as ACTIVE rows into the catalogue. A prover must not litter, least of
  // all in the run where the thing it guards is switched off.
  const create = async (body, qs = '') => {
    const r = await p.evaluate(async ([bd, q]) => {
      try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true' + q, bd) }; }
      catch (e) { return { ok: false, status: e && e.status, detail: (e && (e.detail || e.message)) || String(e) }; }
    }, [body, qs]);
    if (r.ok && r.body && r.body.id) made.push(r.body.id);
    return r;
  };

  // performance.now() counts from PROCESS START, so every run produced SKUs in the same
  // ~4000-5000 range and collided with the soft-deleted rows the previous run left behind.
  // That, not the barcodes, was what made this suite fail one run in two. Wall-clock + a
  // counter is unique across runs, which is the property actually needed.
  const RUN = Date.now();
  let n = 0;
  const base = (extra) => Object.assign({
    name: `ZZPROBE Barcode Guard ${RUN}-${n}`,
    sku: `ZZPROBE-BG-${RUN}-${n++}`,
    price: 1.00, stock_quantity: 1, category: 'Unsorted',
  }, extra);

  console.log('\n1 · the exact bug from the shop floor');
  let r = await create(base({ barcode: '2024VL099B' }));
  ok('a LOT NUMBER is refused', !r.ok && r.status === 422);
  ok('it says what it actually is, in plain words',
     !r.ok && /lot|batch/i.test(JSON.stringify(r.detail)));
  ok('it tells you what to do instead',
     !r.ok && /scan the stripe|leave the barcode blank/i.test(JSON.stringify(r.detail)));

  console.log('\n2 · the other shapes a gun produces');
  r = await create(base({ barcode: '12345' }));
  ok('a 5-digit partial read is refused', !r.ok && r.status === 422);
  r = await create(base({ barcode: '6943498644651' }));   // real code, last digit bumped
  ok('a mistyped digit is caught by the check digit', !r.ok && r.status === 422);

  console.log('\n3 · everything the shop actually uses still goes through');
  for (const [code, what] of [
    [gtin('694349', 13), 'a 13-digit EAN, the ordinary case'],
    [gtin('2000000', 13), 'a Banco-minted 2000000 code'],
    [gtin('50', 8),       'an 8-digit GTIN, like the Rips papers on the shelf'],
    [gtin('716165', 13),  'a 13-digit EAN in the Elements/RAW range'],
  ]) {
    r = await create(base({ barcode: code }));
    ok(`${what} (${code}) is accepted`, r.ok === true);
  }
  r = await create(base({}));
  ok('no barcode at all is still fine — blank is a valid answer', r.ok === true);

  console.log('\n4 · never a trap: there is a way past it');
  r = await create(base({ barcode: 'LOT' + Date.now() + 'X' }), '&allow_nonstandard=true');
  ok('an explicit override is honoured', r.ok === true);

  console.log('\n5 · rebinding an EXISTING row is guarded too');
  const victim = await create(base({ barcode: gtin('426074', 13) }));
  if (victim.ok) {
    const upd = await p.evaluate(async (id) => {
      try { return { ok: true, body: await API.put('/api/v1/pos/products/' + id, { barcode: '2024VL099B' }) }; }
      catch (e) { return { ok: false, status: e && e.status }; }
    }, victim.body.id);
    ok('a working row cannot be rebound to a lot number', !upd.ok && upd.status === 422);
  } else { ok('a working row cannot be rebound to a lot number', false); }

  // Release the barcode BEFORE deactivating: soft-deleted rows keep theirs and would block
  // the next run. allow_nonstandard, because some fixtures hold deliberately bad codes.
  for (const id of made) {
    await p.evaluate(async (i) => {
      try { await API.put('/api/v1/pos/products/' + i + '?allow_nonstandard=true', { barcode: null }); } catch (e) {}
      try { await API.delete('/api/v1/pos/products/' + i); } catch (e) {}
    }, id);
  }
  console.log(`(cleanup: ${made.length} fixture row(s) deactivated)`);
  console.log('\n' + '='.repeat(50));
  console.log(`  ${pass} passed · ${fail} failed`);
  await b.close();
  process.exit(fail ? 1 : 0);
})();
