#!/usr/bin/env python3
"""Live proof that the 18+ gate LEAVES A RECORD — clearances and refusals.

    BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py

    ⛔ DEV / UAT ONLY. This writes REAL COMPLETED SALES. A completed transaction is a
       line in the Kassenbuch. Never point it at the shop's books. Guarded behind
       BANCO_ALLOW_FAKE_SALES=1 so it cannot run by accident. It refunds its own sales
       and leaves the drawer as it found it, but the audit trail will have seen them.

WHY A SCRIPT. Commit d4144d4 shipped with an honest admission in its own message:
"NOT yet exercised against a live database — sandbox next." Everything in it is a
WRITE that happens inside a request, and two of those writes have failure modes no
unit test can see:

  1. THE REFUSAL IS WRITTEN IN ITS OWN SESSION, deliberately, because the caller
     raises 400 one line later and get_db_session() does not roll back explicitly —
     it closes, discarding the transaction. If that isolation is wrong, every refusal
     is silently lost and NOTHING ERRORS. The most valuable evidence in the gate is
     exactly the evidence most easily dropped.
  2. THE CLEARANCE BASIS IS ASSIGNED TO AN ORM OBJECT and depends on the surrounding
     commit. A green test that mocks the session proves nothing about that.

So this asks the live stack the question an inspector would ask: not "does the gate
refuse?" (it always did) but "can you SHOW me it refused?"

What it walks:
    1. a clean cart               -> 'not_required', never NULL
    2. an attested walk-in        -> 'cashier_attest' + the line snapshot
    3. a refusal                  -> 400 AND a row that outlives the 400
    3b. a refusal                 -> does NOT get filed against the next customer's sale
    3c. refused, then sold        -> the two records JOIN on the cart
    4. a member with a DOB        -> 'member_dob'
    5. a legacy member, no DOB    -> 'member_confirmed' (the weaker basis, counted separately)
    6. a member under 18 by DOB   -> refused even WITH cashier attestation
    7. the evidence is append-only -> UPDATE and DELETE both bite

Self-cleaning for SALES only. THE EVIDENCE ROWS IT WRITES ARE PERMANENT — append-only
is the whole point, so nothing can tidy them away afterwards. It therefore rings as
'ralph', never 'pam', so a human reading the log can always tell the machine's noise
from their own testing:

    select ... from age_check_event where cashier = 'pam'   -- what a PERSON did
"""
import os
import subprocess
import sys
import uuid
from datetime import date

import httpx

ROOT = os.environ.get("BANCO_URL", "http://localhost:3000").rstrip("/")
KC_ROOT = os.environ.get("BANCO_KC_URL", "http://localhost:8090").rstrip("/")
REALM = os.environ.get("BANCO_REALM", "kc-pos-realm-dev")
BASE = f"{ROOT}/api/v1/pos"
CUST = f"{ROOT}/api/v1/customers"
KC = f"{KC_ROOT}/realms/{REALM}/protocol/openid-connect/token"

PGUSER = os.environ.get("POSTGRES_USER", "helix_user")
PGDB = os.environ.get("POSTGRES_DB", "helix_db")

FAILURES: list[str] = []
TAG = "prove-age-evidence"


def check(label, got, want=True):
    ok = (got == want)
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: {got!r}" + ("" if ok else f"   (expected {want!r})"))
    if not ok:
        FAILURES.append(f"{label}: got {got!r}, expected {want!r}")
    return ok


def sql(query: str) -> str:
    """Read the evidence back.

    THIS IS THE POINT AND ALSO THE FINDING. Nothing in src/ reads any of these columns —
    no endpoint, no template, no report. The only way to see the shop's 18+ evidence
    today is a psql prompt, which is why this probe needs one. See the note at the end.
    """
    out = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres",
         "psql", "-U", PGUSER, "-d", PGDB, "-tAc", query],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"psql failed: {out.stderr[:300]}")
    return out.stdout.strip()


def login(user, password):
    r = httpx.post(KC, data={"client_id": "helix_pos_web", "username": user,
                             "password": password, "grant_type": "password"}, timeout=30)
    if r.status_code != 200:
        sys.exit(f"login failed for {user}: {r.status_code} {r.text[:200]}")
    return httpx.Client(headers={"Authorization": f"Bearer {r.json()['access_token']}"}, timeout=30)


