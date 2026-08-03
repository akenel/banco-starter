#!/usr/bin/env python3
"""Live proof that the cash box belongs to the SHOP — two cashiers, one box, one chain.

    python3 scripts/prove-cash-box.py        # against the local dev stack

WHY A SCRIPT. The unit tests pin the decisions (17) and were green before any of this was
wired up. What they cannot reach is the CHAIN: two different logins ringing into one box, the
shop-wide open guard, the blind count actually being blind over HTTP, the slope surviving a
reconcile, and a forced close that a later reader cannot mistake for a real count.

This is also the only way to prove the headline bug is dead, because it needs TWO cashiers:

    Felix opens the box. PAM sells cash into it. Felix reconciles.
    Old behaviour: expected counted only Felix's takings -> variance = Pam's sales.
    Wanted:        expected includes everybody -> variance 0.00.

Walks the whole day:
    1. baseline + the §6 guard          5. X-report (reads, changes nothing)
    2. blind open, then the reveal      6. skim to the safe (paid_out, not an expense)
    3. the shop-wide open guard         7. reconcile -> tomorrow's expected
    4. TWO cashiers, ONE box            8. the slope, then a forced close

Self-cleaning: refunds its own sales and leaves the box closed.
"""
import os
import sys
import uuid
from decimal import Decimal

import httpx

ROOT = os.environ.get("BANCO_URL", "http://localhost:3000").rstrip("/")
KC_ROOT = os.environ.get("BANCO_KC_URL", "http://localhost:8090").rstrip("/")
REALM = os.environ.get("BANCO_REALM", "kc-pos-realm-dev")
BASE = f"{ROOT}/api/v1/pos"
KC = f"{KC_ROOT}/realms/{REALM}/protocol/openid-connect/token"

D = lambda v: Decimal(str(v))
FAILURES: list[str] = []


def check(label, got, want=True):
    ok = (got == want)
    print(f"  {'OK ' if ok else 'FAIL'} {label}: {got}" + ("" if ok else f"   (expected {want})"))
    if not ok:
        FAILURES.append(f"{label}: got {got!r}, expected {want!r}")


def login(user, password):
    r = httpx.post(KC, data={"client_id": "helix_pos_web", "username": user,
                             "password": password, "grant_type": "password"}, timeout=30)
    if r.status_code != 200:
        sys.exit(f"login failed for {user}: {r.status_code} {r.text[:200]}")
    return httpx.Client(headers={"Authorization": f"Bearer {r.json()['access_token']}"}, timeout=30)


