#!/usr/bin/env python3
"""Live proof that "Export catalog (CSV)" hands the shop its WHOLE catalog, intact.

    python3 scripts/prove-catalog-export.py        # against the local dev stack

WHY THIS IS A SCRIPT AND NOT A UNIT TEST. The failure modes of an export are not in the SQL —
they are in what a spreadsheet does to the bytes afterwards. A unit test asserting
`row[1] == "7610000123456"` passes on a file Excel renders as `7.61E+12`, which is the single
most common way a barcode column comes back destroyed. So this asks the running endpoint for
a real file and reads it back with a real CSV parser, checking the things that actually bite:

  1. EVERY row comes out          — nothing silently capped (the BL-131 worklist caps at 2,000)
  2. the 500-row keyset SEAM      — >500 rows, no row skipped and none repeated
  3. the EAN survives as TEXT     — and so do the BL-90 alias barcodes
  4. a missing cost stays EMPTY   — never a fabricated 0.00 (see the essay on ProductModel.cost)
  5. a nasty string cannot escape — `;`, `"`, a newline and a leading `=` in one product name
  6. the filters mean what they say — `category`, `include_inactive`
  7. a cashier cannot have it     — the file carries cost, therefore every margin in the shop

Rule 4 (break the guard on purpose): each check below is written so it FAILS on the obvious
wrong implementation — a bare `str(barcode)`, an in-memory `LIMIT 500`, `float(cost or 0)`.

The rows it seeds are its own, prefixed EXPORTTEST-<run>, and it deactivates them at the end.
"""
import csv
import io
import sys
import uuid

import httpx

RUN = uuid.uuid4().hex[:6].upper()
BASE = "http://localhost:3000/api/v1/pos"
KC = "http://localhost:8090/realms/kc-pos-realm-dev/protocol/openid-connect/token"

# Enough to cross the 500-row keyset page TWICE, so a seam bug has two chances to show.
BULK = 1100
# NOT an invented label: `create_product` funnels an unknown category through
# `canonicalize_category`, so anything made up here lands as "Unsorted" anyway and a filter
# test against it would be testing nothing. "Unsorted" is also a useful shape — the filter
# check below re-runs on the FRAGMENT "sorte", which must match it the same way the screen does.
CAT = "Unsorted"

# The product name from hell, in one string: a semicolon (the field separator), a double quote
# (the quote char), a newline (the row terminator) and a leading `=` (an Excel formula). If the
# writer is doing its job this lands in ONE cell and Excel shows it as text.
NASTY = '=SUM(A1:A9) "Big" Grinder; 50mm\nsecond line'
def _ean13(body12: str) -> str:
    """A REAL EAN-13, check digit and all — the catalog rejects a wrong one (BL-129), and a
    fake barcode in an export test would prove nothing about a real barcode column anyway."""
    chk = (10 - sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(body12)) % 10) % 10
    return body12 + str(chk)


# Long and numeric — exactly the shape Excel turns into 7.61E+12 if it is exported as a number.
EAN = _ean13("761" + f"{int(RUN, 16) % 1_000_000_000:09d}")
ALIAS = _ean13("400" + f"{int(RUN, 16) % 1_000_000_000:09d}")


def fail(msg):
    print(f"  ❌ {msg}")
    fail.n += 1
fail.n = 0


def ok(msg):
    print(f"  ✅ {msg}")


def token(user, pwd):
    r = httpx.post(KC, data={"client_id": "helix_pos_web", "username": user,
                             "password": pwd, "grant_type": "password"})
    return r.json()["access_token"]


