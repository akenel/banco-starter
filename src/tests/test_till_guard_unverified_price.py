"""A placeholder price must not reach a customer.

2026-08-06 — the count that forced this: **110 active products** priced 999.99, 99.00 or 0.00,
every one scannable at the till. Scan the RAW Mason Jar (ean 716165298076) and the drawer asks
for CHF 999.99. Thirty-two were created that afternoon during the papers-and-filters intake, so
the pile grows every time the shop does the right thing and captures new stock.

The placeholder is the honest answer to "what does this cost?" before a human has decided. The
defect is that a placeholder and a real price look identical at the moment money changes hands —
the same shape as the green "✅ Balanced within tolerance" printed over a cash box nobody counted.

WHAT IS PINNED HERE

  1. `_guard_unverified_price` raises 400 for every sentinel, passes real prices, and lets a
     giveaway through (a treat rings 0.00 by design and never reads product.price).
  2. BOTH sale paths call it — the atomic `/sales` and the legacy `/transactions/{id}/items`.
     A guard on one of two doors is not a guard: on 2026-08-03 `cashier_id == user_id` was
     removed from `_shift_sales` and left standing in `shift_transactions` twelve hundred lines
     away, and the report disagreed with its own itemised log.
  3. The till's JS list is FED from the Python tuple, never re-typed. This repo's most expensive
     bug shape is a client mirror that drifts silently — the pc./Stk. size table was dead for
     weeks with every unit test green.
  4. The detail modal closes only when the item really went into the cart. It used to close
     unconditionally, which would have slammed shut over the price-fix panel the guard opens —
     the guard would have LOOKED like it did nothing.
"""
import pathlib
import re
from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.routes.pos_router import UNVERIFIED_PRICES, _guard_unverified_price

SRC = pathlib.Path(__file__).resolve().parents[1]
SCAN_HTML = (SRC / "templates" / "pos" / "scan.html").read_text(encoding="utf-8")
ROUTER = (SRC / "routes" / "pos_router.py").read_text(encoding="utf-8")


class _P:
    def __init__(self, price, name="RAW Mason Jar"):
        self.price = price
        self.name = name


@pytest.mark.parametrize("sentinel", [Decimal("99.00"), Decimal("999.99")])
def test_a_placeholder_price_is_refused(sentinel):
    with pytest.raises(HTTPException) as e:
        _guard_unverified_price(_P(sentinel))
    assert e.value.status_code == 400
    # the message must name the product — "invalid price" tells a cashier nothing
    assert "RAW Mason Jar" in e.value.detail
    assert str(sentinel) in e.value.detail


@pytest.mark.parametrize("real", ["2.50", "0.05", "69.00", "120.00", "999.98", "99.01"])
def test_a_real_price_passes(real):
    _guard_unverified_price(_P(Decimal(real)))       # must not raise


def test_a_giveaway_passes_even_at_a_placeholder_price():
    """A treat rings 0.00 by design and never reads product.price — blocking it would break
    the 6 Treats without protecting anybody."""
    _guard_unverified_price(_P(Decimal("999.99")), is_giveaway=True)


def test_a_null_price_is_not_mistaken_for_a_sentinel():
    _guard_unverified_price(_P(None))


def test_both_sale_paths_call_the_guard():
    """/sales and /transactions/{id}/items both reach the drawer. Miss one and it is not a gate.

    Counts CALL sites only. The first version of this test counted
    `_guard_unverified_price(product` and so counted the `def` line too — deleting a real call
    site left 2 and the test still passed. It was checking the wrong thing while looking right,
    which is the failure it exists to prevent."""
    calls = re.findall(r"^\s+_guard_unverified_price\(product,\s*(\w+)\.is_giveaway\)\s*$",
                       ROUTER, re.M)
    assert len(calls) == 2, (
        f"expected exactly 2 call sites, found {len(calls)}: {calls}. The atomic /sales path "
        f"(ln.is_giveaway) and the legacy /transactions/{{id}}/items path (item.is_giveaway) "
        f"must BOTH guard — /scan reaches the drawer through /items.")
    assert set(calls) == {"ln", "item"}, calls
    # and the helper itself must still exist and raise
    assert "def _guard_unverified_price(" in ROUTER


def test_the_till_list_is_fed_from_python_not_retyped():
    """The JS must render the server's tuple, not a hand-copied literal."""
    assert "unverified_prices | default([]) | tojson" in SCAN_HTML, \
        "scan.html stopped rendering the server's list"
    # and no hardcoded sentinel numbers anywhere in the page's JS
    for lit in ("999.99", "99.00"):
        bad = [ln.strip() for ln in SCAN_HTML.splitlines()
               if lit in ln and "UNVERIFIED_PRICES" in ln]
        assert not bad, f"a sentinel was re-typed into scan.html: {bad}"
    # the server must actually pass it in — both render sites
    assert ROUTER.count('"unverified_prices": [str(p) for p in UNVERIFIED_PRICES]') >= 2


def test_the_detail_modal_closes_only_on_a_real_add():
    """Guard the guard: an unconditional close would hide the price-fix panel it opens."""
    assert 'if (addToCart(detailProduct)) detailProduct=null' in SCAN_HTML
    assert 'addToCart(detailProduct); detailProduct=null' not in SCAN_HTML, \
        "the modal is closing unconditionally again — the price panel would flash and vanish"


def test_add_to_cart_returns_whether_it_added():
    """The boolean is load-bearing for the line above; a bare `return;` would read as false."""
    body = re.search(r"addToCart\(product, qty = 1\) \{(.*?)\n            \},", SCAN_HTML, re.S)
    assert body, "addToCart not found — did it get renamed?"
    src = body.group(1)
    assert "return false;" in src and "return true;" in src, src


def test_the_js_guard_actually_blocks_a_sentinel():
    """Run the real predicate in node over the real sentinels — a mirror test that never runs
    the mirror is decoration (2026-08-03)."""
    node = pytest.importorskip("shutil").which("node")
    if not node:
        pytest.skip("node not installed")
    import subprocess, json, tempfile, os
    m = re.search(r"needsPrice\(product\) \{(.*?)\n            \},", SCAN_HTML, re.S)
    assert m, "needsPrice not found in scan.html"
    js = (f"const UNVERIFIED_PRICES = {json.dumps([float(p) for p in UNVERIFIED_PRICES])};\n"
          f"function needsPrice(product) {{{m.group(1)}}}\n"
          "const cases = [[999.99,true],[99.00,true],[2.50,false],[69.00,false],"
          "[null,false],[0.05,false]];\n"
          "for (const [p, want] of cases) {\n"
          "  const got = needsPrice({price: p});\n"
          "  if (got !== want) { console.log('FAIL', p, got, want); process.exit(1); }\n"
          "}\nconsole.log('OK');\n")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(js); path = f.name
    try:
        r = subprocess.run([node, path], capture_output=True, text=True, timeout=20)
        assert r.returncode == 0, f"needsPrice disagrees with the Python sentinels:\n{r.stdout}{r.stderr}"
        assert "OK" in r.stdout
    finally:
        os.unlink(path)
