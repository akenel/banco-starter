"""Re-scan a packet you already sold, and finish the row while you are holding it.

Built 2026-08-03 from Angel playing a cashier at the till. The simulation, in his words:

    a customer spots a new grinder on the counter · the scan misses · Pam types "grinder /
    15.00" and sells it · "now somebody has to go back and say, listen, that's a new box of
    grinders, we got twenty of them, and that was the first one he sold"

Everything about that is correct behaviour. A ten-second quick-add with someone waiting is the
right call, and the till binds the scanned barcode while it does it (`scan.html` mints the SKU
as `LZ-`+barcode). The failure was entirely in what happened NEXT — three screens each dropping
the row in a different way:

  1. the cockpit's SOLD tab sorted busiest-first, so a row sold ONCE sat below 37 others
  2. shelf intake reported the re-scan as "✅ already scans correctly" — true, and a stub
  3. the bench card could fix category, price, cost, description, photo and 18+ … but not the
     NAME, which is the only thing actually wrong with a row called "grinder"

None of the three errored. Every one of them looked like it had done its job. These pin the
decisions, not the plumbing.
"""
import re
import subprocess
from pathlib import Path

import pytest

from src.routes.pos_router import sort_sold_queue, _readiness, _HALFBAKED_CATEGORIES


# ── a stand-in for the row a till quick-add leaves behind ────────────────────────────────

class FakeProduct:
    """Only the fields `_readiness` reads. A narrow copy is exactly what burned us on
    2026-08-03 (a partial SELECT made working code look like a compliance failure), so this
    one is deliberately a TEST double and never loads real rows."""

    def __init__(self, name="grinder", category="Unsorted", cost=None,
                 image_url=None, description=None):
        self.name = name
        self.category = category
        self.cost = cost
        self.image_url = image_url
        self.description = description


def _row(pid, qty, revenue, last_sold):
    return {"product_id": pid, "qty_sold": qty, "revenue": revenue, "last_sold": last_sold}


# ── 1 · the order ────────────────────────────────────────────────────────────────────────

def test_the_thing_that_just_sold_is_first():
    """The bug, exactly as Angel hit it: one sale twenty minutes ago, buried under a backlog.

    Under busiest-first the grinder is LAST of the three. It is the only one he can still do
    anything useful about — he remembers the customer, and the box of twenty is on the counter."""
    items = [
        _row("papers", 40, 120.00, "2026-07-28T09:00:00"),
        _row("filters", 12, 30.00, "2026-08-01T14:00:00"),
        _row("grinder", 1, 15.00, "2026-08-03T17:40:00"),
    ]
    assert sort_sold_queue(items) == "newest"
    assert [i["product_id"] for i in items] == ["grinder", "filters", "papers"]


def test_busiest_is_still_there_for_a_backlog_sweep():
    """Removing it would trade one bad default for another. Most units sold = most tills
    affected, which is the right order when you sit down to clear the whole pile."""
    items = [
        _row("papers", 40, 120.00, "2026-07-28T09:00:00"),
        _row("grinder", 1, 15.00, "2026-08-03T17:40:00"),
    ]
    assert sort_sold_queue(items, "busiest") == "busiest"
    assert [i["product_id"] for i in items] == ["papers", "grinder"]


def test_an_unknown_sort_falls_back_to_newest_not_to_an_error():
    """A stale bookmark or a typo in a query string must not 500 the safety-net screen."""
    items = [_row("a", 1, 1.0, "2026-08-01T10:00:00"), _row("b", 1, 1.0, "2026-08-02T10:00:00")]
    assert sort_sold_queue(items, "sideways") == "newest"
    assert sort_sold_queue(items, "") == "newest"
    assert sort_sold_queue(items, None) == "newest"
    assert [i["product_id"] for i in items] == ["b", "a"]


def test_a_null_last_sold_sorts_last_and_never_crashes():
    """`completed_at` is always set on a completed sale — but the ONE screen whose job is
    catching what fell through is the last place that should trust an invariant."""
    items = [
        _row("ghost", 3, 9.00, None),
        _row("grinder", 1, 15.00, "2026-08-03T17:40:00"),
    ]
    assert sort_sold_queue(items) == "newest"
    assert [i["product_id"] for i in items] == ["grinder", "ghost"]


def test_ties_break_on_quantity_so_the_order_is_stable():
    """Two sales in the same second is a real thing at a busy till."""
    same = "2026-08-03T17:40:00"
    items = [_row("one", 1, 5.0, same), _row("five", 5, 25.0, same)]
    sort_sold_queue(items)
    assert [i["product_id"] for i in items] == ["five", "one"]


# ── 2 · scans fine ≠ finished ────────────────────────────────────────────────────────────

def test_the_grinder_scans_perfectly_and_is_still_a_stub():
    """The whole reason the third bucket exists. Triage asked one question — does this code
    resolve? — and the answer for a till quick-add is a confident yes."""
    score, gripes = _readiness(FakeProduct())
    assert score == 0
    assert set(gripes) == {"category", "cost", "photo", "description"}


def test_unsorted_is_not_a_category():
    """"Unsorted" and "Other" are the same dumping ground wearing different words. If the
    readiness read ever accepts one, a stub starts reporting itself as done."""
    for junk in _HALFBAKED_CATEGORIES:
        score, gripes = _readiness(FakeProduct(category=junk))
        assert "category" in gripes, f"{junk!r} was accepted as a real category"


