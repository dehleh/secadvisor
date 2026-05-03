"""AI advisor engine — generates structured reports from assessments.

Architecture:
  AdvisorEngine (interface)
    ├── ClaudeAdvisor   — real LLM call via Anthropic SDK
    └── MockAdvisor     — deterministic plausible output, no API call

Selection happens via the USE_MOCK_AI feature flag, mirroring SimCheck's
USE_MOCK_TELCO pattern. Tests and dashboard development run on the mock;
production uses Claude.
"""
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.models import Company
from app.services.ai.knowledge import (
    KnowledgeRetriever,
    KnowledgeSnippet,
    default_retriever,
)
from app.services.ai.prompt_builder import build_messages
from app.services.ai.report_schema import (
    Effort,
    FrameworkCitation,
    FrameworkGap,
    ReportContent,
    ReportGenerationResult,
    Risk,
    RoadmapTask,
    Severity,
)
from app.services.questionnaire.schema import QuestionnaireVersion
from app.services.scoring import ScoringResult

logger = logging.getLogger(__name__)


# ----- Knowledge selection helpers -------------------------------------------


def _select_knowledge(
    retriever: KnowledgeRetriever,
    company: Company,
    responses: dict[str, Any],
    scoring: ScoringResult,
    *,
    limit: int = 25,
) -> list[KnowledgeSnippet]:
    """Choose the most relevant knowledge snippets to ground the prompt.

    Strategy:
      - Pull frameworks the company explicitly targets (from goals section)
      - Always include frameworks for the company's country (NDPA for NG, etc.)
      - Use weak controls + sector to derive tag filters
    """
    frameworks: set[str] = set()

    # Company-targeted frameworks
    target_frameworks = responses.get("go.target_frameworks", [])
    if isinstance(target_frameworks, list):
        frameworks.update(target_frameworks)

    # Country-implied frameworks
    country_frameworks = {
        "NG": ["ndpa", "cbn_cyber"],
        "ZA": ["popia"],
        "KE": ["kenya_dpa"],
        "GH": ["ghana_dpa"],
    }
    frameworks.update(country_frameworks.get(company.country.upper(), []))

    # Sector-implied frameworks
    if company.sector.value == "fintech":
        frameworks.update(["cbn_cyber"] if company.country.upper() == "NG" else [])

    # Tags: derived from weakest controls + sector
    tags: set[str] = set()
    if scoring.control_scores:
        weakest = sorted(scoring.control_scores.values(), key=lambda x: x.maturity)[:6]
        # Map control codes to common tag concepts
        tag_hints = {
            "CC6.1": ["access_control", "encryption"],
            "CC6.2": ["access_review", "offboarding"],
            "CC6.7": ["encryption", "tls"],
            "CC7.1": ["vulnerability"],
            "CC7.2": ["monitoring", "logging"],
            "CC7.3": ["incident_response"],
            "CC8.1": ["change_management", "code_review"],
            "CC9.2": ["vendors"],
            "CC1.4": ["training", "background_checks"],
            "A1.2": ["backup"],
            "SEC_24": ["security", "encryption"],
            "SEC_25": ["privacy_policy"],
            "SEC_26": ["retention"],
            "SEC_29": ["vendors", "dpa"],
            "SEC_32": ["dpo"],
            "SEC_40": ["breach", "notification"],
            "4.2": ["access_control", "fintech"],
            "4.5": ["encryption", "fintech"],
            "4.7": ["monitoring", "fintech"],
            "4.8": ["incident_response", "fintech"],
        }
        for cs in weakest:
            tags.update(tag_hints.get(cs.code, []))

    if company.sector.value == "fintech":
        tags.update(["fintech", "fraud", "sim_swap"])

    return retriever.retrieve(
        framework_codes=list(frameworks) if frameworks else None,
        tags=list(tags) if tags else None,
        limit=limit,
    )


# ----- Engine interface -------------------------------------------------------


class AdvisorEngine(ABC):
    @abstractmethod
    def generate_report(
        self,
        company: Company,
        questionnaire: QuestionnaireVersion,
        responses: dict[str, Any],
        scoring: ScoringResult,
    ) -> ReportGenerationResult: ...


