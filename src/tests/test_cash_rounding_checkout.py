"""The 5-rappen rounding, wired into the checkout path. Cash only, recorded, never absorbed.

`total_rounding.py` proved the arithmetic (29 tests) and was wired to nothing. These pin the
WIRING, which is where the risk actually lives:

  - it fires on CASH and on nothing else (a card sale must look exactly as it did yesterday)
  - `total` becomes the amount ACTUALLY charged, so every downstream consumer that already
    reads it -- the drawer expectation, VAT, change, the daily summary, CRM points -- is
    correct without knowing this ran
  - the move is recorded on its own column, so a receipt can name it
  - the Banana export does NOT double-count it (cash_total is already the rounded money)
  - the CLIENT MIRROR agrees with the server, cent for cent

That last one has bitten this repo before: a fix that was real, a mirror that disagreed, and
every unit test green. So the JS is executed here against the same cases, not eyeballed.
"""
import io
import json
import re
import shutil
import subprocess
from decimal import Decimal

import pytest

from src.db.models.transaction_model import PaymentMethod
from src.services.total_rounding import round_total, is_payable

STEP = Decimal("0.05")


class _Txn:
    """Just enough transaction for the helper: it only touches these three attributes."""
    def __init__(self, total):
        self.total = Decimal(str(total))
        self.rounding_adjustment = Decimal("0.00")
        self.transaction_number = "TXN-TEST-0001"


@pytest.fixture
def apply_rounding(monkeypatch):
    """`_apply_cash_rounding` with the store read stubbed to a plain CH shop (regime → 0.05)."""
    from src.routes import pos_router

    async def _no_store(_db):
        return None   # resolve_regime(None) → the CH default, which is what Artemis is

    monkeypatch.setattr(pos_router, "get_active_store_settings", _no_store)

    async def _run(total, method=PaymentMethod.CASH):
        txn = _Txn(total)
        adj = await pos_router._apply_cash_rounding(None, txn, method)
        return txn, adj

    return _run


# ── it fires on cash, and only on cash ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_a_cash_total_becomes_payable_in_coins(apply_rounding):
    """15% off CHF 74.10 = 62.99. There is no 4-rappen coin, so nobody can hand that over."""
    txn, adj = await apply_rounding("62.99")
    assert txn.total == Decimal("63.00")
    assert adj == Decimal("0.01") and txn.rounding_adjustment == Decimal("0.01")
    assert is_payable(txn.total, STEP)


@pytest.mark.asyncio
@pytest.mark.parametrize("method", [
    PaymentMethod.VISA, PaymentMethod.DEBIT, PaymentMethod.TWINT,
    PaymentMethod.BANK_TRANSFER, PaymentMethod.CRYPTO, PaymentMethod.OTHER,
])
async def test_electronic_payment_is_never_rounded(apply_rounding, method):
    """The constraint is physical and applies to coins. TWINT and cards settle the exact cent,
    so rounding them would give away up to four rappen a sale for no benefit at all."""
    txn, adj = await apply_rounding("62.99", method)
    assert txn.total == Decimal("62.99"), "a card sale must charge exactly what the ticket says"
    assert adj == Decimal("0.00") and txn.rounding_adjustment == Decimal("0.00")


@pytest.mark.asyncio
async def test_the_common_case_is_untouched(apply_rounding):
    """Every Artemis shelf price is already a 0.05 multiple, so the vast majority of cash sales
    pass straight through with adjustment 0 — and no Rounding line renders anywhere."""
    for t in ("4.90", "9.90", "40.00", "74.10", "283.00", "0.00"):
        txn, adj = await apply_rounding(t)
        assert txn.total == Decimal(t) and adj == Decimal("0.00")


@pytest.mark.asyncio
async def test_angels_case_the_one_that_set_the_direction(apply_rounding):
    """"the 2.99 becoming 2.95 is not good" — Felix holds the selling price and gives a treat
    instead of a discount, so rounding DOWN would be a silent unrequested discount."""
    txn, _ = await apply_rounding("2.99")
    assert txn.total == Decimal("3.00")


# ── it must never be the reason a sale fails ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_a_failed_store_read_degrades_to_no_rounding(monkeypatch):
    """A DB blip must not block a customer paying for a lighter. No rounding, exact total,
    exactly as yesterday — the sale still completes."""
    from src.routes import pos_router

    async def _boom(_db):
        raise RuntimeError("db gone")

    monkeypatch.setattr(pos_router, "get_active_store_settings", _boom)
    txn = _Txn("62.99")
    adj = await pos_router._apply_cash_rounding(None, txn, PaymentMethod.CASH)
    assert txn.total == Decimal("62.99") and adj == Decimal("0.00")


@pytest.mark.asyncio
async def test_a_regime_without_coins_disables_it(monkeypatch):
    """A shop self-hosting Banco where 1-cent coins still circulate gets exact totals, with
    nothing to configure — the step is a jurisdiction fact, not a store setting."""
    from src.routes import pos_router

    class _Store:
        fiscal_regime = "CH"

    async def _store(_db):
        return _Store()

    monkeypatch.setattr(pos_router, "get_active_store_settings", _store)
    monkeypatch.setattr(pos_router, "rounding_step", lambda _regime: Decimal("0"))
    txn = _Txn("70.39")
    adj = await pos_router._apply_cash_rounding(None, txn, PaymentMethod.CASH)
    assert txn.total == Decimal("70.39") and adj == Decimal("0.00")


