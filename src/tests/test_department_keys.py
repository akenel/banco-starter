"""Department keys — selling the stock that has no barcode and never will.

SPEC: onboarding/ai-coach/SPEC-department-keys.md

Angel, 2026-08-07, on what actually happens at the counter today:

    "figure pam is not going to try harder than a single scan and if nothing to scan she will
     create a whole new bong and never search it out in the catalog ... that is what I see happen
     with every non-ean item -- a fresh new bong or grinder"

Measured on prod the same day: **7% of the catalogue is scannable at all** — Bongs 0 of 178,
Bong & Pipe Accessories 0 of 253, Grinders 8 of 200. So he is describing arithmetic, not pessimism.

THE TWO PROPERTIES THAT MATTER, and both are tested here against a real database:

  1. A department line is NOT a product. It never gets a product_id, never enters the catalogue,
     and can never be turned into one after the fact.
  2. Its VAT comes from the DEPARTMENT, not from the "standard" fallback every other custom line
     uses. Without that, every fridge drink is silently taxed at the full rate — the failure is
     invisible, it is in the shop's favour, and it is exactly the kind that is found by an auditor
     rather than by a test.

And the structural test nobody should delete: BOTH sale paths must go through the same helper.
On 2026-08-03 `cashier_id == user_id` was removed from `_shift_sales`, tested, proved live — and
the identical filter sat twelve hundred lines away in `shift_transactions`. The report totalled 2
transactions while the itemised log underneath listed 1.
"""
import os
import re
import pathlib
import uuid
from decimal import Decimal

import pytest

from src.services.departments import (
    DEPARTMENTS, MAX_DEPARTMENTS, all_departments, get_department,
    is_department, receipt_text, vat_class,
)

PG = os.environ.get(
    "TEST_PG_DSN",
    "postgresql://helix_user:banco_local_dev@localhost:5442/helix_db",
)
PREFIX = "TEST-DEPT-"
# Seeded demo cashier — transactions.cashier_id is a hard FK to users.id.
PAM_UID = "00000000-0000-0000-0000-000000000001"
ROUTER = pathlib.Path(__file__).resolve().parents[1] / "routes" / "pos_router.py"


# ------------------------------------------------------------------ the buttons themselves

def test_there_are_at_most_ten_and_diverses_is_last():
    """SPEC §3.5. Every extra button is a decision at the till with a customer waiting — and if
    the catch-all is the easiest key to reach, everything becomes Diverses and the data is
    worthless."""
    assert len(DEPARTMENTS) <= MAX_DEPARTMENTS, "more than ten buttons — one must come out first"
    assert DEPARTMENTS[-1]["code"] == "DIV", "Diverses must be last on the strip"


def test_every_code_is_unique_and_alphanumeric():
    """SPEC §3.5: Code128 alphanumeric, never numeric, so a collision with a real EAN is
    structurally impossible rather than merely unlikely."""
    codes = [d["code"] for d in DEPARTMENTS]
    assert len(codes) == len(set(codes)), f"duplicate department code: {codes}"
    for c in codes:
        assert re.fullmatch(r"[A-Z]{3,8}", c), f"{c!r} must be letters only, never digits"


def test_receipt_text_is_her_word_not_the_english_heading():
    """The whole design rests on the cashier not having to translate mid-sale. She writes
    `Grips` in the day book, so the button says `Grips` — not `Grinder`, not `Grinders`."""
    assert receipt_text("GRIP") == "Grips"
    assert receipt_text("GLAS") == "Glas"
    assert receipt_text("GETR") == "Getränke"


def test_a_code_can_be_sent_lowercase_or_padded():
    """The till strip is scanned with a gun. Whitespace and case must never be why a sale fails."""
    assert is_department("grip") and is_department("  GRIP  ") and is_department("Grip")
    assert not is_department("NOPE") and not is_department("") and not is_department(None)


def test_every_department_maps_to_a_real_product_class():
    """`vat_class` must be a genuine PRODUCT_CLASSES key. A typo here would silently fall back to
    the standard rate for that whole bucket, and nothing would look wrong."""
    from src.services.catalog_taxonomy import PRODUCT_CLASSES
    for d in DEPARTMENTS:
        assert d["vat_class"] in PRODUCT_CLASSES, \
            f"{d['code']} has vat_class {d['vat_class']!r}, not a real product class"


