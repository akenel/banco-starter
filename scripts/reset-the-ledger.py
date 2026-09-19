#!/usr/bin/env python3
"""Clear the REHEARSAL ledger — sales only — after exporting it.

    python3 scripts/reset-the-ledger.py              # show the plan, change nothing
    python3 scripts/reset-the-ledger.py --yes        # export, then delete

WHY THIS EXISTS (2026-09-19). `banco.wolfhold.app` is PRE-PROD: go-live is a cutover to a
fresh box, and the project's own note says it plainly — **guard the catalogue like production,
treat the ledger as a rehearsal**. After months of testing the ledger held 63 sales of which
six carried a VAT fault that has since been fixed at the write path (162f03c). Angel's call:
clear them so the reconciliation query means something instead of always showing the same
historic ghosts.

ORDER MATTERS, AND IT IS NOT NEGOTIABLE. The fix landed and was proven on a NEW discounted
sale BEFORE this was run. Clearing first would have deleted the only real examples of the bug
and left "0 mismatches" looking green while the write path was still broken — a green summary
over an unchecked box.

WHAT IT DELETES, in foreign-key order (line_items and payments are NO ACTION, not CASCADE,
so a bare `DELETE FROM transactions` fails — the database protects itself here):

    payments  ->  line_items  ->  transactions

AGE CHECKS ARE NOT DELETED, AND THE DATABASE IS THE ONE THAT SAYS SO. The first version of
this script tried. Postgres refused, from a trigger nobody in the conversation remembered:

    trg_ace_append_only  BEFORE DELETE OR UPDATE ON age_check_event
    "compliance evidence is append-only: DELETE is not permitted. A verdict that can be
     edited is not evidence — to correct a wrong one, run the check again. The newer row
     supersedes it by timestamp and the mistake stays visible."

Worth spelling out, because the reasoning in the room went the other way. `age_check_event.
txn_ref` is PLAIN TEXT with no foreign key, so clearing the sales orphans those rows rather
than removing them — and "a compliance record pointing at a deleted sale looks like evidence
and is not" is a fair argument for clearing both. The system's answer is better: the ID check
happened. A person looked at a document and made a call, and that is true whether or not the
sale it belonged to still exists. Evidence outlives the transaction. Do not try to route
around this trigger; it is doing its job.

WHAT IT NEVER TOUCHES, and each for a reason:

    audit_log        13k+ rows, and most of it is CATALOGUE history — real work, not sales
    products         the catalogue is guarded like production, always
    customers        loyalty balances are not rehearsal data
    cash_shifts      the drawer history, including every balanced count so far
    cash_movements   pay-in / pay-out belong to the drawer, not to a sale

The open drawer is left exactly as it is. Its expected cash simply becomes float + movements
once the sales beneath it are gone; whoever counts it next closes it normally.

IT EXPORTS FIRST AND REFUSES TO DELETE IF THE EXPORT DID NOT LAND. Those six broken rows are
the only real examples of that fault anyone will ever have.
"""
import os
import subprocess
import sys
from datetime import datetime

PGC = os.environ.get("BANCO_PG_CONTAINER", "banco-postgres")
DB = os.environ.get("BANCO_PG_DB", "helix_db")
DBUSER = os.environ.get("BANCO_PG_USER", "helix_user")
OUTDIR = os.environ.get("BANCO_EXPORT_DIR", os.path.expanduser("~/banco-ledger-exports"))

# FK order. Do not reorder without re-reading the constraints.
DOOMED = ["payments", "line_items", "transactions"]
SPARED = ["audit_log", "products", "customers", "cash_shifts", "cash_movements",
          "age_check_event"]
# Exported for context even though it is never deleted — reading the sales without the ID
# checks that went with them tells half the story.
EXPORT = DOOMED + ["age_check_event"]


def psql(sql: str) -> str:
    out = subprocess.run(
        ["docker", "exec", "-i", PGC, "psql", "-U", DBUSER, "-d", DB, "-At", "-c", sql],
        capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"psql failed: {out.stderr.strip()[:400]}")
    return out.stdout.strip()


def counts(tables):
    return {t: int(psql(f"SELECT count(*) FROM {t};") or 0) for t in tables}


def main():
    go = "--yes" in sys.argv
    print(f"container: {PGC}  ·  db: {DB}\n")

    before = counts(DOOMED)
    spared = counts(SPARED)

    print("WILL DELETE (in this order):")
    for t in DOOMED:
        print(f"    {t:<18} {before[t]:>6} rows")
    print("\nWILL NOT TOUCH:   (age_check_event is append-only — the DB enforces it)")
    for t in SPARED:
        print(f"    {t:<18} {spared[t]:>6} rows")

    # The reconciliation, so the state being destroyed is on the record.
    bad = psql("""SELECT count(*) FROM transactions tr
                  WHERE (SELECT round(sum(li.vat_amount),2) FROM line_items li
                          WHERE li.transaction_id = tr.id) IS DISTINCT FROM tr.tax_amount;""")
    print(f"\n  of those sales, {bad} do not reconcile (header VAT vs sum of line VAT)")

    if not go:
        print("\nDRY RUN — nothing changed. Re-run with --yes to export and delete.")
        return

    if sum(before.values()) == 0:
        print("\nNothing to do — the ledger is already empty.")
        return

    # ---- export FIRST, and prove it landed --------------------------------------------
    os.makedirs(OUTDIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(OUTDIR, f"ledger-{stamp}.sql")
    args = ["docker", "exec", "-i", PGC, "pg_dump", "-U", DBUSER, "-d", DB, "--data-only"]
    for t in EXPORT:
        args += ["--table", t]
    with open(path, "w") as fh:
        out = subprocess.run(args, stdout=fh, stderr=subprocess.PIPE, text=True)
    if out.returncode != 0:
        sys.exit(f"EXPORT FAILED, nothing deleted: {out.stderr.strip()[:400]}")
    size = os.path.getsize(path)
    if size < 1024:
        sys.exit(f"EXPORT LOOKS EMPTY ({size} bytes), nothing deleted: {path}")
    print(f"\n✅ exported {size:,} bytes -> {path}")

    # ---- delete, in FK order ----------------------------------------------------------
    for t in DOOMED:
        psql(f"DELETE FROM {t};")
        print(f"   cleared {t}")

    after = counts(DOOMED)
    still = counts(SPARED)
    print("\nAFTER:")
    for t in DOOMED:
        print(f"    {t:<18} {after[t]:>6} rows")
    bad_rows = [t for t, n in after.items() if n]
    kept_ok = all(still[t] == spared[t] for t in SPARED)
    print(f"\n  spared tables unchanged: {'yes' if kept_ok else 'NO — LOOK AT THIS'}")
    if bad_rows:
        sys.exit(f"❌ rows remain in {bad_rows}")
    print(f"\n✅ ledger cleared. The export is your only copy: {path}")


if __name__ == "__main__":
    main()
