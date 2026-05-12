"""Pydantic schemas for report endpoints."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.compliance import ReportType


class ReportSummaryOut(BaseModel):
    """Lightweight report record for lists."""
    id: str
    assessment_id: str
    report_type: ReportType
    model_used: str | None
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class ReportOut(BaseModel):
    """Full report payload as stored."""
    id: str
    assessment_id: str
    report_type: ReportType
    executive_summary: str | None
    risk_register: list[dict[str, Any]]
    roadmap: list[dict[str, Any]]
    framework_gaps: dict[str, Any]
    model_used: str | None
    generation_tokens_input: int | None
    generation_tokens_output: int | None
    generation_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


# ---------------------------------------------------------------------------
# Share links
# ---------------------------------------------------------------------------


class ReportShareCreateRequest(BaseModel):
    """Owner/admin/member creates a public share link for a report."""
    label: str | None = Field(default=None, max_length=255)
    expires_in_days: int | None = Field(default=30, ge=1, le=365)


class ReportShareOut(BaseModel):
    """Share link record returned to the creator."""
    id: str
    report_id: str
    token: str
    label: str | None
    expires_at: datetime | None
    revoked_at: datetime | None
    view_count: int
    last_viewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PublicReportOut(BaseModel):
    """Sanitised report payload for public viewers (no internal IDs)."""
    company_name: str
    report_type: ReportType
    executive_summary: str | None
    risk_register: list[dict[str, Any]]
    roadmap: list[dict[str, Any]]
    framework_gaps: dict[str, Any]
    overall_risk_score: int | None
    soc2_readiness_score: int | None
    ndpa_compliance_score: int | None
    generated_at: datetime
    label: str | None

