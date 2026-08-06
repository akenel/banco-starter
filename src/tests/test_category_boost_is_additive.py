"""The category hint must BOOST the score, never sit above it as a sort tier.

2026-08-06, found by running the shelf-wall photos through `_find_catalog_matches` against the
LIVE Artemis catalogue. Angel photographed a **Greengo** grinder. The AI read it correctly —
name `Greengo`, category `Grinders` — and the search returned:

    1..6.  0.625   Grinder Alu 3-teilig Santa Cruz…, Grinder Alu Elektro, Flower Mill…

Ten generic grinders, **not one of them a Greengo**, while the shop's six genuine `Greengo` rows
scored **1.000** and never appeared. Drop the category hint and they come back at 1..6. They lost
because they are filed under `Other` / `Rolling Papers`, and the ORDER BY read:

    ORDER BY is_active DESC,
             CASE WHEN category = :cat THEN 0 ELSE 1 END,   -- hard tier
             CASE WHEN name ILIKE :q||'%' THEN 0 ELSE 1 END, -- hard tier
             score DESC                                      -- …score fourth

**A sort key above `score` is a filter wearing a boost's clothes.** Every same-shelf row, however
bad, outranks every off-shelf row, however perfect; `LIMIT` then turns "ranked lower" into "does
not exist". That is the exact thing the comment two lines above it forbids, and the same shape as
the 2026-07-31 dedup guard and the 2026-08-03 alias filters: a downstream rule quietly discarding
the row the fix existed to find.

The fix makes both bonuses ADDITIVE (+0.15 same category, +0.10 name prefix). A 0.625 shelf-mate
can no longer bury a 1.000 exact hit, and a right-shelf row still wins every close call.

⚠️ These tests need REAL Postgres — `similarity()` / `word_similarity()` are pg_trgm, and the
suite's default fixture is SQLite in memory. They build their own temp table, so the local
catalogue's contents are irrelevant. They **skip** if no Postgres is reachable, so the last test
also pins the ordering structurally in the source, which always runs.
"""
import os
import re
import pathlib

import pytest

PG = os.environ.get(
    "TEST_PG_DSN",
    "postgresql://helix_user:banco_local_dev@localhost:5442/helix_db",
)

# The two ORDER BY clauses, isolated. OLD is what shipped; NEW is the fix.
_SCORE = ("GREATEST(similarity(name, %(q)s), "
          "word_similarity(%(q)s, coalesce(name,'') || ' ' || coalesce(description,'')))")

OLD_ORDER = f"""
    ORDER BY is_active DESC,
             CASE WHEN %(cat)s <> '' AND category = %(cat)s THEN 0 ELSE 1 END,
             CASE WHEN name ILIKE %(q)s || '%%' THEN 0 ELSE 1 END,
             score DESC, name
"""

NEW_ORDER = f"""
    ORDER BY is_active DESC,
             ({_SCORE}
              + CASE WHEN %(cat)s <> '' AND category = %(cat)s THEN 0.15 ELSE 0 END
              + CASE WHEN name ILIKE %(q)s || '%%' THEN 0.10 ELSE 0 END) DESC,
             score DESC, name
"""

# Reproduces the Greengo shape: an exact brand hit on the WRONG shelf, versus
# weak-but-same-shelf rows that share the query's letters via their description.
ROWS = [
    # (name,                       category,         description)
    ("Greengo King Size",          "Other",          "Greengo rolling papers king size."),
    ("Greengo Rolls Slim",         "Rolling Papers", "Greengo unbleached slim rolls."),
    ("Grinder Alu Elektro",        "Grinders",       "Elektrischer Grinder, green housing."),
    ("Grinder aus Bio Hanf 55mm",  "Grinders",       "Grinder made of green bio hemp."),
    ("Grinder Alu 3-teilig M",     "Grinders",       "Shredder in green anodised aluminium."),
]


def _conn():
    psycopg = pytest.importorskip("psycopg", reason="psycopg not installed")
    try:
        return psycopg.connect(PG, connect_timeout=3)
    except Exception as e:                                   # noqa: BLE001
        pytest.skip(f"no Postgres at {PG.split('@')[-1]}: {type(e).__name__}")


def _ranked(order_sql: str, q: str, cat: str) -> list[str]:
    """Create a throwaway table, run the real clause, return names best-first."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cur.execute("""
            CREATE TEMP TABLE t_boost (
                name text, category text, description text,
                is_active boolean DEFAULT true
            ) ON COMMIT DROP
        """)
        cur.executemany(
            "INSERT INTO t_boost (name, category, description) VALUES (%s, %s, %s)", ROWS)
        cur.execute(
            f"SELECT name, {_SCORE} AS score FROM t_boost {order_sql}".replace(
                "FROM t_boost", "FROM t_boost"),
            {"q": q, "cat": cat})
        return [r[0] for r in cur.fetchall()]


def test_old_order_buried_the_exact_brand_match():
    """Pin the bug so the fix can't silently regress: same shelf beat a perfect hit."""
    ranked = _ranked(OLD_ORDER, "Greengo", "Grinders")
    assert not ranked[0].startswith("Greengo"), (
        "expected the OLD ordering to bury the Greengo rows under same-category "
        f"grinders — got {ranked}")
    assert ranked[0].startswith("Grinder"), ranked


def test_additive_boost_puts_the_exact_brand_match_first():
    """The fix: a 1.000 off-shelf hit outranks 0.625 shelf-mates."""
    ranked = _ranked(NEW_ORDER, "Greengo", "Grinders")
    assert ranked[0].startswith("Greengo"), (
        f"the exact brand match must rank first — got {ranked}")
    assert ranked[1].startswith("Greengo"), ranked


def test_same_shelf_still_wins_a_close_call():
    """The boost must still DO something: on comparable scores the right shelf wins.

    `Grinder` matches all three grinder rows and neither Greengo row, so this checks the
    bonus has not been made so small it stopped mattering."""
    ranked = _ranked(NEW_ORDER, "Grinder", "Grinders")
    assert ranked[0].startswith("Grinder"), ranked


def test_the_shipped_sql_keeps_the_boost_additive():
    """Structural guard — runs even with no Postgres.

    This asserts only that the source does not reintroduce a bare category CASE as a sort
    tier ahead of `score`. It does NOT prove ranking; the two tests above do that."""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "routes" / "pos_router.py").read_text(encoding="utf-8")
    order = re.search(
        r"ORDER BY is_active DESC,(.*?)LIMIT :limit", src, re.S)
    assert order, "could not find the _find_catalog_matches ORDER BY"
    clause = order.group(1)

    assert "0.15" in clause and "0.10" in clause, (
        "the category / prefix bonuses must be additive constants:\n" + clause)
    # A bare `CASE …:cat… THEN 0 ELSE 1 END` immediately after the comma is the old tier.
    assert not re.search(r",\s*CASE WHEN :cat[^)]*?THEN 0 ELSE 1 END", clause), (
        "category is back to being a sort TIER above score — that is the Greengo bug:\n"
        + clause)
