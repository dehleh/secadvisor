"""Tests for the response validator."""
import pytest

from app.services.assessment_validator import validate_responses
from app.services.questionnaire import get_questionnaire
from app.services.questionnaire.schema import (
    ControlRef,
    Option,
    Question,
    QuestionnaireVersion,
    QuestionType,
    ScoringRule,
    Section,
)


def _mini_questionnaire() -> QuestionnaireVersion:
    """A small handcrafted questionnaire for focused validator tests."""
    return QuestionnaireVersion(
        version="test-1",
        title="Test",
        description="",
        sections=[
            Section(
                id="s1",
                title="Section 1",
                description=None,
                questions=[
                    Question(
                        id="q.bool",
                        text="Boolean q",
                        type=QuestionType.BOOLEAN,
                        required=True,
                    ),
                    Question(
                        id="q.single",
                        text="Single select",
                        type=QuestionType.SINGLE_SELECT,
                        required=True,
                        options=[
                            Option(value="a", label="A"),
                            Option(value="b", label="B"),
                        ],
                    ),
                    Question(
                        id="q.multi",
                        text="Multi select",
                        type=QuestionType.MULTI_SELECT,
                        required=False,
                        options=[
                            Option(value="x", label="X"),
                            Option(value="y", label="Y"),
                        ],
                    ),
                    Question(
                        id="q.cond",
                        text="Conditional",
                        type=QuestionType.TEXT,
                        required=True,
                        depends_on_question_id="q.single",
                        depends_on_values=["a"],
                    ),
                ],
            )
        ],
    )


class TestDraftValidation:
    def test_empty_responses_pass_in_draft_mode(self):
        result = validate_responses(_mini_questionnaire(), {}, require_all=False)
        assert result.is_valid

    def test_unknown_question_id_rejected(self):
        result = validate_responses(
            _mini_questionnaire(),
            {"q.does_not_exist": "anything"},
            require_all=False,
        )
        assert not result.is_valid
        assert any(i.code == "unknown_question" for i in result.issues)

    def test_invalid_single_select_rejected(self):
        result = validate_responses(
            _mini_questionnaire(),
            {"q.single": "not-an-option"},
            require_all=False,
        )
        assert not result.is_valid

    def test_valid_single_select_accepted(self):
        result = validate_responses(
            _mini_questionnaire(), {"q.single": "a"}, require_all=False
        )
        assert result.is_valid

    def test_multi_select_with_invalid_member_rejected(self):
        result = validate_responses(
            _mini_questionnaire(),
            {"q.multi": ["x", "z"]},
            require_all=False,
        )
        assert not result.is_valid

    def test_boolean_must_be_bool(self):
        result = validate_responses(
            _mini_questionnaire(), {"q.bool": "true"}, require_all=False
        )
        assert not result.is_valid


class TestStrictValidation:
    def test_missing_required_fails_strict(self):
        result = validate_responses(_mini_questionnaire(), {}, require_all=True)
        assert not result.is_valid
        # q.bool, q.single are required and visible (q.cond depends on q.single)
        missing = [i.question_id for i in result.issues if i.code == "missing_required"]
        assert "q.bool" in missing
        assert "q.single" in missing

    def test_conditional_question_skipped_when_dependency_unmet(self):
        result = validate_responses(
            _mini_questionnaire(),
            {"q.bool": True, "q.single": "b"},  # q.cond depends on q.single == "a"
            require_all=True,
        )
        assert result.is_valid
        assert "q.cond" not in result.visible_question_ids

    def test_conditional_question_required_when_dependency_met(self):
        result = validate_responses(
            _mini_questionnaire(),
            {"q.bool": True, "q.single": "a"},  # triggers q.cond
            require_all=True,
        )
        assert not result.is_valid
        missing = {i.question_id for i in result.issues if i.code == "missing_required"}
        assert "q.cond" in missing


class TestRealQuestionnaire:
    def test_real_questionnaire_valid_with_no_responses_in_draft_mode(self):
        result = validate_responses(get_questionnaire(), {}, require_all=False)
        assert result.is_valid

    def test_real_questionnaire_full_response_passes_strict(self, sample_full_responses):
        result = validate_responses(
            get_questionnaire(), sample_full_responses, require_all=True
        )
        assert result.is_valid, result.errors_by_question


@pytest.fixture
def sample_full_responses() -> dict:
    """A complete response set against the real questionnaire (all required filled)."""
    return {
        # Company
        "co.primary_country": "NG",
        "co.serves_eu_users": False,
        "co.has_us_customers": True,
        "co.team_size": "11-50",
        # Data
        "da.data_types": ["names_emails", "phone_numbers", "financial"],
        "da.data_volume": "10k_100k",
        "da.data_retention_policy": "yes_manual",
        "da.encryption_at_rest": "all",
        "da.encryption_in_transit": "all",
        # Access
        "ac.mfa_employees": "all_systems",
        "ac.access_reviews": "annually",
        "ac.offboarding": "same_day_manual",
        "ac.privileged_access": "yes_full",
        # Tech
        "te.cloud_providers": ["aws"],
        "te.code_repository": "github",
        "te.code_review": "required_all",
        "te.backups": "auto_tested",
        "te.vulnerability_scanning": "periodic",
        "te.logging_monitoring": "centralized_alerting",
        # Vendors
        "ve.vendor_count": "6-20",
        "ve.vendor_review": "informal",
        "ve.dpa_signed": "some",
        # Policies
        "po.security_policy": "yes_static",
        "po.privacy_policy_published": True,
        "po.security_training": "onboarding_only",
        "po.background_checks": "sensitive_roles",
        "po.dpo_appointed": False,
        # Incidents
        "in.ir_plan": "yes_untested",
        "in.breach_in_last_year": "no",
        "in.breach_notification_aware": True,
        # Goals
        "go.target_frameworks": ["soc2", "ndpa"],
        "go.target_timeline": "6_months",
        "go.driver": ["customer_requirement", "investor_dd"],
    }
