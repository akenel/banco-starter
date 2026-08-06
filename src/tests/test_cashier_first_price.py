"""A cashier may fill in a blank price. Once. She may never change one.

2026-08-07. The morning's till guard refused to sell a placeholder-priced product. Angel then
simulated Pam hitting it with a customer waiting and showed me what a real shop actually does:

    ITEM-0212               999.99   real EAN 615068009973   <- correct row, blocked, unsold
    OTF-1786054495004-703    12.00   MINTED  2569030438637   <- what she sold instead

Ten seconds, sale saved, and a duplicate row carrying a fabricated barcode. The guard did not
stop an invented price reaching a customer — it RELOCATED it and damaged the catalogue on the
way. "A cashier must never change a price" exists to stop her DISCOUNTING a real one; a
placeholder is not a real price, and she could already type any number through create-on-the-fly,
so the rule was never enforcing anything. Its only measurable effect was duplicates.

Angel's call, and his shape: *"it's a special exception that the cashier can set the price once
when it's not set. After that, it doesn't make sense — once the price has been set, she has to
work with it."*

THE PROPERTY EVERYTHING ELSE HANGS ON: this endpoint can only ever fill a blank. Not a discount,
not a markup, not a "correction". If the current price is not a placeholder it must 409 and touch
nothing — verified here against a real database, not by reading the source, because the whole
point is what happens to the row.
"""
import os
import uuid
from decimal import Decimal

import pytest

from src.routes.pos_router import TILL_PRICED_FLAG, UNVERIFIED_PRICES

PG = os.environ.get(
    "TEST_PG_DSN",
    "postgresql://helix_user:banco_local_dev@localhost:5442/helix_db",
)
PREFIX = "TEST-FIRSTPRICE-"


def _conn():
    psycopg = pytest.importorskip("psycopg", reason="psycopg not installed")
    try:
        return psycopg.connect(PG, connect_timeout=3, autocommit=True)
    except Exception as e:                                    # noqa: BLE001
        pytest.skip(f"no Postgres at {PG.split('@')[-1]}: {type(e).__name__}")