# ----- Real Claude implementation --------------------------------------------


class AdvisorGenerationError(Exception):
    """Raised when the AI response cannot be parsed or is invalid."""


def _strip_json_fences(text: str) -> str:
    """Defensive cleanup if the model wraps JSON in markdown fences anyway."""
    text = text.strip()
    if text.startswith("```"):
        # Strip ```json or ``` opening
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[: -3].rstrip()
    return text.strip()


def _parse_report_content(raw_text: str) -> ReportContent:
    """Parse and validate the model's JSON output."""
    cleaned = _strip_json_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AdvisorGenerationError(
            f"Model output is not valid JSON: {exc}"
        ) from exc

    try:
        return ReportContent.model_validate(data)
    except ValidationError as exc:
        raise AdvisorGenerationError(
            f"Model output failed schema validation: {exc}"
        ) from exc


class ClaudeAdvisor(AdvisorEngine):
    """Calls the Anthropic API to generate a real report."""

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 8000,
    ):
        self._retriever = retriever or default_retriever
        settings = get_settings()
        self._model = model or settings.CLAUDE_MODEL
        self._max_tokens = max_tokens
        self._api_key = settings.ANTHROPIC_API_KEY

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(AdvisorGenerationError),
        reraise=True,
    )
    def generate_report(
        self,
        company: Company,
        questionnaire: QuestionnaireVersion,
        responses: dict[str, Any],
        scoring: ScoringResult,
    ) -> ReportGenerationResult:
        # Lazy import: keeps the SDK out of test paths that use the mock
        from anthropic import Anthropic

        knowledge = _select_knowledge(self._retriever, company, responses, scoring)
        system, messages = build_messages(
            company, questionnaire, responses, scoring, knowledge
        )

        client = Anthropic(api_key=self._api_key)
        # Prompt caching: the system prompt is identical across every
        # report we generate, so we mark it as a cached prefix. Anthropic
        # bills cached input tokens at ~10% of the normal rate after the
        # first call, with a 5-minute TTL that refreshes on each hit.
        # See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        system_blocks = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        start = time.perf_counter()
        response = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_blocks,
            messages=messages,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Concatenate text blocks (typical response is one text block)
        raw_text = "".join(
            block.text for block in response.content if hasattr(block, "text")
        )
        content = _parse_report_content(raw_text)

        return ReportGenerationResult(
            content=content,
            model_used=self._model,
            input_tokens=getattr(response.usage, "input_tokens", 0),
            output_tokens=getattr(response.usage, "output_tokens", 0),
            generation_ms=elapsed_ms,
        )


# ----- Mock implementation (deterministic, free) -----------------------------


