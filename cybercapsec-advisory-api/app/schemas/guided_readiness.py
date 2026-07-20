"""Schemas for founder-guided readiness state."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GuidedReadinessUpdateRequest(BaseModel):
    selected_goal: str | None = Field(default=None, max_length=80)
    target_framework: str | None = Field(default=None, max_length=80)
    program_profile: dict[str, Any] | None = None
    scope_answers: dict[str, Any] | None = None
    baseline_answers: dict[str, Any] | None = None
    questionnaire_drafts: list[dict[str, Any]] | None = None
    readiness_notes: str | None = Field(default=None, max_length=8000)


class GuidedReadinessOut(BaseModel):
    id: str
    company_id: str
    updated_by_user_id: str | None
    selected_goal: str | None
    target_framework: str | None
    program_profile: dict[str, Any]
    scope_answers: dict[str, Any]
    baseline_answers: dict[str, Any]
    questionnaire_drafts: list[dict[str, Any]]
    readiness_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
