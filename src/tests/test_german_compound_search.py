"""German compounds must not lose the right row on score.

2026-08-07. Angel, worrying about the thing that actually kills adoption:

    "pam says i did that could find it after 3 searches and gave up and felix says pam look
     sort by cat papers and you would find it here ... and this type of argument everyday"

That argument is a SEARCH DEFECT wearing a human costume. German writes "Aktivkohlefilter"
where English writes "activated carbon filter", and a Swiss cashier types "Pokerchip" for a
row stored as "… Poker Chip 42mm". Trigram similarity is computed over 3-character windows,
so the SPACE is part of the data and the two spellings score differently against the same row.

MEASURED ON PROD BEFORE THE FIX — and it was worse than the note in CLAUDE.md said:

    "Pokerchip Grinder"   -> Card Grinder, CNC Grinder, Elektro Grinder, Ersatzsieb, ...
    "Poker Chip Grinder"  -> IDENTICAL LIST

Both spellings returned the same useless page, because `grinder` expands to the Grinders
concept and the synonym bonus was a FLOOR inside `GREATEST(…, 0.75)`. **201 rows tied at
exactly 0.750**, every text score below the floor was discarded, and the tiebreak fell through
to `name` — so the screen led with replacement SIEVES in alphabetical order and the one real
Poker Chip grinder was nowhere. The compound bug was real and INVISIBLE underneath it.

Fourth time this shape has bitten (07-31 dedup guard, 08-03 alias filters, 08-06 category
ORDER BY, now the synonym floor): a downstream rule discarding the row the feature exists to
find. A floor a real score cannot exceed is not a boost.

The live ranking test at the bottom is the one that matters. The rest is scaffolding.
"""
import os
import re
import pathlib
import uuid

import pytest

PG = os.environ.get(
    "TEST_PG_DSN",
    "postgresql://helix_user:banco_local_dev@localhost:5442/helix_db",
)
PREFIX = "TEST-COMPOUND-"
SRC = pathlib.Path(__file__).resolve().parents[1] / "routes" / "pos_router.py"


# ---------------------------------------------------------------- token folding

def test_a_compound_and_its_spaced_spelling_fold_to_the_same_tokens():
    from src.routes.pos_router import _despace
    assert _despace("Poker Chip") == _despace("Pokerchip") == "pokerchip"
    assert _despace("Aktiv-Kohle Filter") == _despace("Aktivkohlefilter") == "aktivkohlefilter"


def test_short_tokens_are_left_out_so_brands_are_not_matched_inside_compounds():
    """3-letter brands (OCB, RAW, BIC — all tier-1 in the day book) already match by ILIKE
    and trigram. Admitting them here would match them INSIDE unrelated compounds, where the
    word boundary that made them meaningful is gone."""
    from src.routes.pos_router import _query_compound_tokens
    assert _query_compound_tokens("OCB Slim") == ["slim"]
    assert "raw" not in _query_compound_tokens("RAW Hammercraft")


def test_german_function_words_are_not_counted_as_coverage():
    """"mit"/"und" sit in half the German product names; counting them would add a flat
    bonus to everything, which is the same as adding nothing."""
    from src.routes.pos_router import _query_compound_tokens
    assert _query_compound_tokens("Grinder mit Sieb") == ["grinder", "sieb"] or \
           _query_compound_tokens("Grinder mit Sieb") == ["grinder"]
    assert "mit" not in _query_compound_tokens("Grinder mit Sieb")


# ---------------------------------------------------------------- synonyms on compounds

def test_a_compound_reaches_its_concept_through_its_head():
    """German compounds are head-final: the last element is the type. "Aktivkohlefilter"
    expanded to NOTHING while "Aktiv Kohle Filter" expanded to seven terms — same concept,
    same shop, and filters are rank 2 in the paper day book."""
    from src.services.catalog_search_synonyms import expand_search_terms
    assert "filter" in expand_search_terms("Aktivkohlefilter")
    assert "bong" in expand_search_terms("Glasbong")
    assert "feuerzeug" in expand_search_terms("Sturmfeuerzeug")