def main():
    # Demo realm convention (keycloak/import/realm-export.json): password == username.
    felix = login(os.environ.get("BANCO_USER", "felix"), os.environ.get("BANCO_PASS", "felix"))
    pam = login(os.environ.get("BANCO_USER2", "pam"), os.environ.get("BANCO_PASS2", "pam"))
    print(f"target: {ROOT}\n")

    # --- 0 · put the box in a KNOWN state, AND REMEMBER THE REAL ONE -----------------------
    # This box has a history (the slope is real), so seed a known starting point rather than
    # asserting against whatever the last run happened to leave. Nothing below is meaningful
    # if the chain starts from an unknown number.
    #
    # BUT THE SLOPE IS LOAD-BEARING: whatever this script leaves as the last reconcile becomes
    # TOMORROW MORNING'S EXPECTED. Left alone, a run would hand the next person to open the
    # shop a variance of a few hundred francs to explain -- caused entirely by a test. So
    # capture the real figure now and put it back at the end.
    _prev = felix.get(f"{BASE}/shift/last").json()
    ORIGINAL_SLOPE = (_prev or {}).get("counted_cash") if (_prev or {}).get("ok") else None
    _st0 = felix.get(f"{BASE}/settings/1").json()
    ORIGINAL_BASELINE = _st0.get("cash_box_float")
    print(f"(will restore: slope -> {ORIGINAL_SLOPE}, baseline -> {ORIGINAL_BASELINE})\n")
    if (felix.get(f"{BASE}/shift/current").json() or {}).get("open"):
        cur = felix.get(f"{BASE}/shift/current").json()
        felix.post(f"{BASE}/shift/close", json={"counted_cash": cur["expected_cash"],
                                                "note": "prove-cash-box.py: clearing a stale box"})
    st = felix.get(f"{BASE}/settings/1").json()
    felix.put(f"{BASE}/settings/1", json={**st, "cash_box_float": "600.00",
                                          "cash_box_float_note": "prove-cash-box.py baseline"})
    seed = felix.post(f"{BASE}/shift/open",
                      json={"opening_float": "600.00", "confirm_off_baseline": True,
                            "note": "prove-cash-box.py: seeding a known slope"})
    if seed.status_code != 200:
        sys.exit(f"could not seed the box: {seed.status_code} {seed.text[:300]}")
    felix.post(f"{BASE}/shift/close", json={"counted_cash": "600.00",
                                            "note": "prove-cash-box.py: seed reconcile"})

    prods = felix.get(f"{BASE}/products", params={"limit": 50}).json()
    rows = prods.get("items", prods) if isinstance(prods, dict) else prods
    prod = next((p for p in rows if float(p.get("price") or 0) > 0
                 and not p.get("is_age_restricted")), None)
    if not prod:
        sys.exit("no sellable product — seed the demo treats first")
    unit = D(prod["price"])

    def sell(client, qty=1):
        r = client.post(f"{BASE}/sales", json={
            "client_uuid": str(uuid.uuid4()),
            "lines": [{"product_id": prod["id"], "quantity": qty}],
            "payment_method": "cash", "amount_tendered": "50.00", "age_verified": True})
        if r.status_code not in (200, 201):
            sys.exit(f"sale failed: {r.status_code} {r.text[:300]}")
        return r.json()["id"]

    # --- 1 · the baseline guard (§6) -------------------------------------------------------
    print("1 · the baseline guard (§6) — the CHF 0.05 that started this")
    r = felix.post(f"{BASE}/shift/open", json={"opening_float": "0.05"})
    check("a wildly-off count is QUESTIONED, not accepted", r.status_code, 409)
    check("...and it ASKS rather than refuses",
          (r.json().get("detail") or {}).get("code"), "off_baseline")
    r = felix.post(f"{BASE}/shift/open", json={"opening_float": "0.05",
                                               "confirm_off_baseline": True,
                                               "note": "box really was emptied overnight"})
    check("confirming it lets the shop open ANYWAY (a guard, not a lock)", r.status_code, 200)
    felix.post(f"{BASE}/shift/close", json={"counted_cash": "0.05",
                                            "note": "prove-cash-box.py: undo the guard probe"})
    # restore the slope to 600 for the rest of the walk
    felix.post(f"{BASE}/shift/open", json={"opening_float": "600.00",
                                           "confirm_off_baseline": True,
                                           "note": "prove-cash-box.py: restore"})
    felix.post(f"{BASE}/shift/close", json={"counted_cash": "600.00", "note": "restore"})

    r = felix.post(f"{BASE}/shift/open", json={"opening_float": "600.00"})
    check("a count matching last night opens with no fuss at all", r.status_code, 200)
    opened = r.json()
    check("...and needed no note", opened["within_tolerance"], True)
    print(f"     opened by {opened['opened_by']} · float {opened['opening_float']} "
          f"· expected {opened['expected']}\n")

    # --- 2 · the shop-wide open guard ------------------------------------------------------
    print("2 · one box, one open shift")
    r = pam.post(f"{BASE}/shift/open", json={"opening_float": "600.00"})
    check("a SECOND person cannot open a second drawer on the same box", r.status_code, 409)
    check("...and is told who has it", "felix" in str(r.json().get("detail", "")))
    print()

    # --- 3 · two cashiers, one box — THE headline bug --------------------------------------
    print("3 · TWO cashiers selling into ONE box")
    t_felix = sell(felix)
    t_pam = sell(pam)          # the sale the old code could not see
    cur = pam.get(f"{BASE}/shift/current").json()
    check("Pam sees the box Felix opened (it is not 'her drawer')", cur["open"], True)
    check("expected includes BOTH cashiers' takings",
          D(cur["cash_sales"]), (unit * 2).quantize(D("0.01")))
    check("expected = float + everyone's cash",
          D(cur["expected_cash"]), D("600.00") + (unit * 2).quantize(D("0.01")))
    print(f"     float 600.00 + cash {cur['cash_sales']} = expected {cur['expected_cash']}\n")

    # --- 4 · the X-report reads without changing anything ----------------------------------
    print("4 · X-report (§7.2) — a read that changes nothing")
    x = felix.get(f"{BASE}/shift/x-report").json()
    check("it reports the live position", D(x["expected_cash"]), D(cur["expected_cash"]))
    check("it is explicitly non-resetting", x["resetting"], False)
    still = felix.get(f"{BASE}/shift/current").json()
    check("the box is still open afterwards", still["open"], True)
    check("...and nothing about it moved", D(still["expected_cash"]), D(x["expected_cash"]))
    print()

    # --- 5 · a skim to the safe is not an expense ------------------------------------------
    print("5 · skim to the safe (§7.3)")
    r = pam.post(f"{BASE}/shift/paid", json={"kind": "paid_out", "amount": "500.00",
                                             "reason": "box getting heavy",
                                             "reason_code": "to_safe"})
    check("any cashier may move money to the safe", r.status_code, 200)
    r2 = pam.post(f"{BASE}/shift/paid", json={"kind": "paid_in", "amount": "10.00",
                                              "reason": "nope", "reason_code": "to_safe"})
    check("'to safe' cannot be an inbound movement", r2.status_code, 400)
    x = felix.get(f"{BASE}/shift/x-report").json()
    check("the skim is tracked separately from petty cash", D(x["to_safe_total"]), D("500.00"))
    after = felix.get(f"{BASE}/shift/current").json()
    check("and it still leaves the drawer (expected drops by 500)",
          D(after["expected_cash"]), D(cur["expected_cash"]) - D("500.00"))
    print()

    # --- 6 · reconcile, and the slope ------------------------------------------------------
    print("6 · reconcile — and the counted total becomes tomorrow's expected")
    expected_now = D(after["expected_cash"])
    r = pam.post(f"{BASE}/shift/close", json={"counted_cash": str(expected_now),
                                              "note": ""})
    check("PAM may reconcile a box FELIX opened", r.status_code, 200)
    rep = r.json()
    check("...and both names are recorded", (rep["opened_by"], rep["reconciled_by"]),
          ("felix", "pam"))
    check("a real count is marked verified", rep["counted_verified"], True)
    check("variance 0.00 on a shared box that used to report Pam's sales as missing",
          D(rep["variance"]), D("0.00"))
    print(f"     opened by {rep['opened_by']} · reconciled by {rep['reconciled_by']} "
          f"· counted {rep['counted_cash']}\n")

    # --- 7 · the slope, next morning -------------------------------------------------------
    print("7 · next morning — blind count, then the reveal")
    short_by = D("5.00")   # plausible vs the slope, but well outside tolerance
    counted_today = expected_now - short_by
    r = felix.post(f"{BASE}/shift/open", json={"opening_float": str(counted_today)})
    check("a morning difference must be explained", r.status_code, 400)
    check("...against YESTERDAY's reconcile",
          (r.json().get("detail") or {}).get("code"), "opening_variance")
    r = felix.post(f"{BASE}/shift/open", json={"opening_float": str(counted_today),
                                               "note": "5 short vs last night — see Felix"})
    check("with a note, the shop opens and trades", r.status_code, 200)
    rev = r.json()
    check("the reveal quotes last night's counted total (the slope)",
          D(rev["expected"]), expected_now)
    check("the variance belongs to yesterday", D(rev["variance"]), -short_by)
    check("TODAY's float is what was really counted, not what was expected",
          D(rev["opening_float"]), counted_today)
    check("the chain is walkable", rev["previous_shift_id"], rep["shift_id"])
    print(f"     counted {rev['opening_float']} vs expected {rev['expected']} "
          f"({rev['variance']}) — today starts from the real number\n")

    # --- 8 · the forced close --------------------------------------------------------------
    print("8 · forced close (§5) — must never read as a count")
    r = pam.post(f"{BASE}/shift/force-close", json={"reason": "nobody at the shop to count it"})
    check("a cashier may NOT force-close (the one manager gate)", r.status_code in (401, 403), True)
    r = felix.post(f"{BASE}/shift/force-close", json={"reason": "short"})
    check("a token reason is refused", r.status_code, 400)
    r = felix.post(f"{BASE}/shift/force-close",
                   json={"reason": "prove-cash-box.py — nobody at the shop to count the box"})
    check("a manager may, with a real reason", r.status_code, 200)
    fc = r.json()
    check("variance is 0.00 — which is exactly the danger", D(fc["variance"]), D("0.00"))
    check("SO it is flagged unverified in its own column", fc["counted_verified"], False)
    check("...and marked as forced", fc["forced_close"], True)
    # The COLUMN is what any report must key off (a note can be short, or edited later). The
    # wording is checked too, but loosely — it was deliberately shortened from a 450-character
    # audit essay to one sentence a person can read at 8am, and it may be reworded again.
    check("the note still says it in words", "Never counted" in fc["variance_note"])
    print()

    # --- cleanup ---------------------------------------------------------------------------
    print("cleaning up")
    for tid in (t_felix, t_pam):
        felix.post(f"{BASE}/transactions/{tid}/refund",
                   json={"reason": "prove-cash-box.py self-cleanup"})

    # Put the CHAIN back. Without this the next person to open the shop is told to explain a
    # variance this script invented -- the single most disruptive thing a test can leave behind
    # on a trading shop, precisely because the slope is designed to carry forward.
    if ORIGINAL_SLOPE is not None:
        felix.post(f"{BASE}/shift/open", json={
            "opening_float": ORIGINAL_SLOPE, "confirm_off_baseline": True,
            "note": "prove-cash-box.py: restoring the slope this test moved"})
        felix.post(f"{BASE}/shift/close", json={
            "counted_cash": ORIGINAL_SLOPE,
            "note": "prove-cash-box.py: slope restored — NOT a physical count"})
        now_slope = (felix.get(f"{BASE}/shift/last").json() or {}).get("counted_cash")
        check("the slope is back where the run found it", D(now_slope), D(ORIGINAL_SLOPE))
    # And the baseline, so a shop's own setting is not left as the test's 600.
    felix.put(f"{BASE}/settings/1", json={**_st0, "cash_box_float": ORIGINAL_BASELINE,
                                          "cash_box_float_note": _st0.get("cash_box_float_note")})
    check("the baseline setting is back to the shop's own",
          felix.get(f"{BASE}/settings/1").json().get("cash_box_float"), ORIGINAL_BASELINE)
    check("the box is left closed", (felix.get(f"{BASE}/shift/current").json() or {}).get("open"), False)

    print()
    if FAILURES:
        print("NOT PROVEN:")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("PROVEN — one box, everybody sells into it, and the chain holds overnight.")


if __name__ == "__main__":
    main()
