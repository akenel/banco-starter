# File: src/db/models/cash_shift_model.py
"""
Cash Shift - THE SHOP'S cash box, from count-in to reconcile. One box, one open shift.

REWRITTEN 2026-08-03. This file used to say "per-cashier drawer accountability (the
lockbox model) ... Cashier OPENS a shift by counting the float into THEIR drawer." That
is a real and common retail model -- and it is not how Artemis works. See
`onboarding/12-the-cash-box.md` for the full design; the short version:

  Artemis has ONE physical cash box. Everybody sells into it, it is never emptied
  (~CHF 600 carries over), it sleeps in the safe and comes back out the same. Under the
  old model Felix opened with 200, Pam sold 150 cash into the SAME box, and Felix's close
  expected only HIS OWN takings -> variance +150 -> a note explaining money that was never
  missing. Worse, the open guard was per-user, so two people could hold open drawers on
  one physical box, each blind to the other's sales. That happened on production
  2026-08-03 and nothing objected.

How it works now:
  1. Somebody OPENS the box by COUNTING it -- blind. Banco shows no expected figure until
     the count is submitted (seeing "555" first makes a tired person count until they find
     555). Then it reveals what last night's reconcile recorded, and any difference is
     filed against YESTERDAY. The counted amount becomes today's float: today starts from
     what is really in the box, not from what a record claims.
  2. EVERYONE rings sales into it. Transactions still carry cashier_id, so per-cashier
     SALES reporting is untouched -- but no variance is ever attributed to an individual,
     because with a shared box nobody can honestly say whose twenty francs went astray.
  3. Non-sale cash carries a reason AND a reason_code (petty cash, float top-up, and
     `to_safe` for a skim -- a drop is not an expense and must not be booked as one).
  4. Somebody RECONCILES by counting the box. Expected = float + EVERYONE's cash sales +
     paid-in - paid-out - refunds. The counted total is recorded as tomorrow's expected.
     That chain -- last night's counted -> this morning's expected -- is the slope.

`user_id`/`username` are now OPENED BY, not "owner". `reconciled_by` is who counted it out.
Still separate from ShiftSessionModel: a cash shift is the money story, a session is the
who's-logged-in story. A cashier signing off no longer has anything to do with the box.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (String, DateTime, Boolean, Text, Integer, Numeric, ForeignKey,
                        Enum as SQLEnum, text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.constants import HelixEnum
from .base import Base


class CashShiftStatus(HelixEnum):
    """A cash shift is either taking sales or counted-out and closed."""
    OPEN = "open"
    CLOSED = "closed"


class CashMovementKind(HelixEnum):
    """Non-sale cash that moves in or out of the drawer mid-shift."""
    PAID_IN = "paid_in"      # float top-up, change brought in
    PAID_OUT = "paid_out"    # petty cash, supplier paid from drawer, skim to the safe


# What the movement WAS, as a code (§7.3 of the design note). Deliberately not a Postgres
# enum: `ALTER TYPE ... ADD VALUE` is the one migration in this batch that is awkward to make
# idempotent on a live shop, and a plain code column buys the same thing.
#
# `to_safe` is the important one. Skimming CHF 1,000 into the safe when the box gets heavy is
# NOT an expense -- the money is still the shop's, it has just moved somewhere Banco does not
# track. Booking it as petty cash would overstate expenses by whatever the shop skims.
REASON_CODES = ("to_safe", "petty_cash", "float_top_up", "change_order", "other")

# The codes whose money left the drawer but NOT the business. Anything listed here must be
# excluded from expense reporting; everything else is a real cost.
NON_EXPENSE_REASON_CODES = ("to_safe", "change_order")


class CashShiftModel(Base):
    """One cashier's drawer, from float-in to count-out."""
    __tablename__ = "cash_shifts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Who OPENED the box + where. NOT an owner: the box belongs to the shop (2026-08-03).
    # Kept under the old column names so no data migration is needed -- only the meaning
    # changed, and the meaning was never enforced by the schema.
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True,
        comment="Keycloak sub / username of whoever OPENED the box (not an owner)")
    username: Mapped[str] = mapped_column(String(100), nullable=False,
        comment="Display name of who opened it (pam, ralph, felix)")
    reconciled_by: Mapped[str | None] = mapped_column(String(100), nullable=True,
        comment="Who counted the box out. May be a different person to whoever opened it.")
    store_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    register_id: Mapped[str | None] = mapped_column(String(20), nullable=True,
        comment="Physical register/drawer if more than one (REG-01)")

    status: Mapped[CashShiftStatus] = mapped_column(
        SQLEnum(CashShiftStatus, name="cash_shift_status", create_constraint=True,
                values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=CashShiftStatus.OPEN, index=True)

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
        comment="Float counted in -> shift start (and clock-in)")
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Drawer counted out -> shift end (and clock-out)")

    # --- Opening: the BLIND count, then the reveal ---
    # opening_float IS the counted amount. Today starts from what is really in the box, not
    # from what last night's record claims -- Felix: "I only found five hundred ... I'm just
    # gonna work with the five hundred I got and go from there."
    opening_float: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0,
        comment="What was COUNTED into the box at open = today's float (CHF)")
    opening_denoms: Mapped[str | None] = mapped_column(Text, nullable=True,
        comment="JSON denomination breakdown at open {\"50\":2,\"0.05\":11}")

    # The reveal, recorded so the morning's discrepancy is auditable rather than shrugged off.
    # opening_expected comes from the PREVIOUS shift's counted_cash (the slope), or on the very
    # first open from store_settings.cash_box_float (the bootstrap baseline). NULL = neither was
    # available, so there was nothing to compare against and no claim is made.
    opening_expected: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="What last night's reconcile said should be here (revealed AFTER the count)")
    opening_variance: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="opening_float - opening_expected. Belongs to YESTERDAY, not to today's trading.")
    opening_note: Mapped[str | None] = mapped_column(Text, nullable=True,
        comment="Explanation of the morning difference -- filed against yesterday's reconcile")
    previous_shift_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="The shift whose counted_cash became this one's expected -- the slope, walkable")

    # --- Closing: the count + the math (all snapshotted at close) ---
    cash_sales: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Cash taken from sales during the shift (this cashier)")
    cash_refunds: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Cash refunded during the shift (this cashier)")
    card_sales: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Non-cash sales (visa/twint/debit) -- reported, NOT in the drawer")
    paid_in_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0,
        comment="Sum of non-sale cash brought in")
    paid_out_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0,
        comment="Sum of non-sale cash taken out")

    expected_cash: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="float + cash_sales + paid_in - paid_out - cash_refunds")
    counted_cash: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Cash actually counted in the drawer at close")
    closing_denoms: Mapped[str | None] = mapped_column(Text, nullable=True,
        comment="JSON denomination breakdown at close")
    variance: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="counted_cash - expected_cash (negative = short)")
    tolerance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.20,
        comment="Acceptable |variance| before it's flagged (CHF)")
    within_tolerance: Mapped[bool | None] = mapped_column(Boolean, nullable=True,
        comment="abs(variance) <= tolerance")
    variance_note: Mapped[str | None] = mapped_column(Text, nullable=True,
        comment="Required explanation when outside tolerance")

    # --- The forced close (§5 of the design note) ---------------------------------------
    # A shift may have to be closed when counting it is no longer possible -- the box is not
    # here, nobody is at the shop, the row cannot sit open for ever (the Kassenbuch must be
    # complete and chronological). Closing at counted = expected produces a variance of 0.00,
    # and a zero variance is EXACTLY what a reader takes for "the drawer balanced". It didn't.
    # Nobody looked. So the fact lives in its OWN column, not in prose somebody has to read:
    # any balanced-drawer statistic must filter on counted_verified.
    #
    # Default TRUE is true for history -- every shift closed before this existed was closed by
    # a person with the box in front of them.
    counted_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True,
        server_default=text("true"),
        comment="A human actually counted the box. FALSE = the figure was assumed, never observed.")
    forced_close: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False,
        server_default=text("false"),
        comment="Closed administratively rather than by counting (manager-only, reason required)")

    transaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
        comment="Completed transactions rung during this shift")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    movements: Mapped[list["CashMovementModel"]] = relationship(
        back_populates="shift", cascade="all, delete-orphan",
        order_by="CashMovementModel.created_at")


