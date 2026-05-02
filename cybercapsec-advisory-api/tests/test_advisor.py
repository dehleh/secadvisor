"""Tests for the AI advisor engine.

Coverage:
  - Prompt builder produces well-formed messages
  - MockAdvisor generates valid reports across a range of scoring scenarios
  - ClaudeAdvisor parses valid JSON responses correctly
  - ClaudeAdvisor rejects malformed responses
  - JSON markdown fences are stripped defensively
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.models import Company, CompanySize, CompanyStage, Sector, SubscriptionTier
from app.services.ai.advisor import (
    AdvisorGenerationError,
    ClaudeAdvisor,
    MockAdvisor,
    _parse_report_content,
    _select_knowledge,
    _strip_json_fences,
)
from app.services.ai.knowledge import default_retriever
from app.services.ai.prompt_builder import build_messages
from app.services.ai.report_schema import ReportContent, Severity
from app.services.questionnaire import get_questionnaire
from app.services.scoring import RuleBasedScorer


# ----- Fixtures ---------------------------------------------------------------


@pytest.fixture
def fintech_company() -> Company:
    """A representative African fintech for advisor tests."""
    return Company(
        id="co-1",
        name="Acme Fintech Ltd",
        slug="acme-fintech",
        country="NG",
        sector=Sector.FINTECH,
        size=CompanySize.SMALL,
        stage=CompanyStage.SEED,
        subscription_tier=SubscriptionTier.FREE,
    )


@pytest.fixture
def realistic_responses() -> dict:
    """Mid-tier startup responses — good and bad mixed."""
    return {
        "co.primary_country": "NG",
        "co.serves_eu_users": False,
        "co.has_us_customers": True,
        "co.team_size": "11-50",
        "da.data_types": ["names_emails", "phone_numbers", "financial", "bvn_nin"],
        "da.data_volume": "10k_100k",
        "da.data_retention_policy": "informal",
        "da.encryption_at_rest": "some",
        "da.encryption_in_transit": "external_only",
        "ac.mfa_employees": "critical_only",
        "ac.access_reviews": "ad_hoc",
        "ac.offboarding": "within_week",
        "ac.privileged_access": "logged_not_restricted",
        "te.cloud_providers": ["aws"],
        "te.code_repository": "github",
        "te.code_review": "encouraged",
        "te.backups": "auto_untested",
        "te.vulnerability_scanning": "ad_hoc",
        "te.logging_monitoring": "scattered",
        "ve.vendor_count": "6-20",
        "ve.vendor_review": "informal",
        "ve.dpa_signed": "none",
        "po.security_policy": "draft",
        "po.privacy_policy_published": False,
        "po.security_training": "ad_hoc",
        "po.background_checks": "no",
        "po.dpo_appointed": False,
        "in.ir_plan": "informal",
        "in.breach_in_last_year": "no",
        "in.breach_notification_aware": False,
        "go.target_frameworks": ["soc2", "ndpa"],
        "go.target_timeline": "6_months",
        "go.driver": ["customer_requirement", "investor_dd"],
    }


@pytest.fixture
def healthy_responses() -> dict:
    """High-maturity company — produces few risks."""
    return {
        "co.primary_country": "NG",
        "co.serves_eu_users": False,
        "co.has_us_customers": True,
        "co.team_size": "51-200",
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
        "go.target_timeline": "3_months",
        "go.driver": ["customer_requirement"],
    }


# ----- Knowledge selection ----------------------------------------------------


class TestKnowledgeSelection:
    def test_ng_fintech_gets_ndpa_and_cbn_snippets(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        snippets = _select_knowledge(
            default_retriever, fintech_company, realistic_responses, scoring
        )
        framework_codes_seen = set()
        for s in snippets:
            framework_codes_seen.update(s.framework_codes)
        assert "ndpa" in framework_codes_seen
        # SOC 2 requested via target_frameworks
        assert "soc2" in framework_codes_seen

    def test_weak_controls_pull_relevant_tags(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        snippets = _select_knowledge(
            default_retriever, fintech_company, realistic_responses, scoring
        )
        # Realistic responses have weak access controls and IR plan, so we
        # should retrieve snippets tagged with those concepts
        all_tags = set()
        for s in snippets:
            all_tags.update(s.tags)
        assert "access_control" in all_tags or "incident_response" in all_tags


# ----- Prompt builder ---------------------------------------------------------


class TestPromptBuilder:
    def test_messages_well_formed(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        knowledge = _select_knowledge(
            default_retriever, fintech_company, realistic_responses, scoring
        )

        system, messages = build_messages(
            fintech_company, questionnaire, realistic_responses, scoring, knowledge
        )

        assert isinstance(system, str)
        assert "JSON" in system  # instructs JSON output
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

        user_text = messages[0]["content"]
        assert fintech_company.name in user_text
        assert "Overall risk posture score:" in user_text
        assert "Assessment responses" in user_text
        # Knowledge is injected
        assert "regulatory and control knowledge" in user_text.lower()

    def test_human_readable_response_labels(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        knowledge = []
        _, messages = build_messages(
            fintech_company, questionnaire, realistic_responses, scoring, knowledge
        )
        # Raw value "external_only" should be rendered as the option label
        assert "External web traffic only" in messages[0]["content"]
        # Booleans rendered as Yes/No
        assert "A: No" in messages[0]["content"] or "A: Yes" in messages[0]["content"]


# ----- MockAdvisor ------------------------------------------------------------


class TestMockAdvisor:
    def test_mock_produces_valid_report_for_realistic_company(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        result = MockAdvisor().generate_report(
            fintech_company, questionnaire, realistic_responses, scoring
        )

        assert isinstance(result.content, ReportContent)
        assert result.model_used.startswith("mock-advisor")
        # Realistic mid-tier company should yield meaningful risk count
        assert 5 <= len(result.content.risks) <= 15
        assert len(result.content.roadmap) >= 5

    def test_mock_orders_risks_by_severity(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        result = MockAdvisor().generate_report(
            fintech_company, questionnaire, realistic_responses, scoring
        )
        severity_rank = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFORMATIONAL: 1,
        }
        ranks = [severity_rank[r.severity] for r in result.content.risks]
        # Mock sorts by composite (severity * gap), so within a severity level
        # the order may vary by maturity. The invariant we care about: severity
        # is monotonically non-increasing across the list.
        assert ranks == sorted(ranks, reverse=True), (
            f"Risks not ordered by severity: {ranks}"
        )

    def test_mock_orders_roadmap_by_week(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        result = MockAdvisor().generate_report(
            fintech_company, questionnaire, realistic_responses, scoring
        )
        weeks = [t.week_target for t in result.content.roadmap]
        assert weeks == sorted(weeks)

    def test_mock_links_tasks_to_risks(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        result = MockAdvisor().generate_report(
            fintech_company, questionnaire, realistic_responses, scoring
        )
        risk_ids = {r.id for r in result.content.risks}
        for task in result.content.roadmap:
            for ref in task.addresses_risk_ids:
                assert ref in risk_ids, (
                    f"Task {task.id} references unknown risk {ref}"
                )

    def test_mock_handles_healthy_company(
        self, fintech_company, healthy_responses
    ):
        # Healthy company should still produce a coherent (if minimal) report
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, healthy_responses)
        result = MockAdvisor().generate_report(
            fintech_company, questionnaire, healthy_responses, scoring
        )
        assert isinstance(result.content, ReportContent)
        assert len(result.content.risks) >= 1
        assert len(result.content.roadmap) >= 1

    def test_mock_reflects_company_context_in_summary(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        result = MockAdvisor().generate_report(
            fintech_company, questionnaire, realistic_responses, scoring
        )
        summary = result.content.executive_summary
        assert fintech_company.name in summary
        assert "fintech" in summary.lower() or "Nigeria" in summary or "NG" in summary

    def test_mock_includes_framework_gaps_for_assessed_frameworks(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)
        result = MockAdvisor().generate_report(
            fintech_company, questionnaire, realistic_responses, scoring
        )
        gap_frameworks = {fg.framework for fg in result.content.framework_gaps}
        assert "soc2" in gap_frameworks
        assert "ndpa" in gap_frameworks


# ----- JSON parsing edge cases ------------------------------------------------


class TestJSONParsing:
    def test_strip_json_fences_no_fences(self):
        assert _strip_json_fences('{"a": 1}') == '{"a": 1}'

    def test_strip_json_fences_with_json_fence(self):
        text = '```json\n{"a": 1}\n```'
        assert _strip_json_fences(text) == '{"a": 1}'

    def test_strip_json_fences_with_plain_fence(self):
        text = '```\n{"a": 1}\n```'
        assert _strip_json_fences(text) == '{"a": 1}'

    def test_strip_json_fences_handles_whitespace(self):
        text = '  \n```json\n{"a": 1}\n```  \n'
        assert _strip_json_fences(text) == '{"a": 1}'

    def test_parse_invalid_json_raises(self):
        with pytest.raises(AdvisorGenerationError):
            _parse_report_content("not valid json {")

    def test_parse_schema_violation_raises(self):
        # Valid JSON but missing required fields
        with pytest.raises(AdvisorGenerationError):
            _parse_report_content('{"executive_summary": "too short"}')

    def test_parse_valid_response(self):
        valid = {
            "executive_summary": "x" * 200,
            "risks": [
                {
                    "id": "R1",
                    "title": "A real-looking title",
                    "description": "A description that is long enough to pass.",
                    "severity": "high",
                    "likelihood": "medium",
                    "business_impact": "Significant business impact text.",
                }
            ],
            "roadmap": [
                {
                    "id": "T1",
                    "title": "Implement something concrete",
                    "description": "Do these things to address the risk.",
                    "severity": "high",
                    "effort": "short",
                    "week_target": 2,
                }
            ],
            "framework_gaps": [],
        }
        content = _parse_report_content(json.dumps(valid))
        assert len(content.risks) == 1
        assert content.risks[0].id == "R1"


# ----- ClaudeAdvisor with mocked SDK -----------------------------------------


class TestClaudeAdvisor:
    def _make_anthropic_response(self, text: str):
        """Build a minimal mock matching the Anthropic SDK response shape."""
        block = MagicMock()
        block.text = text
        response = MagicMock()
        response.content = [block]
        response.usage.input_tokens = 1234
        response.usage.output_tokens = 5678
        return response

    def test_claude_advisor_parses_valid_response(
        self, fintech_company, realistic_responses
    ):
        valid_payload = {
            "executive_summary": "A " + ("comprehensive " * 20) + "summary.",
            "risks": [
                {
                    "id": "R1",
                    "title": "Title for the risk",
                    "description": "A description that is long enough.",
                    "severity": "high",
                    "likelihood": "medium",
                    "business_impact": "Concrete business impact stated.",
                }
            ],
            "roadmap": [
                {
                    "id": "T1",
                    "title": "Concrete title for the task",
                    "description": "A description that is long enough.",
                    "severity": "high",
                    "effort": "short",
                    "week_target": 2,
                }
            ],
            "framework_gaps": [],
        }
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)

        with patch("anthropic.Anthropic") as MockClient:
            instance = MockClient.return_value
            instance.messages.create.return_value = self._make_anthropic_response(
                json.dumps(valid_payload)
            )

            advisor = ClaudeAdvisor()
            result = advisor.generate_report(
                fintech_company, questionnaire, realistic_responses, scoring
            )

        assert result.input_tokens == 1234
        assert result.output_tokens == 5678
        assert len(result.content.risks) == 1
        # The system + user messages were assembled
        instance.messages.create.assert_called_once()
        call_kwargs = instance.messages.create.call_args.kwargs
        assert "system" in call_kwargs
        assert "messages" in call_kwargs
        assert call_kwargs["messages"][0]["role"] == "user"

    def test_claude_advisor_retries_on_invalid_json(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)

        valid_payload = {
            "executive_summary": "A " + ("comprehensive " * 20) + "summary.",
            "risks": [
                {
                    "id": "R1",
                    "title": "Title for the risk",
                    "description": "A description that is long enough.",
                    "severity": "high",
                    "likelihood": "medium",
                    "business_impact": "Concrete business impact stated.",
                }
            ],
            "roadmap": [
                {
                    "id": "T1",
                    "title": "Concrete title for the task",
                    "description": "A description that is long enough.",
                    "severity": "high",
                    "effort": "short",
                    "week_target": 2,
                }
            ],
            "framework_gaps": [],
        }

        # First call returns garbage, second returns valid
        responses = [
            self._make_anthropic_response("not json"),
            self._make_anthropic_response(json.dumps(valid_payload)),
        ]

        with patch("anthropic.Anthropic") as MockClient:
            instance = MockClient.return_value
            instance.messages.create.side_effect = responses

            result = ClaudeAdvisor().generate_report(
                fintech_company, questionnaire, realistic_responses, scoring
            )
        # We retried — second response was the valid one
        assert len(result.content.risks) == 1
        assert instance.messages.create.call_count == 2

    def test_claude_advisor_fails_after_max_retries(
        self, fintech_company, realistic_responses
    ):
        questionnaire = get_questionnaire()
        scoring = RuleBasedScorer().score(questionnaire, realistic_responses)

        with patch("anthropic.Anthropic") as MockClient:
            instance = MockClient.return_value
            instance.messages.create.return_value = self._make_anthropic_response(
                "still not json"
            )
            with pytest.raises(AdvisorGenerationError):
                ClaudeAdvisor().generate_report(
                    fintech_company, questionnaire, realistic_responses, scoring
                )
        # Default is 3 attempts
        assert instance.messages.create.call_count == 3


# ----- Engine factory ---------------------------------------------------------


class TestEngineFactory:
    def test_factory_returns_mock_when_flag_set(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK_AI", "true")
        # Reset cached settings
        from app.config import get_settings

        get_settings.cache_clear()
        from app.services.ai.advisor import get_advisor_engine

        engine = get_advisor_engine()
        assert isinstance(engine, MockAdvisor)
        get_settings.cache_clear()

    def test_factory_returns_mock_when_no_api_key(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK_AI", "false")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        from app.config import get_settings

        get_settings.cache_clear()
        from app.services.ai.advisor import get_advisor_engine

        engine = get_advisor_engine()
        assert isinstance(engine, MockAdvisor)
        get_settings.cache_clear()
