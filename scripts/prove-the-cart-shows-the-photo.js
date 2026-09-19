// ============================================================================
// prove-the-cart-shows-the-photo — a product with a picture must never ring up as 📦.
//
// WHY THIS EXISTS (2026-09-19). Four of Layla's eight tickets from the 2026-09-18 shop test
// were this one bug, and her own words are the diagnosis: "no cover miamges but they have
// pictures". `products.image_url` is the COVER and it drifts from the gallery two ways —
//   · cover NULL   : a gallery photo only promotes to cover when none is set yet
//   · cover DANGLES: replacing a photo can leave the cover pointing at a deleted image id
// The catalogue reads the gallery and showed the picture; the CART reads the cover and drew
// the placeholder. Same product, two screens, two answers (LESSON #13).
//
// Measured on the live shop: 5,479 active products, 3 with a picture and no cover, 7 with a
// cover pointing nowhere — and all THREE she touched that day came out broken. It is not a
// 0.2% problem, it is an INTAKE problem, and intake is the whole job right now.
//
// The cure was already written: scan.html has had hasImg()/thumbSrc()/onImgError() since
// BL-043, all reading `fallback_image_url`. Only the SEARCH endpoint ever sent it. The scan
// and detail endpoints — the ones that actually fill the cart — returned the bare row.
//
//   NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-the-cart-shows-the-photo.js
// ============================================================================
const { chromium } = require('playwright');
const { execSync } = require('child_process');

