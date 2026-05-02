"""Tests for the report output schema."""
import pytest
from pydantic import ValidationError

from app.services.ai.report_schema import (
    Effort,
    FrameworkCitation,
    FrameworkGap,
    ReportContent,
    Risk,
    RoadmapTask,
    Severity,
)


def _valid_risk(rid: str = "R1") -> Risk:
    return Risk(
        id=rid,
        title="A high-severity gap in MFA enforcement",
        description=(
            "Multi-factor authentication is not consistently enforced across "
            "production systems, raising the risk of credential compromise."
        ),
        severity=Severity.HIGH,
        likelihood="medium",
        business_impact="Compromised admin credentials could lead to data exposure.",
        affected_areas=["production_systems"],
        framework_citations=[FrameworkCitation(framework="soc2", control_code="CC6.1")],
    )


def _valid_task(tid: str = "T1") -> RoadmapTask:
    return RoadmapTask(
        id=tid,
        title="Enforce MFA on production access",
        description="Roll out MFA enforcement across all production tooling.",
        severity=Severity.HIGH,
        effort=Effort.SHORT,
        week_target=2,
        addresses_risk_ids=["R1"],
        framework_citations=[FrameworkCitation(framework="soc2", control_code="CC6.1")],
        success_criteria=["MFA enforced on cloud admin consoles"],
    )


class TestReportContentValidation:
    def test_minimal_valid_report_passes(self):
        content = ReportContent(
            executive_summary=(
                "This is a sufficiently long executive summary that meets the "
                "minimum length requirement for the report content schema. "
                "It describes posture and priorities."
            ),
            risks=[_valid_risk()],
            roadmap=[_valid_task()],
            framework_gaps=[],
        )
        assert content.executive_summary
        assert len(content.risks) == 1

    def test_executive_summary_too_short_rejected(self):
        with pytest.raises(ValidationError):
            ReportContent(
                executive_summary="too short",
                risks=[_valid_risk()],
                roadmap=[_valid_task()],
            )

    def test_at_least_one_risk_required(self):
        with pytest.raises(ValidationError):
            ReportContent(
                executive_summary=(
                    "Long enough executive summary " * 5
                ),
                risks=[],
                roadmap=[_valid_task()],
            )

    def test_duplicate_risk_ids_rejected(self):
        with pytest.raises(ValidationError):
            ReportContent(
                executive_summary="Long enough executive summary " * 5,
                risks=[_valid_risk("R1"), _valid_risk("R1")],
                roadmap=[_valid_task()],
            )

    def test_duplicate_task_ids_rejected(self):
        with pytest.raises(ValidationError):
            ReportContent(
                executive_summary="Long enough executive summary " * 5,
                risks=[_valid_risk()],
                roadmap=[_valid_task("T1"), _valid_task("T1")],
            )

    def test_invalid_severity_rejected(self):
        with pytest.raises(ValidationError):
            Risk(
                id="R1",
                title="title",
                description="A long enough description for the risk schema.",
                severity="extreme",  # not in enum
                likelihood="medium",
                business_impact="Some impact text here.",
            )

    def test_week_target_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            RoadmapTask(
                id="T1",
                title="Title",
                description="A sufficiently long description for the task.",
                severity=Severity.LOW,
                effort=Effort.SHORT,
                week_target=14,  # max is 13
            )


class TestFrameworkGap:
    def test_readiness_score_clamped_to_0_100(self):
        with pytest.raises(ValidationError):
            FrameworkGap(
                framework="soc2",
                framework_name="SOC 2",
                readiness_score=150,  # too high
                summary="A long enough summary text here.",
            )

    def test_too_many_top_gaps_rejected(self):
        with pytest.raises(ValidationError):
            FrameworkGap(
                framework="soc2",
                framework_name="SOC 2",
                readiness_score=50,
                summary="A long enough summary text here.",
                top_gaps=[f"gap{i}" for i in range(20)],
            )
