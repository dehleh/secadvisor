"""Output schema for AI-generated security & compliance reports.

This is the contract Claude must conform to. Every field is typed and
validated; the AI service rejects malformed output rather than letting
loose JSON poison the database.

The shape was designed with the dashboard in mind: each top-level key
maps to a UI component (executive summary card, risk register table,
roadmap kanban, framework breakdown chart).
"""
from enum import Enum as PyEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Severity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class Effort(str, PyEnum):
    """Rough implementation effort estimate."""
    QUICK_WIN = "quick_win"      # < 1 day
    SHORT = "short"               # 1-5 days
    MEDIUM = "medium"             # 1-4 weeks
    LARGE = "large"               # 1-3 months
    PROGRAM = "program"           # ongoing / cross-team


class FrameworkCitation(BaseModel):
    """A reference to a specific control in a compliance framework."""
    framework: str  # e.g. "soc2", "ndpa"
    control_code: str  # e.g. "CC6.1", "SEC_24"


class Risk(BaseModel):
    """A single entry in the risk register."""
    id: str  # stable within a report, e.g. "R1", "R2"
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=20, max_length=2000)
    severity: Severity
    likelihood: Literal["high", "medium", "low"]
    business_impact: str = Field(min_length=10, max_length=500)
    affected_areas: list[str] = Field(default_factory=list)  # e.g. ["customer_data", "production_systems"]
    framework_citations: list[FrameworkCitation] = Field(default_factory=list)
    related_question_ids: list[str] = Field(default_factory=list)


class RoadmapTask(BaseModel):
    """A concrete action in the 90-day roadmap."""
    id: str  # stable within a report, e.g. "T1", "T2"
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=20, max_length=2000)
    severity: Severity
    effort: Effort
    week_target: int = Field(ge=1, le=13)  # which week to complete by
    addresses_risk_ids: list[str] = Field(default_factory=list)  # references Risk.id
    framework_citations: list[FrameworkCitation] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class FrameworkGap(BaseModel):
    """Per-framework gap narrative."""
    framework: str
    framework_name: str
    readiness_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=20, max_length=1500)
    top_gaps: list[str] = Field(default_factory=list, max_length=10)
    next_steps: list[str] = Field(default_factory=list, max_length=10)


class ReportContent(BaseModel):
    """The full structured AI report payload."""
    executive_summary: str = Field(min_length=100, max_length=3000)
    risks: list[Risk] = Field(min_length=1, max_length=30)
    roadmap: list[RoadmapTask] = Field(min_length=1, max_length=40)
    framework_gaps: list[FrameworkGap] = Field(default_factory=list)

    @field_validator("risks")
    @classmethod
    def risk_ids_unique(cls, v):
        ids = [r.id for r in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Risk IDs must be unique within a report")
        return v

    @field_validator("roadmap")
    @classmethod
    def task_ids_unique(cls, v):
        ids = [t.id for t in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Roadmap task IDs must be unique within a report")
        return v


class ReportGenerationResult(BaseModel):
    """What the AI service returns to callers."""
    content: ReportContent
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    generation_ms: int = 0

    model_config = {"protected_namespaces": ()}