class MockAdvisor(AdvisorEngine):
    """Returns a deterministic plausible report based on assessment scoring.

    Uses scoring weak-points to generate risks and roadmap tasks. Output is
    realistic enough for frontend development and tests, and fully
    deterministic for snapshot-style assertions.

    Not pretending to be intelligent — this is a placeholder for the LLM.
    """

    def generate_report(
        self,
        company: Company,
        questionnaire: QuestionnaireVersion,
        responses: dict[str, Any],
        scoring: ScoringResult,
    ) -> ReportGenerationResult:
        risks = self._generate_risks(scoring, responses)
        roadmap = self._generate_roadmap(risks, scoring)
        framework_gaps = self._generate_framework_gaps(scoring)
        executive_summary = self._generate_executive_summary(
            company, scoring, risks, responses
        )

        content = ReportContent(
            executive_summary=executive_summary,
            risks=risks,
            roadmap=roadmap,
            framework_gaps=framework_gaps,
        )
        return ReportGenerationResult(
            content=content,
            model_used="mock-advisor-1.0",
            input_tokens=0,
            output_tokens=0,
            generation_ms=10,
        )

    # --- generators

    _CONTROL_RISK_TEMPLATES: dict[str, dict[str, Any]] = {
        "CC6.1": {
            "title": "Inadequate logical access controls on production",
            "description": (
                "Production systems and admin consoles lack consistently enforced "
                "access controls, creating an elevated risk of credential compromise "
                "leading to data exposure or service disruption."
            ),
            "severity": Severity.HIGH,
            "likelihood": "medium",
            "business_impact": (
                "A compromised admin credential could lead to data breach with "
                "regulatory notification obligations and customer trust damage."
            ),
            "areas": ["production_systems", "admin_consoles"],
        },
        "CC6.2": {
            "title": "Slow or inconsistent offboarding leaves dormant access",
            "description": (
                "When employees or contractors leave, their access is not revoked "
                "promptly. Dormant accounts are a leading source of insider risk "
                "and are flagged by SOC 2 auditors."
            ),
            "severity": Severity.HIGH,
            "likelihood": "high",
            "business_impact": (
                "Unauthorised access by former staff and SOC 2 audit findings."
            ),
            "areas": ["identity", "hr_processes"],
        },
        "CC6.7": {
            "title": "Gaps in encryption-in-transit coverage",
            "description": (
                "Some services or internal endpoints transmit data unencrypted, "
                "exposing it to network-level interception."
            ),
            "severity": Severity.MEDIUM,
            "likelihood": "low",
            "business_impact": (
                "Potential data interception and SOC 2 / NDPA control gap."
            ),
            "areas": ["network", "data_in_transit"],
        },
        "CC7.1": {
            "title": "No continuous vulnerability scanning",
            "description": (
                "Code, dependencies, and running infrastructure are not regularly "
                "scanned for vulnerabilities. New CVEs in dependencies can sit "
                "unpatched for months."
            ),
            "severity": Severity.HIGH,
            "likelihood": "high",
            "business_impact": (
                "Exploited vulnerabilities leading to compromise; SOC 2 audit gap."
            ),
            "areas": ["application_security", "infrastructure"],
        },
        "CC7.2": {
            "title": "Limited security event monitoring and alerting",
            "description": (
                "Security-relevant logs are not centrally collected or actively "
                "alerted on. Attacks may go undetected for extended periods."
            ),
            "severity": Severity.HIGH,
            "likelihood": "medium",
            "business_impact": (
                "Undetected breach could expand significantly before discovery."
            ),
            "areas": ["detection", "logging"],
        },
        "CC7.3": {
            "title": "Untested incident response plan",
            "description": (
                "Either no IR plan exists or it has never been tested. In a real "
                "incident, response is likely to be slow, error-prone, and miss "
                "regulatory notification deadlines."
            ),
            "severity": Severity.HIGH,
            "likelihood": "medium",
            "business_impact": (
                "Missed 72-hour NDPA / 24-hour CBN notification windows; "
                "uncoordinated response amplifying impact."
            ),
            "areas": ["incident_response", "regulatory"],
        },
        "CC8.1": {
            "title": "Code changes deploy without consistent review",
            "description": (
                "Code reviews are not consistently required before production "
                "deployment, increasing the risk of vulnerable or malicious code "
                "reaching customers."
            ),
            "severity": Severity.MEDIUM,
            "likelihood": "medium",
            "business_impact": (
                "Higher defect and vulnerability rate in production; SOC 2 finding."
            ),
            "areas": ["development", "ci_cd"],
        },
        "CC9.2": {
            "title": "Limited vendor security due diligence",
            "description": (
                "Third parties handling customer data are not formally assessed "
                "for their own security posture, exposing the company to "
                "supply-chain risk."
            ),
            "severity": Severity.MEDIUM,
            "likelihood": "medium",
            "business_impact": (
                "Vendor compromise leading to your data exposure; NDPA §29 gap."
            ),
            "areas": ["third_party"],
        },
        "CC1.4": {
            "title": "Insufficient security awareness training",
            "description": (
                "Staff are not regularly trained on security awareness. Phishing "
                "and social engineering remain leading attack vectors against "
                "African fintech and SaaS companies."
            ),
            "severity": Severity.MEDIUM,
            "likelihood": "high",
            "business_impact": (
                "Successful phishing leading to credential compromise."
            ),
            "areas": ["people", "phishing"],
        },
        "A1.2": {
            "title": "Backups not regularly tested",
            "description": (
                "Backups exist but restore procedures have not been tested. "
                "Untested backups frequently fail when actually needed."
            ),
            "severity": Severity.HIGH,
            "likelihood": "low",
            "business_impact": (
                "Data loss and extended downtime during a recovery scenario."
            ),
            "areas": ["recovery", "availability"],
        },
        "SEC_24": {
            "title": "NDPA §24 security-of-processing gaps",
            "description": (
                "Technical and organisational measures protecting personal data "
                "do not consistently meet NDPA §24 expectations, particularly "
                "around encryption and tested resilience."
            ),
            "severity": Severity.HIGH,
            "likelihood": "medium",
            "business_impact": (
                "NDPC enforcement action; fines up to ₦10M or 2% of revenue."
            ),
            "areas": ["data_protection", "regulatory"],
        },
        "SEC_25": {
            "title": "Privacy policy missing or inaccurate",
            "description": (
                "The published privacy policy does not accurately reflect actual "
                "data practices, or no policy is published. NDPA §25 requires "
                "informed consent at the point of collection."
            ),
            "severity": Severity.HIGH,
            "likelihood": "high",
            "business_impact": (
                "Direct NDPA non-compliance; enforcement risk; customer trust."
            ),
            "areas": ["transparency", "regulatory"],
        },
        "SEC_26": {
            "title": "No documented data retention schedule",
            "description": (
                "Personal data is retained indefinitely or without a documented "
                "purpose-bound schedule, breaching NDPA §26 storage limitation."
            ),
            "severity": Severity.MEDIUM,
            "likelihood": "high",
            "business_impact": (
                "NDPA finding; growing exposure surface from over-retained data."
            ),
            "areas": ["data_lifecycle"],
        },
        "SEC_29": {
            "title": "Missing Data Processing Agreements with vendors",
            "description": (
                "Vendors processing personal data on your behalf lack signed "
                "DPAs, breaching NDPA §29."
            ),
            "severity": Severity.HIGH,
            "likelihood": "high",
            "business_impact": (
                "NDPA enforcement; uncontrolled secondary processing of customer "
                "data by vendors."
            ),
            "areas": ["third_party", "regulatory"],
        },
        "SEC_32": {
            "title": "No designated Data Protection Officer",
            "description": (
                "Where the company processes large volumes of personal data, "
                "NDPA §32 requires a designated DPO. Absence is a direct "
                "compliance gap."
            ),
            "severity": Severity.HIGH,
            "likelihood": "high",
            "business_impact": "Direct NDPA finding; weakened privacy governance.",
            "areas": ["governance", "regulatory"],
        },
        "SEC_40": {
            "title": "Breach notification readiness unclear",
            "description": (
                "Staff are not familiar with the 72-hour NDPA breach "
                "notification obligation. In an incident, the notification "
                "deadline is likely to be missed."
            ),
            "severity": Severity.HIGH,
            "likelihood": "medium",
            "business_impact": "Missed notification triggers NDPC penalties.",
            "areas": ["incident_response", "regulatory"],
        },
        "4.2": {
            "title": "CBN access management requirements not fully met",
            "description": (
                "Access management does not meet CBN §4.2 expectations for "
                "regulated financial entities, particularly around MFA, "
                "privileged access, and quarterly access reviews."
            ),
            "severity": Severity.HIGH,
            "likelihood": "medium",
            "business_impact": "CBN supervisory finding; license risk.",
            "areas": ["access_control", "regulatory"],
        },
    }

    _CONTROL_TASK_TEMPLATES: dict[str, dict[str, Any]] = {
        "CC6.1": {
            "title": "Enforce MFA for all production system access",
            "description": (
                "Roll out MFA enforcement on cloud consoles, code repositories, "
                "production databases, and admin tools. Use phishing-resistant "
                "MFA (security keys or TOTP) where possible."
            ),
            "effort": Effort.SHORT,
            "week": 2,
            "criteria": [
                "MFA enforced (not just available) on AWS/GCP/Azure root",
                "MFA enforced on GitHub/GitLab",
                "MFA enforced on database admin tools",
            ],
        },
        "CC6.2": {
            "title": "Implement same-day offboarding checklist",
            "description": (
                "Document and automate where possible the steps to revoke a "
                "departing employee's access on their last day. Track "
                "completion in the HR/IT system."
            ),
            "effort": Effort.QUICK_WIN,
            "week": 1,
            "criteria": [
                "Documented offboarding checklist",
                "Owner assigned per step",
                "Last 3 offboardings confirmed against the checklist",
            ],
        },
        "CC6.7": {
            "title": "Audit and close encryption-in-transit gaps",
            "description": (
                "Audit all internal and external endpoints. Enforce TLS 1.2+ "
                "everywhere; remove unencrypted internal service-to-service "
                "communication."
            ),
            "effort": Effort.MEDIUM,
            "week": 6,
            "criteria": [
                "All public endpoints use TLS 1.2+ (Mozilla Observatory grade A)",
                "Internal services use TLS or mTLS",
                "HSTS enabled on web properties",
            ],
        },
        "CC7.1": {
            "title": "Set up continuous vulnerability scanning",
            "description": (
                "Enable dependency scanning (Dependabot/Renovate), SAST "
                "(GitHub CodeQL or similar), and external attack surface "
                "monitoring. Establish severity-based remediation SLAs."
            ),
            "effort": Effort.SHORT,
            "week": 3,
            "criteria": [
                "Dependency scanner enabled on all repos",
                "SAST running on every PR",
                "Critical vulns assigned within 24h of detection",
            ],
        },
        "CC7.2": {
            "title": "Centralise security logging with active alerting",
            "description": (
                "Forward auth, access, and security-relevant logs to a "
                "central aggregator (CloudWatch, Datadog, BetterStack). "
                "Alert on failed logins, privilege changes, and unusual "
                "data access."
            ),
            "effort": Effort.MEDIUM,
            "week": 5,
            "criteria": [
                "Authentication logs centralised",
                "Alerts configured for at least 5 use cases",
                "On-call rotation responding to alerts",
            ],
        },
        "CC7.3": {
            "title": "Document and tabletop-test incident response plan",
            "description": (
                "Write a concise IR plan covering detection, triage, "
                "containment, notification (NDPA 72h, CBN 24h where applicable), "
                "and recovery. Run a tabletop exercise within 30 days of "
                "publication."
            ),
            "effort": Effort.MEDIUM,
            "week": 4,
            "criteria": [
                "IR plan published and acknowledged by team",
                "Tabletop exercise completed and gaps documented",
                "Communication templates ready (regulator, customers)",
            ],
        },
        "CC8.1": {
            "title": "Mandate peer code review on production branches",
            "description": (
                "Configure branch protection so all merges to main require at "
                "least one approval. Document the review checklist."
            ),
            "effort": Effort.QUICK_WIN,
            "week": 1,
            "criteria": [
                "Branch protection enforced on main",
                "Reviewer approval required",
                "Review checklist linked from contributing guide",
            ],
        },
        "CC9.2": {
            "title": "Roll out vendor due diligence questionnaire",
            "description": (
                "Build a short security questionnaire (15-25 questions) and "
                "require completion before signing with new vendors that "
                "handle personal data. Reassess critical vendors annually."
            ),
            "effort": Effort.SHORT,
            "week": 7,
            "criteria": [
                "Questionnaire template published",
                "Process for new vendors enforced",
                "Top 5 existing vendors assessed",
            ],
        },
        "CC1.4": {
            "title": "Launch annual security awareness training",
            "description": (
                "Pick a training provider (KnowBe4, Hoxhunt, or in-house). "
                "Track completion. Run quarterly phishing simulations."
            ),
            "effort": Effort.SHORT,
            "week": 8,
            "criteria": [
                "Training assigned to all staff",
                "Completion tracked",
                "First phishing simulation run with results reviewed",
            ],
        },
        "A1.2": {
            "title": "Run a backup restore test",
            "description": (
                "Pick a critical database or system and execute a full restore "
                "from backup into a non-production environment. Document the "
                "outcome and time-to-restore."
            ),
            "effort": Effort.SHORT,
            "week": 6,
            "criteria": [
                "Restore completed end-to-end",
                "RTO and RPO measured and documented",
                "Findings tracked to closure",
            ],
        },
        "SEC_24": {
            "title": "Document NDPA §24 technical and organisational measures",
            "description": (
                "Map your existing security controls to NDPA §24 expectations. "
                "Identify and close the gaps, particularly around encryption "
                "and tested resilience."
            ),
            "effort": Effort.MEDIUM,
            "week": 9,
            "criteria": [
                "§24 measures register published",
                "Gaps assigned with owners and target dates",
                "Encryption and resilience measures documented",
            ],
        },
        "SEC_25": {
            "title": "Publish or update privacy policy to reflect actual practices",
            "description": (
                "Audit current data flows. Rewrite privacy policy to cover "
                "categories of data, purposes, recipients, retention, data "
                "subject rights, and the NDPC complaint pathway."
            ),
            "effort": Effort.SHORT,
            "week": 2,
            "criteria": [
                "Privacy policy live on website",
                "Data flow inventory backing the policy",
                "Internal review by founder/DPO completed",
            ],
        },
        "SEC_26": {
            "title": "Define and enforce data retention schedule",
            "description": (
                "Document retention period per data category (e.g. customer "
                "PII 7 years post-account closure, marketing data 24 months). "
                "Implement automated deletion where feasible."
            ),
            "effort": Effort.MEDIUM,
            "week": 10,
            "criteria": [
                "Retention schedule published",
                "Deletion automated for at least one category",
                "Quarterly review on the calendar",
            ],
        },
        "SEC_29": {
            "title": "Sign DPAs with all data-handling vendors",
            "description": (
                "List every vendor that processes personal data on your "
                "behalf. Sign a DPA covering NDPA §29 requirements with each. "
                "Use a template aligned with NDPA expectations."
            ),
            "effort": Effort.SHORT,
            "week": 3,
            "criteria": [
                "Vendor list complete and classified",
                "DPA template ratified by counsel",
                "DPAs signed with top 5 vendors",
            ],
        },
        "SEC_32": {
            "title": "Designate a Data Protection Officer",
            "description": (
                "Appoint a DPO (internal or external) with NDPA expertise. "
                "Publish their contact details and brief them on current "
                "processing activities."
            ),
            "effort": Effort.QUICK_WIN,
            "week": 1,
            "criteria": [
                "DPO appointed in writing",
                "Contact published in privacy policy",
                "Initial assessment completed by DPO",
            ],
        },
        "SEC_40": {
            "title": "Build breach notification readiness",
            "description": (
                "Prepare templates and decision criteria for the NDPC 72-hour "
                "notification (and CBN 24-hour if regulated). Brief the "
                "incident response team on triggers and timelines."
            ),
            "effort": Effort.SHORT,
            "week": 4,
            "criteria": [
                "Notification templates drafted",
                "Decision tree for 'does this require notification?' published",
                "Walk-through completed in tabletop exercise",
            ],
        },
        "4.2": {
            "title": "Align access management to CBN §4.2 expectations",
            "description": (
                "Implement quarterly privileged access reviews, MFA on all "
                "access, role-based access control with documented "
                "provisioning, and elimination of shared accounts on "
                "production."
            ),
            "effort": Effort.MEDIUM,
            "week": 5,
            "criteria": [
                "Quarterly access review on the calendar",
                "No shared production accounts",
                "Privileged session logging enabled",
            ],
        },
    }

    def _generate_risks(
        self, scoring: ScoringResult, responses: dict[str, Any]
    ) -> list[Risk]:
        candidates: list[tuple[int, float, Risk]] = []
        severity_rank = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFORMATIONAL: 1,
        }

        for cs in scoring.control_scores.values():
            if cs.maturity >= 3.0:
                continue  # not a risk
            template = self._CONTROL_RISK_TEMPLATES.get(cs.code)
            if template is None:
                continue
            risk = Risk(
                id=f"R{len(candidates) + 1}",
                title=template["title"],
                description=template["description"],
                severity=template["severity"],
                likelihood=template["likelihood"],
                business_impact=template["business_impact"],
                affected_areas=template["areas"],
                framework_citations=[
                    FrameworkCitation(framework=cs.framework, control_code=cs.code)
                ],
                related_question_ids=cs.contributing_questions,
            )
            # Sort by severity first (primary), then by maturity gap (tiebreaker)
            candidates.append((severity_rank[risk.severity], 4 - cs.maturity, risk))

        # Sort by severity desc, then gap desc
        candidates.sort(key=lambda x: (-x[0], -x[1]))

        # Renumber to ensure R1 is highest priority
        risks: list[Risk] = []
        for i, (_, _, risk) in enumerate(candidates[:15], start=1):
            risks.append(risk.model_copy(update={"id": f"R{i}"}))

        # Always have at least one risk so ReportContent validates
        if not risks:
            risks.append(
                Risk(
                    id="R1",
                    title="Maintain and continuously improve current posture",
                    description=(
                        "Your current posture scores well across assessed controls. "
                        "The main risk now is regression: control quality drops as "
                        "the team grows. Establish lightweight ongoing review."
                    ),
                    severity=Severity.LOW,
                    likelihood="low",
                    business_impact=(
                        "Gradual control degradation could surface during your next audit."
                    ),
                    affected_areas=["governance"],
                )
            )

        return risks

    def _generate_roadmap(
        self, risks: list[Risk], scoring: ScoringResult
    ) -> list[RoadmapTask]:
        tasks: list[RoadmapTask] = []
        seen_codes: set[str] = set()

        # Map control_code -> risk id for cross-referencing
        code_to_risk_ids: dict[str, list[str]] = {}
        for risk in risks:
            for cite in risk.framework_citations:
                code_to_risk_ids.setdefault(cite.control_code, []).append(risk.id)

        # For each control referenced in our risks, generate a task
        for risk in risks:
            for cite in risk.framework_citations:
                if cite.control_code in seen_codes:
                    continue
                template = self._CONTROL_TASK_TEMPLATES.get(cite.control_code)
                if template is None:
                    continue
                seen_codes.add(cite.control_code)
                task = RoadmapTask(
                    id=f"T{len(tasks) + 1}",
                    title=template["title"],
                    description=template["description"],
                    severity=risk.severity,
                    effort=template["effort"],
                    week_target=template["week"],
                    addresses_risk_ids=code_to_risk_ids.get(cite.control_code, []),
                    framework_citations=[cite],
                    success_criteria=template["criteria"],
                )
                tasks.append(task)

        # Always have at least one task
        if not tasks:
            tasks.append(
                RoadmapTask(
                    id="T1",
                    title="Schedule a quarterly security review",
                    description=(
                        "Set up a recurring quarterly review of access, vendors, "
                        "and incidents. Lightweight but the foundation of "
                        "ongoing security hygiene."
                    ),
                    severity=Severity.LOW,
                    effort=Effort.QUICK_WIN,
                    week_target=1,
                    success_criteria=[
                        "Calendar invite for Q1 review created",
                        "Reviewer assigned",
                    ],
                )
            )

        # Sort by week_target asc, then by severity desc
        severity_rank = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFORMATIONAL: 1,
        }
        tasks.sort(key=lambda t: (t.week_target, -severity_rank[t.severity]))
        # Renumber
        tasks = [t.model_copy(update={"id": f"T{i}"}) for i, t in enumerate(tasks, 1)]
        return tasks

    def _generate_framework_gaps(
        self, scoring: ScoringResult
    ) -> list[FrameworkGap]:
        framework_names = {
            "soc2": "SOC 2",
            "ndpa": "Nigeria Data Protection Act",
            "cbn_cyber": "CBN Cybersecurity Framework",
            "popia": "POPIA",
            "kenya_dpa": "Kenya Data Protection Act",
            "iso27001": "ISO 27001",
            "pci_dss": "PCI DSS",
        }

        gaps: list[FrameworkGap] = []
        for fs in scoring.framework_scores.values():
            weak_controls = [
                cs.code
                for cs in scoring.control_scores.values()
                if cs.framework == fs.framework and cs.maturity < 3.0
            ]
            summary = (
                f"Current readiness: {fs.score}/100 across {fs.controls_assessed} "
                f"assessed controls (avg maturity {fs.avg_maturity:.1f}/4). "
                + (
                    f"{len(weak_controls)} controls need attention to reach audit-ready maturity."
                    if weak_controls
                    else "All assessed controls are at a credible maturity level."
                )
            )
            gaps.append(
                FrameworkGap(
                    framework=fs.framework,
                    framework_name=framework_names.get(fs.framework, fs.framework),
                    readiness_score=fs.score,
                    summary=summary,
                    top_gaps=weak_controls[:8],
                    next_steps=(
                        ["Address controls listed in the roadmap above."]
                        if weak_controls
                        else ["Maintain current controls; prepare evidence for audit."]
                    ),
                )
            )
        return gaps

    def _generate_executive_summary(
        self,
        company: Company,
        scoring: ScoringResult,
        risks: list[Risk],
        responses: dict[str, Any],
    ) -> str:
        critical_count = sum(1 for r in risks if r.severity == Severity.CRITICAL)
        high_count = sum(1 for r in risks if r.severity == Severity.HIGH)
        target_frameworks = responses.get("go.target_frameworks", [])
        timeline = responses.get("go.target_timeline", "exploring")

        framework_str = (
            ", ".join(target_frameworks).upper() if target_frameworks else "no specific target"
        )
        timeline_human = {
            "3_months": "within 3 months",
            "6_months": "within 6 months",
            "12_months": "within 12 months",
            "exploring": "on a flexible timeline",
        }.get(timeline, timeline)

        score = scoring.overall_risk_score
        if score >= 80:
            posture = "strong"
            posture_detail = "Your foundations are in good shape; the focus now is closing remaining gaps and preparing audit evidence."
        elif score >= 60:
            posture = "moderate"
            posture_detail = "Core controls are largely in place but there are meaningful gaps that would surface in a SOC 2 audit or an NDPA enforcement review."
        elif score >= 40:
            posture = "developing"
            posture_detail = "Several foundational controls are missing or inconsistent. Closing these is the single highest-leverage investment you can make in the next quarter."
        else:
            posture = "early-stage"
            posture_detail = "Most security and compliance fundamentals are not yet in place. The roadmap below sequences the critical work in priority order."

        return (
            f"{company.name} is a {company.size.value} {company.sector.value} company "
            f"in {company.country} pursuing {framework_str} compliance {timeline_human}. "
            f"Your current security and compliance posture is {posture} "
            f"(overall score {score}/100). {posture_detail}\n\n"
            f"This report identifies {len(risks)} risks "
            f"({critical_count} critical, {high_count} high) and provides a "
            f"13-week roadmap addressing them in order of impact. The roadmap "
            f"sequences quick wins in weeks 1-2 (ideally completed before your "
            f"next investor or customer review), foundational controls in "
            f"weeks 3-6, and process maturity in weeks 7-13.\n\n"
            f"Highest priorities right now: address the {high_count + critical_count} "
            f"high or critical risks. Most are well-understood control gaps with "
            f"clear remediation paths — none requires specialist expertise to begin."
        )


# ----- Factory ----------------------------------------------------------------


def get_advisor_engine() -> AdvisorEngine:
    """Return the configured advisor engine.

    Honours USE_MOCK_AI feature flag — same pattern as SimCheck's
    USE_MOCK_TELCO mock/live seam.
    """
    settings = get_settings()
    if settings.USE_MOCK_AI or not settings.ANTHROPIC_API_KEY:
        return MockAdvisor()
    return ClaudeAdvisor()