const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
const KC   = process.env.BANCO_KC || 'http://localhost:8090';
if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT)) {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates products.`);
  process.exit(2);
}
const JPEG_B64 = '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIfIiEmKzcvJik0KSEiMEExNDk7Pj4+JS5ESUM8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozv/wAARCABAAEADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDKooor6w+VCiiigAooooAKKKKACiiigD1Wiiivwc/QgooooA811X/kL3n/AF8P/wChGqlW9V/5C95/18P/AOhGqlfuOG/gQ9F+R8DV/iS9WFFFFbmZ6rRRRX4OfoQUUUUAea6r/wAhe8/6+H/9CNVKt6r/AMhe8/6+H/8AQjVSv3HDfwIei/I+Bq/xJerCiiitzMt/2rqP/QQuv+/zf40f2rqP/QQuv+/zf41UorD6tQ/kX3I09rU/mf3lv+1dR/6CF1/3+b/Gj+1dR/6CF1/3+b/GqlFH1ah/IvuQe1qfzP7xzu0js7sWZjksTkk+tNoordK2iIP/2Q==';

let pass = 0, fail = 0;
const ok = (n, c, extra) => {
  c ? (pass++, console.log('  ✅ ' + n))
    : (fail++, console.log('  ❌ ' + n + (extra ? '  → ' + extra : '')));
};
const psql = sql => execSync(
  `docker exec -i banco-postgres psql -U helix_user -d helix_db -At -c "${sql.replace(/"/g, '\\"')}"`,
  { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();

function gtin(seed) {                       // a valid EAN-13 so no guard objects
  const b = ('200000' + String(seed)).padEnd(12, '0').slice(0, 12);
  const t = [...b].map(Number).reverse().reduce((a, x, i) => a + x * (i % 2 === 0 ? 3 : 1), 0);
  return b + String((10 - t % 10) % 10);
}

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 } });
  const made = [];
  try {
    // ---- a token, straight from Keycloak (no browser needed for the API half) ----
    const form = new URLSearchParams({ client_id: 'helix_pos_web', grant_type: 'password',
                                       username: 'ralph', password: 'ralph' });
    const tk = await (await fetch(`${KC}/realms/kc-pos-realm-dev/protocol/openid-connect/token`,
      { method: 'POST', body: form })).json();
    const TOKEN = tk.access_token;
    ok('got an API token', !!TOKEN);
    const auth = { 'Authorization': 'Bearer ' + TOKEN };

    // ---- build the two broken shapes, the way the shop actually made them ----
    async function makeProduct(name, code) {
      const r = await fetch(`${ROOT}/api/v1/pos/products`, {
        method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, sku: 'PROBE-' + code, barcode: code,
                               price: 12.5, category: 'Lighters' }) });
      const p = await r.json();
      if (!p || !p.id) throw new Error('product create failed: ' + JSON.stringify(p).slice(0, 200));
      made.push(p.id);
      // Upload a REAL photo. It has to be real: with no bytes behind it the <img> 404s and
      // onImgError falls to the placeholder anyway, so a byte-less fixture would report the
      // bug as still present and I would "fix" it forever (LESSON #5).
      const fd = new FormData();
      fd.append('file', new Blob([Buffer.from(JPEG_B64, 'base64')], { type: 'image/jpeg' }), 'probe.jpg');
      const up = await fetch(`${ROOT}/api/v1/pos/products/${p.id}/images`, { method: 'POST', headers: auth, body: fd });
      if (!up.ok) throw new Error('image upload failed: ' + up.status);
      return p.id;
    }

    const codeA = gtin(Date.now() % 100000), codeB = gtin((Date.now() % 100000) + 1);
    const idA = await makeProduct('PROBE cover-null ' + codeA, codeA);
    const idB = await makeProduct('PROBE cover-dangles ' + codeB, codeB);

    psql(`UPDATE products SET image_url = NULL WHERE id = '${idA}';`);
    psql(`UPDATE products SET image_url = '/api/v1/pos/products/${idB}/images/` +
         `00000000-0000-0000-0000-0000deadbeef' WHERE id = '${idB}';`);
    ok('shape A built: a gallery photo, and NO cover',
       psql(`SELECT coalesce(image_url,'NULL') FROM products WHERE id='${idA}';`) === 'NULL' &&
       psql(`SELECT count(*) FROM product_images WHERE product_id='${idA}';`) === '1');
    ok('shape B built: a gallery photo, and a cover pointing NOWHERE',
       psql(`SELECT image_url FROM products WHERE id='${idB}';`).includes('deadbeef') &&
       psql(`SELECT count(*) FROM product_images WHERE product_id='${idB}';`) === '1');

    // ---- 1 · the API half: the scan endpoint must offer a spare ----
    console.log('\n1 · GET /products/barcode/{code} — the call the scan gun makes');
    for (const [label, code] of [['cover NULL', codeA], ['cover dangles', codeB]]) {
      const j = await (await fetch(`${ROOT}/api/v1/pos/products/barcode/${code}`, { headers: auth })).json();
      ok(`${label}: response carries fallback_image_url`, !!j.fallback_image_url,
         'image_url=' + JSON.stringify(j.image_url) + ' fallback=' + JSON.stringify(j.fallback_image_url));
    }

    // ---- 2 · the screen half: scan it and look at the cart line ----
    console.log('\n2 · scan it at the till and look at the cart line');
    const p = await ctx.newPage();
    const errs = []; p.on('pageerror', e => errs.push(e.message.slice(0, 160)));
    for (let a = 1; a <= 3; a++) {
      await p.goto(ROOT + '/pos', { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(400);
      if (await p.$('button:has-text("Login")')) { await p.click('button:has-text("Login")'); await p.waitForTimeout(3500); }
      if (await p.$('#username')) {
        await p.fill('#username', 'ralph'); await p.fill('#password', 'ralph');
        await p.click('#kc-login, input[type=submit]');
      }
      try { await p.waitForFunction(() => !!sessionStorage.getItem('pos_token'), null,
                                    { timeout: 15000, polling: 200 }); } catch (e) {}
      if (await p.evaluate(() => sessionStorage.getItem('pos_token'))) break;
    }
    ok('logged in at the till', !!(await p.evaluate(() => sessionStorage.getItem('pos_token'))));

    await p.goto(ROOT + '/pos/scan', { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(2500);

    for (const [label, code] of [['cover NULL', codeA], ['cover dangles', codeB]]) {
      const box = await p.$('input[placeholder*="barcode" i], #barcodeInput');
      if (!box) { ok(`${label}: found the barcode box`, false); continue; }
      await box.fill(code);
      await box.press('Enter');
      await p.waitForTimeout(3500);
      // Ask the PAGE what it decided, not the DOM: hasImg() is the function that draws 📦.
      const v = await p.evaluate(() => {
        const el = document.querySelector('[x-data]');
        const d = window.Alpine && el ? Alpine.$data(el) : null;
        const last = d && d.cart && d.cart.length ? d.cart[d.cart.length - 1] : null;
        return last ? { name: last.name, hasImg: d.hasImg(last), src: d.thumbSrc(last),
                        imgerr: !!last._imgerr, fb: last.fallback_image_url || null } : null;
      });
      ok(`${label}: the item reached the cart`, !!v, 'cart was empty after the scan');
      ok(`${label}: the cart line shows a PHOTO, not 📦`, !!(v && v.hasImg && !v.imgerr),
         v ? `hasImg=${v.hasImg} imgerr=${v.imgerr} fallback=${JSON.stringify(v.fb)}` : 'no item');
    }
    ok('the page did not throw', errs.length === 0, errs.join(' | '));
  } finally {
    // TIDY IN A FINALLY — a prover that only cleans up on the happy path poisons its next run.
    for (const id of made) {
      try { psql(`DELETE FROM product_images WHERE product_id='${id}'; DELETE FROM products WHERE id='${id}';`); }
      catch (e) { console.log('  ⚠️  leftover probe row:', id); }
    }
    await b.close();
  }
  console.log(`\n${pass} pass · ${fail} fail`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('HARNESS FAULT:', e); process.exit(3); });
