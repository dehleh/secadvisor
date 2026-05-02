"""Validation of user responses against a questionnaire version.

Responsibilities:
- Reject unknown question IDs (typos, stale frontends sending v0 questions)
- Reject malformed values (wrong type, value not in options)
- Skip questions whose `depends_on_*` conditions aren't met
- Report missing-required questions when a draft is submitted
"""
from dataclasses import dataclass, field
from typing import Any

from app.services.questionnaire.schema import (
    Question,
    QuestionnaireVersion,
    QuestionType,
)


@dataclass
class ValidationIssue:
    question_id: str
    code: str  # machine-readable: "missing_required", "invalid_value", "unknown_question"
    message: str


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)
    visible_question_ids: set[str] = field(default_factory=set)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    @property
    def errors_by_question(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for issue in self.issues:
            out.setdefault(issue.question_id, []).append(issue.message)
        return out


def _is_question_visible(question: Question, responses: dict[str, Any]) -> bool:
    """A conditional question is only visible if its dependency matches."""
    if not question.depends_on_question_id:
        return True
    parent_response = responses.get(question.depends_on_question_id)
    if parent_response is None:
        return False
    if isinstance(parent_response, list):
        return any(v in question.depends_on_values for v in parent_response)
    return parent_response in question.depends_on_values


def _validate_value(question: Question, value: Any) -> str | None:
    """Return an error message if the value is malformed, else None."""
    if question.type == QuestionType.BOOLEAN:
        if not isinstance(value, bool):
            return "Expected a boolean value"
        return None

    if question.type == QuestionType.TEXT:
        if not isinstance(value, str):
            return "Expected a text string"
        return None

    if question.type == QuestionType.NUMBER:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return "Expected a numeric value"
        return None

    if question.type == QuestionType.SCALE:
        if not isinstance(value, int) or isinstance(value, bool):
            return "Expected an integer scale value"
        if not 1 <= value <= 5:
            return "Scale value must be between 1 and 5"
        return None

    valid_values = {opt.value for opt in question.options}

    if question.type == QuestionType.SINGLE_SELECT:
        if not isinstance(value, str):
            return "Expected a single option value (string)"
        if value not in valid_values:
            return f"Value '{value}' is not a valid option"
        return None

    if question.type == QuestionType.MULTI_SELECT:
        if not isinstance(value, list):
            return "Expected a list of option values"
        for v in value:
            if not isinstance(v, str):
                return "All selected values must be strings"
            if v not in valid_values:
                return f"Value '{v}' is not a valid option"
        return None

    return None


def validate_responses(
    questionnaire: QuestionnaireVersion,
    responses: dict[str, Any],
    *,
    require_all: bool = False,
) -> ValidationResult:
    """Validate a response dict against the questionnaire schema.

    Args:
        questionnaire: The version definition to validate against.
        responses: A dict mapping question_id -> response value.
        require_all: If True, missing required questions become errors. If
            False (draft mode), missing values are allowed.

    Returns:
        ValidationResult with issues and the set of visible question IDs.
    """
    result = ValidationResult()
    valid_question_ids = questionnaire.all_question_ids()

    # Catch unknown question IDs first
    for qid in responses:
        if qid not in valid_question_ids:
            result.issues.append(
                ValidationIssue(
                    question_id=qid,
                    code="unknown_question",
                    message=f"Question '{qid}' is not part of questionnaire {questionnaire.version}",
                )
            )

    # Validate each question
    for question in questionnaire.all_questions():
        if not _is_question_visible(question, responses):
            continue

        result.visible_question_ids.add(question.id)
        value = responses.get(question.id)

        if value is None or (isinstance(value, list) and not value):
            if require_all and question.required:
                result.issues.append(
                    ValidationIssue(
                        question_id=question.id,
                        code="missing_required",
                        message=f"'{question.text}' is required",
                    )
                )
            continue

        error = _validate_value(question, value)
        if error:
            result.issues.append(
                ValidationIssue(
                    question_id=question.id, code="invalid_value", message=error
                )
            )

    return result
