# File: src/db/models/compliance_check_run_model.py
"""
Compliance Check Run Model — the EVIDENCE.

One row = one execution of one rule at one moment, with its verdict and the
raw thing reality returned.

APPEND-ONLY. NEVER UPDATED. NEVER DELETED.
------------------------------------------
"Records stored in an editable folder" is itself a standing audit
nonconformity. A record that can be revised is not a record. So this table has
NO updated_at, and production should revoke UPDATE/DELETE on it:

    REVOKE UPDATE, DELETE ON compliance_check_run FROM helix_user;

If a run was wrong, you do not fix it — you run the check again and the newer
row supersedes it by timestamp. The wrong verdict stays visible, because "we
believed this on Tuesday and found out on Thursday" is exactly the story an
inspector is entitled to see.

WHY EVERYTHING IS SNAPSHOTTED
-----------------------------
The rule can be edited tomorrow. The evidence must still make sense in 2029.
So each run freezes the sentence, the method and the expectation AS THEY READ
AT THE TIME, rather than joining to a rule row that has since moved. This is
the whole Rev C / Rev E problem, solved by refusing to rely on the join.

THE VERDICTS
------------
Inherited deliberately from the Longhand writing-kit CHECK.md, because they
turned out to be the right four for any claim-versus-reality check:

  VERIFIED    — checked against the running system; reality matches
  STALE       — checked; reality CONTRADICTS the statement  ← the nonconformity
  UNSOURCED   — no check is defined; nobody has ever proved this
  UNCHECKABLE — a check exists but could not run (physical, or data missing)
  ERROR       — the check itself broke. NOT a pass and NOT a fail.

ERROR being distinct from STALE matters more than it looks: a monitoring system
that reports failures when it is itself broken teaches people to ignore it, and
a green board produced by a check that never ran is how machine-green lies.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class ComplianceCheckRunModel(Base):
    """One dated, reproducible verdict on one rule."""

    __tablename__ = "compliance_check_run"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    # --- What was checked (snapshotted, not joined) --------------------------
    rule_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        comment="compliance_rule.id — for grouping only. Never trust it for wording."
    )
    rule_code: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="Snapshot of the rule handle, e.g. AGE-18-TABAK"
    )
    rule_revision: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="WHICH revision was verified. The auditor's first question."
    )
    statement_snapshot: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="The sentence exactly as it read when this ran"
    )

    store_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Which store this verdict covers; NULL = all"
    )

    # --- The verdict ---------------------------------------------------------
    verdict: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="VERIFIED | STALE | UNSOURCED | UNCHECKABLE | ERROR"
    )

    severity_snapshot: Mapped[str | None] = mapped_column(
        String(16), nullable=True,
        comment="Rule severity at run time — so a later re-grading cannot rewrite history"
    )

    # --- The evidence --------------------------------------------------------
    # The exact thing executed. An auditor must be able to paste this and get
    # the same answer. Evidence nobody can reproduce is just an assertion.
    method: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="The exact query/endpoint/command executed. Reproducible on demand."
    )
    expected: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="What it had to return (snapshot of the rule's expectation)"
    )
    observed: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="What it actually returned, in one readable line"
    )
    evidence: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Raw payload — rows, response body, config values. The proof itself."
    )
    # sha256 over the canonical evidence JSON. Cheap, and it lets an export be
    # handed to a third party who can confirm nothing was edited in transit.
    evidence_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="sha256 of the canonical evidence JSON — tamper-evidence for exports"
    )

    # --- Who and when --------------------------------------------------------
    ran_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False,
        comment="When this verdict was produced"
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    actor: Mapped[str] = mapped_column(
        String(128), nullable=False, default="system",
        comment="'system' for scheduled runs; a username for a manual attestation"
    )
    # For check_kind='manual': a human walked and looked. That is legitimate
    # evidence — it is how every audit in history has worked — but it must be
    # visibly attributed to a person, never dressed up as a machine result.
    attestation_note: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="For manual checks: what the person saw, in their words"
    )

    # NOTE: there is deliberately no updated_at. See the module docstring.
    #
    # PHASE 2 (not built yet, but designed for): compliance_finding — when a run
    # comes back STALE, open a finding and track it to closure with a corrective
    # action, owner and due date. That is what turns a monitor into an audit
    # product. Deliberately out of scope until a real auditor has looked at an
    # evidence pack and told us the format is right.

    __table_args__ = (
        Index("ix_ccr_rule_ran", "rule_code", "ran_at"),
        Index("ix_ccr_verdict", "verdict", "ran_at"),
        Index("ix_ccr_store_ran", "store_number", "ran_at"),
    )

    def __repr__(self):
        return f"<CheckRun({self.rule_code} rev{self.rule_revision} → {self.verdict})>"
