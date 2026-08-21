const { chromium } = require('playwright');
const OUT='/tmp/claude-1000/-home-angel-repos-banco-starter/24fb2db9-47b2-488c-9d8c-7f593e203786/scratchpad/';
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({viewport:{width:1100,height:1000}})).newPage();
  await p.goto('http://localhost:3000/pos',{waitUntil:'domcontentloaded'});
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) { await p.fill('#username','ralph'); await p.fill('#password','ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**',{timeout:20000}); }
  await p.goto('http://localhost:3000/pos/catalog?lang=en');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(2500);
  await p.locator('button:has-text("New product")').first().click();
  await p.waitForTimeout(900);
  const stamp = Date.now();
  await p.evaluate((s)=>{
    const d = Alpine.$data(document.querySelector('[x-data]'));
    d.form.name = 'ZZPROBE Lot Number Trap ' + s;
    d.form.price = '2.50';
    d.form.barcode = '2024VL099B';
  }, stamp);
  await p.waitForTimeout(400);
  // press the real save button a human presses
  await p.locator('button.btn-success:visible', {hasText: 'Create product'}).first().click();
  await p.waitForTimeout(1500);
  // the error arrives as a toast, which fades — capture the text while it is up
  const t = await p.locator('body').innerText();
  const said = /LOT or BATCH/i.test(t);
  console.log('message shown on screen :', said);
  const m = t.match(/.{0,80}LOT or BATCH.{0,120}/i);
  if (m) console.log('   ->', m[0].replace(/\s+/g,' ').trim());
  await p.screenshot({path:OUT+'lot-trap.png'});
  await b.close();
  process.exit(said?0:1);
})();
