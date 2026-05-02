"""Tests for the questionnaire definition itself.

Catches authoring mistakes: duplicate IDs, broken dependencies, scoring
rules referencing nonexistent option values.
"""
import pytest

from app.services.questionnaire import (
    LATEST_VERSION,
    QUESTIONNAIRE_VERSIONS,
    QuestionType,
    get_questionnaire,
)


def test_latest_version_exists():
    assert LATEST_VERSION in QUESTIONNAIRE_VERSIONS
    q = get_questionnaire()
    assert q.version == LATEST_VERSION


def test_questionnaire_has_sections():
    q = get_questionnaire()
    assert len(q.sections) >= 5
    assert all(s.questions for s in q.sections)


def test_question_ids_are_globally_unique():
    q = get_questionnaire()
    ids = [qq.id for qq in q.all_questions()]
    assert len(ids) == len(set(ids)), "Duplicate question IDs"


def test_section_ids_are_unique():
    q = get_questionnaire()
    ids = [s.id for s in q.sections]
    assert len(ids) == len(set(ids))


def test_dependencies_reference_existing_questions():
    q = get_questionnaire()
    valid_ids = q.all_question_ids()
    for question in q.all_questions():
        if question.depends_on_question_id:
            assert question.depends_on_question_id in valid_ids, (
                f"{question.id} depends on missing {question.depends_on_question_id}"
            )


def test_select_questions_have_options():
    q = get_questionnaire()
    for question in q.all_questions():
        if question.type in (QuestionType.SINGLE_SELECT, QuestionType.MULTI_SELECT):
            assert question.options, f"{question.id} ({question.type}) has no options"


def test_option_values_unique_per_question():
    q = get_questionnaire()
    for question in q.all_questions():
        values = [opt.value for opt in question.options]
        assert len(values) == len(set(values)), (
            f"Duplicate option values in {question.id}"
        )


def test_scoring_rules_only_reference_valid_option_values():
    """Catches the common mistake of typo'd option values in ScoringRule."""
    q = get_questionnaire()
    for question in q.all_questions():
        if question.scoring is None:
            continue
        if question.type == QuestionType.BOOLEAN:
            allowed = {"true", "false"}
        elif question.type in (
            QuestionType.SINGLE_SELECT,
            QuestionType.MULTI_SELECT,
        ):
            allowed = {opt.value for opt in question.options}
        elif question.type == QuestionType.SCALE:
            allowed = {str(i) for i in range(1, 6)}
        else:
            continue

        for key in question.scoring.response_score:
            assert key in allowed, (
                f"Scoring rule for {question.id} references unknown value '{key}'"
            )


def test_control_refs_have_valid_framework_codes():
    """Sanity check that we're using known framework codes."""
    from app.models.compliance import FrameworkCode

    valid = {fc.value for fc in FrameworkCode}
    q = get_questionnaire()
    for question in q.all_questions():
        for ref in question.control_refs:
            assert ref.framework in valid, (
                f"Question {question.id} references unknown framework '{ref.framework}'"
            )


def test_at_least_one_question_per_target_framework():
    """Every framework we claim to assess must have at least one question feeding it."""
    q = get_questionnaire()
    target_frameworks = {"soc2", "ndpa", "cbn_cyber"}
    referenced = set()
    for question in q.all_questions():
        for ref in question.control_refs:
            referenced.add(ref.framework)
    for fw in target_frameworks:
        assert fw in referenced, f"No questions reference framework {fw}"
