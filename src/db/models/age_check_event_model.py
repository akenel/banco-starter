# File: src/db/models/age_check_event_model.py
"""
Age Check Event — the refusals.

WHY THIS TABLE EXISTS
---------------------
Proof that a control works is the record of the times it said NO.

A shop with thousands of 18+ sales and zero refusals reads exactly like a shop
that never checks. This is the same instinct already written into
store_settings.cash_tolerance, in its own words:

    "An auditor wants a complete, reasoned record, NOT a drawer that is always
     perfect. A box balancing to 0.00 every day for a year is a red flag, not a
     gold star."

Identical principle, different control.

Before this table, a refused sale left NOTHING. `_assert_age_cleared()` raised a
400 and the request unwound — no row, no log line, no trace. The single most
useful piece of evidence in the whole age gate was the one thing not kept.

WHY IT CANNOT LIVE ON transactions
----------------------------------
A refusal means no sale happened, so there is no transaction row to hang it on.
It needs its own home.

It also has to survive the exception. `get_db_session` does not roll back
explicitly — it just closes, which discards an uncommitted transaction. So the
writer uses its OWN short-lived session and commits before the 400 is raised.
That isolation is deliberate: recording a refusal must never be able to commit a
half-built cart, and a half-built cart must never be able to erase a refusal.

WHAT IT IS NOT
--------------
Not a customer record. There is deliberately no name, no photo, no document
number, no date of birth of the person turned away. The shop needs to prove the
gate bit, not build a file on whoever it bit. Swiss FADP: collect the minimum
that answers the question, and this table answers it with a count and a time.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, Text, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class AgeCheckEventModel(Base):
    """One age-gate decision worth keeping outside the sale record."""

    __tablename__ = "age_check_event"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(), nullable=False,
        comment="When the gate made this decision (server_default: a non-ORM writer must not fail on it)"
    )

    # 'refused' is the reason the table exists. The cleared outcomes are recorded
    # on the transaction itself; they may also be mirrored here later if a single
    # timeline turns out to be easier to hand an inspector.
    outcome: Mapped[str] = mapped_column(
        String(24), nullable=False,
        comment="refused | member_dob | member_confirmed | cashier_attest"
    )

    # Which sale attempt this was, when there was one. For a refusal the
    # transaction may never be completed, so this is a reference string
    # (transaction_number), not a foreign key that could block or cascade.
    txn_ref: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="transaction_number of the attempt, if one existed. Not an FK by design."
    )

    store_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # WHO was at the till. This is the accountability half — no software can force
    # a cashier to actually look at an ID, but a decision attributable to a named
    # person on a dated attempt is evidence, where a habit is not.
    cashier: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
        comment="Username of the staff member at the till"
    )

    # What kind of product triggered the gate — 'tobacco', 'cbd', etc. Enough to
    # report by category without touching the buyer.
    product_class: Mapped[str | None] = mapped_column(
        String(40), nullable=True,
        comment="Class that triggered the gate; no product identity needed"
    )

    note: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Optional free text from the cashier. Never the buyer's identity."
    )

    __table_args__ = (
        Index("ix_age_check_event_outcome_at", "outcome", "occurred_at"),
        Index("ix_age_check_event_at", "occurred_at"),
    )

    def __repr__(self):
        return f"<AgeCheckEvent({self.outcome} @ {self.occurred_at:%Y-%m-%d %H:%M})>"
