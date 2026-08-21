const { chromium } = require('playwright');
const OUT='/tmp/claude-1000/-home-angel-repos-banco-starter/24fb2db9-47b2-488c-9d8c-7f593e203786/scratchpad/';
const CODES = ['6941908339899','6943498644650','4260748411544','7612400041724','3661075283438'];
let pass=0, fail=0;
const ok=(n,c)=>{ c?(pass++,console.log('  ✅ '+n)):(fail++,console.log('  ❌ '+n)); };
(async () => {
  const b = await chromium.launch();
  // ONE persistent profile = one browser identity across a simulated reboot
  const dir = OUT+'profile-shelf';
  await b.close();
  const ctx = await chromium.launchPersistentContext(dir, {viewport:{width:1100,height:1000}});
  let p = await ctx.newPage();
  await p.goto('http://localhost:3000/pos',{waitUntil:'domcontentloaded'});
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) { await p.fill('#username','ralph'); await p.fill('#password','ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**',{timeout:20000}); }

  await p.goto('http://localhost:3000/pos/shelf-intake?lang=en');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1200);
  // start clean
  await p.evaluate(()=>localStorage.removeItem('banco_shelf_intake_v1'));
  await p.reload(); await p.waitForTimeout(1200);

  console.log('\n1 · type codes, NEVER press triage (Angel\'s exact situation)');
  const ta = p.locator('textarea').first();
  await ta.click();
  await ta.fill(CODES.join('\n'));
  await p.fill('input[type=number]', '5');
  await p.waitForTimeout(900);          // let the 400ms debounce land
  const stored = await p.evaluate(()=>localStorage.getItem('banco_shelf_intake_v1'));
  ok('codes written to localStorage before any triage', !!stored && stored.includes('6941908339899'));
  ok('the expected-count survived too', !!stored && /"expected":5/.test(stored));

  console.log('\n2 · KILL the browser entirely and relaunch it — a real reboot');
  await ctx.close();
  const ctx2 = await chromium.launchPersistentContext(dir, {viewport:{width:1100,height:1000}});
  p = await ctx2.newPage();
  await p.goto('http://localhost:3000/pos/shelf-intake?lang=en');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(1800);

  const after = await p.evaluate(()=>{
    const ta=document.querySelector('textarea');
    return { box: ta ? ta.value : '', text: document.body.innerText };
  });
  ok('all 5 codes are back in the box', CODES.every(c=>after.box.includes(c)));
  ok('the count reads 5, not 0', /\b5\b[\s\S]{0,30}codes in the box/.test(after.text));
  ok('he is TOLD they came back', /Your codes came back/i.test(after.text));
  ok('no "Total Counters=0" empty screen', !/\b0\s+codes in the box/.test(after.text));

  console.log('\n3 · clearing the box on purpose still works');
  await p.screenshot({path:OUT+'shelf-restored.png'});
  await p.locator('textarea').first().fill('');
  await p.waitForTimeout(900);
  const cleared = await p.evaluate(()=>localStorage.getItem('banco_shelf_intake_v1'));
  ok('an emptied box is not resurrected', !cleared || !cleared.includes('6941908339899'));

  console.log('\n'+'='.repeat(50));
  console.log(`  ${pass} passed · ${fail} failed`);
  await ctx2.close();
  process.exit(fail?1:0);
})();
