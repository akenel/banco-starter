# File: src/db/models/compliance_rule_model.py
"""
Compliance Rule Model — the RULE PACK.

One row = one sentence a shop asserts about itself, plus how to prove it.

    "We do not sell age-restricted products to anyone under 18."
    "Every hemp SKU carries a recorded THC value below 1%."

That sentence is what an inspector reads. The check is how the system proves
it is still TRUE — not that the document exists, but that reality matches it.

WHY THIS TABLE EXISTS
---------------------
Control of documented information is the most commonly cited audit
nonconformity there is, and the classic finding is never "the SOP is missing".
It is "the operator is working to Rev C while the master list says Rev E" —
the document drifted away from the practice and nobody noticed. Every quality
product on the market solves that as a DOCUMENT problem (versions, approvals,
sign-offs). None of them go and look.

So: the statement lives here WITH its check. They are one object. A rule you
cannot check is still allowed (check_kind='none') but it is honestly marked as
such rather than silently assumed to be fine.

RELATIONSHIP TO audit_log
-------------------------
`audit_log` (scripts/db/audit_log_setup.sql) answers "who changed this row?".
This answers a different question: "is the stated rule still true right now?"
One is a change history, the other a periodic assertion. Neither replaces the
other and they must not be merged.

REVISIONS ARE NEVER DELETED
---------------------------
An obsolete rule is marked obsolete and kept, because an auditor in 2028 may
ask what the rule said in 2026 and what was checked against it then. Editing a
rule in place would destroy exactly the evidence the table exists to produce.
Bump `revision`, set `obsoleted_at` + `superseded_by` on the old row.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, Boolean, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class ComplianceRuleModel(Base):
    """One checkable assertion the shop makes about itself."""

    __tablename__ = "compliance_rule"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    # NULL = applies to every store (the shared pack). A store_number pins it to
    # one shop, which is how a tenant adds its own house rules without forking
    # the pack. The vertical difference is CONFIG, never a branch.
    store_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="NULL = applies to all stores; else pins the rule to one store"
    )

    # Stable human handle, e.g. 'AGE-18-TABAK'. Stable ACROSS revisions — this is
    # what a person cites in a meeting. (code, revision) is the unique pair.
    code: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="Stable rule handle, e.g. AGE-18-TABAK. Constant across revisions."
    )

    revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Bumped on every wording/check change. The Rev C vs Rev E problem."
    )

    # THE SENTENCE. Plain language, no jargon, readable by a cashier and by an
    # inspector. If it needs a footnote to understand, it is two rules.
    statement: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="The SOP sentence in plain language. What the inspector reads."
    )

    rationale: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Why this rule exists. Written for the person who inherits the shop."
    )

    # --- The external document register -------------------------------------
    # "External documents drifted and nobody owned the register" is a standard
    # finding. The law changes; the SOP quoting it does not. So each rule names
    # its authority AND records when a human last confirmed the authority still
    # says this. A rule whose authority has not been re-read in a year is itself
    # a finding, and the engine can surface that without reading any law.
    authority: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Legal/standard source, e.g. 'TabPG (in force 2024-10-01), Abgabealter 18'"
    )
    authority_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="Where the authority can be read"
    )
    authority_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When a HUMAN last confirmed the source still says this. Ages into a finding."
    )

    # --- How it gets proved --------------------------------------------------
    # sql     — run a query against this database (the strongest evidence)
    # http    — call an endpoint and assert on the response
    # config  — read a config/setting value
    # manual  — a human walks and attests (the physical world; still recorded)
    # none    — deliberately unchecked, and honestly marked UNSOURCED
    check_kind: Mapped[str] = mapped_column(
        String(16), nullable=False, default="none",
        comment="sql | http | config | manual | none"
    )

    # The query, endpoint or config path. Stored as text and SNAPSHOTTED into
    # every run, so an auditor can re-execute exactly what was executed then.
    # Evidence nobody can reproduce is an assertion, not evidence.
    check_spec: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="The exact query/endpoint/path to execute. Reproducibility is the point."
    )

    # What the result has to be for the rule to hold. Kept human-readable
    # ('0 rows', 'true', '< 1.0') rather than a clever DSL — a compliance
    # officer must be able to read this without a developer present.
    expectation: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="What the check must return to pass, e.g. '0 rows'. Human-readable on purpose."
    )

    # critical — an inspector finding here can close the shop or bring a fine
    # major    — a nonconformity that must be corrected
    # minor    — an observation
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="major",
        comment="critical | major | minor"
    )

    # How often the check should run. NULL = on demand only.
    frequency_hours: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Run cadence in hours. NULL = on demand only."
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Inactive rules are not run but are never deleted"
    )

    # --- The revision chain (ISO: obsolete documents retained but marked) ----
    obsoleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Set when superseded. The row is KEPT — deleting destroys the audit trail."
    )
    superseded_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="The compliance_rule.id that replaced this revision"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
        comment="Who wrote this revision (app.actor)"
    )

    __table_args__ = (
        Index("ix_compliance_rule_code_rev", "code", "revision", unique=True),
        Index("ix_compliance_rule_active", "is_active", "store_number"),
    )

    def __repr__(self):
        return f"<ComplianceRule({self.code} rev{self.revision}, {self.check_kind})>"