@pytest.mark.parametrize("word", ["Durchmesser", "Durchmesser 50mm", "rootjuice", "Silicone"])
def test_measured_false_friends_do_not_expand(word):
    """Found by running the expander over all 1,401 catalogue words of 8+ letters and READING
    the output, not by imagining what might go wrong. "Durchmesser" is the dangerous one —
    diameter appears in half the bong and grinder names here, and it ends in "messer" (knife),
    so a size query would have boosted the entire knife shelf."""
    from src.services.catalog_search_synonyms import expand_search_terms
    assert expand_search_terms(word) == []


# ---------------------------------------------------------------- the floor must stay gone

def test_the_synonym_bonus_is_additive_and_not_a_floor():
    """THE REGRESSION GUARD. `GREATEST(text_score, 0.75)` tied 201 grinders at 0.750 and threw
    every text score away. Only an ADDITIVE term can boost without saturating."""
    src = SRC.read_text(encoding="utf-8")
    assert "THEN 0.75" not in src, "the saturating synonym floor is back"
    assert re.search(r'"\s*\+\s*CASE WHEN category ILIKE ANY\(:syn_like\)', src), \
        "the synonym bonus is no longer an additive term"


def test_the_bonuses_are_applied_outside_the_greatest():
    """Placement is the whole bug: inside GREATEST() it is a floor, outside it is a bonus.
    Assert the fragments are appended AFTER the closing paren of GREATEST(...)."""
    src = SRC.read_text(encoding="utf-8")
    assert "){syn_score}{compound_score} AS relevance" in src, \
        "syn_score/compound_score moved back inside GREATEST() — that makes them floors again"


def test_the_compound_clause_is_an_additive_score():
    src = SRC.read_text(encoding="utf-8")
    assert re.search(r"compound_score\s*=\s*f\"\s*\+\s*\{_COMPOUND_BONUS\}", src), \
        "the compound score is not an additive term"


def test_there_is_no_compound_recall_arm():
    """Deliberately absent, and this test exists so nobody helpfully adds one back.

    I wrote a recall arm first — "without it the compound row is never fetched" — and it was
    wrong. Measured across 20 German/English spellings against the live 5,361-row catalogue it
    added **0 rows every time**: `word_similarity` matches the best EXTENT of the target, so
    "aktivkohlefilter" is already recalled by "Aktiv Kohle Filter".

    It was also UNTESTABLE BY CONSTRUCTION — deleting it broke no test, because it had no
    behaviour to break. That is the tell for machinery that is not earning its place, and it
    would have cost a correlated subquery on every row of every search."""
    src = SRC.read_text(encoding="utf-8")
    assert "compound_recall" not in src, \
        "a compound recall arm is back — measure that it adds rows before keeping it"


# ---------------------------------------------------------------- the live ranking proof

def _conn():
    psycopg = pytest.importorskip("psycopg", reason="psycopg not installed")
    try:
        return psycopg.connect(PG, connect_timeout=3, autocommit=True)
    except Exception as e:                                        # noqa: BLE001
        pytest.skip(f"no Postgres at {PG.split('@')[-1]}: {type(e).__name__}")


# The real competing names, copied from prod. The distractors matter as much as the target:
# every one of these outranked the Poker Chip row before the fix.
_FIXTURES = [
    ("Grinder Metall 3teilig mit Sieb Poker Chip 42mm", "Grinders"),      # <- the target
    ("Grinder Alu CNC 4teilig mit Sieb Hello Kitty 50mm", "Grinders"),
    ("Card Grinder, Peace", "Grinders"),
    ("CNC Grinder Schwarz 4-Teilig Klein", "Grinders"),
    ("Ersatzsieb Edelstahl Steely Dan 2.0", "Grinders"),
    ("Flower Mill Next-Gen Premium Ersatzsieb für 54mm Mill extrafein", "Grinders"),
    ("Aktivkohlefilter actiTube Slim 7mm 50stk", "Filters & Tips"),
    ("Air Filter XHALE Buddy Mushroom grün", "Filters & Tips"),
]