def test_drinks_do_not_resolve_to_the_standard_class():
    """The one button with a different rate. If this ever reads "standard", every fridge drink is
    taxed at the full rate — invisible, in the shop's favour, and found by an auditor.
    (Whether the shop actually charges the reduced rate is SPEC §10.1 Q5, open for Ralph.)"""
    assert vat_class("GETR") == "cafe_food"
    assert vat_class("GLAS") == "standard"


def test_an_unknown_code_falls_back_to_the_conservative_rate():
    """Never a crash at the till, and never the cheaper rate by accident."""
    assert vat_class("WHATEVER") == "standard"
    assert vat_class(None) == "standard"


def test_all_departments_returns_copies():
    """The till gets this list every scan session. A caller mutating it must not edit the shop's
    tax configuration by accident."""
    got = all_departments()
    got[0]["receipt"] = "MUTATED"
    assert DEPARTMENTS[0]["receipt"] != "MUTATED"


# ------------------------------------------------------------------ the line resolver

class _Ln:
    """The fields `_resolve_custom_line` reads off a LineItemCreate."""
    def __init__(self, department_code=None, unit_price=None, name=None, notes=None,
                 is_giveaway=False):
        self.department_code = department_code
        self.unit_price = unit_price
        self.name = name
        self.notes = notes
        self.is_giveaway = is_giveaway


def _resolve(ln):
    from src.routes.pos_router import _resolve_custom_line
    return _resolve_custom_line(ln)


def test_a_plain_custom_line_is_completely_unchanged():
    """The product-as-change treat and manual entry must behave exactly as before — this branch
    is the shop's existing behaviour and the regression risk of the whole feature."""
    cls, notes = _resolve(_Ln(unit_price=Decimal("5.00"), name="Handmade thing"))
    assert cls == "standard"
    assert notes == "Handmade thing"


def test_a_department_line_takes_its_vat_from_the_department():
    cls, notes = _resolve(_Ln(department_code="GETR", unit_price=Decimal("3.50")))
    assert cls == "cafe_food"
    assert notes == "Getränke"


def test_the_department_name_leads_on_the_receipt_even_with_a_note():
    """A typed note must never replace the bucket the customer is being charged under."""
    cls, notes = _resolve(_Ln(department_code="GLAS", unit_price=Decimal("95.00"),
                              notes="blaue Bong"))
    assert notes.startswith("Glas"), notes
    assert "blaue Bong" in notes


def test_the_client_cannot_choose_the_receipt_text_or_the_tax():
    """The till sends four characters. Everything printed and everything taxed is resolved
    server-side, so a tampered client cannot ring CHF 95 of glass as café food."""
    cls, notes = _resolve(_Ln(department_code="GLAS", unit_price=Decimal("95.00"),
                              name="Getränke"))
    assert cls == "standard" and notes == "Glas"


@pytest.mark.parametrize("code", ["NOPE", "GRINDER", "123"])
def test_an_unknown_department_is_refused_not_guessed(code):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        _resolve(_Ln(department_code=code, unit_price=Decimal("5.00")))
    assert e.value.status_code == 422


@pytest.mark.parametrize("price", [Decimal("0"), Decimal("-1"), None])
def test_a_department_line_needs_a_real_price(price):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        _resolve(_Ln(department_code="GLAS", unit_price=price))
    assert e.value.status_code == 422


def test_the_fat_finger_ceiling_holds():
    """SPEC §4.4. A typo of 9500 instead of 95.00 must not become a sale — and above the ceiling
    the right answer is the catalogue, where the product is recorded properly."""
    from fastapi import HTTPException
    from src.routes.pos_router import _DEPT_PRICE_CEILING
    _resolve(_Ln(department_code="GLAS", unit_price=_DEPT_PRICE_CEILING))     # must not raise
    with pytest.raises(HTTPException) as e:
        _resolve(_Ln(department_code="GLAS", unit_price=_DEPT_PRICE_CEILING + Decimal("0.01")))
    assert e.value.status_code == 422


