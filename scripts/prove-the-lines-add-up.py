#!/usr/bin/env python3
"""Live proof that a sale's LINES add up to its HEADER — on a discounted sale.

    python3 scripts/prove-the-lines-add-up.py        # against the local dev stack

WHY (2026-09-19). Four completed sales on the live shop had
`transactions.tax_amount` and `sum(line_items.vat_amount)` disagreeing by up to
80 rappen — every one of them discounted, and no undiscounted sale ever wrong.

The header was always RIGHT. It comes from split_vat(), which prorates the
cart-wide discount across the lines. The LINES were written when each item was
scanned, before any cart-wide discount existed, and nothing ever went back to
tell them. So the money charged was correct and the paperwork under it was not.

That matters because `/reports/product-sales` SUMS THE LINES
(pos_router.py:7654). A report that states more VAT than the books declare is
exactly the kind of thing that makes an inspector open every transaction.

WHAT THIS RINGS, and it rings REAL SALES:
    1. discounted, via POST /sales        <- THE PATH THE SHOP ACTUALLY USES
    2. cart -> checkout, no discount         (the other write path I changed; see below)
    3. NOT discounted, via POST /sales       (the control: it was always right,
                                              and a fix that breaks it is not a fix)
    4. all three re-read from the table      (the reconciliation, exactly as run on prod)

ON TEST 2, because the gap is deliberate and not laziness. checkout.html posts to
POST /api/v1/pos/sales — the direct path — so that is the live one. The cart ->
/transactions/{id}/checkout path is real, is still wired, and I changed it too,
but a CART-WIDE DISCOUNT CANNOT REACH IT: CheckoutRequest has no discount field
and there is no PATCH/PUT on /transactions, so the API offers no way to set one.
Test 2 therefore rings it undiscounted and proves only that I did not break it.
If a discount ever becomes reachable there, this is the test to extend first.

It refunds its own sales at the end. A refunded row is still permanent history —
Banco never deletes line items — so know that before pointing it anywhere real.

LOCAL ONLY, deliberately. It reads `line_items.vat_amount` straight from Postgres
because the API does not expose it (the receipt prints a rate CODE, not an
amount), and it writes money. If you want it against another shop, read it first
and decide for yourself.
"""
import os
import subprocess
import sys
import uuid
from decimal import Decimal

import httpx

ROOT = os.environ.get("BANCO_URL", "http://localhost:3000").rstrip("/")
REALM = os.environ.get("BANCO_REALM", "kc-pos-realm-dev")
KC_ROOT = os.environ.get("BANCO_KC_URL", "http://localhost:8090").rstrip("/")
USER = os.environ.get("BANCO_USER", "felix")
PASS = os.environ.get("BANCO_PASS", "felix")
PGC = os.environ.get("BANCO_PG_CONTAINER", "banco-postgres")

if not ROOT.startswith(("http://localhost", "http://127.0.0.1")):
    sys.exit(f"REFUSING: {ROOT} is not localhost, and this script rings real sales.")

BASE = f"{ROOT}/api/v1/pos"
KC = f"{KC_ROOT}/realms/{REALM}/protocol/openid-connect/token"

D = lambda v: Decimal(str(v or 0))
FAILURES: list[str] = []


def check(label, got, want):
    ok = got == want
    print(f"  {'✅' if ok else '❌'} {label}: {got}" + ("" if ok else f"   (expected {want})"))
    if not ok:
        FAILURES.append(f"{label}: got {got}, expected {want}")
    return ok


def line_vat_sum(txn_id) -> Decimal:
    """Sum of the STORED per-line VAT. Straight from the table, because that column is
    what the report sums and what an inspector would be shown."""
    out = subprocess.run(
        ["docker", "exec", "-i", PGC, "psql", "-U", "helix_user", "-d", "helix_db", "-At",
         "-c", f"SELECT coalesce(round(sum(vat_amount),2),0) FROM line_items "
               f"WHERE transaction_id = '{txn_id}';"],
        capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"psql failed: {out.stderr[:300]}")
    return D(out.stdout.strip())


