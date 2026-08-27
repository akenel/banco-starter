#!/usr/bin/env node
/**
 * prove-no-duplicate-on-a-miss.js — when a scan misses, does the till find what we ALREADY OWN?
 *
 * WHY THIS EXISTS
 * ---------------
 * 2026-08-27, measured on the shop's live database:
 *
 *     4,971 of 5,447 active products (91%) carry a barcode starting 200… — the GS1
 *     RESTRICTED-CIRCULATION range, valid inside one building. Minted. They cannot be
 *     on a packet. Only 188 of 5,435 codes (3.5%) exist in any real supplier feed.
 *
 * 3.5% is exactly what the shop owner lives as "scan once, find it, move on — happens by luck
 * 3% of the time". So the question that decides whether this till is usable is: when a REAL
 * packet misses, does the screen offer the row we already own — or does it offer to create a
 * second one?
 *
 * IT ALREADY OFFERS THE ROW. That was built on 2026-08-21 (scan.html:1543) and this test is
 * not the fix for it — it is the PROOF, which did not exist. On a miss the till asks the
 * supplier feed by barcode, and a hit re-opens the capture panel with the packet's real title
 * already in the search box, so the live catalogue is searched for a name nobody typed. That
 * is how a Tamar row filed under a minted 2xxxxxxxxxxxx gets the packet's real EAN bound to it.
 *
 * I asserted the opposite first, out loud, to Angel — that the catalogue was never searched on
 * a miss and the till was a duplicate factory. I had read `openLazyCapture` and not its
 * CALLERS, which pass the resolved name in. Reverting the code is what proved me wrong: eight
 * of these nine assertions pass with tonight's change removed. The one that does not is the
 * banner. LESSON #3 — a remembered failure is a hypothesis with a timestamp; so is a
 * remembered ABSENCE, and absence read off one function is not absence in the program.
 *
 * WHAT TONIGHT ACTUALLY ADDED: the amber banner. The panel opens with a name the operator
 * never typed and a list appears under it — correct, and unexplained. Now it says where the
 * name came from. That is the whole change (20 lines), and this file is the reason it is
 * possible to say so without guessing.
 *
 * WHAT IT ASSERTS — through the real screen, never by poking Alpine state to make it pass
 *   1  a miss on a code the SUPPLIER FEED knows opens the capture panel
 *   2  the catalogue search box carries the packet's name — the operator types nothing
 *   3  the amber "you may already have it" banner explains where that name came from   <- new
 *   4  the product we already own is LISTED
 *   5  the CREATE form stays collapsed — create is not the lead action
 *   6  tapping the row makes NO second product row
 *   7  the real EAN is PROMOTED to primary, the minted code kept as an alias
 *   8  scanning the same packet again FINDS it — sell-to-seed, closed                 <- the thesis
 *
 * AND SCENARIO B — the miss NOBODY knows, which is where the duplicates were actually born.
 * A code the supplier feed cannot name never opens that panel at all. It leaves the department
 * strip and the ON-THE-FLY create form on screen — "New item — with the code you scanned" —
 * and until 2026-08-27 nothing between the name she types there and POST /products/quick ever
 * asked our own catalogue. On a shelf that is 91% minted codes, "the scan missed" is the normal
 * state of a product we ALREADY OWN, so this is the path that made the second row.
 *   9  a miss the feed does not know leaves the on-the-fly form on screen
 *  10  typing the name there lists the product we already own
 *  11  tapping it makes NO second product row
 *  12  the scanned code now resolves to the row we already had
 *
 * ⚠️  IT WRITES PRODUCTS. It rings NO sales — nothing here reaches the Kassenbuch — but it
 *     creates a catalogue row and removes it at the end (name prefix `ZZPROBE`). It refuses
 *     to run anywhere but localhost unless you insist.
 *
 * RUN
 *   NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-no-duplicate-on-a-miss.js
 */
'use strict';

const { execFileSync } = require('child_process');
const path = require('path');

const ROOT = (process.env.BANCO_URL || 'http://localhost:3000').replace(/\/$/, '');
const REPO = path.resolve(__dirname, '..');
const USER = process.env.BANCO_USER || 'ralph';
const PASS = process.env.BANCO_PASS || 'ralph';