# ── the property the books rely on ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_the_adjustment_reconciles_the_ticket_to_what_was_charged(apply_rounding):
    """subtotal - discount + adjustment == total, across 200 totals. Nothing is absorbed, so a
    rounding difference is always a recordable line rather than an unexplained rappen in the
    drawer — which is the whole reason the column exists rather than just rounding in place."""
    for i in range(200):
        ticket = Decimal("10.00") + Decimal(i) / Decimal("100")
        txn, adj = await apply_rounding(ticket)
        assert ticket + adj == txn.total
        assert is_payable(txn.total, STEP), f"{txn.total} cannot be handed over in coins"


# ── the Banana export must not count the rappen twice ────────────────────────────────────

def _banana_cash_lines(cash_total, rounding_total):
    """The export's decision, isolated: cash_total is ALREADY the rounded money (it sums
    `total`), so booking a Rundungsdifferenz on top of it without splitting the takings would
    count the same rappen twice. Mirrors get_daily_summary_csv."""
    cash_total, rounding_total = Decimal(str(cash_total)), Decimal(str(rounding_total))
    if rounding_total == 0:
        return [("POS daily sales - Cash", cash_total)]
    return [("POS daily sales - Cash (at ticket price)", cash_total - rounding_total),
            ("Rounding difference (5 Rp.) - Rundungsdifferenz", rounding_total)]


def test_the_export_lines_still_sum_to_what_is_in_the_drawer():
    """Felix reconciles the file against the box. Whatever we do with the presentation, the
    lines must add up to the money he counted."""
    for cash, rnd in [("540.79", "0.04"), ("283.00", "-0.06"), ("100.00", "0.00")]:
        lines = _banana_cash_lines(cash, rnd)
        assert sum(a for _, a in lines) == Decimal(cash)


def test_a_day_with_no_rounding_exports_exactly_as_before():
    """Nearly every day. The file Felix already imports must not change shape for nothing."""
    assert _banana_cash_lines("540.79", "0.00") == [("POS daily sales - Cash", Decimal("540.79"))]


def test_the_rounding_line_is_named_in_the_word_a_swiss_bookkeeper_knows():
    """Dissolved into the takings it is an unexplained few rappen a day; as a Rundungsdifferenz
    it is a thing every Swiss bookkeeper recognises on sight. Explainable beats invisible."""
    labels = [l for l, _ in _banana_cash_lines("540.79", "0.04")]
    assert any("Rundungsdifferenz" in l for l in labels)


# ── the client mirror, actually executed ─────────────────────────────────────────────────

_JS_HELPERS = re.compile(
    r"cashRoundStep\(\)\s*\{.*?\n            \},\s*"
    r".*?payableTotal\(\)\s*\{.*?\n            \},", re.S)


def _extract_mirror():
    """Pull cashRoundStep()/payableTotal() straight out of checkout.html, so this test breaks
    if someone edits the template and not the server (or the other way round)."""
    src = io.open("src/templates/pos/checkout.html", encoding="utf-8").read()
    m = _JS_HELPERS.search(src)
    assert m, "could not find the rounding mirror in checkout.html — did it get renamed?"
    return m.group(0)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_the_till_screen_agrees_with_the_server_cent_for_cent():
    """THE ONE THAT MATTERS. A client mirror that drifts from the server is this repo's most
    expensive bug shape: the fix is real, every unit test is green, and the screen still lies.
    So run the actual JS from the template over the same totals and compare.

    A disagreement here means the cashier sees one figure and the receipt prints another.
    """
    totals = [f"{c / 100:.2f}" for c in range(0, 2001)] + [
        "62.99", "8.91", "42.66", "16.92", "6.21", "70.40", "2.99", "2.91", "1234.56"]
    script = """
    const M = { cartData: { totals: {} }, paymentMethod: 'cash', %s };
    global.POSConfig = { regime: { cash_rounding_step: '0.05' } };
    const out = {};
    for (const t of %s) { M.cartData.totals.total = parseFloat(t); out[t] = M.payableTotal(); }
    console.log(JSON.stringify(out));
    """ % (_extract_mirror().rstrip().rstrip(","), json.dumps(totals))
    # The helpers reference POSConfig as a bare identifier; expose it as a global for node.
    script = script.replace("(POSConfig || {})", "(global.POSConfig || {})")
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, f"the mirror did not run:\n{res.stderr}"
    js = json.loads(res.stdout)

    for t in totals:
        server = round_total(t, STEP)["rounded"]
        client = Decimal(str(js[t])).quantize(Decimal("0.01"))
        assert client == server, f"total {t}: till shows {client}, server charges {server}"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_the_till_screen_does_not_round_a_card_sale_either():
    """The mirror has to make the same cash-only distinction, or the screen would show a
    rounded TO PAY and the card would then be charged the exact cent."""
    script = """
    const M = { cartData: { totals: { total: 62.99 } }, paymentMethod: 'visa', %s };
    global.POSConfig = { regime: { cash_rounding_step: '0.05' } };
    console.log(JSON.stringify(M.payableTotal()));
    """ % _extract_mirror().rstrip().rstrip(",")
    script = script.replace("(POSConfig || {})", "(global.POSConfig || {})")
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    assert Decimal(str(json.loads(res.stdout))) == Decimal("62.99")
