#!/usr/bin/env python3
"""Make every placeholder price 999.99, so it cannot hide among the real ones.

2026-08-07, Angel: "I've got some at ninety nine and others at nine hundred and ninety nine.
They should all be tuned up ... then it's really obvious, they stick out like a sore thumb."

He is right, and `UNVERIFIED_PRICES` already says why: 99.00 is a plausible price for a bong or
a vaporizer, so it can hide among real ones. 999.99 cannot be anything but a flag.

⚠️ WHICH 99.00 ROWS, THOUGH — the whole point of this script.

A blanket `UPDATE ... WHERE price = 99.00` would have destroyed 34 real prices. The 99.00
population splits cleanly in two:

    39  ITEM-  created 2026-08-05   Angel's placeholders   -> convert
     1  LZ-    created 2026-08-05   shelf intake, same day -> convert
    34  TAM-   created 2026-07-07   the July Tamar import  -> LEAVE ALONE

The TAM- rows are `Blaze Gear Titan 455mm`, `Dragon Bong Gold 40cm`, 400-470mm percolator bongs,
CBD oils. Bongs in this catalogue average CHF 78.64 and run to 590. And the price histogram
settles it — 99.00 is an ordinary retail price point, not a spike:

     79.00  31    89.00  23    99.00  34   119.00  27   129.00  19

If 99.00 were a placeholder marker it would tower over its neighbours. It does not. So the
selector here is PROVENANCE (sku prefix + created_at), never the price alone.

This is the 2026-08-02 lesson in a new coat: two rows can look identical in the database and mean
completely different things, and the disagreement is the evidence. Smoothing it over destroys it.

Run with --write to apply; default is a dry run. Prints an exact undo.
"""
import argparse
import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, "/app")

from src.db.database import AsyncSessionLocal  # noqa: E402

# Angel's placeholders: created during his own sessions, never from the July supplier import.
SELECT_MINE = """
    FROM products
    WHERE price = 99.00
      AND (sku LIKE 'ITEM-%' OR sku LIKE 'LZ-%' OR sku LIKE 'OTF-%' OR sku LIKE 'SKU-%')
      AND created_at >= DATE '2026-08-01'
"""


async def main(write: bool) -> int:
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text(
            f"SELECT id, sku, name, category, created_at {SELECT_MINE} ORDER BY sku"))).fetchall()

        kept = (await db.execute(text("""
            SELECT count(*) FROM products WHERE price = 99.00
              AND NOT (
                (sku LIKE 'ITEM-%' OR sku LIKE 'LZ-%' OR sku LIKE 'OTF-%' OR sku LIKE 'SKU-%')
                AND created_at >= DATE '2026-08-01')
        """))).scalar()

        print(f"\n=== {'CONVERTING' if write else 'WOULD CONVERT (dry run)'}: "
              f"{len(rows)} row(s)  99.00 -> 999.99 ===")
        for r in rows:
            print(f"  {r.sku:<26} {r.name[:46]:<46} [{(r.category or '')[:16]}] "
                  f"{r.created_at:%Y-%m-%d}")

        print(f"\n=== LEFT ALONE: {kept} row(s) still at 99.00 ===")
        print("    The July Tamar import. 99.00 is a real price point there "
              "(79:31  89:23  99:34  119:27  129:19) — converting them would")
        print("    have thrown away 34 genuine supplier prices with no undo.")

        if write and rows:
            res = await db.execute(text(f"UPDATE products SET price = 999.99, updated_at = now() "
                                        f"WHERE id IN (SELECT id {SELECT_MINE})"))
            await db.commit()
            print(f"\n  ✅ updated {res.rowcount} row(s)")
            print("  Undo:")
            print("    UPDATE products SET price = 99.00 WHERE sku IN ("
                  + ", ".join(f"'{r.sku}'" for r in rows) + ");")

        after = (await db.execute(text(
            "SELECT price, count(*) FROM products WHERE price IN (99.00, 999.99) "
            "GROUP BY price ORDER BY price"))).fetchall()
        print("\n  placeholder prices now: "
              + ", ".join(f"{p} × {n}" for p, n in after))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply; default is a dry run")
    raise SystemExit(asyncio.run(main(ap.parse_args().write)))
