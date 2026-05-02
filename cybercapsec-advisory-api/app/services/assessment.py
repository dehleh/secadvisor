"""Assessment service — orchestrates the assessment lifecycle.

States:
    DRAFT       — created, no/partial responses
    IN_PROGRESS — responses being saved (alias for DRAFT in v1)
    SUBMITTED   — user has submitted; validation passed; ready to score
    PROCESSING  — scoring/AI report generation in flight
    COMPLETED   — scores stored, report available
    FAILED      — scoring or report gen errored

Session 3 wires AI report generation into the submit flow. Submission now:
  1. Validates strictly
  2. Scores
  3. Generates the AI report
  4. Persists scores + report atomically
"""
import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Assessment, AssessmentStatus, Company, Report, ReportType, User
from app.services.ai import AdvisorEngine, AdvisorGenerationError, get_advisor_engine
from app.services.assessment_validator import (
    ValidationResult,
    validate_responses,
)
from app.services.questionnaire import LATEST_VERSION, get_questionnaire
from app.services.scoring import ScoringResult, default_scorer

logger = logging.getLogger(__name__)


# --- State transitions ---------------------------------------------------------

ALLOWED_TRANSITIONS = {
    AssessmentStatus.DRAFT: {AssessmentStatus.IN_PROGRESS, AssessmentStatus.SUBMITTED},
    AssessmentStatus.IN_PROGRESS: {AssessmentStatus.SUBMITTED, AssessmentStatus.DRAFT},
    AssessmentStatus.SUBMITTED: {AssessmentStatus.PROCESSING, AssessmentStatus.COMPLETED},
    AssessmentStatus.PROCESSING: {AssessmentStatus.COMPLETED, AssessmentStatus.FAILED},
    AssessmentStatus.COMPLETED: set(),  # terminal
    AssessmentStatus.FAILED: {AssessmentStatus.SUBMITTED},  # allow retry
}


def _transition(assessment: Assessment, new_status: AssessmentStatus) -> None:
    if new_status not in ALLOWED_TRANSITIONS[assessment.status]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot transition assessment from {assessment.status.value} "
                f"to {new_status.value}"
            ),
        )
    assessment.status = new_status


# --- Lifecycle operations ------------------------------------------------------


def create_draft(
    db: Session,
    company: Company,
    user: User,
    *,
    questionnaire_version: str | None = None,
) -> Assessment:
    """Create a new draft assessment for a company."""
    version = questionnaire_version or LATEST_VERSION
    # Validate version exists
    get_questionnaire(version)

    # Tier limit check — count active (non-terminal) assessments
    from app.services.billing import require_within_limit

    active_count = (
        db.query(Assessment)
        .filter(
            Assessment.company_id == company.id,
            Assessment.status.in_(
                [
                    AssessmentStatus.DRAFT,
                    AssessmentStatus.IN_PROGRESS,
                    AssessmentStatus.SUBMITTED,
                    AssessmentStatus.PROCESSING,
                ]
            ),
        )
        .count()
    )
    require_within_limit(company, "max_active_assessments", active_count)

    assessment = Assessment(
        company_id=company.id,
        submitted_by_user_id=user.id,
        questionnaire_version=version,
        status=AssessmentStatus.DRAFT,
        responses={},
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def save_responses(
    db: Session,
    assessment: Assessment,
    new_responses: dict[str, Any],
    *,
    merge: bool = True,
) -> tuple[Assessment, ValidationResult]:
    """Save partial or full responses on a draft assessment.

    Validates in non-strict mode (missing required allowed during drafts).
    Unknown questions and malformed values still raise validation errors.

    If `merge` is True, new responses are merged on top of existing ones.
    If False, responses replace entirely.
    """
    if assessment.status not in (
        AssessmentStatus.DRAFT,
        AssessmentStatus.IN_PROGRESS,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot save responses on a {assessment.status.value} assessment",
        )

    questionnaire = get_questionnaire(assessment.questionnaire_version)
    merged = {**assessment.responses, **new_responses} if merge else dict(new_responses)

    result = validate_responses(questionnaire, merged, require_all=False)
    if not result.is_valid:
        # Reject the save outright — never persist invalid data
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Invalid responses", "errors": result.errors_by_question},
        )

    assessment.responses = merged
    if assessment.status == AssessmentStatus.DRAFT and merged:
        _transition(assessment, AssessmentStatus.IN_PROGRESS)

    db.commit()
    db.refresh(assessment)
    return assessment, result


