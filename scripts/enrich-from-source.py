#!/usr/bin/env python3
# ============================================================================
# enrich-from-source — pull each product's OWN page for the data it already has.
#
#   python3 scripts/enrich-from-source.py --limit 5        # DRY RUN, 5 products
#   python3 scripts/enrich-from-source.py --apply          # write, whole catalogue
#
# THE INSIGHT IS ANGEL'S, 2026-07-31:
#   "I think we do have the URLs for every SKU that Tamar has. So I just don't
#    see what went wrong here... I'm working way too hard when I don't need to."
#
# He is right. 5,111 products carry a source_url pointing at the shop's own site,
# and those pages publish the RETAIL tier ladder and a spec table. No searching,
# no clicking, no matching — the row already knows which page describes it.
#
# WHAT THIS CAN AND CANNOT DO — the division that matters:
#
#   MACHINE (this script)          the tier ladder, the spec table. 5,111 products,
#                                  zero human decisions, because identity is already known.
#   HUMAN (shelf intake)           the EAN. The page does not publish one, and a barcode
#                                  can only be learned from the packet in someone's hand.
#
# So this does not remove the human. It removes the CLICKING AROUND THE HUMAN, which
# is the part that was never their job.
#
# POLITE BY CONSTRUCTION. One request at a time with a delay, a real UA, and it stops
# on repeated failures rather than hammering. This is the shop's own site, which is why
# a bulk pass is reasonable at all — do NOT point it at anyone else's.
# ============================================================================
import argparse
import asyncio
import html as H
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

C = {"grn": "\033[32m", "yel": "\033[33m", "red": "\033[31m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126 Safari/537.36"}

# "CHF 1.30 ab 10 Stück" — the shop's own retail ladder. The digits arrive split across
# markup ("1.", "30"), hence the tolerant middle.
_TIER = re.compile(r"(\d+)\.\s*(\d+)\s*ab\s*(\d+)\s*St", re.I)


def _text_of(html: str) -> list[str]:
    t = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = H.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [re.sub(r"\s+", " ", ln).strip() for ln in t.split("\n") if ln.strip()]


def parse_page(html: str) -> dict:
    """The two things the page knows that the catalogue does not: tiers and specs."""
    lines = _text_of(html)
    out = {}

    tiers = [{"min_qty": int(q), "unit_price": f"{int(a)}.{b.zfill(2)}"}
             for a, b, q in _TIER.findall(" ".join(lines))]
    if tiers:
        # ascending min_qty, deduped, and always descending in price — a ladder that rises
        # is the bug that overcharged a customer this morning, so refuse to build one.
        tiers = sorted({t["min_qty"]: t for t in tiers}.values(), key=lambda t: t["min_qty"])
        if all(float(tiers[i]["unit_price"]) >= float(tiers[i + 1]["unit_price"])
               for i in range(len(tiers) - 1)):
            out["tiers"] = tiers

    if "Details" in lines:
        i = lines.index("Details")
        rest = lines[i + 1:]
        stop = next((j for j, l in enumerate(rest)
                     if l.startswith(("Diese Artikel", "Automaten", "Warenkorb"))), len(rest))
        pairs, block = {}, rest[:stop]
        for k, v in zip(block[0::2], block[1::2]):
            if k and v and len(k) <= 60 and len(v) <= 200:
                pairs[k] = v
        if pairs:
            out["facets"] = pairs
    return out


