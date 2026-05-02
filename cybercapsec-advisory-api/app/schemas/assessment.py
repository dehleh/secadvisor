"""Pydantic schemas for assessment endpoints."""
from typing import Any

from pydantic import BaseModel, Field

from app.models.assessment import AssessmentStatus


class QuestionnaireOptionOut(BaseModel):
    value: str
    label: str
    description: str | None = None


class QuestionnaireQuestionOut(BaseModel):
    id: str
    text: str
    help_text: str | None
    type: str
    required: bool
    options: list[QuestionnaireOptionOut]
    depends_on_question_id: str | None
    depends_on_values: list[str]


class QuestionnaireSectionOut(BaseModel):
    id: str
    title: str
    description: str | None
    questions: list[QuestionnaireQuestionOut]


class QuestionnaireOut(BaseModel):
    version: str
    title: str
    description: str
    sections: list[QuestionnaireSectionOut]


class AssessmentCreate(BaseModel):
    questionnaire_version: str | None = Field(default=None, max_length=20)


class AssessmentResponses(BaseModel):
    responses: dict[str, Any]
    merge: bool = True


class AssessmentProgressOut(BaseModel):
    version: str
    visible_questions: int
    answered_questions: int
    completion_pct: int
    remaining_question_ids: list[str]


class FrameworkScoreOut(BaseModel):
    framework: str
    score: int
    avg_maturity: float
    controls_assessed: int
    controls_total: int
    coverage_pct: int


class ControlScoreOut(BaseModel):
    framework: str
    code: str
    maturity: float
    maturity_pct: int
    contributing_questions: list[str]


class ScoringSummaryOut(BaseModel):
    overall_risk_score: int
    framework_scores: list[FrameworkScoreOut]
    control_scores: list[ControlScoreOut]
    response_count: int


class AssessmentOut(BaseModel):
    id: str
    company_id: str
    questionnaire_version: str
    status: AssessmentStatus
    responses: dict[str, Any]
    overall_risk_score: int | None
    soc2_readiness_score: int | None
    ndpa_compliance_score: int | None

    model_config = {"from_attributes": True}


class AssessmentSubmitOut(BaseModel):
    assessment: AssessmentOut
    scoring: ScoringSummaryOut
    report_id: str