def submit_assessment(
    db: Session,
    assessment: Assessment,
    company: Company,
    *,
    advisor: AdvisorEngine | None = None,
) -> tuple[Assessment, ScoringResult, Report]:
    """Submit a completed assessment: validate strictly, score, generate report.

    Steps:
      1. Validate responses strictly (all required answered)
      2. Transition to PROCESSING
      3. Score the assessment
      4. Generate the AI report (mock or Claude)
      5. Persist scores + report; transition to COMPLETED
      6. On any failure, transition to FAILED for retry

    The advisor engine is injectable for tests; defaults to the configured
    engine (mock or Claude based on USE_MOCK_AI flag).
    """
    if assessment.status not in (
        AssessmentStatus.DRAFT,
        AssessmentStatus.IN_PROGRESS,
        AssessmentStatus.FAILED,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot submit a {assessment.status.value} assessment",
        )

    questionnaire = get_questionnaire(assessment.questionnaire_version)
    result = validate_responses(
        questionnaire, assessment.responses, require_all=True
    )
    if not result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Assessment is incomplete",
                "errors": result.errors_by_question,
            },
        )

    _transition(assessment, AssessmentStatus.SUBMITTED)
    _transition(assessment, AssessmentStatus.PROCESSING)
    db.commit()  # commit transition so PROCESSING is visible if generation is long

    try:
        scoring = default_scorer.score(questionnaire, assessment.responses)
        # Resolve the advisor engine: if the company's tier doesn't include
        # AI advisor access, force the mock engine so they get *something*
        # (rules-based output) rather than a 402 mid-submission.
        if advisor is None:
            from app.services.ai import MockAdvisor
            from app.services.billing import get_limits

            limits = get_limits(company)
            engine = (
                get_advisor_engine() if limits.ai_advisor_enabled else MockAdvisor()
            )
        else:
            engine = advisor
        report_result = engine.generate_report(
            company, questionnaire, assessment.responses, scoring
        )
    except (AdvisorGenerationError, Exception) as exc:
        logger.exception("Failed to generate report for assessment %s", assessment.id)
        _transition(assessment, AssessmentStatus.FAILED)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Report generation failed: {exc.__class__.__name__}",
        ) from exc

    # Persist scoring on the assessment
    assessment.overall_risk_score = scoring.overall_risk_score
    soc2 = scoring.get_framework("soc2")
    if soc2:
        assessment.soc2_readiness_score = soc2.score
    ndpa = scoring.get_framework("ndpa")
    if ndpa:
        assessment.ndpa_compliance_score = ndpa.score

    # Determine report type based on prior reports for this company
    prior_count = (
        db.query(Report)
        .join(Assessment, Report.assessment_id == Assessment.id)
        .filter(Assessment.company_id == company.id)
        .count()
    )
    report_type = ReportType.INITIAL if prior_count == 0 else ReportType.REASSESSMENT

    # Persist the AI report
    content = report_result.content
    report = Report(
        assessment_id=assessment.id,
        report_type=report_type,
        executive_summary=content.executive_summary,
        risk_register=[r.model_dump(mode="json") for r in content.risks],
        roadmap=[t.model_dump(mode="json") for t in content.roadmap],
        framework_gaps={
            fg.framework: fg.model_dump(mode="json") for fg in content.framework_gaps
        },
        model_used=report_result.model_used,
        generation_tokens_input=report_result.input_tokens,
        generation_tokens_output=report_result.output_tokens,
        generation_ms=report_result.generation_ms,
    )
    db.add(report)

    _transition(assessment, AssessmentStatus.COMPLETED)
    db.commit()
    db.refresh(assessment)
    db.refresh(report)

    # Seed roadmap items from the new report so the user can start tracking
    # immediately. Failure here doesn't fail the submission — the user can
    # always re-seed manually via the API.
    try:
        from app.services.roadmap import seed_roadmap_from_report

        seed_roadmap_from_report(db, company, report)
    except Exception:
        logger.exception(
            "Failed to seed roadmap items for report %s; continuing", report.id
        )

    return assessment, scoring, report


def get_progress(assessment: Assessment) -> dict:
    """Return how much of the questionnaire has been completed."""
    questionnaire = get_questionnaire(assessment.questionnaire_version)
    result = validate_responses(questionnaire, assessment.responses, require_all=False)

    visible = result.visible_question_ids
    answered = {qid for qid in visible if assessment.responses.get(qid) not in (None, [])}

    return {
        "version": assessment.questionnaire_version,
        "visible_questions": len(visible),
        "answered_questions": len(answered),
        "completion_pct": (
            round(len(answered) / len(visible) * 100) if visible else 0
        ),
        "remaining_question_ids": sorted(visible - answered),
    }
