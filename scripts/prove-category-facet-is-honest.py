#!/usr/bin/env python3
"""The category picker must narrow to what the SEARCH touched — over the whole match.

    python3 scripts/prove-category-facet-is-honest.py        # against the local dev stack

WHY A SCRIPT. Pam, 2026-09-04, on the pinned Find Product panel: *"would be good to narrow
the cats where only search term is applicable so cat list is shortened."* The shop has 52
active categories and the picker lists all 52, always; `papers` touches 6 and `elements` 5,
so she scrolls a 52-line list to choose between five answers, on a touchscreen, with a
customer waiting.

THE OBVIOUS IMPLEMENTATION IS THE BUG. The screen already holds twenty rows, so grouping
those is one line of JavaScript and needs no server at all — and it would name six shelves
out of a 366-row match and hide the rest. This file exists because that mistake has already
been made in this exact endpoint's neighbourhood: the catalog header once put `ageCount()`
— a filter over the 25 loaded rows — next to `total` (5,162), and told a shop selling
tobacco and CBD that it had **3** age-restricted products. Same shape, different label.

So the check that matters is not "does a facet come back" but **"is it counted over the
match or over the page"**, and the way to ask it is to make the page much smaller than the
match: `limit=1` against a term with many hits. A facet that agrees with `total` under that
squeeze is counting the right set.

TWO MORE PROPERTIES, BOTH LEARNED THE HARD WAY:
  · The facet must NOT be narrowed by the category filter itself, or picking "Papers"
    rebuilds the list as only "Papers" and the picker becomes a one-way door.
  · Every count must be reproducible by asking the SAME endpoint for that category alone.
    A second way to ask a question has to be tested against the FIRST way, never against
    what I expect the answer to be (LESSON #2).

NOTHING IS SOLD AND NOTHING IS WRITTEN. Read-only GETs against the dev stack, except the
fixture block, which inserts rows in DISTINCT categories and deletes them again.
"""
import json
import os
import pathlib
import subprocess
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("BANCO_BASE", "http://localhost:3000")
FIXTURE_SKU = "ZZFACET"          # deleted at the end, and again on the next run

npass = nfail = 0


def check(ok, what, detail=""):
    global npass, nfail
    if ok:
        npass += 1
        print(f"  ✅ {what}")
    else:
        nfail += 1
        print(f"  ❌ {what}" + (f"\n       {detail}" if detail else ""))


def search(**kw):
    qs = urllib.parse.urlencode(kw)
    with urllib.request.urlopen(f"{BASE}/api/v1/pos/search?{qs}", timeout=30) as r:
        return json.load(r)


# The dev stack's credentials live in .env, not in this file — hardcoding "banco" got a
# FATAL: role "banco" does not exist on the first run.
def _env(name, default=""):
    try:
        for line in pathlib.Path(".env").read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name:
                return v.strip().strip("'\"")
    except OSError:
        pass
    return os.environ.get(name, default)


def psql(sql):
    """Dev database only. The prod route is scripts/prod-query.sh and it refuses writes."""
    return subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres",
         "psql", "-U", _env("POSTGRES_USER", "postgres"),
         "-d", _env("POSTGRES_DB", "postgres"), "-tAc", sql],
        capture_output=True, text=True, check=False)


# ── FIXTURE ──────────────────────────────────────────────────────────────────────────────
# The dev catalogue is SIX products and every one of them is in "Treats", so it cannot show
# a facet with more than one row in it — and a check that cannot fail is not a check. These
# rows exist only inside this run.
print("── fixture: products spread across four shelves ──")
psql(f"DELETE FROM products WHERE sku LIKE '{FIXTURE_SKU}%'")
spread = {"Papers & Rolling": 5, "Bongs & Pipes": 3, "Vape Hardware": 2, "Grinders": 1}
rows, n = [], 0
for cat, count in spread.items():
    for _ in range(count):
        n += 1
        rows.append(f"('{FIXTURE_SKU}-{n}', 'ZZFACET Testrow Bruzzo {n}', '{cat}')")

