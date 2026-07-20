"""Guided readiness persistence models."""

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class GuidedReadinessProfile(Base, UUIDPKMixin, TimestampMixin):
    """Company-scoped state for the founder-friendly guided readiness flow."""

    __tablename__ = "guided_readiness_profiles"

    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    updated_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    selected_goal: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_framework: Mapped[str | None] = mapped_column(String(80), nullable=True)
    program_profile: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    scope_answers: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    baseline_answers: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    questionnaire_drafts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    readiness_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
