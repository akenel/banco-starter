#!/usr/bin/env python3
# ============================================================================
# adopt-images — pull every hotlinked product picture into OUR storage.
#
#   docker exec banco-app python /tmp/adopt-images.py --limit 20      # DRY RUN
#   docker exec banco-app python /tmp/adopt-images.py --apply         # the lot
#
# WHY. Angel: "we should grab that image at the time we bind the EAN — and
# download it too." Capture does that now; this is the back-catalogue.
#
# A cover pointing at somebody else's server means the shop does not own its own
# catalogue — the premise of this whole project — and it fails silently months
# later. Metrop MR2's agrowstore.hu cover now 403s to EVERYONE: gone from the
# label, the postcard and the product page, with no copy ever taken. It also
# pings a third party every time a till renders a row.
#
# Reuses _copy_external_image_to_storage, the helper written for exactly this
# ("so we own the bytes instead of hotlinking a URL that may rot").
#
# SAFE BY CONSTRUCTION: dry-run default, one at a time with a delay, skips
# anything already ours, and the copy helper never raises — a picture that
# cannot be fetched leaves the row exactly as it was.
#
# Must run INSIDE the app container: it needs MinIO, Pillow and the app's
# session factory.
# ============================================================================
import argparse
import asyncio
import sys

sys.path.insert(0, "/app")

C = {"grn": "\033[32m", "yel": "\033[33m", "red": "\033[31m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


async def main(args):
    from sqlalchemy import text
    from src.db.database import AsyncSessionLocal as async_session_maker
    from src.routes.pos_router import _copy_external_image_to_storage

    async with async_session_maker() as db:
        rows = (await db.execute(text(
            "SELECT id, sku, name, image_url FROM products "
            "WHERE is_active AND image_url LIKE 'http%' "
            "ORDER BY sku" + (f" LIMIT {int(args.limit)}" if args.limit else "")
        ))).all()

    total = len(rows)
    print(f"{C['b']}Adopt hotlinked pictures into our own storage{C['x']}  "
          f"{C['dim']}({'APPLY' if args.apply else 'dry run'} · {total} products · "
          f"{args.delay}s apart){C['x']}\n")

    if not args.apply:
        hosts = {}
        for _, _, _, u in rows:
            h = (u or "").split("//", 1)[-1].split("/", 1)[0]
            hosts[h] = hosts.get(h, 0) + 1
        for h, n in sorted(hosts.items(), key=lambda x: -x[1]):
            print(f"  {n:>6}  {h}")
        mins = round(total * (args.delay + 1.2) / 60)
        print(f"\n{C['dim']}Dry run — nothing written. ~{mins} min to do all {total}."
              f" Re-run with --apply.{C['x']}")
        return 0

    ok = fail = 0
    fails_in_a_row = 0
    async with async_session_maker() as db:
        for i, (pid, sku, name, url) in enumerate(rows, 1):
            product = (await db.execute(text(
                "SELECT id, image_url FROM products WHERE id = :i"), {"i": pid})).first()
            if product is None:
                continue

            class _P:      # the helper only needs .id and .image_url
                pass
            p = _P(); p.id = pid; p.image_url = url

            stored = await _copy_external_image_to_storage(db, p, url)
            if stored:
                ok += 1
                fails_in_a_row = 0
                print(f"  {C['grn']}✓{C['x']} [{i}/{total}] {sku:<14} {name[:32]}")
            else:
                fail += 1
                fails_in_a_row += 1
                print(f"  {C['yel']}–{C['x']} [{i}/{total}] {sku:<14} {name[:32]}  "
                      f"{C['dim']}kept the external URL{C['x']}")
                if fails_in_a_row >= 15:
                    print(f"{C['red']}15 failures in a row — stopping rather than hammering. "
                          f"Check the network, then re-run; done ones are skipped.{C['x']}")
                    break
            await asyncio.sleep(args.delay)

    print(f"\n{C['grn']}adopted {ok}{C['x']} · {C['yel']}left alone {fail}{C['x']}")
    print(f"{C['dim']}Re-runnable: anything already ours is skipped by the helper.{C['x']}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Copy hotlinked product images into our storage.")
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.4, help="seconds between fetches")
    sys.exit(asyncio.run(main(ap.parse_args())))
