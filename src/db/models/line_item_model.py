# File: src/db/models/line_item_model.py
"""
LineItemModel - Individual products in a transaction cart.
Similar to TaskModel - represents one product added to a sale.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class LineItemModel(Base):
    """
    Individual product in a transaction cart.
    One transaction has many line items (one per product scanned).
    """
    __tablename__ = 'line_items'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Foreign Keys
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('transactions.id'),
        nullable=False,
        comment="Parent transaction this item belongs to"
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('products.id'),
        nullable=True,
        comment="Product from catalog. NULL for custom lines (manual catalog entry, "
                "product-as-change treats) -- name lives in notes, price is sent by the till."
    )
    # DEPARTMENT KEY (2026-08-07) -- a non-catalog sale: stock with no barcode that never will
    # have one (glass, grinders, pipes, grow supplies -- 7% of this catalogue scans at all).
    # Always accompanies product_id IS NULL. Deliberately a plain code and NOT a foreign key:
    # a department is an accounting bucket, not a row somebody can rename or delete out from
    # under a closed sale. The receipt text and VAT class are resolved from it at sale time via
    # services/departments.py and SNAPSHOTTED onto the line, same as vat_rate -- so renaming a
    # button next year never rewrites a past receipt.
    department_code: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        index=True,
        comment="Non-catalog department bucket (GLAS/GRIP/...). NULL on every catalog line."
    )
    # The barcode scanned immediately before this line that resolved to nothing. Feeds
    # catalog_miss so the enrichment backlog is ranked by real scan frequency rather than by
    # somebody's guess. NULL is the common case -- most department items have nothing to scan.
    unresolved_barcode: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Barcode that failed to resolve just before this department line was rung"
    )

    # Line Item Details
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="How many units of this product"
    )
    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Price per unit at time of sale (snapshot from product)"
    )
    discount_percent: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=0.00,
        nullable=False,
        comment="Percentage discount applied (loyalty, promo)"
    )
    discount_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Total discount in CHF for this line"
    )
    line_total: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Final price: (quantity * unit_price) - discount_amount"
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Special notes for this item (e.g., 'gift wrap requested')"
    )
    is_giveaway: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Free promotional giveaway (a 'treat'): zero revenue, but real stock "
                "leaves inventory -- tracked for COGS / tax."
    )

    # --- Per-line Swiss VAT (cafe multi-line tax: dine-in 8.1% / takeaway 2.6%) -----
    # `consumption` drives the rate for cafe food/drink (alcohol + tobacco stay 8.1%
    # regardless). `vat_rate` and `vat_amount` are SNAPSHOTTED at sale time (resolved
    # from the product's class via vat_resolver.line_vat) so a later rate change never
    # rewrites a past receipt. Rate/amount are nullable for lines rung before this shipped.
    consumption: Mapped[str] = mapped_column(
        String(16),
        default="dine_in",
        nullable=False,
        comment="dine_in | takeaway -- sets the per-line VAT rate (cafe food/drink)"
    )
    vat_rate: Mapped[float | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="VAT rate % snapshotted at sale (8.10 / 2.60); null on legacy lines"
    )
    vat_amount: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="VAT contained in this line's gross at vat_rate; null on legacy lines"
    )

    # --- 18+ evidence (2026-08-12) ------------------------------------------
    # Was THIS line age-restricted at the moment it was sold? Snapshotted for the
    # same reason vat_rate and department_code are: products.product_class is
    # mutable, and re-classifying an item next year must not rewrite what a sale
    # meant today. Without it, a product later un-flagged as 18+ makes every old
    # transaction unexplainable — "why did this need an ID check?" has no answer,
    # and worse, "why didn't it?" has the wrong one.
    #
    # It is also what makes transactions.age_check_outcome checkable: the rule
    # AGE-18-TABAK joins the two to find any completed sale with a restricted
    # line and no recorded basis.
    #
    # NULL on legacy lines — never backfilled from today's classes, because that
    # would invent a fact about a sale nobody observed.
    was_age_restricted: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Was this line 18+ at the time of sale? Snapshot; NULL on legacy lines"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When item was added to cart"
    )

    # Relationships
    transaction: Mapped["TransactionModel"] = relationship(
        back_populates="line_items"
    )
    product: Mapped["ProductModel"] = relationship(
        back_populates="line_items"
    )

    def __repr__(self):
        return f"<LineItemModel(product_id='{self.product_id}', quantity={self.quantity}, total={self.line_total} CHF)>"