def main():
    mgr = httpx.Client(headers={"Authorization": f"Bearer {token('felix', 'felix')}"}, timeout=120)

    print(f"\n📦 Seeding {BULK} products in category {CAT} …")
    made = []
    for i in range(BULK):
        # SKU is the keyset cursor, so make the order NON-obvious: if the paging were secretly
        # OFFSET-based over a different sort, the seam would still look fine on sorted input.
        sku = f"EXPORTTEST-{RUN}-{(i * 7919) % BULK:05d}"
        # allow_duplicate: "Export probe 1" and "Export probe 11" are near-identical by
        # design (they exist to fill 1,100 rows), which is precisely what the trigram dedup
        # guard is there to refuse. Nothing about the export depends on them being distinct.
        body = {"sku": sku, "name": f"Export probe {i}", "price": 9.90,
                "category": CAT, "stock_quantity": 0}
        if i == 0:
            body.update({"name": NASTY, "barcode": EAN, "description": 'He said "hi"; then left'})
        if i == 1:
            body.update({"price_tiers": [{"min_qty": 3, "unit_price": 4.50},
                                         {"min_qty": 10, "unit_price": 4.00}],
                         "tier_mode": "per_unit"})
        if i == 2:
            body.update({"cost": 3.25})          # the ONLY seeded row with a cost
        r = mgr.post(f"{BASE}/products", params={"allow_duplicate": "true"}, json=body)
        if r.status_code not in (200, 201):
            # Clean up before dying. A bare sys.exit() here left two live probe rows in the
            # catalogue — one of them named `=SUM(A1:A9) "Big" Grinder; 50mm` — and they were
            # still sitting in the product list two runs later, showing up in an export I was
            # reading as if it were real data. A test that FAILS is fine; a test that fails and
            # leaves its litter in the shop's catalogue is not.
            print(f"  seed {sku} -> {r.status_code} {r.text[:200]}")
            print(f"  🧹 removing the {len(made)} row(s) already seeded …")
            for _, pid in made:
                mgr.delete(f"{BASE}/products/{pid}")
            sys.exit(1)
        made.append((sku, r.json()["id"]))
    print(f"  seeded {len(made)}")

    # BL-90 alias barcode on the nasty row — the second code the packet carries.
    nasty_sku, nasty_id = made[0]
    ra = mgr.post(f"{BASE}/products/{nasty_id}/barcodes", json={"barcode": ALIAS})
    alias_seeded = ra.status_code in (200, 201)
    if not alias_seeded:
        print(f"  (alias seed -> {ra.status_code} {ra.text[:160]} — alias check will be skipped)")

    # One DISCONTINUED row, to prove include_inactive actually changes the file.
    dead_sku, dead_id = made[-1]
    mgr.delete(f"{BASE}/products/{dead_id}")

    def pull(**params):
        r = mgr.get(f"{BASE}/catalog/export.csv", params=params)
        assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
        raw = r.content
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
        return r, raw, rows[0], rows[1:]

    print("\n📄 The whole catalog …")
    resp, raw, hdr, rows = pull()
    idx = {c: i for i, c in enumerate(hdr)}
    mine = [r for r in rows if r[idx["sku"]].startswith(f"EXPORTTEST-{RUN}-")]

    # 0. The bytes a spreadsheet needs before it will open the file correctly.
    if raw[:3] == b"\xef\xbb\xbf":
        ok("UTF-8 BOM present (Excel reads accents/umlauts on double-click)")
    else:
        fail("no UTF-8 BOM — Excel will mangle non-ASCII names")
    if b"\r\n" in raw:
        ok("CRLF line endings")
    else:
        fail("no CRLF line endings")

    # 1 + 2. Every row, exactly once — the cap and the keyset seam in one assertion.
    expected = {s for s, _ in made} - {dead_sku}
    got = [r[idx["sku"]] for r in mine]
    missing, dupes = expected - set(got), len(got) - len(set(got))
    if not missing and not dupes and len(got) == len(expected):
        ok(f"all {len(expected)} active rows present, none repeated "
           f"(crossed the 500-row seam {len(expected) // 500}×)")
    else:
        fail(f"row set wrong: {len(missing)} missing, {dupes} repeated, "
             f"{len(got)} rows for {len(expected)} products")
    if resp.headers.get("X-Banco-Row-Count", "").isdigit() and \
            int(resp.headers["X-Banco-Row-Count"]) == len(rows):
        ok(f"X-Banco-Row-Count header agrees with the file ({len(rows)} rows)")
    else:
        fail(f"X-Banco-Row-Count={resp.headers.get('X-Banco-Row-Count')} "
             f"but the file has {len(rows)} rows")

    nasty = next((r for r in mine if r[idx["sku"]] == nasty_sku), None)
    if nasty is None:
        fail("the seeded edge-case row is not in the file — skipping its checks")
        return report(mgr, made)

    # 3. The EAN, still an EAN.
    if nasty[idx["barcode"]] == "'" + EAN:
        ok(f"EAN exported as TEXT ('{EAN}) — Excel cannot turn it into 7.61E+12")
    else:
        fail(f"barcode cell is {nasty[idx['barcode']]!r}, expected \"'{EAN}\"")
    if alias_seeded:
        if "'" + ALIAS in nasty[idx["alt_barcodes"]]:
            ok(f"BL-90 alias barcode {ALIAS} came along in alt_barcodes")
        else:
            fail(f"alias {ALIAS} missing from alt_barcodes={nasty[idx['alt_barcodes']]!r}")

    # 4. A missing cost is EMPTY, never a fabricated zero.
    costed = next((r for r in mine if r[idx["sku"]] == made[2][0]), None)
    blanks = [r for r in mine if r[idx["cost_CHF"]] == ""]
    zeros = [r for r in mine if r[idx["cost_CHF"]] == "0.00"]
    if costed and costed[idx["cost_CHF"]] == "3.25":
        ok("a real cost exports as 3.25")
    else:
        fail(f"seeded cost 3.25 came out as {costed and costed[idx['cost_CHF']]!r}")
    if blanks and not zeros:
        ok(f"{len(blanks)} rows with no cost export as EMPTY, not 0.00")
    else:
        fail(f"{len(zeros)} rows invented a 0.00 cost")

    # 5. The nasty string is one cell, and defused.
    if nasty[idx["name"]].startswith("'="):
        ok("a name starting with `=` is defused with a leading apostrophe")
    else:
        fail(f"formula-injection name not defused: {nasty[idx['name']]!r}")
    if ";" in nasty[idx["name"]] and '"' in nasty[idx["name"]]:
        ok("`;` and `\"` survive inside the cell without splitting the row")
    else:
        fail(f"separator/quote lost from the name: {nasty[idx['name']]!r}")
    if "\n" not in nasty[idx["name"]] and len(nasty) == len(hdr):
        ok("an embedded newline cannot break the row into two")
    else:
        fail("embedded newline leaked into the file")

    # The price ladder, as something a human can check at a glance.
    tiered = next((r for r in mine if r[idx["sku"]] == made[1][0]), None)
    if tiered and tiered[idx["price_tiers"]] == "3@4.50 | 10@4.00":
        ok("price ladder renders as `3@4.50 | 10@4.00`, not raw JSON")
    else:
        fail(f"price_tiers cell is {tiered and tiered[idx['price_tiers']]!r}")

    # 6. The filters — checked against the SCREEN, not against my own expectations.
    #
    # This is the check that earned its place. The export first shipped with
    # `lower(category) = lower(:category)` while the catalog screen's `/search` uses
    # `category ILIKE '%:category%'`. Every self-consistent assertion passed. The two only
    # disagree when one category name CONTAINS another ("Bongs" inside "Pipes & Bongs") —
    # so the only way to see it is to ask both endpoints the same question and diff them.
    # `substr` below is deliberately a fragment of a real category for exactly that reason.
    print("\n🔎 Filters — the file must agree with the list on screen …")
    for label in (CAT, CAT[2:-2]):
        _, _, chdr, cat_rows = pull(category=label)
        cidx = {c: i for i, c in enumerate(chdr)}
        seen = {r[cidx["sku"]] for r in cat_rows}
        # page the screen's own endpoint to the end, so this is a SET comparison, not a count
        screen, skip = set(), 0
        while True:
            data = mgr.get(f"{BASE}/search",
                           params={"q": "", "category": label, "limit": 200, "skip": skip}).json()
            items = data.get("items") or []
            if not items:
                break
            screen |= {i["sku"] for i in items}
            skip += 200
        if seen == screen:
            ok(f"?category={label!r}: export and the catalog screen agree exactly "
               f"({len(seen)} rows)")
        else:
            fail(f"?category={label!r}: export has {len(seen)} rows, the screen shows "
                 f"{len(screen)} — {len(screen - seen)} on screen but NOT in the file, "
                 f"{len(seen - screen)} in the file but not on screen")
    if dead_sku not in {r[idx["sku"]] for r in rows}:
        ok("a discontinued product is NOT in the default export")
    else:
        fail("a discontinued product leaked into the default export")
    _, _, _, all_rows = pull(include_inactive="true")
    if dead_sku in {r[idx["sku"]] for r in all_rows}:
        ok("?include_inactive=true brings the discontinued row back")
    else:
        fail("include_inactive=true did not include the discontinued row")

    # 7. The door.
    print("\n🔒 Who may take it …")
    cashier = httpx.Client(headers={"Authorization": f"Bearer {token('pam', 'pam')}"}, timeout=30)
    rc = cashier.get(f"{BASE}/catalog/export.csv")
    if rc.status_code in (401, 403):
        ok(f"a cashier gets {rc.status_code} — cost stays behind the manager door")
    else:
        fail(f"a CASHIER downloaded the cost column: {rc.status_code}")
    ra = httpx.get(f"{BASE}/catalog/export.csv", timeout=30)
    if ra.status_code in (401, 403):
        ok(f"no token gets {ra.status_code}")
    else:
        fail(f"the catalog is downloadable with NO TOKEN: {ra.status_code}")

    report(mgr, made)


def report(mgr, made):
    print(f"\n🧹 Deactivating {len(made)} probe rows …")
    for _, pid in made:
        mgr.delete(f"{BASE}/products/{pid}")
    print()
    if fail.n:
        print(f"❌ {fail.n} check(s) FAILED")
        sys.exit(1)
    print("✅ ALL CHECKS PASSED — the shop can take its catalog with it.")


if __name__ == "__main__":
    main()
