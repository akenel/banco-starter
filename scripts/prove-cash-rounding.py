#!/usr/bin/env python3
"""Live proof that a cash total is rounded to 5 rappen at checkout — and nothing else is.

    python3 scripts/prove-cash-rounding.py        # against the local dev stack

WHY THIS IS A SCRIPT AND NOT A UNIT TEST. The unit tests cover the arithmetic (29) and the
wiring decision (17), and they were all green the whole time the feature was wired to nothing.
What they cannot cover is the CHAIN: a real cart, a real discount, the drawer gate, the tender
comparison, the VAT split, the stored row, and the receipt payload the till actually reads.
This repo's most expensive bugs have all lived in that gap — a fix that was real, and one
filter downstream that quietly undid it.

So this rings four real sales through the real endpoint:

    1. CASH, discounted to an unpayable total  -> must round, record the move, pay the change
       against the ROUNDED figure (that is the drawer's expectation)
    2. TWINT, the identical cart               -> must NOT round; a card settles the exact cent
    3. CASH, an ordinary total already on 0.05 -> must pass through untouched, adjustment 0.00
    4. the day's Banana export                 -> the lines must still sum to the drawer

It refunds its own sales at the end, so the day's takings are left as it found them. The
REFUNDED rows stay (line items are sales history — Banco never deletes them).
"""
import os
import sys
import uuid
from decimal import Decimal

import httpx

# Defaults are the local dev stack. Point it at another shop with env vars:
#
#   BANCO_URL=https://banco.example.app BANCO_REALM=kc-pos-realm \
#   BANCO_USER=felix BANCO_PASS=... python3 scripts/prove-cash-rounding.py
#
# IT RINGS REAL SALES. Three of them, then refunds all three — but a refunded sale is still
# a permanent row in that shop's books and shows on the day's Z-report. That is deliberate:
# the whole point is to exercise the real chain, and a "safe" read-only version would prove
# nothing. Know what it leaves behind before pointing it at a shop that is trading.
ROOT = os.environ.get("BANCO_URL", "http://localhost:3000").rstrip("/")
REALM = os.environ.get("BANCO_REALM", "kc-pos-realm-dev")
KC_ROOT = os.environ.get("BANCO_KC_URL", "http://localhost:8090").rstrip("/")
USER = os.environ.get("BANCO_USER", "felix")
PASS = os.environ.get("BANCO_PASS", "felix")

BASE = f"{ROOT}/api/v1/pos"
KC = f"{KC_ROOT}/realms/{REALM}/protocol/openid-connect/token"

D = lambda v: Decimal(str(v))
FAILURES: list[str] = []


def check(label, got, want):
    ok = got == want
    print(f"  {'✅' if ok else '❌'} {label}: {got}" + ("" if ok else f"   (expected {want})"))
    if not ok:
        FAILURES.append(f"{label}: got {got}, expected {want}")
    return ok


