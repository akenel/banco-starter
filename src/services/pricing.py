"""BL-26 quantity-break (tier) pricing.

A product may carry ``price_tiers`` = ``[{"min_qty": int, "unit_price": "4.90"}, ...]``.
When a cart line's quantity reaches a tier's ``min_qty``, that tier's unit price applies
to the WHOLE line. It is a PRICE (feeds VAT + totals), not a discount.

Per Angel's decision (2026-07-11), a line that got a *volume* break (``min_qty >= 2``) is
FINAL — no further member/manual discount stacks on it. ``tier_unit_price`` returns that
flag so the checkout can exclude the line from the discount base.

unit_price is stored as a STRING in JSON (e.g. "4.90") to keep money exact through the
JSON round-trip; everything quantizes to cents on read.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP

_CENT = Decimal("0.01")


def _q(v) -> Decimal:
    """Quantize any numeric-ish value to cents (money-safe compare/serialize)."""
    return Decimal(str(v)).quantize(_CENT, rounding=ROUND_HALF_UP)


logger = logging.getLogger(__name__)


def _bundle_total(price_tiers, base, qty):
    """Total for ``qty`` under BUNDLE tiers: whole packs, then start again.

    2026-08-21. Angel asked Ralph, who works the counter, what a customer pays for FOUR packs
    when the deal is "3 for 10". Ralph: *"I would give the tier pricing for the first 3 packs,
    but if the customer buys 4 then the pricing starts again — so 4 packs would be 14 total."*
    Felix added that ~90% of customers buy exactly 3, or else a whole box.

    That is not what Banco charged. Bundle mode divided the pack price into a UNIT rate and
    applied it to everything past the threshold, so four packs rang up 13.33 and five 16.67 —
    right on exact multiples, quietly generous everywhere in between. On 41 rolls, a 4-pack
    basket is an ordinary Tuesday.

    Greedy, one pack at a time, recursing on the remainder. That handles a nested ladder for
    free: with "3 for 10" and "10 for 24", thirteen packs is one ten (24.00) and then the
    remaining three fall to their own rung (10.00) — 34.00, not four threes and a single.
    """
    if qty <= 0:
        return Decimal("0")
    best_qty = None
    best_up = None
    for t in price_tiers or []:
        try:
            mq = int(t.get("min_qty"))
            up = t.get("unit_price")
        except (TypeError, ValueError, AttributeError):
            continue
        if up is None or mq < 1 or qty < mq:
            continue
        if best_qty is None or mq > best_qty:
            best_qty, best_up = mq, up
    if best_qty is None:
        return base * Decimal(qty)
    return Decimal(str(best_up)) + _bundle_total(price_tiers, base, qty - best_qty)


def tier_unit_price(price_tiers, base_price, qty, mode="per_unit"):
    """Resolve the effective UNIT price for ``qty`` from ``price_tiers``.

    Returns ``(unit_price: Decimal, volume_break: bool)``. The winning tier is the one with
    the highest ``min_qty`` still ``<= qty``. ``mode`` decides what a tier's stored value means:
      - ``"per_unit"`` (default, Artemis style): the value is the price EACH at ``qty >= min_qty``.
      - ``"bundle"`` ("N for X"): the value is the TOTAL for a pack of ``min_qty``. WHOLE PACKS
        are taken, then the deal starts again on the remainder — "3 for 10" charges 14.00 for
        four, not 13.33 (Ralph's rule, see ``_bundle_total``). The per-unit rate returned is
        that total divided by qty, FULL-PRECISION, so a caller that multiplies by qty lands
        exactly on it (the caller quantizes the LINE — see ``tier_line_total``).
    ``volume_break`` is True only for a genuine break (``min_qty >= 2``) — flags the line
    discount-final. Falls back to ``base_price`` when there are no tiers or none apply.
    """
    base = _q(base_price)
    if not price_tiers:
        return base, False
    best_qty = None
    best_up = None
    for t in price_tiers:
        try:
            mq = int(t.get("min_qty"))
            up = t.get("unit_price")
        except (TypeError, ValueError, AttributeError):
            continue
        if up is None or mq < 1 or qty < mq:
            continue
        if best_qty is None or mq > best_qty:
            best_qty, best_up = mq, up
    if best_qty is None:
        return base, False
    if mode == "bundle":
        # Whole packs then start again (see _bundle_total). Returned as a per-unit RATE because
        # both till callers store a unit price and multiply by qty — the rate carries full
        # precision so that multiplication lands back on the exact pack total.
        total = _bundle_total(price_tiers, base, qty)
        # Never above the flat price. Same doctrine as the guard below, and it also stops a
        # badly-ordered ladder (a bigger pack priced worse than a smaller one) from costing the
        # customer more than having no deal at all.
        if total > base * Decimal(qty):
            total = base * Decimal(qty)
        eff = total / Decimal(qty)
    else:
        eff = _q(best_up)

    # ── A QUANTITY BREAK CAN NEVER COST MORE THAN BUYING ONE ──────────────────────────────
    #
    # Found live 2026-07-31 on TAM-21669 "Gizeh King Size": base CHF 1.40, tiers
    # [{3: 4.00}, {10: 12.00}], and tier_mode NULL — so the till fell back to per_unit and
    # would have charged 3 × 4.00 = CHF 12.00 for three packs that cost CHF 4.20 flat, and
    # CHF 120.00 for ten. A 3x overcharge, on a live product, in a live shop.
    #
    # The data is plainly BUNDLE-shaped ("3 for 4.00", "10 for 12.00" — both a real discount
    # against 4.20 and 14.00), it just never had its mode recorded. Rather than guess the
    # operator's intent, enforce the one thing that is true of every quantity break in
    # existence: BUYING MORE MUST NEVER RAISE THE UNIT PRICE. A "per unit" tier above the base
    # price is a contradiction, not a price.
    #
    # So: re-read such a tier as the pack TOTAL, which is what it always was — and if even that
    # exceeds base, ignore the tier entirely and charge the flat price. Both branches can only
    # ever move money toward the customer, which is the only safe direction for a guess.
    if eff > base:
        as_bundle = Decimal(str(best_up)) / Decimal(best_qty)

        # ── HOW FAR A GUESS IS ALLOWED TO GO ──────────────────────────────────────────────
        #
        # The re-read above was written to protect the customer, and its comment said both
        # branches "can only ever move money toward the customer, which is the only safe
        # direction for a guess." That reasoning was wrong, and on 2026-08-21 the live shop
        # showed how wrong:
        #
        #   Gizeh Rolls Slim Pink — base CHF 2.90, tier {min_qty 10, unit_price "3.10"}
        #   3.10 > 2.90, so it was re-read as "10 for 3.10" = CHF 0.31 each.
        #   TEN packs rang up at CHF 3.10. Nineteen rang up at CHF 5.89.
        #
        # Moving money toward the customer WITHOUT LIMIT is not safety, it is just the other
        # loss. A guess is only worth making while it stays plausible: "3 for 5.00" against a
        # base of 2.00 is a believable 17% deal, "10 for 3.10" against 2.90 is a 89% collapse
        # and no shop has ever offered it. Past that line the honest reading is that the data
        # is simply wrong, and the safe answer is the price on the shelf label.
        #
        # This bounds ONLY the guess. A tier written properly — at or below base, or with
        # tier_mode='bundle' — never reaches here, so genuine deep discounts (Purize 500 for
        # 0.60 against a base of 1.50) are untouched.
        _PLAUSIBLE_FLOOR = Decimal("0.5")
        if as_bundle <= base and as_bundle >= base * _PLAUSIBLE_FLOOR:
            logger.warning(
                "tier price %s for min_qty %s is ABOVE the base price %s — reading it as a pack "
                "total (%s/unit). Set tier_mode='bundle' on this product to make it explicit.",
                best_up, best_qty, base, as_bundle)
            return as_bundle, best_qty >= 2
        logger.warning(
            "tier price %s for min_qty %s is above the base price %s, and reading it as a pack "
            "total gives %s/unit — too far below %s to be a real deal. The tier data is wrong; "
            "charging the flat price. FIX THIS PRODUCT.",
            best_up, best_qty, base, as_bundle, base)
        return base, False

    return eff, best_qty >= 2


def tier_line_total(price_tiers, base_price, qty, mode="per_unit"):
    """The quantized LINE total for ``qty`` (effective unit × qty, rounded to cents).

    Line-level rounding is what makes bundle exact: "3 for 4.00" → unit 1.3333… → 1.3333…×3
    quantizes to 4.00. Used by the till AND the client cart-preview so shown == charged."""
    unit, _ = tier_unit_price(price_tiers, base_price, qty, mode)
    return (unit * Decimal(qty)).quantize(_CENT, rounding=ROUND_HALF_UP)


def validate_price_tiers(raw, mode="per_unit"):
    """Validate + normalize a tier list for storage (the editor path).

    Rules: each row is ``{min_qty (int >= 1), unit_price (>= 0)}``; ``min_qty`` values are
    unique; the list is returned sorted ascending. ``None``/empty -> ``[]`` (tiers cleared,
    flat price). Raises ``ValueError`` on bad input so the caller can 422 with the reason.

    The FIRST-ROW rule depends on ``mode``:
      - ``"per_unit"`` (Artemis ladder): the first tier must be ``min_qty == 1`` — it *is* the
        single-unit base price, the rung every higher break is measured against.
      - ``"bundle"`` ("N for X total"): there is no bundle of one — the base price is the
        product's own ``price``. So the first break must be a real pack, ``min_qty >= 2``.
        (Requiring a qty-1 row here was the bug that made the editor reject valid bundle data.)
    """
    if not raw:
        return []
    rows = []
    seen = set()
    for t in raw:
        if not isinstance(t, dict):
            raise ValueError("each tier must be an object")
        try:
            mq = int(t["min_qty"])
            up = _q(t["unit_price"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("each tier needs a whole min_qty and a numeric unit_price")
        if mq < 1:
            raise ValueError("min_qty must be >= 1")
        if up < 0:
            raise ValueError("unit_price must be >= 0")
        if mq in seen:
            raise ValueError(f"duplicate min_qty {mq}")
        seen.add(mq)
        rows.append({"min_qty": mq, "unit_price": str(up)})
    rows.sort(key=lambda r: r["min_qty"])
    if mode == "bundle":
        # A "bundle of one" is just the base price (the product's own `price`), not a break.
        # The editor seeds a qty-1 row for per_unit, and a per_unit→bundle switch (or legacy
        # bundle data) can leave one behind — FOLD it away rather than dead-end the save
        # (BL-31). If that leaves no real packs, tiers clear to a flat price.
        rows = [r for r in rows if r["min_qty"] >= 2]
    elif rows[0]["min_qty"] != 1:
        raise ValueError("the first tier must start at min_qty 1 (the base price)")
    return rows
