"""Tests for the scoring engine."""
import pytest

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
from app.services.scoring import (
    MAX_MATURITY,
    RuleBasedScorer,
    _score_response,
)


def _scoring_questionnaire() -> QuestionnaireVersion:
    return QuestionnaireVersion(
        version="t1",
        title="t",
        description="",
        sections=[
            Section(
                id="s",
                title="s",
                description=None,
                questions=[
                    Question(
                        id="q1",
                        text="Q1",
                        type=QuestionType.SINGLE_SELECT,
                        options=[
                            Option(value="best", label="Best"),
                            Option(value="ok", label="OK"),
                            Option(value="bad", label="Bad"),
                        ],
                        scoring=ScoringRule(
                            response_score={"best": 4, "ok": 2, "bad": 0}, weight=1.0
                        ),
                        control_refs=[ControlRef(framework="soc2", code="CC6.1")],
                    ),
                    Question(
                        id="q2",
                        text="Q2",
                        type=QuestionType.BOOLEAN,
                        scoring=ScoringRule(response_score={"true": 4, "false": 0}),
                        control_refs=[
                            ControlRef(framework="soc2", code="CC6.1"),
                            ControlRef(framework="ndpa", code="SEC_24"),
                        ],
                    ),
                    Question(
                        id="q3",
                        text="Q3",
                        type=QuestionType.MULTI_SELECT,
                        options=[
                            Option(value="a", label="A"),
                            Option(value="b", label="B"),
                            Option(value="c", label="C"),
                        ],
                        scoring=ScoringRule(
                            response_score={"a": 2, "b": 2, "c": 1}
                        ),
                        control_refs=[ControlRef(framework="ndpa", code="SEC_24")],
                    ),
                ],
            )
        ],
    )


class TestResponseScoring:
    def test_single_select_resolves_score(self):
        q = _scoring_questionnaire().get_question("q1")
        assert _score_response(q, "best") == 4
        assert _score_response(q, "ok") == 2
        assert _score_response(q, "bad") == 0

    def test_unknown_value_returns_none(self):
        q = _scoring_questionnaire().get_question("q1")
        assert _score_response(q, "unknown") is None

    def test_boolean_scoring(self):
        q = _scoring_questionnaire().get_question("q2")
        assert _score_response(q, True) == 4
        assert _score_response(q, False) == 0

    def test_multi_select_sums_capped(self):
        q = _scoring_questionnaire().get_question("q3")
        assert _score_response(q, ["a"]) == 2
        assert _score_response(q, ["a", "b"]) == 4
        # caps at MAX_MATURITY even with 5 selections
        assert _score_response(q, ["a", "b", "c"]) == MAX_MATURITY

    def test_no_response_returns_none(self):
        q = _scoring_questionnaire().get_question("q1")
        assert _score_response(q, None) is None


class TestRuleBasedScorer:
    def test_no_responses_yields_zero_score(self):
        result = RuleBasedScorer().score(_scoring_questionnaire(), {})
        assert result.overall_risk_score == 0
        assert result.framework_scores == {}
        assert result.response_count == 0

    def test_perfect_responses_yield_100(self):
        result = RuleBasedScorer().score(
            _scoring_questionnaire(),
            {"q1": "best", "q2": True, "q3": ["a", "b"]},
        )
        assert result.overall_risk_score == 100
        assert result.framework_scores["soc2"].score == 100
        assert result.framework_scores["ndpa"].score == 100

    def test_worst_responses_yield_zero(self):
        result = RuleBasedScorer().score(
            _scoring_questionnaire(),
            {"q1": "bad", "q2": False, "q3": []},
        )
        # q3 (multi-select) empty list is treated as no-response
        assert result.overall_risk_score == 0

    def test_control_aggregation_averages_across_questions(self):
        # CC6.1 is referenced by q1 and q2. With q1=ok (2) and q2=true (4),
        # average maturity should be 3 -> 75
        result = RuleBasedScorer().score(
            _scoring_questionnaire(),
            {"q1": "ok", "q2": True},
        )
        soc2_cc61 = result.control_scores[("soc2", "CC6.1")]
        assert soc2_cc61.maturity == 3.0
        assert soc2_cc61.maturity_pct == 75
        assert "q1" in soc2_cc61.contributing_questions
        assert "q2" in soc2_cc61.contributing_questions

    def test_framework_score_distinct_per_framework(self):
        # q1 only feeds SOC 2; q3 only feeds NDPA
        result = RuleBasedScorer().score(
            _scoring_questionnaire(),
            {"q1": "best", "q3": ["a"]},
        )
        # SOC 2: only CC6.1 with maturity 4 -> 100
        assert result.framework_scores["soc2"].score == 100
        # NDPA: SEC_24 with maturity 2 (from q3 a=2) -> 50
        assert result.framework_scores["ndpa"].score == 50


