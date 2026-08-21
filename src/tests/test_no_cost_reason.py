"""The honest "no" for the cost done-flag (2026-08-21).

Angel made a filled-in COST the signal that a product has been properly reviewed, and he is
right to: it is the only field on the cleanup form a machine cannot honestly supply. A name, a
description, a photo, a category, even the EAN can all come from a supplier feed or a model, and
a row that was auto-filled LOOKS finished. Cost can only come from a person holding an invoice.

But a flag with no honest "no" is a flag people clear with a lie. A gift, a sample, consignment
or old stock with a lost invoice had no way off the bench except typing a number that was not
true — and a fabricated cost is WORSE than a missing one, because afterwards nobody can tell a
made-up 1.00 from a real one and it poisons every margin figure quietly. Same disease as the
minted EANs.

So: the cost stays NULL, a person answers WHY, and the row leaves the bench.
"""
from src.services.catalog_taxonomy import NO_COST_REASONS


def test_the_answers_are_a_closed_set():
    # Free text here would be unreadable in aggregate, would drift into being a second
    # work_note, and would break the one thing this exists for: a report excluding these rows.
    assert set(NO_COST_REASONS) == {"gift", "sample", "consignment", "unknown"}
    for key, why in NO_COST_REASONS.items():
        assert key == key.lower() and " " not in key, key
        assert why and len(why) > 10, key      # every answer explains itself to the reader


def test_unknown_is_one_of_them():
    # The most important one, and the easiest to leave out. Old stock whose invoice is gone is
    # the single commonest real case; without it the operator is pushed straight back to lying.
    assert "unknown" in NO_COST_REASONS


def test_zero_is_not_an_answer():
    # Never zero. Zero is a NUMBER: it lands in margin as a 100% markup and reads as a fact.
    # The whole design is that the cost stays absent and the ABSENCE is explained.
    assert "0" not in NO_COST_REASONS and "zero" not in NO_COST_REASONS
    assert "free" not in NO_COST_REASONS   # 'free' invites cost=0.00; 'gift' does not
