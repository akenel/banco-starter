#!/usr/bin/env python3
"""Prove the re-scan cleanup path end to end: Pam's rushed till quick-add, then finishing it.

    ⛔ DEV / UAT ONLY. This writes REAL COMPLETED SALES and deletes them again.
       A completed transaction is a line in the Kassenbuch. Never point it at a shop's
       books — even though it cleans up after itself, the audit trail will have seen it.
       Guarded behind BANCO_ALLOW_FAKE_SALES=1 so it cannot run by accident.

Run it:
    BANCO_ALLOW_FAKE_SALES=1 POSTGRES_HOST=localhost POSTGRES_PORT=5442 \
      PYTHONPATH=. python3 scripts/probe-rescan-cleanup.py

What it simulates (Angel, 2026-08-03, playing a cashier):

    a customer spots a new grinder on the counter · the scan misses · Pam types
    "grinder / 15.00" and sells it · "now somebody has to go back and enter it correctly"

Everything in that is correct behaviour, including the ten-second name. The failures were all
downstream, and this checks each of them is really gone:

    1 the SOLD queue put a once-sold row below 37 busier ones (it now leads)
    2 shelf intake reported the re-scan as "✅ already scans correctly" (it now says stub)
    3 "Finish it" reaches exactly one card, even with stale filters in the URL
    4 the catalog header's 18+ counter counts the CATALOGUE, not the 25 rows on screen
    5 a duplicate can be merged from the catalog row, where duplicates are actually seen

Check 3 is here because it CAUGHT a bug the tests missed: the first version of the pid filter
reset the gap clause but left the shelf scope standing, so `?pid=<grinder>&category=Grinders`
returned zero cards — a dead end answering a scan the operator had just made.
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, delete, func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import AsyncSessionLocal                       # noqa: E402
from src.db.models.product_model import ProductModel                # noqa: E402
from src.db.models.line_item_model import LineItemModel             # noqa: E402
from src.db.models.user_model import UserModel                      # noqa: E402
from src.db.models.transaction_model import (                       # noqa: E402
    TransactionModel, TransactionStatus, PaymentMethod)
from src.routes.pos_router import (                                 # noqa: E402
    get_cleanup_queue, catalog_shelf_intake_triage, ShelfIntakeRequest,
    search_products_fast, catalog_merge_products, MergeRequest,
    _find_product_by_any_barcode)

USER = {"username": "probe", "roles": ["manager"]}
# A real EAN, and a real lookup: three shops in three countries return "Champ High White Leaf
# Grinder, 4-part, Ø50mm" for it. That is the whole point — the row says "grinder" and the
# barcode on the packet already knows better.
EAN = "3661075283438"
PREFIX = "PROBE-RESCAN"

made = {"products": [], "txns": []}
checks = []


async def _sweep(db):
    """Delete anything this probe has ever left behind, by PREFIX — not just this run's ids.

    Learned immediately: the first version tore down by tracked id, then a crash mid-run (two
    event loops) killed the teardown, and the NEXT run died on a duplicate SKU from the corpse
    of the last one. A probe that can only run once on a clean database is a probe nobody runs.
    Every row it creates is prefixed for exactly this reason.
    """
    pids = (await db.execute(select(ProductModel.id).where(
        ProductModel.sku.like(f"{PREFIX}%")))).scalars().all()
    tids = (await db.execute(select(TransactionModel.id).where(
        TransactionModel.transaction_number.like(f"{PREFIX}%")))).scalars().all()
    if tids:
        await db.execute(delete(LineItemModel).where(LineItemModel.transaction_id.in_(tids)))
        await db.execute(delete(TransactionModel).where(TransactionModel.id.in_(tids)))
    if pids:
        await db.execute(delete(LineItemModel).where(LineItemModel.product_id.in_(pids)))
        await db.execute(delete(ProductModel).where(ProductModel.id.in_(pids)))
    await db.commit()
    return len(pids), len(tids)


def check(ok, label, detail=""):
    checks.append(bool(ok))
    print(f"  {'✅' if ok else '❌'} {label}" + (f"  ({detail})" if detail else ""))


async def _product(db, **kw):
    p = ProductModel(id=uuid.uuid4(), is_active=True, **kw)
    db.add(p)
    await db.flush()
    made["products"].append(p.id)
    return p


async def _sale(db, cashier_id, product, qty, when, n):
    total = float(product.price) * qty
    t = TransactionModel(
        id=uuid.uuid4(), transaction_number=f"{PREFIX}-{n}", cashier_id=cashier_id,
        status=TransactionStatus.COMPLETED, payment_method=PaymentMethod.CASH,
        subtotal=total, discount_amount=0, tax_amount=0, total=total,
        created_at=when, updated_at=when, completed_at=when)
    db.add(t)
    await db.flush()
    db.add(LineItemModel(id=uuid.uuid4(), transaction_id=t.id, product_id=product.id,
                         quantity=qty, unit_price=product.price, line_total=total))
    await db.flush()
    made["txns"].append(t.id)


async def run():
    async with AsyncSessionLocal() as db:
        stale_p, stale_t = await _sweep(db)
        if stale_p or stale_t:
            print(f"  (cleared {stale_p} product(s) and {stale_t} sale(s) from an earlier run)")
        cashier = (await db.execute(select(UserModel).limit(1))).scalar_one_or_none()
        if cashier is None:
            print("No users in this database — is it seeded?")
            return 1
        now = datetime.now(timezone.utc)

        # The backlog: sold plenty, days ago. Under busiest-first this one wins.
        papers = await _product(db, name=f"{PREFIX} papers", sku=f"{PREFIX}-PAPERS",
                                price=2.00, category="Unsorted", cost=None)
        await _sale(db, cashier.id, papers, 40, now - timedelta(days=6), 1)

        # Pam's grinder: ONE sale, twenty minutes ago, name typed with a customer waiting.
        # The real till mints the SKU as `LZ-<barcode>`; this one carries the probe prefix too so
        # the sweep above can always find it. The BARCODE is the part that has to be authentic —
        # it is what the re-scan looks up, and it is the whole point of the exercise.
        grinder = await _product(db, name="grinder", sku=f"{PREFIX}-LZ-{EAN}", barcode=EAN,
                                 price=15.00, category="Unsorted", cost=None)
        await _sale(db, cashier.id, grinder, 1, now - timedelta(minutes=20), 2)
        await db.commit()
        gid = str(grinder.id)

        print("\n1 · THE ORDER — what just happened has to be reachable")
        busiest = await get_cleanup_queue(mode="sold", sort="busiest", db=db, current_user=USER)
        newest = await get_cleanup_queue(mode="sold", sort="newest", db=db, current_user=USER)
        b_ids = [i["product_id"] for i in busiest["items"]]
        n_ids = [i["product_id"] for i in newest["items"]]
        check(b_ids and b_ids[0] != gid, "busiest-first buries the once-sold row",
              f"grinder at #{b_ids.index(gid)} of {len(b_ids)}")
        check(n_ids and n_ids[0] == gid, "newest-first puts it at the top", "position 0")
        check(newest.get("sort") == "newest", "the response says which order it used")

        g = next(i for i in newest["items"] if i["product_id"] == gid)
        check(g["barcode"] == EAN, "the card carries the barcode", g["barcode"])
        check(g["quality"]["score"] == 0, "and says how finished it really is",
              f"{g['quality']['score']}% · {', '.join(g['quality']['gripes'])}")

        print("\n2 · THE RE-SCAN — scanning fine is not the same as being finished")
        t = await catalog_shelf_intake_triage(ShelfIntakeRequest(raw=EAN), db=db, current_user=USER)
        k = t["known"][0] if t["known"] else {}
        check(t["known_count"] == 1 and t["unknown_count"] == 0,
              "the barcode the till bound resolves on a re-scan")
        check(t["unfinished_count"] == 1, "and is counted as a STUB, not as nothing-to-do")
        check(k.get("is_finished") is False, "the row itself says it is unfinished",
              f"{k.get('ready_score')}% · {', '.join(k.get('ready_gaps', []))}")

        print("\n3 · FINISH IT — one card, whatever else is in the URL")
        one = await get_cleanup_queue(mode="bench", pid=grinder.id, db=db, current_user=USER)
        check(one["count"] == 1 and one["items"][0]["product_id"] == gid,
              "?pid= lands on exactly the packet in your hand", one["items"][0]["name"])
        stale = await get_cleanup_queue(mode="bench", pid=grinder.id, gap="photo",
                                        category="Grinders", period="today",
                                        db=db, current_user=USER)
        check(stale["count"] == 1,
              "a stale shelf/gap/period filter cannot hide the scan", f"{stale['count']} card")
        check(one["items"][0].get("barcode") == EAN,
              "and the card can edit the name AND the barcode", "both fields present")

        # ── the catalog header's 18+ counter ──────────────────────────────────────────
        # Different screen, same failure shape, so it lives with the others: a stat counted
        # over the PAGE while printed beside a catalogue-wide total. Angel's prod header read
        # "Products 5,162 · Age-restricted (18+) 3" for a shop that sells tobacco and CBD.
        # Nothing was misclassified — `ageCount()` filtered the 25 rows on screen.
        print("\n4 · THE 18+ COUNTER — a compliance number must not be page-scoped")
        for i in range(7):
            await _product(db, name=f"{PREFIX} tobacco tin {i}", sku=f"{PREFIX}-AGE-{i}",
                           price=9.90, category="Tobacco", is_age_restricted=True)
        await db.commit()
        truth = (await db.execute(select(func.count()).select_from(ProductModel).where(
            ProductModel.is_active == True,            # noqa: E712
            ProductModel.is_age_restricted == True))).scalar_one()   # noqa: E712

        small = await search_products_fast(q="", category=None, sort=None, limit=2, skip=0, db=db)
        big = await search_products_fast(q="", category=None, sort=None, limit=100, skip=0, db=db)
        page_scoped = sum(1 for i in small["items"] if i.get("is_age_restricted"))
        check(small["age_total"] == truth,
              "a 2-row page still reports every 18+ product in the catalogue",
              f"age_total={small['age_total']} · truth={truth} · the old count said {page_scoped}")
        check(small["age_total"] == big["age_total"],
              "and the number does not move with the page size")
        narrowed = await search_products_fast(q="", category="Tobacco", sort=None,
                                              limit=2, skip=0, db=db)
        check(narrowed["age_total"] <= narrowed["total"] and narrowed["age_total"] >= 7,
              "narrowing to a category narrows the count with it",
              f"{narrowed['age_total']} of {narrowed['total']}")

        # ── the merge, now reachable from the catalog row ─────────────────────────────
        # Angel's real pair, 2026-08-03: "Canna Cannazym 1L" twice — an OTF row at CHF 43.90
        # with a good category and NO barcode, and an LZ row at CHF 21.00 carrying the real
        # EAN but filed under Unsorted. POST /catalog/merge has existed since 2026-07-31 and
        # was reachable only from a shelf-intake card for an UNKNOWN code, so the moment the
        # EAN got bound the tool for duplicates disappeared. It now lives on the catalog row.
        print("\n5 · MERGE A DUPLICATE — survivor keeps its content, the twin donates its code")
        ZYM = "8717524956387"
        otf = await _product(db, name=f"{PREFIX} Canna Cannazym 1L", sku=f"{PREFIX}-OTF-ZYM",
                             price=43.90, category="Grow Supplies", cost=None,
                             description="Bodenverbesserer, erhoeht die Widerstandskraft.")
        lz = await _product(db, name=f"{PREFIX} Canna Cannazym 1L", sku=f"{PREFIX}-LZ-ZYM",
                            barcode=ZYM, price=21.00, category="Unsorted", cost=None)
        await db.commit()
        otf_id, lz_id = otf.id, lz.id

        plan = await catalog_merge_products(
            MergeRequest(keep_id=otf_id, retire_id=lz_id, dry_run=True),
            db=db, current_user=USER)
        check(plan["applied"] is False, "dry_run reports the plan and says it changed nothing")
        check(plan["new_primary_barcode"] == ZYM,
              "the plan moves the REAL EAN onto the survivor", plan["new_primary_barcode"])
        untouched = (await db.execute(select(ProductModel).where(
            ProductModel.id == otf_id))).scalar_one()
        await db.refresh(untouched)
        check(untouched.barcode is None,
              "and the database really is untouched until you confirm")

        res = await catalog_merge_products(
            MergeRequest(keep_id=otf_id, retire_id=lz_id, dry_run=False),
            db=db, current_user=USER)
        check(res["applied"] is True, "applying reports applied=True")
        keep = (await db.execute(select(ProductModel).where(ProductModel.id == otf_id))).scalar_one()
        twin = (await db.execute(select(ProductModel).where(ProductModel.id == lz_id))).scalar_one()
        await db.refresh(keep)
        await db.refresh(twin)
        check(keep.barcode == ZYM, "the survivor now carries the packet's EAN", keep.barcode)
        check(float(keep.price) == 43.90,
              "its PRICE is untouched — a merge never decides what a shop charges",
              f"CHF {float(keep.price):.2f} (the twin's was 21.00)")
        check(keep.category == "Grow Supplies", "its category is untouched too", keep.category)
        check(twin.is_active is False and twin.barcode is None,
              "the twin is switched OFF, never deleted — its line items are somebody's receipt")
        found = await _find_product_by_any_barcode(db, ZYM)
        check(found is not None and found.id == otf_id,
              "and scanning that EAN now lands on the survivor")

    return 0


async def cleanup():
    async with AsyncSessionLocal() as db:
        await _sweep(db)
    # PROVE the cleanup, don't assume it. A probe that leaves a fake sale in the books is worse
    # than no probe at all — and "the delete ran" is not the same claim as "nothing is left".
    async with AsyncSessionLocal() as db:
        prods = (await db.execute(select(ProductModel).where(
            ProductModel.sku.like(f"{PREFIX}%")))).scalars().all()
        txns = (await db.execute(select(TransactionModel).where(
            TransactionModel.transaction_number.like(f"{PREFIX}%")))).scalars().all()
    print("\n6 · PUT IT BACK")
    check(not prods, "no probe products left", f"{len(prods)} found")
    check(not txns, "no probe sales left in the books", f"{len(txns)} found")


async def main_async():
    """ONE event loop for the whole probe. Two `asyncio.run()` calls each build their own loop
    while the engine's pool stays bound to the first, so the cleanup pass died with "attached to
    a different loop" — leaving the fake sales it had just promised to remove. try/finally, so
    the books get put back even when a check raises."""
    try:
        return await run()
    finally:
        await cleanup()


def main():
    if os.environ.get("BANCO_ALLOW_FAKE_SALES") != "1":
        print(__doc__)
        print("REFUSING: set BANCO_ALLOW_FAKE_SALES=1 to run. Never on a shop's live books.")
        return 2
    print("=" * 72)
    print("  RE-SCAN CLEANUP PROBE — writes fake sales, then deletes them")
    print("=" * 72)
    rc = asyncio.run(main_async())
    if rc:
        return rc
    ok, total = sum(checks), len(checks)
    print("\n" + "=" * 72)
    print(f"  {ok}/{total} checks passed" + ("  ✅ PROVEN" if ok == total else "  ❌ SOMETHING IS OFF"))
    print("=" * 72)
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