class TestRealQuestionnaireScoring:
    def test_full_responses_produce_meaningful_scores(self, sample_full_responses):
        result = RuleBasedScorer().score(
            get_questionnaire(), sample_full_responses
        )
        assert 0 < result.overall_risk_score < 100
        assert "soc2" in result.framework_scores
        assert "ndpa" in result.framework_scores
        # With our sample (mix of good and bad responses) we should land in
        # a credible range
        assert 30 <= result.overall_risk_score <= 90

    def test_all_best_responses_produce_high_score(self):
        # Strongest answer for every scored question
        ideal = {
            "co.primary_country": "NG",
            "co.serves_eu_users": False,
            "co.has_us_customers": True,
            "co.team_size": "11-50",
            "da.data_types": ["names_emails"],
            "da.data_volume": "1k_10k",
            "da.data_retention_policy": "yes_enforced",
            "da.encryption_at_rest": "all",
            "da.encryption_in_transit": "all",
            "ac.mfa_employees": "all_systems",
            "ac.access_reviews": "quarterly",
            "ac.offboarding": "same_day",
            "ac.privileged_access": "yes_full",
            "te.cloud_providers": ["aws"],
            "te.code_repository": "github",
            "te.code_review": "required_all",
            "te.backups": "auto_tested",
            "te.vulnerability_scanning": "continuous",
            "te.logging_monitoring": "centralized_alerting",
            "ve.vendor_count": "1-5",
            "ve.vendor_review": "formal_dd",
            "ve.dpa_signed": "all",
            "po.security_policy": "yes_reviewed",
            "po.privacy_policy_published": True,
            "po.security_training": "annual_tracked",
            "po.background_checks": "all",
            "po.dpo_appointed": True,
            "in.ir_plan": "yes_tested",
            "in.breach_in_last_year": "no",
            "in.breach_notification_aware": True,
            "go.target_frameworks": ["soc2", "ndpa"],
            "go.target_timeline": "6_months",
            "go.driver": ["customer_requirement"],
        }
        result = RuleBasedScorer().score(get_questionnaire(), ideal)
        assert result.overall_risk_score >= 95


@pytest.fixture
def sample_full_responses() -> dict:
    """Reusable canonical full-response fixture."""
    return {
        "co.primary_country": "NG",
        "co.serves_eu_users": False,
        "co.has_us_customers": True,
        "co.team_size": "11-50",
        "da.data_types": ["names_emails", "phone_numbers", "financial"],
        "da.data_volume": "10k_100k",
        "da.data_retention_policy": "yes_manual",
        "da.encryption_at_rest": "all",
        "da.encryption_in_transit": "all",
        "ac.mfa_employees": "all_systems",
        "ac.access_reviews": "annually",
        "ac.offboarding": "same_day_manual",
        "ac.privileged_access": "yes_full",
        "te.cloud_providers": ["aws"],
        "te.code_repository": "github",
        "te.code_review": "required_all",
        "te.backups": "auto_tested",
        "te.vulnerability_scanning": "periodic",
        "te.logging_monitoring": "centralized_alerting",
        "ve.vendor_count": "6-20",
        "ve.vendor_review": "informal",
        "ve.dpa_signed": "some",
        "po.security_policy": "yes_static",
        "po.privacy_policy_published": True,
        "po.security_training": "onboarding_only",
        "po.background_checks": "sensitive_roles",
        "po.dpo_appointed": False,
        "in.ir_plan": "yes_untested",
        "in.breach_in_last_year": "no",
        "in.breach_notification_aware": True,
        "go.target_frameworks": ["soc2", "ndpa"],
        "go.target_timeline": "6_months",
        "go.driver": ["customer_requirement", "investor_dd"],
    }
