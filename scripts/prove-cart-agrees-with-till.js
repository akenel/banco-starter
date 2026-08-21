// The cart preview and the till must agree to the cent. "shown != charged" is the one thing
// the tier ladder exists to prevent, and Banco has TWO implementations of it — Python in
// services/pricing.py and JavaScript in base.html — so nothing but a test keeps them level.
// Compares 160 quantities across four real ladders.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
// Ask the SERVER's own pricing function, right now — do not reimplement it here and do not
// read a file someone generated earlier. Lesson 5: a script that recomputes what the server
// computes will accuse working code.
const server = JSON.parse(execFileSync('python3', ['-c', `
import sys, logging, json
sys.path.insert(0, '${process.env.BANCO_REPO || '/home/angel/repos/banco-starter'}')
logging.disable(logging.WARNING)
from decimal import Decimal
from src.services.pricing import tier_line_total
CASES = [("3 for 10", [{"min_qty":3,"unit_price":"10.00"}], "4.00"),
         ("nested",   [{"min_qty":3,"unit_price":"10.00"},{"min_qty":10,"unit_price":"24.00"}], "4.00"),
         ("gizeh",    [{"min_qty":1,"unit_price":"1.40"},{"min_qty":3,"unit_price":"4.00"},{"min_qty":10,"unit_price":"12.00"}], "1.40"),
         ("3 for 5",  [{"min_qty":3,"unit_price":"5.00"}], "2.00")]
print(json.dumps({nm: [str(tier_line_total(t, Decimal(b), q, mode='bundle')) for q in range(1,41)]
                  for nm, t, b in CASES}))
`], { encoding: 'utf8' }));
(async()=>{
  const b=await chromium.launch(); const p=await (await b.newContext()).newPage();
  await p.goto('http://localhost:3000/pos',{waitUntil:'domcontentloaded'});
  if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
  if (await p.$('#username')) { await p.fill('#username','ralph'); await p.fill('#password','ralph');
    await p.click('#kc-login, input[type=submit]'); await p.waitForURL('**/pos/**',{timeout:20000}); }
  const client = await p.evaluate(()=>{
    const CASES={"3 for 10":[[{min_qty:3,unit_price:"10.00"}],4.00],
                 "nested":[[{min_qty:3,unit_price:"10.00"},{min_qty:10,unit_price:"24.00"}],4.00],
                 "gizeh":[[{min_qty:1,unit_price:"1.40"},{min_qty:3,unit_price:"4.00"},{min_qty:10,unit_price:"12.00"}],1.40],
                 "3 for 5":[[{min_qty:3,unit_price:"5.00"}],2.00]};
    const out={};
    for (const k of Object.keys(CASES)) {
      const [tiers,price]=CASES[k]; out[k]=[];
      for (let q=1;q<=40;q++) out[k].push(tierLineTotal({quantity:q,price,price_tiers:tiers,tier_mode:'bundle'}).toFixed(2));
    }
    return out;
  });
  let bad=0, n=0;
  for (const k of Object.keys(server)) for (let i=0;i<40;i++){
    n++;
    if (server[k][i] !== client[k][i]) { bad++;
      if (bad<=6) console.log(`  ❌ ${k} qty ${i+1}: till ${server[k][i]} · cart ${client[k][i]}`); }
  }
  console.log(bad? `\n  ${bad} of ${n} disagree` : `\n  ✅ cart and till agree on all ${n} quantities`);
  await b.close(); process.exit(bad?1:0);
})();