def main():
    if os.environ.get("BANCO_ALLOW_FAKE_SALES") != "1":
        print(__doc__)
        print("REFUSING: set BANCO_ALLOW_FAKE_SALES=1 to run. Never on a shop's live books.")
        return 2

    print("=" * 74)
    print("  18+ EVIDENCE PROBE — the gate always refused; can it PROVE it?")
    print("=" * 74)

    # RINGS AS 'ralph', NOT 'pam' — deliberately, and it is not cosmetic.
    # age_check_event is append-only, so every refusal this probe writes is PERMANENT
    # and sits in the same list a human is reading. Angel hit this immediately: he ran
    # the D2 query mid-test and saw twelve refusals that were all mine, timestamped
    # four minutes earlier, attributed to 'pam' — the account he was testing on. There
    # is no way to tell them apart and no way to delete them.
    # So the machine rings as ralph (manager + cashier in the demo realm) and leaves
    # 'pam' to mean a person actually stood at a till. `cashier` becomes the filter:
    #     ... where cashier = 'pam'   -> what a HUMAN did
    till = login(os.environ.get("BANCO_USER", "ralph"), os.environ.get("BANCO_PASS", "ralph"))
    felix = login(os.environ.get("BANCO_USER2", "felix"), os.environ.get("BANCO_PASS2", "felix"))

    # --- the two products: one 18+, one not -------------------------------------
    prods = till.get(f"{BASE}/products", params={"limit": 200}).json()
    items = prods.get("items", prods) if isinstance(prods, dict) else prods
    gated = next((p for p in items if p.get("is_age_restricted")), None)
    plain = next((p for p in items if not p.get("is_age_restricted")), None)
    if not gated or not plain:
        sys.exit("need one 18+ product and one normal one in the catalogue (TREAT-GUMMY / TREAT-LIGHTER)")
    print(f"\n  18+ product : {gated['name']}  ({gated.get('product_class')})")
    print(f"  normal      : {plain['name']}")

    made_txns: list[str] = []

    def sell(client, product, *, age_verified=False, customer_id=None):
        body = {
            # client_uuid is the idempotency key — required, and the reason a sale posted
            # twice by a flaky tablet connection only rings once.
            "client_uuid": str(uuid.uuid4()),
            "lines": [{"product_id": product["id"], "quantity": 1}],
            "payment_method": "twint", "amount_tendered": "50.00",
            "age_verified": age_verified,
        }
        if customer_id:
            body["customer_id"] = customer_id
        r = client.post(f"{BASE}/sales", json=body)
        if r.status_code in (200, 201):
            made_txns.append(r.json()["id"])
        return r

    def outcome_of(txn_id):
        return sql(f"select coalesce(age_check_outcome,'<NULL>') from transactions where id='{txn_id}'")

    def refusals():
        return int(sql("select count(*) from age_check_event where outcome='refused'"))

    # --- 1 · a clean cart must say 'not_required', never NULL --------------------
    print("\n1 · A CLEAN CART — silence is not a record")
    r = sell(till, plain)
    check("a normal sale completes", r.status_code in (200, 201), True)
    if r.status_code in (200, 201):
        check("clean cart records 'not_required' (NULL cannot tell 'no 18+ line' from "
              "'nobody checked')", outcome_of(r.json()["id"]), "not_required")

    # --- 2 · attested walk-in ----------------------------------------------------
    print("\n2 · AN ATTESTED WALK-IN — the cashier's word, on the record")
    r = sell(till, gated, age_verified=True)
    check("18+ sale with attestation completes", r.status_code in (200, 201), True)
    if r.status_code in (200, 201):
        tid = r.json()["id"]
        check("basis recorded as 'cashier_attest'", outcome_of(tid), "cashier_attest")
        check("the LINE carries the 18+ snapshot (re-classifying the product next year "
              "must not rewrite what this sale meant)",
              sql(f"select coalesce(was_age_restricted::text,'<NULL>') from line_items "
                  f"where transaction_id='{tid}'"), "true")

    # --- 3 · the refusal must OUTLIVE the 400 ------------------------------------
    print("\n3 · A REFUSAL — the separate session is the whole ballgame")
    before = refusals()
    r = sell(till, gated, age_verified=False)
    check("18+ sale with no attestation is REFUSED (400)", r.status_code, 400)
    after = refusals()
    check("the refusal SURVIVED the 400 (written in its own session — a shared one "
          "would be discarded when get_db_session closes)", after - before, 1)
    if after > before:
        row = sql("select outcome||' | '||coalesce(product_class,'-')||' | '||coalesce(cashier,'-') "
                  "from age_check_event order by occurred_at desc limit 1")
        print(f"       newest evidence row: {row}")
        check("no buyer identity stored (FADP — prove the gate bit, do not file the person)",
              sql("select count(*) from information_schema.columns where table_name='age_check_event' "
                  "and column_name in ('customer_id','buyer','real_name','email')"), "0")

    # --- 3b · the refusal must not be filed against SOMEBODY ELSE'S SALE ---------
    # Angel's sandbox run, 2026-08-12. This is a REGRESSION TEST for a real defect:
    # txn_ref was filled from `TXN-{today}-{count+1}`, computed from COMMITTED
    # transactions. A refusal never commits, so it never consumed its number and the
    # NEXT sale took it — 12 of 13 refusals "belonged" to a completed sale, three of
    # those with no 18+ line at all. A false link in a compliance record is worse
    # than no link: it reads as authoritative.
    print("\n3b · THE REFUSAL MUST NOT LAND ON THE NEXT CUSTOMER'S SALE")
    r = sell(till, gated, age_verified=False)
    check("an 18+ customer is turned away", r.status_code, 400)
    ref_txn, ref_cart = (sql(
        "select coalesce(txn_ref,'<NULL>')||'|'||coalesce(cart_ref,'<NULL>') "
        "from age_check_event order by occurred_at desc limit 1") + "|").split("|")[:2]
    check("the refusal stores NO transaction number (none exists yet on /sales)",
          ref_txn, "<NULL>")
    check("the refusal DOES identify the cart it happened on", ref_cart != "<NULL>", True)

    # now ring an unrelated sale — the one that used to inherit the refusal
    r = sell(till, plain)
    if r.status_code in (200, 201):
        nxt = r.json()["transaction_number"]
        print(f"       next customer's unrelated sale: {nxt}")
        check("that sale carries NO refusal (the exact bug Angel found)",
              sql(f"select count(*) from age_check_event where txn_ref='{nxt}'"), "0")

    # and the join that SHOULD work: refused, then the same cart completed
    print("\n3c · REFUSED, THEN SOLD ANYWAY — the pattern an inspector cares about")
    same_cart = str(uuid.uuid4())
    body = {"client_uuid": same_cart,
            "lines": [{"product_id": gated["id"], "quantity": 1}],
            "payment_method": "twint", "amount_tendered": "50.00", "age_verified": False}
    check("cart is refused", till.post(f"{BASE}/sales", json=body).status_code, 400)
    body["age_verified"] = True          # the cashier ticks the box and retries
    r = till.post(f"{BASE}/sales", json=body)   # the till REUSES the uuid on a retry
    if r.status_code in (200, 201):
        made_txns.append(r.json()["id"])
        check("the same cart then completes", True, True)
        check("refusal and sale JOIN on the cart — 'turned away, then sold' is now "
              "queryable for the first time",
              sql(f"select count(*) from age_check_event e join transactions t "
                  f"on t.client_uuid::text = e.cart_ref where e.cart_ref='{same_cart}'"), "1")

    # --- 4/5 · the two member bases, split on purpose ----------------------------
    print("\n4 · A MEMBER WITH A DATE OF BIRTH vs 5 · A LEGACY MEMBER WITH A TICKED BOX")
    print("       Both clear the sale. Only one is evidence an inspector would accept.")
    suffix = uuid.uuid4().hex[:6]
    people = {}
    for label, payload in {
        "adult_dob": {"handle": f"probe_dob_{suffix}", "birthdate": "1990-05-04",
                      "age_confirmed": True},
        "legacy": {"handle": f"probe_legacy_{suffix}", "age_confirmed": True},
        "minor_dob": {"handle": f"probe_minor_{suffix}",
                      "birthdate": date.today().replace(year=date.today().year - 15).isoformat(),
                      "age_confirmed": True},
    }.items():
        rr = felix.post(CUST, json=payload)
        if rr.status_code not in (200, 201):
            print(f"  SKIP  could not enrol {label}: {rr.status_code} {rr.text[:120]}")
        else:
            people[label] = rr.json()["id"]

    if "adult_dob" in people:
        r = sell(till, gated, customer_id=people["adult_dob"])
        check("member with a DOB clears", r.status_code in (200, 201), True)
        if r.status_code in (200, 201):
            check("basis is 'member_dob' — rests on a date", outcome_of(r.json()["id"]), "member_dob")

    if "legacy" in people:
        r = sell(till, gated, customer_id=people["legacy"])
        check("legacy member (no DOB, box ticked) clears", r.status_code in (200, 201), True)
        if r.status_code in (200, 201):
            check("basis is 'member_confirmed' — the WEAKER basis, kept separate so it "
                  "can be counted", outcome_of(r.json()["id"]), "member_confirmed")

    # --- 6 · DOB beats attestation ----------------------------------------------
    print("\n6 · A PROVEN MINOR — no attestation may override a date of birth")
    if "minor_dob" in people:
        before = refusals()
        r = sell(till, gated, age_verified=True, customer_id=people["minor_dob"])
        check("under-18 member REFUSED even with the cashier attesting", r.status_code, 400)
        check("and that refusal is on the record too", refusals() - before, 1)

    # --- 7 · the evidence cannot be edited ---------------------------------------
    print("\n7 · APPEND-ONLY — a verdict that can be edited is not evidence")
    print("       (commit caaab67: the first version used REVOKE, and a table OWNER keeps")
    print("        full rights, so the protection was a comforting no-op.)")
    for tbl, col, val in (("age_check_event", "outcome", "cleared"),
                          ("compliance_check_run", "verdict", "pass")):
        if sql(f"select count(*) from {tbl}") == "0":
            print(f"  SKIP  {tbl} is empty — a FOR EACH ROW trigger needs a row to fire on")
            continue
        for op in (f"update {tbl} set {col}='{val}'", f"delete from {tbl}"):
            out = subprocess.run(
                ["docker", "compose", "exec", "-T", "postgres",
                 "psql", "-U", PGUSER, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c", op],
                capture_output=True, text=True)
            check(f"{op.split()[0].upper()} on {tbl} is refused", out.returncode != 0, True)

    # --- cleanup: refund every sale this probe rang ------------------------------
    print("\n8 · CLEANUP — refunding the sales this probe rang")
    for tid in made_txns:
        rr = felix.post(f"{BASE}/transactions/{tid}/refund",
                        json={"reason": f"{TAG} teardown"})
        if rr.status_code not in (200, 201):
            print(f"  WARN  could not refund {tid}: {rr.status_code} {rr.text[:100]}")
    print(f"       {len(made_txns)} sale(s) refunded. Evidence rows stay — they are append-only.")

    # --- the verdict --------------------------------------------------------------
    print("\n" + "=" * 74)
    if FAILURES:
        print(f"  ❌ {len(FAILURES)} FAILURE(S)")
        for f in FAILURES:
            print(f"     - {f}")
    else:
        print("  ✅ ALL CHECKS PASSED — the gate refuses AND can prove it.")
    print("=" * 74)
    print("""
  ⚠️  WHAT THIS PROBE CANNOT FIX, and a human must see:

      Every check above read the evidence with `psql`, because THAT IS THE ONLY WAY
      TO READ IT. grep src/ for age_check_outcome, was_age_restricted or
      age_check_event and every hit is a WRITE. No endpoint, no template, no report.

      This is the repo's most repeated bug (cash_box_float, the force-close,
      /catalog/merge, honest confidence, best_match_score) — and it lands harder here,
      because the entire purpose of this work is that someone can be SHOWN the record.
      The seed SQL itself calls "records stored in editable folders" a standing
      nonconformity; records reachable only from a database prompt are not better.
""")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
