"""Anyone on the till may look back; the page must say which days it is showing.

Two decisions, both Angel's, both made on 2026-08-07 while testing as `pam`.

1. HE COULD NOT SEE LAST WEEK. `list_transactions` honoured `date_from`/`date_to` for a
   manager only, so a cashier's date pickers were live on screen and thrown away by the
   server — she set 01.05–07.08, got four rows from today, and nothing said why.

       "bro i wanted to see all cash sales that is the point so if they want to go and look
        at last week they can"

   Opened to every pos role. It costs nothing: the endpoint is READ-ONLY, cashiers already
   see every one of today's sales by every cashier (BL-95), and refund/void/edit are separate
   manager-gated endpoints. `is_manager` is still computed there — it is what a bigger shop
   would re-gate on.

2. THE HEADLINE NUMBER LIED ABOUT ITS SCOPE. The page opens filtered to today and labelled
   the totals "Total Transactions" / "Total Sales" with nothing saying so: 7 and CHF 216.60,
   over 46 transactions and CHF 2,051.24 of real history. Third time for that exact shape —
   "Age-restricted (18+): 3" over a 5,162-product catalogue, "Uncategorized: 0" hiding 78
   products. The arithmetic was right every time and the caption was wrong.
"""
import pathlib
import re

ROUTER = (pathlib.Path(__file__).resolve().parents[1] / "routes" / "pos_router.py")
PAGE = (pathlib.Path(__file__).resolve().parents[1] / "templates" / "pos" / "transactions.html")


def _endpoint_src() -> str:
    s = ROUTER.read_text(encoding="utf-8")
    i = s.index('@router.get("/transactions", response_model=list[TransactionRead])')
    return s[i:i + 4000]


def test_a_date_range_is_not_gated_on_being_a_manager():
    """The regression guard. If someone re-adds `is_manager and` here, a cashier's date
    pickers go back to being decoration that silently does nothing."""
    src = _endpoint_src()
    assert not re.search(r"if\s+is_manager\s+and\s+\(date_from\s+or\s+date_to\)", src), \
        "the date range is manager-gated again — a cashier's pickers would be silently ignored"
    assert re.search(r"if\s+date_from\s+or\s+date_to:", src), \
        "the date range branch is gone entirely"


def test_no_date_filter_still_means_today():
    """Today-first is the right landing page for a till — opening on all-time would get slower
    every week and answer a question nobody asked."""
    src = _endpoint_src()
    assert re.search(r"else:\s*\n\s*lo = hi = datetime\.now\(SHOP_TZ\)\.date\(\)", src), \
        "the default is no longer today"


def test_refunds_and_voids_are_still_manager_only():
    """Opening the READ path must not have opened a write path. The whole argument for widening
    the date range was that this endpoint changes nothing."""
    s = ROUTER.read_text(encoding="utf-8")
    i = s.index('/transactions/{transaction_id}/refund')
    window = s[i:i + 1200]
    assert "require_roles" in window, "the refund endpoint lost its role gate"
    assert "pos-manager" in window or "pos-admin" in window, \
        "refund is no longer restricted to managers/admins"


def test_the_page_prints_the_range_it_is_showing():
    """A scoped number must carry its scope. This is the third instance of the same bug in this
    repo, so it gets a test rather than a comment."""
    s = PAGE.read_text(encoding="utf-8")
    assert "rangeLabel()" in s, "the transaction history no longer states its date range"
    assert 'data-i18n="transactions.showing"' in s, "the 'Showing …' caption is gone"
    # and it must sit ABOVE the totals, not somewhere further down the page
    assert s.index("rangeLabel()") < s.index('data-i18n="transactions.total_transactions"'), \
        "the range caption must appear before the numbers it qualifies"


def test_the_range_label_handles_every_shape():
    """Executed rather than read — see the node check in the commit. Here we only pin that all
    four branches still exist, so a refactor cannot quietly drop one."""
    s = PAGE.read_text(encoding="utf-8")
    fn = s[s.index("rangeLabel() {"):]
    fn = fn[:fn.index("\n            },")]
    for key in ("range_all", "range_today", "range_from", "range_until"):
        assert key in fn, f"rangeLabel lost the {key} case"
