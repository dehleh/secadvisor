"""Assessment models — the structured intake that feeds the AI advisor."""
from enum import Enum as PyEnum

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class AssessmentStatus(str, PyEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Assessment(Base, UUIDPKMixin, TimestampMixin):
    """A point-in-time security & compliance self-assessment for a company.

    Responses are stored as a structured JSON document so we can evolve the
    questionnaire without schema migrations. The AI advisor reads from this
    plus the company profile to generate the report.
    """

    __tablename__ = "assessments"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitted_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Versioning lets us iterate the questionnaire over time
    questionnaire_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus), nullable=False, default=AssessmentStatus.DRAFT
    )

    # Structured responses — see app.services.assessment for schema
    responses: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Computed scores (populated post-submission)
    overall_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    soc2_readiness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    ndpa_compliance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="assessments")  # type: ignore  # noqa
    reports: Mapped[list["Report"]] = relationship(  # type: ignore  # noqa
        "Report", back_populates="assessment", cascade="all, delete-orphan"
    )
