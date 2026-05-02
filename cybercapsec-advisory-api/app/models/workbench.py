"""Workbench models — the working surfaces for compliance prep.

Three concepts:

  Policy        — a rendered policy document tied to a company. Generated from
                  a versioned template + company variables. Tracks acknowledgments.

  Evidence      — a record proving a control is implemented. Holds metadata and
                  external URLs in v1; real file uploads come later.

  RoadmapItem   — a mutable task seeded from an immutable report. Owns status,
                  assignee, due date, and evidence links.

Reports stay snapshots; RoadmapItems are the surface the company actually
works against day-to-day.
"""
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


# ----- Policies ---------------------------------------------------------------


class PolicyTemplateCode(str, PyEnum):
    """Identifiers for built-in policy templates.

    Adding a template means: add a Markdown file under
    `app/services/policies/templates/` and add a code here. Existing rendered
    policies are immune to template changes (they store a snapshot).
    """
    INFORMATION_SECURITY = "information_security"
    ACCESS_CONTROL = "access_control"
    DATA_PROTECTION = "data_protection"
    DATA_RETENTION = "data_retention"
    INCIDENT_RESPONSE = "incident_response"
    ACCEPTABLE_USE = "acceptable_use"
    BUSINESS_CONTINUITY = "business_continuity"
    VENDOR_MANAGEMENT = "vendor_management"
    CHANGE_MANAGEMENT = "change_management"
    SECURE_DEVELOPMENT = "secure_development"
    PASSWORD = "password"
    REMOTE_WORK = "remote_work"
    BACKUP_RECOVERY = "backup_recovery"
    PRIVACY = "privacy"
    SECURITY_AWARENESS = "security_awareness"


class PolicyStatus(str, PyEnum):
    DRAFT = "draft"           # rendered, not yet published
    PUBLISHED = "published"   # active and acknowledged by team
    ARCHIVED = "archived"     # superseded by a newer version


class Policy(Base, UUIDPKMixin, TimestampMixin):
    """A rendered policy document for a specific company.

    Once rendered, the content is frozen. To update, render a new version —
    the previous becomes ARCHIVED. Acknowledgments are tied to a specific
    version so we have an audit trail of who agreed to what.
    """

    __tablename__ = "policies"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_code: Mapped[PolicyTemplateCode] = mapped_column(
        Enum(PolicyTemplateCode), nullable=False, index=True
    )
    template_version: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # rendered Markdown
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus), nullable=False, default=PolicyStatus.DRAFT
    )

    # Variables used to render this policy (snapshot for audit)
    rendered_variables: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Frameworks/controls this policy contributes to (denormalized for fast filtering)
    framework_codes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    control_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    acknowledgments: Mapped[list["PolicyAcknowledgment"]] = relationship(
        "PolicyAcknowledgment",
        back_populates="policy",
        cascade="all, delete-orphan",
    )


class PolicyAcknowledgment(Base, UUIDPKMixin, TimestampMixin):
    """A user's acknowledgment that they have read a specific policy version."""

    __tablename__ = "policy_acknowledgments"

    policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    acknowledged_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    policy: Mapped[Policy] = relationship("Policy", back_populates="acknowledgments")

    __table_args__ = (
        UniqueConstraint("policy_id", "user_id", name="uq_policy_user_ack"),
    )


# ----- Evidence ---------------------------------------------------------------


class EvidenceKind(str, PyEnum):
    """How the evidence is provided."""
    EXTERNAL_LINK = "external_link"  # Notion page, Google Doc, GitHub PR, etc.
    POLICY_REF = "policy_ref"         # references a Policy in our system
    SCREENSHOT_URL = "screenshot_url"  # a hosted image
    NARRATIVE = "narrative"           # text-only description (interim)
    FILE_UPLOAD = "file_upload"       # reserved for future S3-backed uploads


class EvidenceStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"        # current accepted evidence
    EXPIRED = "expired"      # was active, no longer current
    REJECTED = "rejected"    # auditor or admin marked invalid


class Evidence(Base, UUIDPKMixin, TimestampMixin):
    """A piece of evidence attached to one or more controls.

    Cross-framework propagation: an evidence record is attached to a single
    "anchor" (framework, control_code), but via ControlMapping it implicitly
    contributes to mapped controls in other frameworks. The
    propagated coverage is computed on read, not duplicated in storage.
    """

    __tablename__ = "evidence"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitted_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[EvidenceKind] = mapped_column(Enum(EvidenceKind), nullable=False)
    status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus), nullable=False, default=EvidenceStatus.ACTIVE
    )

    # The "anchor" control: where the user attached the evidence
    framework_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    control_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Kind-specific payload
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    referenced_policy_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True
    )
    narrative_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional expiry (e.g. annual training certificate expires after 12 months)
    valid_until: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ----- Roadmap items ----------------------------------------------------------


class RoadmapStatus(str, PyEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class RoadmapItem(Base, UUIDPKMixin, TimestampMixin):
    """A working roadmap task, seeded from a report task.

    Reports are immutable snapshots. RoadmapItem is the mutable, day-to-day
    surface: status changes, assignees, evidence links, due dates. We
    preserve the report linkage so we can render a "progress against the
    initial roadmap" view.
    """

    __tablename__ = "roadmap_items"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The id within the report's roadmap array (e.g. "T1", "T2") so we can
    # reconcile reseeded items if the user reseeds from a new report.
    source_task_id: Mapped[str] = mapped_column(String(20), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    effort: Mapped[str] = mapped_column(String(20), nullable=False)
    week_target: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[RoadmapStatus] = mapped_column(
        Enum(RoadmapStatus), nullable=False, default=RoadmapStatus.TODO
    )
    assignee_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Snapshot from the source report
    framework_citations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    success_criteria: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    addresses_risk_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # User notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "report_id", "source_task_id", name="uq_roadmap_report_source_task"
        ),
    )
