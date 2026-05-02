"""Pydantic schemas for policy, evidence, and roadmap endpoints."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import (
    EvidenceKind,
    EvidenceStatus,
    PolicyStatus,
    PolicyTemplateCode,
    RoadmapStatus,
)


# ----- Policy templates ------------------------------------------------------


class PolicyTemplateVariableOut(BaseModel):
    name: str
    label: str
    description: str | None = None
    required: bool
    default: Any | None = None


class PolicyTemplateOut(BaseModel):
    template_code: str
    template_version: str
    title: str
    description: str
    framework_codes: list[str]
    control_refs: list[dict[str, str]]
    variables: list[PolicyTemplateVariableOut]


# ----- Policies ---------------------------------------------------------------


class PolicyGenerateRequest(BaseModel):
    template_code: PolicyTemplateCode
    variable_overrides: dict[str, Any] | None = None


class PolicyAcknowledgmentOut(BaseModel):
    id: str
    user_id: str
    acknowledged_text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PolicyOut(BaseModel):
    id: str
    company_id: str
    template_code: PolicyTemplateCode
    template_version: str
    version: int
    title: str
    content: str
    status: PolicyStatus
    rendered_variables: dict[str, Any]
    framework_codes: list[str]
    control_refs: list[dict[str, str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicySummaryOut(BaseModel):
    id: str
    template_code: PolicyTemplateCode
    template_version: str
    version: int
    title: str
    status: PolicyStatus
    framework_codes: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PolicyAcknowledgeRequest(BaseModel):
    acknowledged_text: str | None = Field(default=None, max_length=2000)


class StarterPackResponse(BaseModel):
    generated: list[PolicySummaryOut]


# ----- Evidence ---------------------------------------------------------------


class EvidenceCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    kind: EvidenceKind
    framework_code: str = Field(min_length=2, max_length=50)
    control_code: str = Field(min_length=1, max_length=50)
    external_url: str | None = Field(default=None, max_length=2048)
    referenced_policy_id: str | None = None
    narrative_text: str | None = Field(default=None, max_length=8000)
    valid_until: datetime | None = None


class EvidenceUpdateStatusRequest(BaseModel):
    status: EvidenceStatus


class EvidenceOut(BaseModel):
    id: str
    company_id: str
    submitted_by_user_id: str | None
    title: str
    description: str | None
    kind: EvidenceKind
    status: EvidenceStatus
    framework_code: str
    control_code: str
    external_url: str | None
    referenced_policy_id: str | None
    narrative_text: str | None
    valid_until: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PropagatedControlOut(BaseModel):
    framework_code: str
    control_code: str
    title: str
    strength: str


class EvidenceWithCoverageOut(BaseModel):
    evidence: EvidenceOut
    propagated_controls: list[PropagatedControlOut]


class CoverageMatrixOut(BaseModel):
    """Per-framework set of controls the company has coverage for."""
    coverage: dict[str, list[str]]


class ControlEvidenceOut(BaseModel):
    framework_code: str
    control_code: str
    direct_evidence: list[EvidenceOut]
    propagated_evidence: list[EvidenceOut]


# ----- Roadmap ---------------------------------------------------------------


class RoadmapSeedResponse(BaseModel):
    seeded: int
    items: list["RoadmapItemOut"]


class RoadmapItemOut(BaseModel):
    id: str
    company_id: str
    report_id: str
    source_task_id: str
    title: str
    description: str
    severity: str
    effort: str
    week_target: int
    status: RoadmapStatus
    assignee_user_id: str | None
    due_date: datetime | None
    completed_at: datetime | None
    framework_citations: list[dict[str, str]]
    success_criteria: list[str]
    addresses_risk_ids: list[str]
    notes: str | None
    blocked_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoadmapItemUpdateRequest(BaseModel):
    status: RoadmapStatus | None = None
    assignee_user_id: str | None = None
    due_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)
    blocked_reason: str | None = Field(default=None, max_length=2000)


class RoadmapProgressOut(BaseModel):
    total: int
    done: int
    in_progress: int
    blocked: int
    todo: int
    cancelled: int
    overdue: int
    completion_pct: int
    by_status: dict[str, int]


# Resolve forward reference
RoadmapSeedResponse.model_rebuild()
