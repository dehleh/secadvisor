"""Questionnaire schema types.

The questionnaire is a versioned, declarative document. Each version is
immutable — once published, responses against it must remain interpretable
forever. To evolve, ship a new version.

A QuestionnaireVersion is composed of Sections, each with Questions. Each
question declares:
  - id (stable across edits within a version)
  - type (single_select, multi_select, boolean, text, scale, ...)
  - control_refs (which compliance controls this answer feeds into)
  - scoring (how the answer translates to a maturity score)
"""
from enum import Enum as PyEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class QuestionType(str, PyEnum):
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
    TEXT = "text"
    SCALE = "scale"  # 1-5 maturity scale
    NUMBER = "number"


class ControlRef(BaseModel):
    """Pointer to a compliance control by framework + code."""
    framework: str  # FrameworkCode value, e.g. "soc2"
    code: str       # Control code, e.g. "CC6.1"


class ScoringRule(BaseModel):
    """How a question response contributes to a control's maturity score.

    For SINGLE_SELECT / SCALE: response_score is a dict mapping option value
    to maturity score (0-4).
    For BOOLEAN: response_score has keys "true" and "false".
    For MULTI_SELECT: each selected option contributes its score, summed and
    capped at the max (default 4).

    Weight scales the contribution when aggregated with other questions for
    the same control (defaults to 1.0).
    """
    response_score: dict[str, int] = Field(default_factory=dict)
    weight: float = 1.0


class Option(BaseModel):
    value: str
    label: str
    description: str | None = None


class Question(BaseModel):
    id: str
    text: str
    help_text: str | None = None
    type: QuestionType
    required: bool = True
    options: list[Option] = Field(default_factory=list)
    control_refs: list[ControlRef] = Field(default_factory=list)
    scoring: ScoringRule | None = None
    # Conditional display: only show this question if another question's
    # response matches one of these values. Empty means always show.
    depends_on_question_id: str | None = None
    depends_on_values: list[str] = Field(default_factory=list)

    @field_validator("options")
    @classmethod
    def validate_options_for_type(cls, v, info):
        qtype = info.data.get("type")
        if qtype in (QuestionType.SINGLE_SELECT, QuestionType.MULTI_SELECT) and not v:
            raise ValueError(f"Question type {qtype} requires options")
        return v


class Section(BaseModel):
    id: str
    title: str
    description: str | None = None
    questions: list[Question]


class QuestionnaireVersion(BaseModel):
    version: str  # semver e.g. "1.0.0"
    title: str
    description: str
    sections: list[Section]

    def get_question(self, question_id: str) -> Question | None:
        for section in self.sections:
            for question in section.questions:
                if question.id == question_id:
                    return question
        return None

    def all_questions(self) -> list[Question]:
        return [q for section in self.sections for q in section.questions]

    def all_question_ids(self) -> set[str]:
        return {q.id for q in self.all_questions()}
