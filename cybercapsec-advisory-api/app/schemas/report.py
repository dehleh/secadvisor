"""Pydantic schemas for report endpoints."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel

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
