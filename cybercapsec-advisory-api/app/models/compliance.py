"""Compliance framework, control library, and AI-generated report models."""
from enum import Enum as PyEnum

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class MappingStrength(str, PyEnum):
    """How strongly two controls correspond.

    EQUIVALENT — same intent, evidence satisfies both fully.
    PARTIAL    — overlapping intent, evidence is contributory but not sufficient.
    RELATED    — adjacent topic, useful context but doesn't cross-satisfy.
    """
    EQUIVALENT = "equivalent"
    PARTIAL = "partial"
    RELATED = "related"


class FrameworkCode(str, PyEnum):
    """Supported compliance frameworks."""
    SOC2 = "soc2"
    ISO_27001 = "iso27001"
    NDPA = "ndpa"           # Nigeria Data Protection Act 2023
    NDPR = "ndpr"           # NITDA Regulation (preceded NDPA)
    CBN_CYBER = "cbn_cyber"  # CBN Risk-Based Cybersecurity Framework
    POPIA = "popia"          # South Africa
    KENYA_DPA = "kenya_dpa"  # Kenya Data Protection Act 2019
    GHANA_DPA = "ghana_dpa"
    PCI_DSS = "pci_dss"


class Framework(Base, UUIDPKMixin, TimestampMixin):
    """A compliance framework supported by the platform."""

    __tablename__ = "frameworks"

    code: Mapped[FrameworkCode] = mapped_column(
        Enum(FrameworkCode), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    controls: Mapped[list["Control"]] = relationship(
        "Control", back_populates="framework", cascade="all, delete-orphan"
    )


class Control(Base, UUIDPKMixin, TimestampMixin):
    """An individual compliance control within a framework.

    Example: SOC 2 CC6.1 (logical access controls), NDPA Sec 24 (security of
    processing), CBN 4.2 (access management).
    """

    __tablename__ = "controls"

    framework_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "CC6.1"
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "access_control"
    guidance: Mapped[str | None] = mapped_column(Text, nullable=True)

    framework: Mapped[Framework] = relationship("Framework", back_populates="controls")

    # Outgoing mappings: this control → other controls
    mappings_from: Mapped[list["ControlMapping"]] = relationship(
        "ControlMapping",
        foreign_keys="ControlMapping.source_control_id",
        back_populates="source_control",
        cascade="all, delete-orphan",
    )
    # Incoming mappings: other controls → this control
    mappings_to: Mapped[list["ControlMapping"]] = relationship(
        "ControlMapping",
        foreign_keys="ControlMapping.target_control_id",
        back_populates="target_control",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("framework_id", "code", name="uq_framework_control_code"),
    )


class ControlMapping(Base, UUIDPKMixin, TimestampMixin):
    """Cross-framework mapping between two controls.

    Mappings are directional but logically symmetric — when querying "what
    other controls does X satisfy?" we look in both directions. Storing
    both directions explicitly lets us record asymmetric strength (e.g.,
    SOC 2 CC6.1 fully covers NDPA Sec 24, but NDPA Sec 24 only partially
    covers CC6.1).
    """

    __tablename__ = "control_mappings"

    source_control_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_control_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strength: Mapped[MappingStrength] = mapped_column(
        Enum(MappingStrength), nullable=False, default=MappingStrength.PARTIAL
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_control: Mapped[Control] = relationship(
        "Control", foreign_keys=[source_control_id], back_populates="mappings_from"
    )
    target_control: Mapped[Control] = relationship(
        "Control", foreign_keys=[target_control_id], back_populates="mappings_to"
    )

    __table_args__ = (
        UniqueConstraint("source_control_id", "target_control_id", name="uq_control_mapping_pair"),
    )


class ReportType(str, PyEnum):
    INITIAL = "initial"
    REASSESSMENT = "reassessment"
    QUARTERLY = "quarterly"
    AD_HOC = "ad_hoc"


class Report(Base, UUIDPKMixin, TimestampMixin):
    """An AI-generated security & compliance report tied to an assessment."""

    __tablename__ = "reports"

    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType), nullable=False, default=ReportType.INITIAL
    )

    # Generated content
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_register: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    roadmap: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    framework_gaps: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Metadata about the generation
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="reports")  # type: ignore  # noqa