def read_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def psql(env, sql, container):
    """Run SQL, whichever side of the container wall we happen to be on.

    This script needs BOTH httpx (to fetch pages) and a route to Postgres. On the host there
    is docker but no httpx; inside the app container there is httpx but no docker. Trying to
    live on the host meant it could not run at all — so: talk to Postgres DIRECTLY when a
    driver is available (inside the container), and shell out to `docker exec psql` only as
    the fallback (on a laptop). Same script, either place, no flags to remember.
    """
    user = env.get("POSTGRES_USER") or os.environ.get("POSTGRES_USER") or "helix_user"
    db = env.get("POSTGRES_DB") or os.environ.get("POSTGRES_DB") or "helix_db"

    try:
        import psycopg
    except ImportError:
        psycopg = None

    if psycopg is not None:
        host = os.environ.get("POSTGRES_HOST") or env.get("POSTGRES_HOST") or "postgres"
        pwd = os.environ.get("POSTGRES_PASSWORD") or env.get("POSTGRES_PASSWORD") or ""
        port = os.environ.get("POSTGRES_PORT") or env.get("POSTGRES_PORT") or "5432"
        try:
            with psycopg.connect(host=host, port=port, user=user, password=pwd,
                                 dbname=db, connect_timeout=10, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if cur.description is None:
                        return ""
                    return "\n".join("\x1f".join("" if v is None else str(v) for v in row)
                                     for row in cur.fetchall())
        except Exception as e:
            print(f"{C['red']}postgres: {type(e).__name__}: {str(e)[:90]}{C['x']}", file=sys.stderr)
            return None

    try:
        p = subprocess.run(["docker", "exec", "-i", container, "psql", "-U", user, "-d", db,
                            "-tA", "-F", "\x1f", "-v", "ON_ERROR_STOP=1"],
                           input=sql, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"{C['red']}could not reach postgres: {e}{C['x']}", file=sys.stderr)
        return None
    if p.returncode != 0:
        print(f"{C['red']}psql failed:{C['x']}\n{p.stderr.strip()}", file=sys.stderr)
        return None
    return p.stdout


async def main_async(args, env, rows):
    import httpx
    updates, stats = [], {"fetched": 0, "tiers": 0, "facets": 0, "failed": 0, "skipped": 0}
    fails_in_a_row = 0

    async with httpx.AsyncClient(follow_redirects=True, timeout=25, headers=UA) as client:
        for pid, sku, name, url, has_tiers, has_facets in rows:
            if has_tiers and has_facets:
                stats["skipped"] += 1
                continue
            try:
                r = await client.get(url)
                stats["fetched"] += 1
                fails_in_a_row = 0
            except Exception as e:
                stats["failed"] += 1
                fails_in_a_row += 1
                print(f"  {C['red']}✗{C['x']} {sku:<12} {type(e).__name__}")
                if fails_in_a_row >= 5:
                    print(f"{C['red']}Five failures in a row — stopping rather than hammering "
                          f"the site.{C['x']}")
                    break
                await asyncio.sleep(args.delay)
                continue

            got = parse_page(r.text)
            u = {"id": pid}
            if got.get("tiers") and not has_tiers:
                u["tiers"] = got["tiers"]; stats["tiers"] += 1
            if got.get("facets") and not has_facets:
                u["facets"] = got["facets"]; stats["facets"] += 1
            if len(u) > 1:
                updates.append(u)
                bits = []
                if "tiers" in u:
                    bits.append(" ".join(f"{t['min_qty']}+→{t['unit_price']}" for t in u["tiers"]))
                if "facets" in u:
                    bits.append(f"{len(u['facets'])} specs")
                print(f"  {C['grn']}✓{C['x']} {sku:<12} {name[:34]:<34} {' · '.join(bits)}")
            await asyncio.sleep(args.delay)
    return updates, stats


def main():
    ap = argparse.ArgumentParser(
        description="Fill tier pricing + spec facets from each product's own source page.")
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="only the first N products")
    ap.add_argument("--sku", default="", help="comma-separated SKUs — check a specific shortlist")
    ap.add_argument("--name", default="", help="only products whose name matches (ILIKE)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (be polite)")
    ap.add_argument("--container", default="banco-postgres")
    args = ap.parse_args()

    env = read_env(os.path.join(ROOT, ".env"))
    where = ["is_active", "source_url IS NOT NULL"]
    if args.sku:
        skus = ",".join("'" + re.sub(r"[^A-Za-z0-9_-]", "", x.strip()) + "'"
                        for x in args.sku.split(",") if x.strip())
        if skus:
            where.append(f"sku IN ({skus})")
    if args.name:
        where.append("name ILIKE '%" + args.name.replace("'", "''").replace("%", "") + "%'")

    raw = psql(env,
               "SELECT id, sku, name, source_url, "
               "  (price_tiers IS NOT NULL AND price_tiers::text NOT IN ('[]','null')), "
               "  (raw_facets IS NOT NULL AND raw_facets::text <> '{}') "
               "FROM products WHERE " + " AND ".join(where) +
               " ORDER BY sku" + (f" LIMIT {int(args.limit)}" if args.limit else "") + ";",
               args.container)
    if raw is None:
        return 2

    rows = []
    for line in raw.splitlines():
        p = line.split("\x1f")
        if len(p) >= 6:
            rows.append((p[0], p[1], p[2], p[3], p[4] == "t", p[5] == "t"))

    print(f"{C['b']}Enrich from each product's own page{C['x']}  "
          f"{C['dim']}({'APPLY' if args.apply else 'dry run'}, {len(rows)} products, "
          f"{args.delay}s apart){C['x']}\n")

    updates, stats = asyncio.run(main_async(args, env, rows))

    print(f"\n  fetched {stats['fetched']} · already complete {stats['skipped']} · "
          f"failed {stats['failed']}")
    print(f"  {C['grn']}tier ladders found: {stats['tiers']}{C['x']}   "
          f"{C['grn']}spec tables found: {stats['facets']}{C['x']}")
    if not updates:
        print(f"\n{C['yel']}Nothing to write.{C['x']}")
        return 0
    if not args.apply:
        print(f"\n{C['dim']}Dry run — nothing written. Re-run with --apply.{C['x']}")
        return 0
    if not args.yes and input(f"\nWrite {len(updates)} product(s)? [y/N] ").strip().lower() \
            not in ("y", "yes"):
        print("Stopped. Nothing changed.")
        return 1

    stmts = ["BEGIN;"]
    for u in updates:
        sets = []
        if "tiers" in u:
            # per_unit: the ladder on the shop's own page is a price EACH at that quantity.
            sets.append("price_tiers = " + repr(json.dumps(u["tiers"])).replace('"', "'")
                        .replace("'''", "'") + "::jsonb")
            sets.append("tier_mode = 'per_unit'")
        if "facets" in u:
            sets.append("raw_facets = " + repr(json.dumps(u["facets"])).replace('"', "'")
                        .replace("'''", "'") + "::jsonb")
        sets.append("updated_at = now()")
        stmts.append(f"UPDATE products SET {', '.join(sets)} WHERE id = '{u['id']}';")
    stmts.append("COMMIT;")
    if psql(env, "\n".join(stmts), args.container) is None:
        print(f"{C['red']}✗ failed — rolled back, nothing changed.{C['x']}", file=sys.stderr)
        return 2
    print(f"\n{C['grn']}✅ enriched {len(updates)} product(s) from their own source pages.{C['x']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