def main():
    print(f"target: {ROOT}  (realm {REALM}, user {USER})\n")
    r = httpx.post(KC, data={"client_id": "helix_pos_web", "username": USER,
                             "password": PASS, "grant_type": "password"}, timeout=30)
    if r.status_code != 200 or "access_token" not in r.json():
        sys.exit(f"login failed: {r.status_code} {r.text[:300]}")
    c = httpx.Client(headers={"Authorization": f"Bearer {r.json()['access_token']}"}, timeout=30)

    prods = c.get(f"{BASE}/products", params={"limit": 50}).json()
    rows = prods.get("items", prods) if isinstance(prods, dict) else prods
    # TWO different prices, so the cart has lines of unequal size: an equal-sized cart can hide
    # a proration bug, because the wrong answer and the right one round to the same rappen.
    sellable = [p for p in rows if float(p.get("price") or 0) > 1 and not p.get("is_age_restricted")]
    if len(sellable) < 2:
        sys.exit("need two sellable, non-age-restricted products — seed the demo catalogue first")
    a, b = sellable[0], sellable[1]
    print(f"selling: {a['name']} @ {a['price']}  +  {b['name']} @ {b['price']}\n")

    cur = c.get(f"{BASE}/shift/current")
    if not (cur.status_code == 200 and (cur.json() or {}).get("open")):
        rr = c.post(f"{BASE}/shift/open", json={"opening_float": "200.00"})
        if rr.status_code not in (200, 201):
            sys.exit(f"could not open a drawer: {rr.status_code} {rr.text[:300]}")

    rung = []

    def via_sales(discount_pct):
        body = {"client_uuid": str(uuid.uuid4()),
                "lines": [{"product_id": a["id"], "quantity": 2},
                          {"product_id": b["id"], "quantity": 1}],
                "payment_method": "twint", "discount_percent": discount_pct,
                "age_verified": True}
        rr = c.post(f"{BASE}/sales", json=body)
        if rr.status_code not in (200, 201):
            sys.exit(f"sale failed: {rr.status_code} {rr.text[:400]}")
        rung.append(rr.json()["id"])
        return c.get(f"{BASE}/transactions/{rr.json()['id']}").json()

    def via_checkout(discount_pct):
        rr = c.post(f"{BASE}/transactions", json={"client_uuid": str(uuid.uuid4())})
        if rr.status_code not in (200, 201):
            sys.exit(f"open cart failed: {rr.status_code} {rr.text[:400]}")
        tid = rr.json()["id"]
        for prod, qty in ((a, 2), (b, 1)):
            ri = c.post(f"{BASE}/transactions/{tid}/items",
                        json={"product_id": prod["id"], "quantity": qty})
            if ri.status_code not in (200, 201):
                sys.exit(f"add item failed: {ri.status_code} {ri.text[:400]}")
        rc = c.post(f"{BASE}/transactions/{tid}/checkout",
                    json={"payment_method": "twint", "discount_percent": discount_pct,
                          "age_verified": True})
        if rc.status_code not in (200, 201):
            sys.exit(f"checkout failed: {rc.status_code} {rc.text[:400]}")
        rung.append(tid)
        return c.get(f"{BASE}/transactions/{tid}").json()

    try:
        print("1 · DISCOUNTED, via POST /sales — the direct sale path")
        t1 = via_sales(15)
        h1, l1 = D(t1["tax_amount"]), line_vat_sum(t1["id"])
        print(f"    subtotal {t1['subtotal']} · discount {t1['discount_amount']} · total {t1['total']}")
        check("the lines add up to the header", l1, h1)
        print()

        print("2 · cart -> checkout, NO discount — the other path I touched (see the header)")
        t2 = via_checkout(0)
        h2, l2 = D(t2["tax_amount"]), line_vat_sum(t2["id"])
        print(f"    subtotal {t2['subtotal']} · discount {t2['discount_amount']} · total {t2['total']}")
        check("the lines add up to the header", l2, h2)
        print()

        print("3 · NO DISCOUNT — the control, which was never broken")
        t3 = via_sales(0)
        h3, l3 = D(t3["tax_amount"]), line_vat_sum(t3["id"])
        check("the lines still add up to the header", l3, h3)
        check("and nothing was discounted", D(t3["discount_amount"]), D("0"))
        print()

        print("4 · RECONCILIATION — the same query that found this on the live shop")
        # An assertion that cannot fail is worse than none (LESSON #4). The first version of
        # this step compared the report's VAT with `>=`, which is true for any report on any
        # day, fix or no fix. This re-reads every sale we just rang and counts the ones whose
        # lines do not equal their header — which is exactly the prod query, and which was 4
        # when this bug was found.
        mismatched = []
        for tid in rung:
            hdr = D(c.get(f"{BASE}/transactions/{tid}").json()["tax_amount"])
            if line_vat_sum(tid) != hdr:
                mismatched.append(tid)
        check("sales that do not reconcile", len(mismatched), 0)
    finally:
        # PUT THE DAY BACK. A prover that leaves live sales in the takings poisons every
        # report run after it, and the next person reads the mess as a finding.
        for tid in rung:
            try:
                c.post(f"{BASE}/transactions/{tid}/refund",
                       json={"reason": "prove-the-lines-add-up cleanup"})
            except Exception as e:
                print(f"  ⚠️  could not refund {tid}: {e}")

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} FAILED")
        for f in FAILURES:
            print(f"   - {f}")
        sys.exit(1)
    print("✅ all checks passed — the lines add up to the header on a discounted sale")


if __name__ == "__main__":
    main()
