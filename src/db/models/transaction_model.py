# File: src/db/models/transaction_model.py
"""
TransactionModel - Represents a sale/checkout session at Artemis POS.
Similar to JobModel - tracks the entire sale from scan to payment.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Enum, Text, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.core.constants import HelixEnum

from .base import Base


class TransactionStatus(HelixEnum):
    """Transaction lifecycle states"""
    OPEN = "open"              # Cart active, customer adding items
    PENDING = "pending"        # Awaiting payment
    COMPLETED = "completed"    # Payment successful
    CANCELLED = "cancelled"    # Transaction aborted
    REFUNDED = "refunded"      # Full refund issued


class PaymentMethod(HelixEnum):
    """Payment types for Felix's store"""
    CASH = "cash"
    VISA = "visa"
    DEBIT = "debit"
    TWINT = "twint"
    BANK_TRANSFER = "bank_transfer"  # Felix: invoice/IBAN paid into the shop account
    CRYPTO = "crypto"
    OTHER = "other"


class TransactionModel(Base):
    """
    Represents a complete sale transaction.
    Maps to 'Job' concept - one checkout session.
    """
    __tablename__ = 'transactions'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Transaction Number (Human-readable)
    transaction_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Sequential receipt number (e.g., 'TXN-20251126-0001')"
    )

    # Offline outbox idempotency key (P2.1). A client-generated UUID that makes the
    # atomic create-sale endpoint idempotent: a replayed sale (network retry, or an
    # offline outbox draining on reconnect) is adopted EXACTLY ONCE instead of double-
    # ringing. Null for sales rung the legacy 3-step way (online only). Unique among
    # non-null values — Postgres treats NULLs as distinct, so legacy rows never collide.
    client_uuid: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        unique=True,
        index=True,
        comment="Client idempotency key for the atomic/offline sale path (P2.1)"
    )

    # Foreign Keys
    cashier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        comment="Staff member who processed the sale (Pam, Rafi, Michel)"
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('customers.id'),
        nullable=True,
        comment="Optional - the loyalty CRM customer this sale belongs to (CustomerModel)"
    )

    # Transaction Status
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        default=TransactionStatus.OPEN,
        nullable=False
    )

    # --- 18+ evidence (2026-08-12) ------------------------------------------
    # WHY: the age gate (_assert_age_cleared in pos_router) has always been real
    # and enforced server-side on BOTH sale paths — it REJECTS the sale with 400
    # unless an of-age member is attached or the cashier attests. What it never
    # did was leave a record: the function returned the method used and both call
    # sites discarded it, so the only trace was a log line that rotates away and
    # does not survive a restart. An inspector asking "prove you checked" six
    # months later got nothing, for a control that had worked perfectly every time.
    #
    # This column is that proof. It changes NOTHING at the till — same popup,
    # same click — it only makes the till remember what it already knew.
    #
    #   not_required     no age-restricted line in this basket
    #   member_dob       customer on file whose birthdate proves 18+  (strongest)
    #   member_confirmed customer on file, age_confirmed ticked, NO birthdate —
    #                    the deliberate back-compat path in member_of_age().
    #                    Intended and correct operationally, but it is a tick, not
    #                    a document. Recorded distinctly instead of folded into
    #                    "member" because you cannot fix a weakness you cannot count.
    #   cashier_attest   cashier confirmed ID at the counter (walk-in)
    #
    # NULL = a row written before this column existed. Deliberately nullable: no
    # historical transaction gets retro-labelled with a check nobody performed.
    #
    # Plain String, not a DB Enum — the value set grows with the rule pack, and
    # ALTER TYPE ... ADD VALUE does not fit the additive-migration mechanism.
    age_check_outcome: Mapped[str | None] = mapped_column(
        String(24),
        nullable=True,
        comment="18+ clearance basis: not_required | member_dob | member_confirmed | cashier_attest. NULL = legacy row."
    )

    # Payment Details
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod),
        nullable=True,
        comment="How customer paid (null until checkout)"
    )

    # Financial Totals (in CHF)
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Sum of all line items before discounts"
    )
    discount_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Total discounts applied (loyalty, coupons)"
    )
    tax_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="VAT/tax (if applicable)"
    )
    total: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Final amount charged to customer"
    )

    # Swiss 5-rappen cash rounding (2026-08-03). `total` is always what was ACTUALLY charged,
    # so on a cash sale it has already been moved to the nearest payable amount and every
    # existing consumer -- drawer expectation, VAT, change, daily summary, CRM points -- is
    # correct without knowing this column exists. THIS column records how far it moved, so the
    # receipt and the Banana export can show `Rundungsdifferenz -0.04` instead of an
    # unexplained rappen. Always 0.00 on card/TWINT/debit (they settle the exact cent) and on
    # every sale rung before this shipped.
    #
    # subtotal - discount_amount + rounding_adjustment == total. The adjustment is NEVER
    # absorbed into the discount: rounding is physics, discounting is pricing.
    rounding_adjustment: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        server_default=text("0"),
        comment="Cash rounding moved the total by this much (0.00 unless a cash sale rounded)"
    )

    # Payment Processing
    amount_tendered: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Amount given by customer (cash only)"
    )
    change_given: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Change returned to customer (cash only), in the HOME currency"
    )

    # Multi-currency TENDER (Block 1): when a customer pays in FOREIGN cash, the sale stays recorded in
    # the home currency (subtotal/total/tax above stay home) — we stamp what was physically handed over
    # so the drawer + receipt are honest. NULL tender_currency = paid in the home currency (byte-identical
    # to today). amount_tendered/change_given are always the HOME-currency equivalents.
    tender_currency: Mapped[str | None] = mapped_column(
        String(8), nullable=True,
        comment="Foreign cash currency handed over (NULL = paid in the home currency)")
    tender_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True,
        comment="Face amount handed over in tender_currency (e.g. EUR 10.00)")
    tender_rate: Mapped[float | None] = mapped_column(
        Numeric(12, 6), nullable=True,
        comment="Plan-rate applied: home_amount = tender_amount * tender_rate")

    # Receipt Information
    receipt_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Printed receipt reference"
    )
    receipt_pdf_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="MinIO URL for stored receipt PDF"
    )

    # Notes and Metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Cashier notes, special requests, etc."
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When transaction started"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When payment was finalized"
    )

    # Relationships
    cashier: Mapped["UserModel"] = relationship(
        foreign_keys=[cashier_id],
        back_populates="cashier_transactions"
    )
    # The loyalty CRM customer this sale belongs to (one-directional -- CustomerModel
    # doesn't carry a transactions back-ref). customer_id -> customers.id.
    customer: Mapped["CustomerModel | None"] = relationship(
        "CustomerModel", foreign_keys=[customer_id]
    )
    line_items: Mapped[list["LineItemModel"]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TransactionModel(number='{self.transaction_number}', total={self.total} CHF, status='{self.status.value}')>"