@pytest.fixture
def catalog():
    """Swept BY PREFIX, never by remembered id — a probe that tears down what it thinks it
    created dies on the corpse of the last crashed run (2026-08-03)."""
    conn = _conn()
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_extension WHERE extname='pg_trgm'")
        if not cur.fetchone():
            pytest.skip("pg_trgm not installed on the test database")
        cur.execute(f"DELETE FROM products WHERE sku LIKE '{PREFIX}%'")
        for i, (name, cat) in enumerate(_FIXTURES):
            cur.execute("""
                INSERT INTO products (id, sku, name, category, price, stock_quantity,
                                      is_active, is_age_restricted, vending_compatible,
                                      sync_override, created_at, updated_at)
                VALUES (gen_random_uuid(), %s, %s, %s, 9.90, 1,
                        true, false, false, false, now(), now())
            """, (f"{PREFIX}{i:02d}-{uuid.uuid4().hex[:6]}", name, cat))
    yield conn
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM products WHERE sku LIKE '{PREFIX}%'")
    conn.close()


def _search(q):
    """Call the ACTUAL endpoint function against a real database.

    Own engine per call with NullPool: the module-level AsyncSessionLocal pools against
    whichever event loop touched it first, and asyncio.run() makes a new loop every time —
    which surfaces as "got Future attached to a different loop" and has nothing to do with
    the code under test (2026-08-07, the first-price tests)."""
    import asyncio
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from src.routes.pos_router import search_products_fast

    dsn = PG.replace("postgresql://", "postgresql+asyncpg://")

    async def go():
        engine = create_async_engine(dsn, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                return await search_products_fast(q=q, limit=10, db=db)
        finally:
            await engine.dispose()

    return [i["name"] for i in asyncio.run(go())["items"]]


TARGET = "Grinder Metall 3teilig mit Sieb Poker Chip 42mm"


@pytest.mark.parametrize("q", [
    "Pokerchip Grinder",     # how a Swiss person types it — ranked out of sight before
    "Poker Chip Grinder",    # the spelling that used to be the "good" one
    "Pokerchip",
    "poker chip",
])
def test_both_spellings_find_the_poker_chip_grinder_first(catalog, q):
    """The whole point. Before the fix these two queries returned the IDENTICAL list of
    other grinders, tied at 0.750 and ordered alphabetically."""
    names = _search(q)
    assert names, f"{q!r} returned nothing at all"
    assert names[0] == TARGET, f"{q!r} ranked {names[0]!r} above the Poker Chip grinder\n  {names}"


def test_a_spaced_query_finds_a_compound_name(catalog):
    """The other direction, and the one a lexicon-based decompounder would miss: the CATALOGUE
    holds the compound and the person types it spaced."""
    names = _search("Aktiv Kohle Filter")
    assert names, "'Aktiv Kohle Filter' returned nothing"
    assert any("Aktivkohlefilter" in n for n in names[:3]), \
        f"the compound row is not in the top 3: {names[:5]}"


def test_the_shelf_still_wins_over_an_incidental_mention(catalog):
    """The regression the 0.75 floor existed to prevent. An English query scores ~0 against a
    German name, so the whole shelf must still outrank a row that merely mentions the word.
    Making the bonus additive must not cost this."""
    names = _search("grinder")
    assert names, "'grinder' returned nothing"
    top = names[:6]
    assert sum(1 for n in top if n in
               [f for f, c in _FIXTURES if c == "Grinders"]) >= 4, \
        f"the Grinders shelf stopped dominating a category query: {top}"