class CashMovementModel(Base):
    """An audited paid-in / paid-out -- every non-sale cash move carries a reason."""
    __tablename__ = "cash_movements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    shift_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_shifts.id", ondelete="CASCADE"),
        nullable=False, index=True)
    kind: Mapped[CashMovementKind] = mapped_column(
        SQLEnum(CashMovementKind, name="cash_movement_kind", create_constraint=True,
                values_callable=lambda x: [e.value for e in x]),
        nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False,
        comment="Always positive; kind says in or out")
    reason: Mapped[str] = mapped_column(String(300), nullable=False,
        comment="Why the cash moved (petty cash: milk, float top-up)")
    # WHAT KIND of movement, as a code rather than free text (§7.3). A skim to the safe is
    # money leaving the drawer -- so `kind` stays paid_out -- but it is NOT an expense, and
    # it must never land in petty cash in the Banana export next to milk and window cleaner.
    # A code makes that correct by construction instead of by matching on prose somebody
    # typed at a till. NULL on every movement recorded before this existed.
    reason_code: Mapped[str | None] = mapped_column(String(20), nullable=True,
        comment="to_safe | petty_cash | float_top_up | change_order | other (NULL = legacy)")
    actor: Mapped[str] = mapped_column(String(100), nullable=False,
        comment="Who recorded it")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    shift: Mapped["CashShiftModel"] = relationship(back_populates="movements")