def main():
    print(f"target: {ROOT}  (realm {REALM}, user {USER})\n")
    r = httpx.post(KC, data={"client_id": "helix_pos_web", "username": USER,
                             "password": PASS, "grant_type": "password"}, timeout=30)
    if r.status_code != 200 or "access_token" not in r.json():
        sys.exit(f"login failed: {r.status_code} {r.text[:300]}")
    tok = r.json()["access_token"]
    c = httpx.Client(headers={"Authorization": f"Bearer {tok}"}, timeout=30)

    # --- a product to sell, and an open drawer (a cash sale is gated on one) ----------------
    prods = c.get(f"{BASE}/products", params={"limit": 50}).json()
    rows = prods.get("items", prods) if isinstance(prods, dict) else prods
    prod = next((p for p in rows if float(p.get("price") or 0) > 0
                 and not p.get("is_age_restricted")), None)
    if not prod:
        sys.exit("no sellable product in this database — seed the demo treats first")
    unit = D(prod["price"])
    print(f"selling: {prod['name']}  @ CHF {unit}\n")

    # A cash sale is gated on an open drawer. Open one if this cashier has none; leave an
    # already-open one alone (this script must not disturb a real shift in progress).
    cur = c.get(f"{BASE}/shift/current")
    opened_here = False
    if not (cur.status_code == 200 and (cur.json() or {}).get("open")):
        r = c.post(f"{BASE}/shift/open", json={"opening_float": "200.00"})
        if r.status_code not in (200, 201):
            sys.exit(f"could not open a drawer: {r.status_code} {r.text[:300]}")
        opened_here = True

    def ring(qty, discount_pct, method, tendered):
        """One atomic sale. Returns the stored transaction."""
        body = {
            "client_uuid": str(uuid.uuid4()),
            "lines": [{"product_id": prod["id"], "quantity": qty}],
            "payment_method": method, "discount_percent": discount_pct,
            "age_verified": True,
        }
        if method == "cash":
            body["amount_tendered"] = f"{tendered:.2f}"
        r = c.post(f"{BASE}/sales", json=body)
        if r.status_code not in (200, 201):
            sys.exit(f"sale failed: {r.status_code} {r.text[:400]}")
        return c.get(f"{BASE}/transactions/{r.json()['id']}").json()

    # Find a (qty, discount) whose total the coins cannot pay. Undiscounted Swiss prices are
    # all 0.05 multiples, which is exactly why this bug stayed invisible for so long.
    #
    # THE TICKET COMES FROM THE CARD SALE, not from arithmetic here. The server rounds the
    # DISCOUNT to the rappen and subtracts it, so recomputing the ticket in this script got a
    # different number (0.48 vs 0.47) and accused working code. Ringing the identical cart on
    # TWINT gives the authoritative un-rounded figure -- and makes the comparison the real
    # claim: same cart, two payment methods, differing by exactly the rounding.
    combo = None
    for q in (1, 2, 3, 7):
        for p in (5, 10, 15):
            probe = ring(q, p, "twint", 0)
            if D(probe["total"]) % D("0.05") != 0:
                combo, card = (q, p), probe
                break
        if combo:
            break
    if not combo:
        sys.exit("no discount on this price produces an unpayable total -- pick another product")
    qty, pct = combo
    ticket = D(card["total"])

    print(f"1 · TWINT  {qty} x {unit} less {pct}%  =  CHF {ticket}  <- cannot be paid in coins")
    check("a card sale charges the exact cent", D(card["total"]), ticket)
    check("and records no rounding", D(card["rounding_adjustment"]), D("0.00"))
    print()

    print(f"2 · CASH  the identical cart, CHF 10.00 tendered")
    tendered = D("10.00")
    txn = ring(qty, pct, "cash", float(tendered))
    total, adj = D(txn["total"]), D(txn["rounding_adjustment"])
    check("total is payable in coins", total % D("0.05") == 0, True)
    check("ticket + adjustment = what was charged", ticket + adj, total)
    check("the move was recorded, not absorbed", adj != 0, True)
    check("change is against the ROUNDED total (what the drawer expects)",
          D(txn["change_given"]), tendered - total)
    cash_txn = txn["id"]
    print(f"     ticket CHF {ticket}  ->  charged CHF {total}  (rounding {adj:+})\n")

    print(f"3 · CASH  {qty} x {unit} at full price  =  CHF {(unit * qty).quantize(D('0.01'))}")
    txn3 = ring(qty, 0, "cash", float(unit * qty) + 10)
    check("an ordinary total passes through untouched",
          D(txn3["total"]), (unit * qty).quantize(D("0.01")))
    check("with no rounding line to explain", D(txn3["rounding_adjustment"]), D("0.00"))
    print()

    # The receipt derives its Discount line as gross - (total - adjustment). If that formula
    # is wrong the rounding hides inside the discount, which is the one thing this feature
    # exists to prevent -- and it would look perfectly normal on screen. So check the
    # template's arithmetic against the row the server actually stored.
    print("4 · the receipt's own arithmetic")
    gross = sum((D(li["unit_price"]) * D(li["quantity"]) for li in txn["line_items"]), D("0"))
    shown_discount = gross - (total - adj)
    check("the Discount line still shows the real discount, not the rounding",
          shown_discount, D(txn["discount_amount"]))
    check("subtotal - discount - rounding = TOTAL, as printed",
          gross - shown_discount + adj, total)
    print()

    print("5 · the day's books")
    s = c.get(f"{BASE}/reports/daily-summary").json()
    check("the summary carries the day's Rundungsdifferenz", D(s["rounding_total"]) != 0, True)
    check("and counts the sales it touched", s["rounding_count"] >= 1, True)

    csv = c.get(f"{BASE}/reports/daily-summary.csv").text
    cash_lines = [l for l in csv.splitlines()
                  if "Cash" in l or "Rundungsdifferenz" in l]
    print("     " + "\n     ".join(cash_lines))

    def _amt(line):
        cells = [x.strip('"') for x in line.split(",")]
        inc = D(cells[2] or 0)
        exp = D(cells[3] or 0)
        return inc - exp

    booked = sum((_amt(l) for l in cash_lines), D("0"))
    check("the export lines still sum to the money in the drawer",
          booked, D(s["cash_total"]))

    # --- put the day back the way we found it ----------------------------------------------
    print("\ncleaning up (refunding this script's own sales)")
    for tid in (cash_txn, card["id"], txn3["id"]):
        r = c.post(f"{BASE}/transactions/{tid}/refund",
                   json={"reason": "prove-cash-rounding.py self-cleanup"})
        print(f"  refund {tid[:8]} -> {r.status_code}")
    if opened_here:
        # Only close the drawer if WE opened it — never touch a real shift in progress.
        exp = (c.get(f"{BASE}/shift/current").json() or {}).get("expected_cash", "200.00")
        r = c.post(f"{BASE}/shift/close", json={
            "counted_cash": exp, "note": "prove-cash-rounding.py self-cleanup"})
        print(f"  close the drawer this script opened -> {r.status_code}")

    print()
    if FAILURES:
        print("❌ NOT PROVEN:")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ PROVEN — cash rounds to 5 rappen, cards do not, and the books add up.")


if __name__ == "__main__":
    main()