@pytest.fixture
def row():
    """A throwaway product. Swept BY PREFIX, never by remembered id — a probe that tears down
    what it thinks it created dies on the corpse of the last crashed run (2026-08-03)."""
    conn = _conn()
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM products WHERE sku LIKE '{PREFIX}%'")

    def make(price):
        sku = f"{PREFIX}{uuid.uuid4().hex[:8]}"
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products (id, sku, name, category, price, stock_quantity,
                                      is_active, is_age_restricted, vending_compatible,
                                      sync_override, created_at, updated_at)
                VALUES (gen_random_uuid(), %s, 'Test Candle', 'Other', %s, 1,
                        true, false, false, false, now(), now())
                RETURNING id
            """, (sku, price))
            return cur.fetchone()[0], sku

    yield make, conn
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM products WHERE sku LIKE '{PREFIX}%'")
    conn.close()


def _call(pid, price):
    """Drive the endpoint function directly against a real database.

    Builds its OWN engine per call with NullPool. The module-level AsyncSessionLocal pools
    connections against whichever event loop touched it first, and asyncio.run() makes a new loop
    every time — which surfaces as "got Future attached to a different loop", nothing to do with
    the code under test. NullPool + dispose keeps each call self-contained."""
    import asyncio
    from fastapi import HTTPException
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from src.routes.pos_router import set_first_price

    dsn = PG.replace("postgresql://", "postgresql+asyncpg://")

    async def go():
        engine = create_async_engine(dsn, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                return await set_first_price(
                    product_id=pid, body={"price": price}, db=db,
                    current_user={"preferred_username": "pam"})
        finally:
            await engine.dispose()

    try:
        return asyncio.run(go()), None
    except HTTPException as e:
        return None, e


@pytest.mark.parametrize("placeholder", [str(p) for p in UNVERIFIED_PRICES])
def test_a_blank_price_can_be_filled_once(row, placeholder):
    make, conn = row
    pid, sku = make(placeholder)
    out, err = _call(pid, "12.00")
    assert err is None, f"filling a blank should succeed, got {err.detail if err else ''}"
    with conn.cursor() as cur:
        cur.execute("SELECT price, enrichment_flags, work_note FROM products WHERE id=%s", (pid,))
        price, flags, note = cur.fetchone()
    assert Decimal(str(price)) == Decimal("12.00")
    assert TILL_PRICED_FLAG in (flags or []), f"row not flagged for review: {flags}"
    assert "pam" in (note or ""), "the work note must name who typed it"
    assert placeholder in (note or ""), "the note must record what it replaced"


def test_it_refuses_to_change_a_price_that_already_exists(row):
    """The one that matters. A real price must be untouchable from the till."""
    make, conn = row
    pid, sku = make("12.00")
    out, err = _call(pid, "2.00")
    assert err is not None and err.status_code == 409, "a set price must not be changeable here"
    with conn.cursor() as cur:
        cur.execute("SELECT price FROM products WHERE id=%s", (pid,))
        assert Decimal(str(cur.fetchone()[0])) == Decimal("12.00"), "the price was modified anyway"


def test_the_same_row_cannot_be_priced_twice(row):
    """"Once" has to mean once — the second attempt hits the same 409 as any real price."""
    make, conn = row
    pid, _ = make("999.99")
    _, err1 = _call(pid, "12.00")
    assert err1 is None
    _, err2 = _call(pid, "3.00")
    assert err2 is not None and err2.status_code == 409
    with conn.cursor() as cur:
        cur.execute("SELECT price FROM products WHERE id=%s", (pid,))
        assert Decimal(str(cur.fetchone()[0])) == Decimal("12.00")


@pytest.mark.parametrize("bad", ["0", "-5", "abc", ""])
def test_a_nonsense_price_is_rejected_and_nothing_is_written(row, bad):
    make, conn = row
    pid, _ = make("999.99")
    _, err = _call(pid, bad)
    assert err is not None and err.status_code == 422
    with conn.cursor() as cur:
        cur.execute("SELECT price, enrichment_flags FROM products WHERE id=%s", (pid,))
        price, flags = cur.fetchone()
    assert Decimal(str(price)) == Decimal("999.99")
    assert TILL_PRICED_FLAG not in (flags or [])


def test_retyping_the_placeholder_is_refused(row):
    """Typing 999.99 into the box would otherwise clear the flag and change nothing —
    the row would look priced and reviewed while still being neither."""
    make, conn = row
    pid, _ = make("999.99")
    _, err = _call(pid, "999.99")
    assert err is not None and err.status_code == 422
    with conn.cursor() as cur:
        cur.execute("SELECT enrichment_flags FROM products WHERE id=%s", (pid,))
        assert TILL_PRICED_FLAG not in (cur.fetchone()[0] or [])


def test_a_priced_row_then_sells(row):
    """End to end: the till guard blocked it, the price is set, the guard now passes."""
    from fastapi import HTTPException
    from src.routes.pos_router import _guard_unverified_price

    class _P:
        def __init__(self, price, name="Test Candle"):
            self.price, self.name = price, name

    make, conn = row
    pid, _ = make("999.99")
    with pytest.raises(HTTPException):
        _guard_unverified_price(_P(Decimal("999.99")))
    out, err = _call(pid, "20.00")
    assert err is None
    _guard_unverified_price(_P(Decimal("20.00")))          # must not raise


def test_it_is_a_bench_gap_kind_so_the_manager_gets_a_list():
    """A flag nobody can filter on is a flag nobody acts on."""
    from src.routes.pos_router import _BENCH_GAP_KINDS, _bench_gap_expr
    assert "till_priced" in _BENCH_GAP_KINDS
    assert _bench_gap_expr("till_priced") is not None


def test_the_cashier_panel_names_a_ROLE_not_a_person():
    """Angel, on reading "flagged for Felix" in the toast: *"should that be hard code or like
    role like manager or admin ... or did you pull that from the kc"*

    It was hardcoded — I typed it. Banco is meant to be cloned and self-hosted by other shops,
    and a shop that clones it should not find the previous owner's name in their till. A role is
    true in every deployment; a name is true in exactly one. (Comments naming Felix are
    provenance and stay — this is about text a cashier reads.)"""
    import pathlib
    html = (pathlib.Path(__file__).resolve().parents[1]
            / "templates" / "pos" / "scan.html").read_text(encoding="utf-8")

    # the two strings this feature puts on screen
    panel = "a manager to check"
    toast = "flagged for review"
    assert panel in html, "the cashier price panel stopped naming a role"
    assert toast in html, "the confirmation toast stopped naming a role"

    # and neither may name a person again
    for marker in ("flagged for Felix", "Felix to check"):
        assert marker not in html, f"a person's name is back in the till UI: {marker!r}"
