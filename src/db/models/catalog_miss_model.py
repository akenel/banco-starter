"""A barcode that was scanned at the till and resolved to nothing.

SPEC §6 calls this "the highest-value output of the whole feature", and that is right: it turns
the failure into a **self-prioritising backlog**. A code scanned nine times is a real mover worth
an hour of enrichment; one scanned once is noise. The back office works it top-down by
`hit_count` — never at the till, never with a customer waiting.

⚠️ KNOWN AND ACCEPTED BLIND SPOT (SPEC §10.2 #14). This only fires when a barcode is scanned and
FAILS. Bongs and grinders — the exact stock that motivated department keys — have no barcode to
scan at all, so nothing is ever logged for them. This table will do real work on drinks,
cigarettes and newly-arrived stock. For glass, the department total is the only signal there will
ever be. Better to know that now than to discover it after trusting the list.

Deliberately NOT here: no product name, no photo, no guess at what the item was. §5 is explicit —
if nobody knew what it was at the till, nobody knows at 20:00. Storing a guess would make the
backlog look richer and be worth less.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CatalogMissModel(Base):
    """One row per unresolved barcode, counted up over time."""

    __tablename__ = 'catalog_miss'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # UNIQUE: one row per code, counted up. The whole value of this table is the count, so a
    # second row for the same barcode would split the evidence and bury a real mover.
    barcode: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True,
        comment="The code that did not resolve")

    hit_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="How many times it has been scanned and missed — the backlog ranking")

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc))

    # Which button the cashier reached for. The single most useful clue about what the thing
    # actually was, and it costs nothing — she pressed it anyway.
    department_code: Mapped[str | None] = mapped_column(
        String(8), nullable=True,
        comment="Department the cashier rang it under, most recently")

    # Every price it has been sold at, newest last, JSON list of strings. A code that always
    # rings 12.00 is a single product worth binding; one ringing 5/45/120 is a shelf position,
    # a mis-scan, or a code shared across a range — and worth far less effort.
    prices_seen: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="JSON list of prices it has been rung at, newest last (capped)")

    last_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
        comment="Most recent price — the sortable one")

    # Set when the code finally becomes a real catalog product. Counting then STOPS (SPEC §6):
    # the row is history, not a live backlog item. Past sales are never restated — those lines
    # stay department revenue forever.
    resolved_ean: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="Set once this code became a real catalog product — counting stops")
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<CatalogMiss({self.barcode!r} ×{self.hit_count} {self.department_code})>"
