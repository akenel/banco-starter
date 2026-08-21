const { chromium } = require('playwright');
const OUT='/tmp/claude-1000/-home-angel-repos-banco-starter/24fb2db9-47b2-488c-9d8c-7f593e203786/scratchpad/';
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

  const codes = ['8419036900001','8419036900002','8419036900003'];

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
  if (!hasStub) { await b.close(); process.exit(1); }

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
  await b.close();
  process.exit(fail?1:0);
})();