if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(ROOT) &&
    process.env.BANCO_ALLOW_CATALOG_WRITES !== '1') {
  console.error(`REFUSING: ${ROOT} is not localhost, and this script creates and deletes`);
  console.error('products. If you really mean it: BANCO_ALLOW_CATALOG_WRITES=1');
  process.exit(2);
}

let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  console.error('playwright not found. Set NODE_PATH to a node_modules directory that has it:');
  console.error('  NODE_PATH=/path/to/node_modules node scripts/prove-no-duplicate-on-a-miss.js');
  process.exit(2);
}

let pass = 0, fail = 0;
const ok  = (l, d) => { pass++; console.log(`  ✅ ${l}${d ? '  — ' + d : ''}`); };
const bad = (l, d) => { fail++; console.log(`  ❌ ${l}${d ? '  — ' + d : ''}`); };
const check = (c, l, d) => { (c ? ok : bad)(l, d); return !!c; };

function psql(q) {
  return execFileSync('docker', ['compose', 'exec', '-T', 'postgres', 'psql',
    '-U', process.env.POSTGRES_USER || 'helix_user',
    '-d', process.env.POSTGRES_DB || 'helix_db', '-tAc', q],
    { cwd: REPO, encoding: 'utf8' }).trim();
}

const PROBE  = 'ZZPROBE';
const MINTED = '2000000999991';          // the fiction the row is filed under today
const stamp  = String(Date.now()).slice(-7);

// The packet: a code that IS in reference_products with a real EAN, and is NOT in the catalogue.
// Picked from the live feed rather than invented, because the whole assertion is that the FEED
// names a packet the scan could not.
const PACKET_EAN = process.env.PROBE_EAN || '8718403231335';
let   PACKET_TITLE = '';

// SCENARIO B's packet: a real EAN that is NOT in the feed, so the till cannot name it and the
// on-the-fly form is what she is left standing in front of. Chosen from outside the headshop
// range on purpose — the point is a code our reference has never heard of.
const WEB_EAN  = process.env.PROBE_WEB_EAN || '4000417025005';
const MINTED_B = '2000000999992';

// A probe row from an EARLIER run can be referenced by line_items (an old sandbox cart), and
// then DELETE raises a foreign-key error that reads like a broken test and is not one. Delete
// what is free; retire the rest so it cannot answer a search. Never touch line_items — those
// are somebody's transactions, even in a sandbox.
const cleanup = () => {
  psql(`delete from product_barcodes where product_id in
          (select id from products where name like '${PROBE}%')`);
  psql(`delete from products p where p.name like '${PROBE}%'
          and not exists (select 1 from line_items li where li.product_id = p.id)`);
  psql(`update products set is_active = false, updated_at = now()
          where name like '${PROBE}%' and is_active`);
};
const rowsProbe = () => parseInt(psql(
  `select count(*) from products where name like '${PROBE}%' and is_active`), 10);
const primaryOf = n => psql(`select coalesce(barcode,'') from products where name='${n}'`);
const aliasesOf = n => psql(`select coalesce(string_agg(pb.barcode,','),'') from product_barcodes pb
                             join products p on p.id=pb.product_id where p.name='${n}'`);

async function newPage(b) {
  const p = await (await b.newContext({ viewport: { width: 1280, height: 1100 } })).newPage();
  p.on('dialog', async d => { await d.accept(); });
  return p;
}

