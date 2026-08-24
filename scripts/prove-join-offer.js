// The join offer on screen IS the offer the till will honour — and 0 means "no offer", not "0%".
//
//   NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-join-offer.js
//
// WHY. These two numbers used to be hardcoded in two files that had to agree: kiosk.html
// ADVERTISED `isTouch ? 15 : 10` and the signup endpoint GRANTED the same two literals. Nobody
// had made them disagree yet, but whoever edited one and not the other would have had the page
// promise a customer a discount the till then refused, at the counter, in front of them. They
// now come from one store setting — and this proves the whole chain, page and grant together.
//
// Zero is the case that matters as of 2026-08-24. Angel, at UAT: signup is anonymous and
// unlimited, so a standing welcome discount is a coupon a customer re-mints on every visit — a
// new code, another 15%, for ever. The offer is switched OFF, and a page that reads
// "Become a member — 0% off today" would be worse than no offer at all.
const { chromium } = require('playwright');
const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
const KC = process.env.BANCO_KC || 'http://localhost:8090/realms/kc-pos-realm-dev/protocol/openid-connect/token';
const USER = process.env.BANCO_USER || 'felix', PWD = process.env.BANCO_PWD || 'felix';
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  ✅ ' + n)) : (fail++, console.log('  ❌ ' + n)); };

async function token() {
  const r = await fetch(KC, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: 'helix_pos_web', username: USER, password: PWD, grant_type: 'password' }) });
  return (await r.json()).access_token;
}
async function setOffer(tok, kiosk, phone) {
  const r = await fetch(`${ROOT}/api/v1/pos/settings/1`, { method: 'PUT',
    headers: { 'Authorization': `Bearer ${tok}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ welcome_discount_kiosk_pct: kiosk, welcome_discount_phone_pct: phone }) });
  if (!r.ok) throw new Error(`settings PUT ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const d = await r.json();
  return [d.welcome_discount_kiosk_pct, d.welcome_discount_phone_pct];
}

(async () => {
  const tok = await token();
  const before = await (await fetch(`${ROOT}/api/v1/pos/settings/1`, { headers: { Authorization: `Bearer ${tok}` } })).json();
  const restore = [before.welcome_discount_kiosk_pct, before.welcome_discount_phone_pct];

  const b = await chromium.launch();
  // Phone viewport: `isTouch` picks the PHONE number, which is the bigger one and the path a
  // customer actually takes off the counter card.
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const p = await ctx.newPage();

  async function bannerText() {
    await p.goto(ROOT + '/pos/kiosk', { waitUntil: 'networkidle' });
    await p.waitForTimeout(600);
    await p.locator('button:has-text("🇬🇧")').first().click({ timeout: 5000 }).catch(() => {});
    await p.waitForTimeout(500);
    return p.evaluate(() => document.body.innerText);
  }

  try {
    console.log('\n🎁 With an offer running (12% / 20%) …');
    ok('the setting saves and reads back', JSON.stringify(await setOffer(tok, 12, 20)) === '[12,20]');
    let txt = await bannerText();
    ok('the phone banner advertises 20% — the PHONE number, not the kiosk one', /20\s*%/.test(txt));
    ok('it does not leak the old hardcoded 15', !/\b15\s*%/.test(txt));

    console.log('\n🚫 Switched OFF (0 / 0) …');
    ok('zero saves as zero and is not treated as "unset"', JSON.stringify(await setOffer(tok, 0, 0)) === '[0,0]');
    txt = await bannerText();
    ok('the page never says "0% off"', !/0\s*%/.test(txt));
    // POINTS, and no percentage. Angel, 2026-08-24: the discount is gone because an anonymous,
    // unlimited signup makes a standing % a re-mintable coupon. POINTS rather than "credit"
    // because credit reads as francs the shop owes you, while the rule is 1 credit per CHF
    // SPENT — and because nothing at the till can redeem them yet, so the vaguer word is the
    // honest one. It also matches loyalty_service.py's "bronze (points only)".
    ok('the copy offers POINTS', /\bpoints?\b|Punkte|punti/i.test(txt));
    ok('it does not promise redeemable CREDIT the till cannot yet spend',
       !/\bcredit\b|crédit|credito|Guthaben/i.test(txt));
    ok('no discount word survives on the zero-offer page', !/discount|Rabatt|remise|sconto/i.test(txt.replace(/No discount|Kein Rabatt|Sans remise|Nessuno sconto/gi, '')));

    // The grant has to agree with the page — that is the whole reason this is one setting.
    const r = await fetch(`${ROOT}/api/v1/pos/kiosk/signup`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ handle: null, age_confirmed: true, source: 'phone' }) });
    const m = await r.json();
    ok(`signing up now grants 0% (got ${m.discount_pct}%, member ${m.handle})`, m.ok && m.discount_pct === 0);
  } finally {
    await setOffer(tok, restore[0], restore[1]);
    console.log(`\n↩️  restored to ${restore[0]} / ${restore[1]}`);
    await b.close();
  }
  console.log(`${fail ? '❌' : '✅'} ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})();