def test_a_department_line_cannot_be_a_giveaway():
    """A treat is a real product handed over free and is tracked for COGS. A department line has
    no product and no cost, so a free one would record nothing at all."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        _resolve(_Ln(department_code="GLAS", unit_price=Decimal("95.00"), is_giveaway=True))
    assert e.value.status_code == 422


# ------------------------------------------------------------------ BOTH sale paths

def test_both_sale_paths_go_through_the_one_helper():
    """THE STRUCTURAL GUARD. Two sale paths exist (`/transactions/{id}/items` and the atomic
    `/sales`), and on 2026-08-03 a fix landed in one and not its twin — the shift report totalled
    2 transactions while the itemised log under it listed 1.

    Counted with a regex that EXCLUDES the definition line, because on 2026-08-07 a guard test
    counted `_guard_unverified_price(product` and the `def` line matched the same pattern: a real
    call site could be deleted and all 15 tests still passed."""
    src = ROUTER.read_text(encoding="utf-8")
    calls = re.findall(r"(?<!def )_resolve_custom_line\((\w+)\)", src)
    assert sorted(calls) == ["item", "ln"], \
        f"expected exactly two call sites (item, ln); found {calls}"


def test_both_sale_paths_persist_the_department_code():
    """A code resolved for VAT but never written to the row is a sale nobody can report on."""
    src = ROUTER.read_text(encoding="utf-8")
    assert len(re.findall(r"department_code=\(", src)) == 2, \
        "both LineItemModel constructions must set department_code"
    assert len(re.findall(r"unresolved_barcode=\(", src)) == 2


def test_both_sale_paths_record_the_miss():
    src = ROUTER.read_text(encoding="utf-8")
    assert len(re.findall(r"await _record_catalog_miss\(", src)) == 2


def test_the_code_is_snapshotted_uppercase():
    """`GRIP`, `grip` and ` Grip ` must be one bucket in the day-close block, not three."""
    src = ROUTER.read_text(encoding="utf-8")
    assert len(re.findall(r"department_code\.strip\(\)\.upper\(\)", src)) >= 2


# ------------------------------------------------------------------ the miss log, against a real DB

def _conn():
    psycopg = pytest.importorskip("psycopg", reason="psycopg not installed")
    try:
        return psycopg.connect(PG, connect_timeout=3, autocommit=True)
    except Exception as e:                                     # noqa: BLE001
        pytest.skip(f"no Postgres at {PG.split('@')[-1]}: {type(e).__name__}")


@pytest.fixture
def misses():
    """Swept BY PREFIX, never by remembered id — a probe that tears down what it thinks it
    created dies on the corpse of the last crashed run (2026-08-03)."""
    conn = _conn()
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('catalog_miss')")
        if cur.fetchone()[0] is None:
            pytest.skip("catalog_miss table not created yet — start the app once")
        cur.execute(f"DELETE FROM catalog_miss WHERE barcode LIKE '{PREFIX}%'")
    yield conn
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM catalog_miss WHERE barcode LIKE '{PREFIX}%'")
    conn.close()


def _log(barcode, dept, price):
    import asyncio
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from src.routes.pos_router import _record_catalog_miss

    dsn = PG.replace("postgresql://", "postgresql+asyncpg://")

    async def go():
        engine = create_async_engine(dsn, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                await _record_catalog_miss(db, barcode, dept, price)
                await db.commit()
        finally:
            await engine.dispose()
    asyncio.run(go())


def test_the_same_code_counts_up_instead_of_making_a_second_row(misses):
    """The entire value of this table is the count. A second row for the same barcode would split
    the evidence and bury a real mover under two 'seen once' entries."""
    code = f"{PREFIX}{uuid.uuid4().hex[:8]}"
    for _ in range(3):
        _log(code, "GLAS", Decimal("95.00"))
    with misses.cursor() as cur:
        cur.execute("SELECT count(*), max(hit_count) FROM catalog_miss WHERE barcode=%s", (code,))
        rows, hits = cur.fetchone()
    assert rows == 1 and hits == 3


def test_it_remembers_every_price_it_was_rung_at(misses):
    """A code that always rings 12.00 is one product worth binding; one ringing 5/45/120 is a
    shelf position, a mis-scan, or a code shared across a range — and worth far less effort."""
    import json
    code = f"{PREFIX}{uuid.uuid4().hex[:8]}"
    for p in ("5.00", "45.00", "120.00"):
        _log(code, "ZUBE", Decimal(p))
    with misses.cursor() as cur:
        cur.execute("SELECT prices_seen, last_price FROM catalog_miss WHERE barcode=%s", (code,))
        seen, last = cur.fetchone()
    assert [str(Decimal(x)) for x in json.loads(seen)] == ["5.00", "45.00", "120.00"]
    assert Decimal(str(last)) == Decimal("120.00")


def test_counting_stops_once_the_code_became_a_real_product(misses):
    """SPEC §6. A resolved code is history, not a live backlog item — otherwise it keeps climbing
    the list forever and buries the codes that still need work."""
    code = f"{PREFIX}{uuid.uuid4().hex[:8]}"
    _log(code, "GLAS", Decimal("95.00"))
    with misses.cursor() as cur:
        cur.execute("UPDATE catalog_miss SET resolved_ean='7610000000000' WHERE barcode=%s", (code,))
    _log(code, "GLAS", Decimal("95.00"))
    with misses.cursor() as cur:
        cur.execute("SELECT hit_count FROM catalog_miss WHERE barcode=%s", (code,))
        assert cur.fetchone()[0] == 1, "a resolved code kept counting"


def test_an_empty_barcode_is_not_logged(misses):
    """The common case: a bong has nothing to scan. An empty row would be pure noise at the top
    of a backlog ranked by frequency."""
    before = _count(misses)
    _log("", "GLAS", Decimal("95.00"))
    _log(None, "GLAS", Decimal("95.00"))
    assert _count(misses) == before


def _count(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM catalog_miss")
        return cur.fetchone()[0]


def test_a_broken_miss_log_never_fails_the_sale():
    """Bookkeeping must not be able to stop the shop selling. Proven by handing it a session that
    raises on everything."""
    import asyncio

    class _Boom:
        async def execute(self, *a, **k):
            raise RuntimeError("database on fire")
        def add(self, *a, **k):
            raise RuntimeError("database on fire")

    from src.routes.pos_router import _record_catalog_miss
    asyncio.run(_record_catalog_miss(_Boom(), "123456", "GLAS", Decimal("5.00")))   # must not raise


# ------------------------------------------------------------------ END TO END, real DB

def _ring(lines, age_verified=False):
    """Ring a real sale through the ACTUAL atomic /sales endpoint function.

    Own engine per call with NullPool — the module-level AsyncSessionLocal pools against
    whichever event loop touched it first and asyncio.run() makes a new one every time, which
    surfaces as "got Future attached to a different loop" and has nothing to do with the code
    under test (2026-08-07, the first-price tests)."""
    import asyncio
    from fastapi import HTTPException
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from src.routes.pos_router import create_sale
    from src.schemas.pos_schema import SaleCreate

    dsn = PG.replace("postgresql://", "postgresql+asyncpg://")
    # TWINT, not cash, on purpose: a cash sale is gated on an OPEN cash box (the 2026-08-03
    # shop-owned drawer work), which is a different feature and would make these tests fail for
    # a reason that has nothing to do with department keys.
    payload = SaleCreate(client_uuid=uuid.uuid4(), lines=lines, payment_method="twint",
                         age_verified=age_verified)

    async def go():
        engine = create_async_engine(dsn, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                # `sub` must be a real users.id — transactions.cashier_id is a hard FK, and
                # _resolve_cashier_uid returns the username string when the sub is unusable,
                # which then fails the INSERT with an unrelated UUID error. Pam is the seeded
                # demo cashier (fixed PK 0000…0001).
                txn = await create_sale(sale=payload, db=db, current_user={
                    "sub": PAM_UID, "preferred_username": "pam"})
                return str(txn.id), txn.transaction_number
        finally:
            await engine.dispose()

    try:
        return asyncio.run(go()), None
    except HTTPException as e:
        return (None, None), e


@pytest.fixture
def sold():
    """Sweeps by transaction id captured during the test — and by the TEST note prefix, so a run
    that crashes mid-way does not poison the next one."""
    conn = _conn()
    made = []
    yield conn, made
    with conn.cursor() as cur:
        for tid in made:
            cur.execute("DELETE FROM line_items WHERE transaction_id=%s", (tid,))
            cur.execute("DELETE FROM transactions WHERE id=%s", (tid,))
        cur.execute(f"DELETE FROM catalog_miss WHERE barcode LIKE '{PREFIX}%'")
    conn.close()


def test_a_department_sale_rings_and_is_not_a_product(sold):
    """The whole feature in one test: a bong with no barcode is sold, the money is right, and
    NOTHING was added to the catalogue."""
    conn, made = sold
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM products")
        products_before = cur.fetchone()[0]

    (tid, num), err = _ring([{"department_code": "GLAS", "unit_price": "95.00", "quantity": 1}])
    assert err is None, f"department sale refused: {getattr(err, 'detail', err)}"
    made.append(tid)

    with conn.cursor() as cur:
        cur.execute("""SELECT product_id, department_code, notes, unit_price, line_total, vat_rate
                       FROM line_items WHERE transaction_id=%s""", (tid,))
        product_id, dept, notes, unit, total, rate = cur.fetchone()
        cur.execute("SELECT count(*) FROM products")
        products_after = cur.fetchone()[0]

    assert product_id is None, "a department line must never reference a catalog product"
    assert dept == "GLAS"
    assert notes == "Glas", f"the receipt must read the department name, got {notes!r}"
    assert Decimal(str(total)) == Decimal("95.00")
    assert products_after == products_before, "the catalogue grew — that is the bug this replaces"


def test_the_drinks_button_is_taxed_at_its_own_rate(sold):
    """The failure this prevents is invisible, in the shop's favour, and found by an auditor:
    without a per-department VAT class every fridge drink rings at the full rate."""
    conn, made = sold
    (tid_g, _), e1 = _ring([{"department_code": "GETR", "unit_price": "3.50", "quantity": 1,
                             "consumption": "takeaway"}])
    assert e1 is None, getattr(e1, "detail", e1)
    made.append(tid_g)
    (tid_s, _), e2 = _ring([{"department_code": "GLAS", "unit_price": "3.50", "quantity": 1,
                             "consumption": "takeaway"}])
    assert e2 is None
    made.append(tid_s)

    with conn.cursor() as cur:
        cur.execute("SELECT vat_rate FROM line_items WHERE transaction_id=%s", (tid_g,))
        drink_rate = Decimal(str(cur.fetchone()[0]))
        cur.execute("SELECT vat_rate FROM line_items WHERE transaction_id=%s", (tid_s,))
        glass_rate = Decimal(str(cur.fetchone()[0]))
    assert drink_rate < glass_rate, \
        f"takeaway drinks ({drink_rate}) must not be taxed like glass ({glass_rate})"


def test_the_unresolved_barcode_lands_in_the_miss_log(sold):
    """SPEC §6 — the scan that failed becomes a ranked backlog entry, attributed to the button
    the cashier actually reached for."""
    conn, made = sold
    code = f"{PREFIX}{uuid.uuid4().hex[:8]}"
    (tid, _), err = _ring([{"department_code": "GRIP", "unit_price": "15.00", "quantity": 1,
                            "unresolved_barcode": code}])
    assert err is None, getattr(err, "detail", err)
    made.append(tid)

    with conn.cursor() as cur:
        cur.execute("SELECT hit_count, department_code, last_price FROM catalog_miss WHERE barcode=%s",
                    (code,))
        row = cur.fetchone()
        cur.execute("SELECT unresolved_barcode FROM line_items WHERE transaction_id=%s", (tid,))
        on_line = cur.fetchone()[0]
    assert row is not None, "the failed scan was not recorded"
    assert row[0] == 1 and row[1] == "GRIP" and Decimal(str(row[2])) == Decimal("15.00")
    assert on_line == code, "the line must carry the code it was rung against"


def test_an_ordinary_custom_line_still_works(sold):
    """The regression risk of this whole feature: the product-as-change treat and manual entry
    share the branch a department line now goes through."""
    conn, made = sold
    (tid, _), err = _ring([{"name": "Handmade thing", "unit_price": "7.00", "quantity": 1}])
    assert err is None, getattr(err, "detail", err)
    made.append(tid)
    with conn.cursor() as cur:
        cur.execute("SELECT product_id, department_code, notes FROM line_items WHERE transaction_id=%s",
                    (tid,))
        pid, dept, notes = cur.fetchone()
    assert pid is None and dept is None and notes == "Handmade thing"


def test_a_bad_department_never_reaches_the_database(sold):
    conn, made = sold
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM line_items")
        before = cur.fetchone()[0]
    (tid, _), err = _ring([{"department_code": "NOPE", "unit_price": "5.00", "quantity": 1}])
    assert err is not None and err.status_code == 422
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM line_items")
        assert cur.fetchone()[0] == before, "a rejected sale still wrote lines"