async function login(p) {
  await p.goto(`${ROOT}/pos`, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('button:has-text("Login")', { timeout: 20000 });
  const landed = () => p.waitForFunction(
    () => !!(document.querySelector('#username') || sessionStorage.getItem('pos_token')
             || localStorage.getItem('pos_token')), null, { timeout: 8000 });
  await p.click('button:has-text("Login")');
  try { await landed(); } catch (e) { await p.click('button:has-text("Login")'); await landed(); }
  if (await p.$('#username')) {
    await p.fill('#username', USER);
    await p.fill('#password', PASS);
    await p.click('#kc-login, input[type=submit]');
    await p.waitForURL('**/pos/**', { timeout: 20000 });
  }
  await p.waitForLoadState('networkidle');
  const authed = await p.evaluate(() =>
    !!(sessionStorage.getItem('pos_token') || localStorage.getItem('pos_token')));
  if (!authed) throw new Error(`login did not produce a token: ${p.url()}`);
}

async function waitAlpine(p) {
  await p.waitForFunction(() => {
    const el = document.querySelector('[x-data]');
    if (!el || !window.Alpine) return false;
    try { return !!Alpine.$data(el); } catch (e) { return false; }
  }, null, { timeout: 20000 });
  await p.waitForTimeout(400);
}

async function goto(p, where) {
  await p.goto(`${ROOT}${where}${where.includes('?') ? '&' : '?'}lang=en`);
  await p.waitForLoadState('networkidle');
  await waitAlpine(p);
}

const lazy = p => p.evaluate(() => {
  const d = Alpine.$data(document.querySelector('[x-data]'));
  return { open: d.lazyOpen, query: d.lazyLinkQuery, seed: d.ownedSeed,
           results: (d.lazyLinkResults || []).map(r => r.name),
           createOpen: d.lazyCreateOpen, cart: (d.cart || []).map(c => c.name),
           searchMode: d.searchMode, deptOpen: d.deptOpen, pending: d.pendingBarcode,
           otfOwned: (d.otfOwned || []).map(r => r.name) };
});

async function scan(p, code) {
  await p.locator('button:has-text("Barcode")').first().click();
  await p.fill('input[x-model="barcodeInput"]', code);
  await p.click('button:has-text("Find by Barcode")');
  // the miss fans out to the feed AND the web lookup; both are network
  await p.waitForTimeout(4000);
}

(async () => {
  PACKET_TITLE = psql(`select title from reference_products where barcode='${PACKET_EAN}' limit 1`);
  if (!PACKET_TITLE) {
    console.log(`\nSKIPPED, LOUDLY: ${PACKET_EAN} is not in reference_products on this box.`);
    console.log('This test needs the supplier feed loaded — it asserts the feed names a packet');
    console.log('the scan could not. Load the feed, or set PROBE_EAN to a code that is in it.');
    process.exit(2);
  }
  const inCatalog = parseInt(psql(
    `select count(*) from products where barcode='${PACKET_EAN}'`), 10);
  if (inCatalog) { console.log(`SKIPPED: ${PACKET_EAN} is already a catalogue row here.`); process.exit(2); }

  cleanup();
  // The row we ALREADY OWN — filed, like 91% of this shop, under a code no packet carries.
  const NAME = `${PROBE} ${stamp} ${PACKET_TITLE}`.slice(0, 90);
  psql(`insert into products (id, sku, name, price, barcode, stock_quantity, is_active,
          is_age_restricted, vending_compatible, sync_override, created_at, updated_at)
        values (gen_random_uuid(), '${PROBE}-${stamp}', '${NAME.replace(/'/g, "''")}', 9.90,
                '${MINTED}', 1, true, false, false, false, now(), now())`);

  console.log(`\nprove-no-duplicate-on-a-miss — ${ROOT}`);
  console.log(`  packet   : ${PACKET_EAN}  "${PACKET_TITLE}"  (in the supplier feed, not in the catalogue)`);
  console.log(`  we own   : "${NAME}"  filed under the minted ${MINTED}\n`);

  const browser = await chromium.launch();
  const p = await newPage(browser);
  try {
    await login(p);
    await goto(p, '/pos/scan');
    await scan(p, PACKET_EAN);

    const s = await lazy(p);
    check(s.open, '1  the miss opens the capture panel');
    check((s.query || '').trim().length > 0,
          '2  the catalogue search box carries the packet name', JSON.stringify(s.query));
    const banner = await p.locator('p[x-text*="owned_seed"]').first().isVisible().catch(() => false);
    check(banner, '3  the "you may already have it" banner is on screen');
    check(s.results.some(n => n.startsWith(PROBE)),
          '4  the product we already own is listed', s.results.join(' | ') || '(none)');
    check(s.createOpen === false, '5  the CREATE form stays collapsed');

    // 6/7 — tap the row the way an operator does.
    const before = rowsProbe();
    await p.locator(`div:has-text("${PROBE}")`).locator('visible=true').last().click({ timeout: 5000 })
      .catch(async () => { await p.locator(`span:has-text("${PROBE}")`).first().click(); });
    await p.waitForTimeout(2500);
    check(rowsProbe() === before, '6  tapping it made NO second product row',
          `${before} before, ${rowsProbe()} after`);
    const prim = primaryOf(NAME), al = aliasesOf(NAME);
    check(prim === PACKET_EAN,
          '7  the real EAN is promoted to primary, minted kept as an alias',
          `primary=${prim} aliases=${al}`);
    check(al.split(',').includes(MINTED), '7b the minted code survives for printed shelf labels', al);

    // 8 — the thesis. Scan the same packet again.
    await goto(p, '/pos/scan');
    await scan(p, PACKET_EAN);
    const s2 = await lazy(p);
    check(!s2.open && s2.cart.some(n => n.startsWith(PROBE)),
          '8  scanning that packet again FINDS it — no panel, straight to the cart',
          `panel=${s2.open} cart=${s2.cart.join(' | ') || '(empty)'}`);

    // ── SCENARIO B — the miss the feed cannot name ───────────────────────────────────────
    //
    // Everything above needed the supplier feed to KNOW the packet. That is the lucky case.
    // The ordinary one is a code nobody has: no panel, no seeded name, just the department
    // strip and a create form with the code held in a yellow box. She types what is in her
    // hand and taps Create — and a row we already own, filed under a minted code, gets a
    // twin. These four assertions are the ones that were red before 2026-08-27.
    if (parseInt(psql(`select count(*) from reference_products where barcode='${WEB_EAN}'`), 10)) {
      console.log(`\n  SCENARIO B SKIPPED: ${WEB_EAN} IS in the feed here — it must not be.`);
      console.log('  Set PROBE_WEB_EAN to a real code your reference_products does not hold.\n');
    } else if (parseInt(psql(`select count(*) from products where barcode='${WEB_EAN}'`), 10)) {
      console.log(`\n  SCENARIO B SKIPPED: ${WEB_EAN} is already a catalogue row here.\n`);
    } else {
      const NAME_B = `${PROBE} ${stamp} Ritter Sport Marzipan`;
      psql(`insert into products (id, sku, name, price, barcode, stock_quantity, is_active,
              is_age_restricted, vending_compatible, sync_override, created_at, updated_at)
            values (gen_random_uuid(), '${PROBE}-B-${stamp}', '${NAME_B}', 4.50,
                    '${MINTED_B}', 1, true, false, false, false, now(), now())`);
      console.log(`\n  scenario B — packet ${WEB_EAN} (the feed does NOT know it)`);
      console.log(`  we own   : "${NAME_B}"  filed under the minted ${MINTED_B}\n`);

      await goto(p, '/pos/scan');
      await scan(p, WEB_EAN);
      const b1 = await lazy(p);
      check(b1.open === false && b1.searchMode === 'catalog' && b1.deptOpen === false
            && b1.pending === WEB_EAN,
            '9  the unknown miss leaves the on-the-fly form on screen, holding the code',
            `panel=${b1.open} mode=${b1.searchMode} pending=${b1.pending}`);

      // Type it the way she does — into the name box, not into Alpine.
      await p.fill('input[x-model="otfName"]', `${PROBE} ${stamp} Ritter Sport`);
      await p.waitForTimeout(2500);
      const b2 = await lazy(p);
      const listed = check(b2.otfOwned.some(n => n.startsWith(PROBE)),
            '10 typing the name lists the product we ALREADY OWN',
            b2.otfOwned.join(' | ') || '(none)');
      const bannerB = await p.locator('p[x-text*="otf_owned"]').first().isVisible().catch(() => false);
      check(bannerB, '10b the "you may already have this" line is on screen');

      if (listed) {
        const beforeB = rowsProbe();
        await p.locator(`div:has-text("${NAME_B}")`).locator('visible=true').last()
          .click({ timeout: 5000 })
          .catch(async () => { await p.locator(`span:has-text("${NAME_B}")`).first().click(); });
        await p.waitForTimeout(2500);
        check(rowsProbe() === beforeB, '11 tapping it made NO second product row',
              `${beforeB} before, ${rowsProbe()} after`);
        const boundTo = psql(`select coalesce(p.name,'') from products p
                              join product_barcodes pb on pb.product_id = p.id
                              where pb.barcode = '${WEB_EAN}'`)
                     || psql(`select coalesce(name,'') from products where barcode='${WEB_EAN}'`);
        check(boundTo === NAME_B,
              '12 the scanned code now resolves to the row we already had',
              boundTo || '(bound to nothing)');
      } else {
        bad('11 tapping it made NO second product row', 'skipped — nothing was listed to tap');
        bad('12 the scanned code now resolves to the row we already had', 'skipped');
      }
    }
  } catch (e) {
    bad('run', e.message);
  } finally {
    await browser.close();
    cleanup();
  }
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
