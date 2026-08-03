#!/usr/bin/env python3
"""Live proof that the merge's name alias makes a product findable by its PACKET name.

    python3 scripts/prove-name-alias.py        # against the local dev stack

WHY THIS IS A SCRIPT AND NOT A UNIT TEST. The match runs on `pg_trgm` (`similarity`,
`word_similarity`), which the sqlite test database has no answer for — so the unit tests can
cover the WRITER (`record_name_alias`, 10 tests) and never the reader. That gap is exactly
where this fix broke the first time: the alias was written perfectly, the SQL matched it at
1.000, and a downstream brand filter comparing the query against the product's HEADLINE name
threw the row away. Every unit test was green. Only calling the live endpoint showed it.

So this walks the whole chain the fix runs in — create, merge, search — and creates then
removes its own throwaway rows. Re-run it after touching `_name_match_candidates`,
`record_name_alias`, `brands_conflict` or `_product_size`.

The pair is chosen so the DE<->EN folding CANNOT bridge it — "Purize Xtra Slim Charcoal
Filters" shares no word with "Aktivkohlefilter 6mm 50er Beutel". So after the merge
deactivates the twin, the ONLY reason the survivor can still be found by the packet name
is the alias row. If the alias is not written, the after-search must come back empty.
"""
import json
import uuid

import httpx

# A fresh SKU per run. `DELETE /products/{id}` DEACTIVATES rather than removes — line items are
# somebody's sales history — so the rows from the last run are still sitting there holding their
# SKU, and a fixed one would 409 on the second run.
RUN = uuid.uuid4().hex[:6].upper()

BASE = "http://localhost:3000/api/v1/pos"
KC = "http://localhost:8090/realms/kc-pos-realm-dev/protocol/openid-connect/token"

DE = "Aktivkohlefilter 6mm 50er Beutel"          # the wholesale row that survives
EN = "Purize Xtra Slim Charcoal Filters 50pcs"   # the packet name, hand-typed at the counter


def main():
    tok = httpx.post(KC, data={"client_id": "helix_pos_web", "username": "felix",
                               "password": "felix", "grant_type": "password"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    c = httpx.Client(headers=h, timeout=30)

    def mk(sku, name, barcode):
        r = c.post(f"{BASE}/products", json={
            "sku": sku, "name": name, "price": 4.90, "barcode": barcode,
            "category": "accessories", "stock_quantity": 0})
        if r.status_code not in (200, 201):
            print(f"  create {name!r} -> {r.status_code} {r.text[:300]}")
            return None
        return r.json()["id"]

    def candidates(q):
        r = c.post(f"{BASE}/catalog/match-candidates", json={"name": q})
        if r.status_code != 200:
            return f"HTTP {r.status_code} {r.text[:200]}"
        d = r.json()
        rows = d if isinstance(d, list) else d.get("candidates", d.get("matches", []))
        return [(x.get("name"), round(float(x.get("score", x.get("sim", 0))), 3)) for x in rows]

    print("── setup ──")
    keep_id = mk(f"ZZTEST-{RUN}-DE", DE, "2000000499001")      # minted, as the July import left it
    retire_id = mk(f"ZZTEST-{RUN}-EN", EN, "7640183261763")    # the real EAN off the packet
    print(f"  keep   {keep_id}  {DE}")
    print(f"  retire {retire_id}  {EN}")
    if not keep_id or not retire_id:
        return

    print("\n── BEFORE the merge: search the PACKET name ──")
    before = candidates(EN)
    print(f"  {before}")

    print("\n── dry run ──")
    r = c.post(f"{BASE}/catalog/merge",
               json={"keep_id": keep_id, "retire_id": retire_id, "dry_run": True})
    print(f"  HTTP {r.status_code}")
    print("  name_alias:", json.dumps(r.json().get("name_alias"), ensure_ascii=False))

    print("\n── apply ──")
    r = c.post(f"{BASE}/catalog/merge",
               json={"keep_id": keep_id, "retire_id": retire_id, "dry_run": False})
    print(f"  HTTP {r.status_code}")
    print("  name_alias:", json.dumps(r.json().get("name_alias"), ensure_ascii=False))

    print("\n── AFTER the merge: the twin is deactivated. Search the PACKET name again ──")
    after = candidates(EN)
    print(f"  {after}")

    hit = [n for n, _ in after if n == DE]
    print("\n" + ("✅ PROVEN — the German row answers to the English packet name."
                  if hit else
                  "❌ NOT PROVEN — the packet name finds nothing. The alias is not reaching search."))

    # Leave the catalogue as we found it. A prover that silently seeds two fake products is a
    # prover nobody runs twice.
    print("\n── cleanup ──")
    for pid in (retire_id, keep_id):
        r = c.delete(f"{BASE}/products/{pid}")
        print(f"  deactivate {pid} -> {r.status_code}")
    print("  (deactivated, not removed — they keep their SKU. Purge with:\n     DELETE FROM products WHERE sku LIKE 'ZZTEST-%';)")
    return 0 if hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
