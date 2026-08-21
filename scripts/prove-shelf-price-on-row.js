const { chromium } = require('playwright');
const OUT='/tmp/claude-1000/-home-angel-repos-banco-starter/24fb2db9-47b2-488c-9d8c-7f593e203786/scratchpad/';
// ── fixtures ──────────────────────────────────────────────────────────────────────────
// Seeds its OWN rows and deletes them. The first cut of this script leaned on products a
// human had inserted by hand, so it passed on my machine and would have failed on a clean
// checkout — a prover that needs a fixture it does not create is a prover that lies.
// Everything it makes is prefixed ZZPROBE and removed in the finally block.
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT) &&
    process.env.BANCO_ALLOW_CATALOG_WRITES !== '1') {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates and deletes`);
  console.error('products. Set BANCO_ALLOW_CATALOG_WRITES=1 if you really mean it.');
  process.exit(2);
}
const made = [];
async function seed(page, body) {
  // Use the page's own API helper, not raw fetch: it attaches the bearer token the same
  // way every screen does. A raw fetch here just proved my probe was unauthenticated.
  const r = await page.evaluate(async (b) => {
    try { return { ok: true, body: await API.post('/api/v1/pos/products?allow_duplicate=true', b) }; }
    catch (e) { return { ok: false, status: e && e.status, body: (e && e.message) || String(e) }; }
  }, body);
  if (!r.ok) { console.error('seed failed', r.status, JSON.stringify(r.body).slice(0, 300)); process.exit(1); }
  made.push(r.body.id);
  return r.body;
}
// NOTE: DELETE on a product is a SOFT delete by design — a row that has ever sold cannot
// vanish from the books. So this deactivates its fixtures rather than erasing them; they
// drop out of the catalogue, the bench and search, which is what "clean" means here. On a
// dev box, `DELETE FROM products WHERE sku LIKE 'ZZPROBE%'` finishes the job.
async function cleanup(page) {
  for (const id of made) {
    await page.evaluate(async (i) => {
      // release the barcode first: a soft-deleted row keeps it and would collide next run
      try { await API.put('/api/v1/pos/products/' + i + '?allow_nonstandard=true', { barcode: null }); } catch (e) {}
      try { await API.delete('/api/v1/pos/products/' + i); } catch (e) {}
    }, id).catch(() => {});
  }
}
// Valid GTINs, unique per run. Invented codes like "8419036900001" do not pass a check digit —
// the barcode guard added on 2026-08-21 rejected them, correctly, and broke this script. That
// was the guard doing its job: my fixtures were never real barcodes.
let _seq = 0;
function gtin(prefix, length) {
  const need = length - 1 - prefix.length;
  const uniq = (String(Date.now()) + String(_seq++)).slice(-need).padStart(need, '0');
  const body = prefix + uniq;
  const total = [...body].map(Number).reverse()
    .reduce((a, x, i) => a + x * (i % 2 === 0 ? 3 : 1), 0);
  return body + String((10 - total % 10) % 10);
}
let pass=0, fail=0;
const ok=(n,c)=>{ c?(pass++,console.log('  ✅ '+n)):(fail++,console.log('  ❌ '+n)); };
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({viewport:{width:1100,height:1000}})).newPage();
  const errs=[]; p.on('pageerror', e=>errs.push(e.message.slice(0,160)));
  await p.goto('http://localhost:3000/pos',{waitUntil:'domcontentloaded'});
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) { await p.fill('#username','ralph'); await p.fill('#password','ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**',{timeout:20000}); }

  const codes = [gtin('841903', 13), gtin('841903', 13), gtin('841903', 13)];
  await seed(p, {sku:'ZZPROBE-01-'+Date.now(), name:'ZZPROBE Smoking King Size green', barcode:codes[0], price:2.00, category:'Unsorted', stock_quantity:1});
  await seed(p, {sku:'ZZPROBE-02-'+Date.now(), name:'ZZPROBE Smoking King Size red',   barcode:codes[1], price:999.99, category:'Unsorted', stock_quantity:1});
  await seed(p, {sku:'ZZPROBE-03-'+Date.now(), name:'ZZPROBE Smoking King Size gold',  barcode:codes[2], price:2.00, category:'Unsorted', stock_quantity:1});

  await p.goto('http://localhost:3000/pos/shelf-intake');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1000);
  await p.evaluate(()=>localStorage.removeItem('banco_shelf_intake_v1'));
  await p.reload(); await p.waitForTimeout(1200);
  await p.locator('textarea').first().fill(codes.join('\n'));
  await p.locator('button:has-text("Triage the shelf")').click();
  await p.waitForTimeout(3500);

  const stub = p.locator('div.px-6 > div:has-text("% ready")').first();
  const hasStub = await stub.count() > 0;
  ok('there are stub rows to work with', hasStub);
  if (!hasStub) { await cleanup(p); await b.close(); process.exit(1); }

  console.log('\n1 · the price is ON the row, without clicking anything');
  const rowText = await stub.innerText();
  ok('row shows a price or says "no price"', /CHF\s*[\d.]+|no price/i.test(rowText));
  await p.screenshot({path:OUT+'price-row.png'});

  console.log('\n2 · tap the price → edit in place');
  await stub.locator('button.group').first().click();
  await p.waitForTimeout(500);
  const box = stub.locator('input[type=number]');
  ok('an input appears on the row', await box.first().isVisible());
  ok('it is focused, so you just type', await box.first().evaluate(el=>el===document.activeElement));

  console.log('\n3 · a placeholder value is refused');
  await box.first().fill('999.99');
  await stub.locator('button:has-text("✔")').click();
  await p.waitForTimeout(600);
  ok('999.99 rejected as the placeholder itself', /placeholder/i.test(await stub.innerText()));

  console.log('\n4 · a real price saves and the row re-reads from the server');
  const before = await stub.innerText();
  await box.first().fill('2.00');
  await stub.locator('button:has-text("✔")').click();
  await p.waitForTimeout(2500);
  const after = await stub.innerText();
  ok('the row now shows 2.00 without a reload', /2\.00/.test(after));
  ok('the edit box closed', !(await stub.locator('input[type=number]').first().isVisible()));
  ok('readiness badge was re-read (row text changed)', before !== after);

  console.log('\n5 · it survives the reboot too');
  const saved = await p.evaluate(()=>localStorage.getItem('banco_shelf_intake_v1'));
  ok('the priced row is in localStorage', !!saved && saved.includes('"price":2'));

  console.log('\npageerrors: '+errs.length+' '+(errs[0]||''));
  ok('no javascript errors', errs.length===0);
  await p.screenshot({path:OUT+'price-after.png'});
  console.log('\n'+'='.repeat(50));
  console.log(`  ${pass} passed · ${fail} failed`);
  await cleanup(p);
  console.log(`(cleanup: ${made.length} fixture row(s) deactivated)`);
  await b.close();
  process.exit(fail?1:0);
})();
