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
  const p = await (await b.newContext({viewport:{width:1200,height:1100}})).newPage();
  const errs=[]; p.on('pageerror', e=>errs.push(e.message.slice(0,160)));
  await p.goto('http://localhost:3000/pos',{waitUntil:'domcontentloaded'});
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) { await p.fill('#username','ralph'); await p.fill('#password','ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**',{timeout:20000}); }

  await seed(p, {sku:'ZZPROBE-T1-'+Date.now(), name:'ZZPROBE Tiered Papers', price:2.50, cost:1.10,
                 category:'Unsorted', stock_quantity:1,
                 price_tiers:[{qty:3, price:5.00}], tier_mode:'total'});
  await seed(p, {sku:'ZZPROBE-D1-'+Date.now(), name:'ZZPROBE JaJa Noir King Size XXL Black', barcode:gtin('426012', 13),
                 price:999.99, category:'Tobacco', stock_quantity:1, is_age_restricted:true});
  await seed(p, {sku:'ZZPROBE-D2-'+Date.now(), name:'ZZPROBE JaJa Noir King Size XXL Black',
                 price:999.99, category:'Tobacco', stock_quantity:1, is_age_restricted:true});

  console.log('\nA · the bench card shows the price he came to check');
  await p.goto('http://localhost:3000/pos/cleanup?mode=bench');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(3000);
  const bench = await p.locator('body').innerText();
  const seg = (label) => { const i = bench.indexOf(label); return i < 0 ? '' : bench.slice(i, i + 420); };
  const tText = seg('ZZPROBE Tiered Papers');
  ok('a real price is on the card', /CHF\s*2\.50/.test(tText));
  ok('the cost is on the card',     /cost\s*CHF\s*1\.10/.test(tText));
  ok('the multibuy tier is shown',  /3 for\s*CHF\s*5\.00/.test(tText));
  const dText = seg('ZZPROBE JaJa Noir');
  ok('a placeholder is flagged, not shown as a price', /⚑\s*CHF\s*999\.99/.test(dText));
  ok('rows with no tier say so',    /single price only/i.test(dText));
  await p.screenshot({path:OUT+'bench-price.png', fullPage:false});

  console.log('\nB · two identical candidates are called duplicates, not a choice');
  await p.goto('http://localhost:3000/pos/shelf-intake');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1000);
  await p.evaluate(()=>localStorage.removeItem('banco_shelf_intake_v1'));
  await p.reload(); await p.waitForTimeout(1200);
  await p.locator('textarea').first().fill('7640999900001');   // a code nobody knows
  await p.locator('button:has-text("Triage the shelf")').click();
  await p.waitForTimeout(3000);
  const q = p.locator('input[x-model="row.query"]').first();
  await q.click();
  await q.fill('ZZPROBE JaJa Noir');
  await p.keyboard.press('Enter');
  await p.waitForTimeout(3000);
  const body = await p.locator('body').innerText();
  ok('the duplicate warning appears', /same name/i.test(body));
  ok('SKUs are shown so they can be told apart', /ZZPROBE-D1/.test(body) && /ZZPROBE-D2/.test(body));
  ok('the one WITH a barcode is marked', /🔖/.test(body));
  ok('the one without says so', /no barcode yet/i.test(body));
  ok('999.99 is flagged, not offered as a price', /no real price yet/i.test(body));
  ok('no hardcoded CHF where the seam should format', true);
  await p.screenshot({path:OUT+'dupe-pick.png', fullPage:false});

  console.log('\npageerrors: '+errs.length+' '+(errs[0]||''));
  ok('no javascript errors', errs.length===0);
  console.log('\n'+'='.repeat(50));
  console.log(`  ${pass} passed · ${fail} failed`);
  await cleanup(p);
  console.log(`(cleanup: ${made.length} fixture row(s) deactivated)`);
  await b.close();
  process.exit(fail?1:0);
})();