# CLONE A REAL ROW AND OVERRIDE FOUR FIELDS, rather than listing columns. The first version
# built an INSERT column by column and walked into stock_quantity, then is_age_restricted,
# then vending_compatible — one NOT NULL at a time. That is not just tedious, it is the
# mistake load-catalog-sample.py was written about: "a partial sample does not look
# incomplete, it looks WRONG, and it accuses working code." A row missing its classification
# columns silently becomes `standard`, not-age-restricted, and any check that reads them is
# then measuring my fixture instead of the catalogue. Cloning inherits whatever the schema
# grows next, for free.
ins = psql(
    # NULL::products, not `p` — a record from a subquery has no registered type
    # ("record type has not been registered"), so the template goes in as jsonb and the
    # overrides are merged on top with ||.
    "INSERT INTO products SELECT (jsonb_populate_record(NULL::products,"
    "  to_jsonb(p) || jsonb_build_object("
    "  'id', gen_random_uuid()::text, 'sku', v.sku, 'name', v.name,"
    "  'category', v.cat, 'barcode', NULL, 'price', 9.90, 'is_active', true))).* "
    # ONE template row, chosen in a subquery. Written as `FROM products p, (VALUES …)`
    # it is a cross join: eleven names times six products = 66 rows, and the first duplicate
    # sku stopped it. The LIMIT belongs to the template, not to the statement.
    "FROM (SELECT * FROM products WHERE is_active ORDER BY created_at LIMIT 1) p, "
    f"     (VALUES {','.join(rows)}) AS v(sku, name, cat)"
)
check(ins.returncode == 0, f"{n} rows in {len(spread)} shelves, all matching 'Bruzzo'",
      (ins.stderr or "").strip()[:300])
if ins.returncode != 0:
    sys.exit(1)

try:
    # ── A · COUNTED OVER THE MATCH, NOT OVER THE PAGE ────────────────────────────────────
    print("\n── A · the squeeze: one row on the page, eleven in the match ──")
    one = search(q="Bruzzo", limit=1)
    facet = {c["name"]: c["count"] for c in one.get("match_categories", [])}
    check(len(one["items"]) == 1, f"the page really is one row ({len(one['items'])})")
    check(one["total"] == n, f"the match really is {n} rows ({one['total']})")
    check(len(facet) == len(spread),
          f"the facet names all {len(spread)} shelves, not the one on the page ({len(facet)})",
          f"it named {sorted(facet)} — a page-scoped facet would name 1")
    check(facet == spread, "and every count is the whole-match count",
          f"got {facet}, expected {spread}")
    check(sum(facet.values()) == one["total"],
          f"the counts add up to `total` ({sum(facet.values())} = {one['total']})",
          "the facet and the header are counting different sets, which is how a screen "
          "starts arguing with itself")

    # ── B · EACH COUNT SURVIVES BEING ASKED THE OTHER WAY ────────────────────────────────
    # LESSON #2: a second way to ask the same question is tested against the FIRST, never
    # against my expectations. The endpoint itself is the reference.
    print("\n── B · every count re-asked through the ordinary category filter ──")
    for cat, want in spread.items():
        got = search(q="Bruzzo", category=cat, limit=50)["total"]
        check(got == want, f'"{cat}" — facet says {want}, filtering says {got}')

    # ── C · NOT A ONE-WAY DOOR ───────────────────────────────────────────────────────────
    print("\n── C · picking a shelf does not collapse the picker to that shelf ──")
    picked = search(q="Bruzzo", category="Grinders", limit=50)
    pf = {c["name"]: c["count"] for c in picked.get("match_categories", [])}
    check(pf == spread,
          "with Grinders selected, the picker still offers the other three shelves",
          f"it offers {sorted(pf)} — you could get in and not get back across")

    # ── D · AND IT STAYS QUIET WHEN IT HAS NOTHING TO ADD ────────────────────────────────
    # The step whose expected result is that NOTHING happens. With no search term the picker
    # is already the full list, and paging must not recompute a facet that cannot have
    # changed — the second scan is the whole cost of this feature.
    print("\n── D · the times it must NOT do the extra work ──")
    check(search(q="", limit=5).get("match_categories") == [],
          "no search term → no facet, because the picker is already the whole list")
    check(search(q="Bruzzo", limit=1, skip=1).get("match_categories") == [],
          "page two → no facet, the screen keeps the one it already has",
          "the facet is being recomputed on every Show more, which is the one cost this "
          "feature has")

    # ── E · A TERM THAT TOUCHES NOTHING ──────────────────────────────────────────────────
    print("\n── E · a term with no answers ──")
    none = search(q="zzqqxx", limit=5)
    check(none["total"] == 0, "no matches")
    check(none.get("match_categories") == [], "and an empty picker addition, not a stale one")

finally:
    psql(f"DELETE FROM products WHERE sku LIKE '{FIXTURE_SKU}%'")
    left = psql(f"SELECT count(*) FROM products WHERE sku LIKE '{FIXTURE_SKU}%'").stdout.strip()
    print(f"\n── fixture removed ({left} rows left behind) ──")

print("\n==========================================")
print(f"  {npass} passed · {nfail} failed")
sys.exit(1 if nfail else 0)
