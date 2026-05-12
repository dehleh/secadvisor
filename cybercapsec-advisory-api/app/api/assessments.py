"""Assessment API endpoints.

Lifecycle:
    POST   /assessments/             create draft
    GET    /assessments/             list company's assessments
    GET    /assessments/{id}         retrieve one
    PATCH  /assessments/{id}/responses  save responses (merge or replace)
    GET    /assessments/{id}/progress   completion progress
    POST   /assessments/{id}/submit  submit + score

    GET    /questionnaires/latest    latest questionnaire schema
    GET    /questionnaires/{ver}     specific version
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import get_tenant_object_or_404
from app.database import get_db
from app.deps import get_current_company, get_current_user, require_writer
from app.models import Assessment, Company, User
from app.schemas import (
    AssessmentCreate,
    AssessmentOut,
    AssessmentProgressOut,
    AssessmentResponses,
    AssessmentSubmitOut,
    ControlScoreOut,
    FrameworkScoreOut,
    QuestionnaireOptionOut,
    QuestionnaireOut,
    QuestionnaireQuestionOut,
    QuestionnaireSectionOut,
    ScoringSummaryOut,
)
from app.services.assessment import (
    create_draft,
    get_progress,
    save_responses,
    submit_assessment,
)
from app.services.questionnaire import (
    QUESTIONNAIRE_VERSIONS,
    LATEST_VERSION,
    get_questionnaire,
)
from app.services.scoring import ScoringResult


router = APIRouter(tags=["assessments"])


# --- Questionnaire endpoints --------------------------------------------------


def _serialize_questionnaire(version: str) -> QuestionnaireOut:
    if version not in QUESTIONNAIRE_VERSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire version {version} not found",
        )
    q = get_questionnaire(version)
    return QuestionnaireOut(
        version=q.version,
        title=q.title,
        description=q.description,
        sections=[
            QuestionnaireSectionOut(
                id=s.id,
                title=s.title,
                description=s.description,
                questions=[
                    QuestionnaireQuestionOut(
                        id=qq.id,
                        text=qq.text,
                        help_text=qq.help_text,
                        type=qq.type.value,
                        required=qq.required,
                        options=[
                            QuestionnaireOptionOut(
                                value=opt.value,
                                label=opt.label,
                                description=opt.description,
                            )
                            for opt in qq.options
                        ],
                        depends_on_question_id=qq.depends_on_question_id,
                        depends_on_values=qq.depends_on_values,
                    )
                    for qq in s.questions
                ],
            )
            for s in q.sections
        ],
    )


@router.get(
    "/questionnaires/latest",
    response_model=QuestionnaireOut,
    summary="Get the latest questionnaire schema",
)
def get_latest_questionnaire(
    user: Annotated[User, Depends(get_current_user)],  # auth required
) -> QuestionnaireOut:
    return _serialize_questionnaire(LATEST_VERSION)


@router.get(
    "/questionnaires/{version}",
    response_model=QuestionnaireOut,
    summary="Get a specific questionnaire version",
)
def get_questionnaire_by_version(
    version: str,
    user: Annotated[User, Depends(get_current_user)],
) -> QuestionnaireOut:
    return _serialize_questionnaire(version)


# --- Assessment endpoints -----------------------------------------------------


def _scoring_to_out(scoring: ScoringResult) -> ScoringSummaryOut:
    return ScoringSummaryOut(
        overall_risk_score=scoring.overall_risk_score,
        framework_scores=[
            FrameworkScoreOut(
                framework=fs.framework,
                score=fs.score,
                avg_maturity=round(fs.avg_maturity, 2),
                controls_assessed=fs.controls_assessed,
                controls_total=fs.controls_total,
                coverage_pct=fs.coverage_pct,
            )
            for fs in scoring.framework_scores.values()
        ],
        control_scores=[
            ControlScoreOut(
                framework=cs.framework,
                code=cs.code,
                maturity=round(cs.maturity, 2),
                maturity_pct=cs.maturity_pct,
                contributing_questions=cs.contributing_questions,
            )
            for cs in scoring.control_scores.values()
        ],
        response_count=scoring.response_count,
    )


@router.post(
    "/assessments",
    response_model=AssessmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft assessment",
    dependencies=[Depends(require_writer())],
)
def create_assessment(
    payload: AssessmentCreate,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentOut:
    try:
        assessment = create_draft(
            db, company, user, questionnaire_version=payload.questionnaire_version
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire version not found",
        )
    return AssessmentOut.model_validate(assessment)


@router.get(
    "/assessments",
    response_model=list[AssessmentOut],
    summary="List assessments for the current company",
)
def list_assessments(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AssessmentOut]:
    rows = (
        db.query(Assessment)
        .filter(Assessment.company_id == company.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return [AssessmentOut.model_validate(r) for r in rows]


@router.get(
    "/assessments/{assessment_id}",
    response_model=AssessmentOut,
    summary="Retrieve a single assessment",
)
def get_assessment(
    assessment_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentOut:
    assessment = get_tenant_object_or_404(db, Assessment, assessment_id, company.id)
    return AssessmentOut.model_validate(assessment)


@router.patch(
    "/assessments/{assessment_id}/responses",
    response_model=AssessmentOut,
    summary="Save partial or full responses on a draft",
    dependencies=[Depends(require_writer())],
)
def update_responses(
    assessment_id: str,
    payload: AssessmentResponses,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentOut:
    assessment = get_tenant_object_or_404(db, Assessment, assessment_id, company.id)
    updated, _ = save_responses(db, assessment, payload.responses, merge=payload.merge)
    return AssessmentOut.model_validate(updated)


@router.get(
    "/assessments/{assessment_id}/progress",
    response_model=AssessmentProgressOut,
    summary="Completion progress on an assessment",
)
def assessment_progress(
    assessment_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentProgressOut:
    assessment = get_tenant_object_or_404(db, Assessment, assessment_id, company.id)
    return AssessmentProgressOut(**get_progress(assessment))


@router.post(
    "/assessments/{assessment_id}/submit",
    response_model=AssessmentSubmitOut,
    summary="Submit and score an assessment, generating an AI report",
    dependencies=[Depends(require_writer())],
)
def submit(
    assessment_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentSubmitOut:
    assessment = get_tenant_object_or_404(db, Assessment, assessment_id, company.id)
    updated, scoring, report = submit_assessment(db, assessment, company)
    return AssessmentSubmitOut(
        assessment=AssessmentOut.model_validate(updated),
        scoring=_scoring_to_out(scoring),
        report_id=report.id,
    )