def test_a_finished_row_is_finished():
    """The other direction — the bucket must not manufacture work. A complete row has to come
    back clean or every shelf scan grows a fake to-do list."""
    p = FakeProduct(
        name="Champ High White Leaf Grinder 4-part 50mm",
        category="Grinders", cost=8.50,
        image_url="https://example.invalid/grinder.jpg",
        description="Four-part aluminium grinder, 50 mm, white leaf design, with pollen catcher.",
    )
    score, gripes = _readiness(p)
    assert (score, gripes) == (100, [])


def test_a_description_that_is_just_the_name_again_is_not_a_description():
    """The lazy 'done' this read exists to catch: something in the box, nothing in the words."""
    name = "Champ High White Leaf Grinder 4-part 50mm"
    _, gripes = _readiness(FakeProduct(
        name=name, category="Grinders", cost=8.50,
        image_url="https://example.invalid/g.jpg", description=name))
    assert "description" in gripes


# ── 3 · the client split, EXECUTED ───────────────────────────────────────────────────────
#
# `finishedKnown()` / `unfinishedKnown()` decide whether Angel's grinder appears in the new
# bucket at all, and they turn on `is_finished === false` vs `!== false` — a predicate that
# fails silently and looks fine. This repo's most expensive bug shape is client logic that
# drifts with every unit test green (the `pc.`/`Stk.` size table, dead for weeks), so the test
# EXTRACTS the helpers out of the template and runs them in node. A mirror test that never runs
# the mirror is decoration.

_INTAKE = Path(__file__).resolve().parents[2] / "src/templates/pos/shelf_intake.html"


def _extract(fn_name: str) -> str:
    """Pull one method body out of the Alpine data object in the template."""
    src = _INTAKE.read_text(encoding="utf-8")
    m = re.search(rf"^    {re.escape(fn_name)}\(.*?^    \}},", src, re.S | re.M)
    if not m:
        m = re.search(rf"^    {re.escape(fn_name)}\(\w*\)\s*\{{.*?\}},$", src, re.S | re.M)
    assert m, f"{fn_name} not found in {_INTAKE.name} — did the template change shape?"
    return m.group(0).rstrip(",")


@pytest.mark.skipif(not __import__("shutil").which("node"), reason="node not installed")
def test_the_known_split_runs_and_puts_the_grinder_in_the_work_bucket():
    helpers = ",\n".join(_extract(f) for f in ("_known", "finishedKnown", "unfinishedKnown"))
    script = f"""
const page = {{
  result: {{ known: [
    {{ barcode: "3661075283438", name: "grinder", is_finished: false, ready_score: 0 }},
    {{ barcode: "7611889110310", name: "Quollfrisch Hell", is_finished: true, ready_score: 100 }},
    {{ barcode: "84157072", name: "legacy row with no readiness field" }}
  ] }},
  {helpers}
}};
const fin = page.finishedKnown().map(k => k.name);
const un  = page.unfinishedKnown().map(k => k.name);
console.log(JSON.stringify({{fin, un, total: page._known().length}}));
"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    import json
    r = json.loads(out.stdout)

    # the grinder — and ONLY the grinder — is work
    assert r["un"] == ["grinder"]
    # a row from an older response carries no is_finished at all. Treat it as finished rather
    # than inventing work: a shelf scan that suddenly claims fifty new to-dos after a deploy
    # would be indistinguishable from a real regression.
    assert r["fin"] == ["Quollfrisch Hell", "legacy row with no readiness field"]
    # and nothing is lost or double-counted between the two lists
    assert len(r["fin"]) + len(r["un"]) == r["total"] == 3


@pytest.mark.skipif(not __import__("shutil").which("node"), reason="node not installed")
def test_the_split_survives_a_response_with_no_known_list_at_all():
    """A failed triage leaves `result` null. The summary cards call these helpers on every
    render, so an exception here blanks the whole screen rather than one number."""
    helpers = ",\n".join(_extract(f) for f in ("_known", "finishedKnown", "unfinishedKnown"))
    script = f"""
const empty = {{ result: null, {helpers} }};
const noKnown = {{ result: {{}}, {helpers} }};
console.log(JSON.stringify([
  empty.finishedKnown().length, empty.unfinishedKnown().length,
  noKnown.finishedKnown().length, noKnown.unfinishedKnown().length,
]));
"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[0,0,0,0]"


@pytest.mark.skipif(not __import__("shutil").which("node"), reason="node not installed")
def test_gap_words_reads_as_english_not_as_field_names():
    """The badge sits next to a barcode on a shelf. "no real category · no cost" is a sentence
    a person acts on; "category · cost" is a schema."""
    script = f"""
const page = {{ {_extract("gapWords")} }};
console.log(JSON.stringify([
  page.gapWords({{ready_gaps: ["category", "cost", "photo", "description"]}}),
  page.gapWords({{ready_gaps: []}}),
  page.gapWords({{}}),
  page.gapWords(null),
  page.gapWords({{ready_gaps: ["something_new"]}}),
]));
"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    import json
    words, empty, missing, null, unknown = json.loads(out.stdout)
    assert words == "no real category · no cost · no photo · no description"
    assert empty == missing == null == ""
    # an unrecognised code prints itself rather than vanishing — a silently dropped gap is how
    # a screen ends up quietly claiming a row is more finished than it is
    assert unknown == "something_new"
