const { chromium } = require('playwright');
let _s=0;
function gtin(pre,len){const need=len-1-pre.length;const u=(String(Date.now())+String(_s++)).slice(-need).padStart(need,'0');
 const b=pre+u;const t=[...b].map(Number).reverse().reduce((a,x,i)=>a+x*(i%2===0?3:1),0);return b+String((10-t%10)%10);}
let pass=0,fail=0; const ok=(n,c)=>{c?(pass++,console.log('  ✅ '+n)):(fail++,console.log('  ❌ '+n));};
const made=[];
(async()=>{
  const b=await chromium.launch(); const p=await (await b.newContext({viewport:{width:1200,height:1000}})).newPage();
  const errs=[]; p.on('pageerror',e=>errs.push(e.message.slice(0,140)));
  await p.goto('http://localhost:3000/pos',{waitUntil:'domcontentloaded'});
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) { await p.fill('#username','ralph'); await p.fill('#password','ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**',{timeout:20000}); }
  const RUN=Date.now();
  const withDeal=gtin('841477',13), without=gtin('716165',13);
  for (const [sku,name,code,tiers,mode] of [
    ['ZZPROBE-D-'+RUN, 'ZZPROBE Smoking Rolls blue', withDeal, [{min_qty:3,unit_price:'10.00'}], 'bundle'],
    ['ZZPROBE-N-'+RUN, 'ZZPROBE Smoking Rolls brown', without, null, null]]) {
    const r=await p.evaluate(async ([sku,name,code,tiers,mode])=>{
      try { const body={sku,name,barcode:code,price:4.00,stock_quantity:1,category:'Unsorted'};
            if (tiers){body.price_tiers=tiers;body.tier_mode=mode;}
            return {ok:true,body:await API.post('/api/v1/pos/products?allow_duplicate=true',body)}; }
      catch(e){ return {ok:false,detail:(e&&e.message)||String(e)}; }
    },[sku,name,code,tiers,mode]);
    if(!r.ok){console.error('seed failed',r.detail);process.exit(1);} made.push(r.body.id);
  }
  await p.goto('http://localhost:3000/pos/shelf-intake');
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(900);
  await p.evaluate(()=>localStorage.removeItem('banco_shelf_intake_v1'));
  await p.reload(); await p.waitForTimeout(1100);
  await p.locator('textarea').first().fill(withDeal+'\n'+without);
  await p.locator('button:has-text("Triage the shelf")').click();
  await p.waitForTimeout(3200);
  const t=await p.locator('body').innerText();
  console.log('\nthe deal must be readable WITHOUT opening anything');
  ok('a row with the deal shows it',  /🏷️\s*3 for 10\.00/.test(t));
  ok('a row without one says "no deal"', /no deal/.test(t));
  ok('the price is still shown',       /CHF\s*4\.00/.test(t));
  console.log('\npageerrors: '+errs.length+' '+(errs[0]||''));
  ok('no javascript errors', errs.length===0);
  for (const id of made) await p.evaluate(async i=>{
    try{await API.put('/api/v1/pos/products/'+i+'?allow_nonstandard=true',{barcode:null});}catch(e){}
    try{await API.delete('/api/v1/pos/products/'+i);}catch(e){}}, id);
  console.log('\n'+'='.repeat(46)+`\n  ${pass} passed · ${fail} failed`);
  await b.close(); process.exit(fail?1:0);
})();
