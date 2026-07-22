"""Questionnaire v1.0.0 — initial intake for CyberCapSec Advisory.

Designed for African startups and SMEs targeting SOC 2 + NDPA + sector-specific
compliance. Approximately 40 questions across 8 sections, ~15-20 minutes to
complete.

Question IDs use a stable prefix per section (e.g. "co.*" for company,
"da.*" for data) so they remain stable across version edits.
"""
from app.services.questionnaire.schema import (
    ControlRef,
    Option,
    Question,
    QuestionnaireVersion,
    QuestionType,
    ScoringRule,
    Section,
)


def _yes_score(yes: int = 4, no: int = 0, partial: int | None = None) -> ScoringRule:
    """Helper for boolean / yes-no-partial questions."""
    response_score = {"true": yes, "false": no}
    if partial is not None:
        response_score["partial"] = partial
    return ScoringRule(response_score=response_score)


# --- Section 1: Company profile (mostly informational, light scoring) ----------

SECTION_COMPANY = Section(
    id="company",
    title="Company profile",
    description="Tell us about your company. This shapes which regulations apply to you.",
    questions=[
        Question(
            id="co.primary_country",
            text="Where is your company primarily registered and operating?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="NG", label="Nigeria"),
                Option(value="KE", label="Kenya"),
                Option(value="ZA", label="South Africa"),
                Option(value="GH", label="Ghana"),
                Option(value="EG", label="Egypt"),
                Option(value="other_africa", label="Other African country"),
                Option(value="outside_africa", label="Outside Africa"),
            ],
        ),
        Question(
            id="co.serves_eu_users",
            text="Do you serve users or process data of EU residents?",
            help_text="If yes, GDPR likely applies in addition to local regulations.",
            type=QuestionType.BOOLEAN,
        ),
        Question(
            id="co.has_us_customers",
            text="Do you have enterprise US customers or plan to within 12 months?",
            help_text="US enterprise procurement typically requires SOC 2.",
            type=QuestionType.BOOLEAN,
        ),
        Question(
            id="co.team_size",
            text="How many employees and contractors work at your company?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="1", label="Just me"),
                Option(value="2-10", label="2-10"),
                Option(value="11-50", label="11-50"),
                Option(value="51-200", label="51-200"),
                Option(value="200+", label="200+"),
            ],
        ),
        Question(
            id="co.industry",
            text="Which industry best describes your business?",
            required=False,
            help_text=(
                "We use this to tailor the recommended frameworks, policy "
                "templates, and report language (e.g. fintechs see PCI DSS "
                "and CBN guidance prioritised; healthtechs see HIPAA-style "
                "PHI handling)."
            ),
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="fintech", label="Fintech / Payments / Lending"),
                Option(value="insurtech", label="Insurtech"),
                Option(value="healthtech", label="Healthtech / Digital health"),
                Option(value="edtech", label="Edtech"),
                Option(value="ecommerce", label="E-commerce / Retail"),
                Option(value="logistics", label="Logistics / Mobility"),
                Option(value="agritech", label="Agritech"),
                Option(value="proptech", label="Proptech / Real estate"),
                Option(
                    value="saas",
                    label="B2B SaaS (horizontal — CRM, HR, dev tools, etc.)",
                ),
                Option(value="other", label="Other / not listed"),
            ],
        ),
        Question(
            id="co.business_model",
            text="What is your primary business model?",
            required=False,
            help_text=(
                "Affects which controls we emphasise — e.g. B2C consumer apps "
                "get heavier privacy/breach-notification weighting, B2B SaaS "
                "gets heavier subprocessor and DPA emphasis."
            ),
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="b2c", label="B2C — direct to consumers"),
                Option(value="b2b", label="B2B — selling to businesses"),
                Option(value="b2b2c", label="B2B2C — embedded in partners' products"),
                Option(value="marketplace", label="Marketplace — connecting two sides"),
                Option(value="gov", label="Government / public sector"),
            ],
        ),
        Question(
            id="co.regulated_activity",
            required=False,
            text=(
                "Do you hold (or are you applying for) a financial-services "
                "licence such as PSP, MMO, MFB, PSSP, BNPL, lending, or "
                "insurance underwriting?"
            ),
            help_text=(
                "Regulated entities have stricter cybersecurity reporting "
                "obligations (CBN 24-hour rule, NAICOM, CMA, FSCA, etc.)."
            ),
            type=QuestionType.BOOLEAN,
        ),
        Question(
            id="co.handles_card_data",
            required=False,
            text=(
                "Do you store, process, or transmit payment card data (PAN, "
                "CVV) directly — even if only for a portion of your flows?"
            ),
            help_text=(
                "If yes, PCI DSS applies. If you fully outsource card data to "
                "a PCI-certified processor (Flutterwave, Stripe, or similar), "
                "answer no — your scope is reduced to SAQ-A."
            ),
            type=QuestionType.BOOLEAN,
        ),
    ],
)


# --- Section 2: Data handling --------------------------------------------------

SECTION_DATA = Section(
    id="data",
    title="Data you handle",
    description="What kinds of data does your company collect, process, or store?",
    questions=[
        Question(
            id="da.data_types",
            text="Which types of personal or sensitive data do you handle? (Select all that apply)",
            type=QuestionType.MULTI_SELECT,
            options=[
                Option(value="names_emails", label="Names and email addresses"),
                Option(value="phone_numbers", label="Phone numbers"),
                Option(value="financial", label="Financial data (account numbers, transactions)"),
                Option(value="payment_cards", label="Payment card data (PAN, CVV)"),
                Option(value="bvn_nin", label="BVN, NIN, or other government IDs"),
                Option(value="health", label="Health or medical records"),
                Option(value="biometric", label="Biometric data (fingerprints, face)"),
                Option(value="location", label="Real-time location data"),
                Option(value="children", label="Data about children under 18"),
                Option(value="none_sensitive", label="None of the above"),
            ],
            control_refs=[
                ControlRef(framework="ndpa", code="SEC_24"),
                ControlRef(framework="soc2", code="C1.1"),
            ],
        ),
        Question(
            id="da.data_volume",
            text="Approximately how many individual data subjects' records do you hold?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="lt_1k", label="Fewer than 1,000"),
                Option(value="1k_10k", label="1,000 to 10,000"),
                Option(value="10k_100k", label="10,000 to 100,000"),
                Option(value="100k_1m", label="100,000 to 1 million"),
                Option(value="gt_1m", label="More than 1 million"),
            ],
        ),
        Question(
            id="da.data_retention_policy",
            text="Do you have a documented data retention and deletion policy?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="yes_enforced", label="Yes, documented and automatically enforced"),
                Option(value="yes_manual", label="Yes, documented but manually enforced"),
                Option(value="informal", label="Informal — we delete when asked"),
                Option(value="no", label="No policy"),
            ],
            scoring=ScoringRule(
                response_score={"yes_enforced": 4, "yes_manual": 2, "informal": 1, "no": 0}
            ),
            control_refs=[
                ControlRef(framework="ndpa", code="SEC_26"),
                ControlRef(framework="soc2", code="C1.2"),
            ],
        ),
        Question(
            id="da.encryption_at_rest",
            text="Is sensitive data encrypted at rest (in databases, backups, file storage)?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="all", label="Yes, all sensitive data"),
                Option(value="some", label="Some, but not consistently"),
                Option(value="no", label="No"),
                Option(value="unknown", label="I'm not sure"),
            ],
            scoring=ScoringRule(response_score={"all": 4, "some": 2, "no": 0, "unknown": 0}),
            control_refs=[
                ControlRef(framework="soc2", code="CC6.1"),
                ControlRef(framework="ndpa", code="SEC_24"),
                ControlRef(framework="cbn_cyber", code="4.5"),
            ],
        ),
        Question(
            id="da.encryption_in_transit",
            text="Is all data encrypted in transit (HTTPS/TLS for web traffic, TLS for internal services)?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="all", label="Yes, everywhere including internal services"),
                Option(value="external_only", label="External web traffic only"),
                Option(value="partial", label="Partial — some endpoints unencrypted"),
                Option(value="no", label="No"),
            ],
            scoring=ScoringRule(
                response_score={"all": 4, "external_only": 3, "partial": 1, "no": 0}
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC6.7"),
                ControlRef(framework="ndpa", code="SEC_24"),
            ],
        ),
    ],
)


# --- Section 3: Access management ----------------------------------------------

SECTION_ACCESS = Section(
    id="access",
    title="Access management",
    description="How do you control who has access to systems and data?",
    questions=[
        Question(
            id="ac.mfa_employees",
            text="Is multi-factor authentication (MFA) required for all employees on critical systems?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="all_systems", label="Yes, on all systems"),
                Option(value="critical_only", label="Yes, on critical systems only"),
                Option(value="optional", label="Available but not enforced"),
                Option(value="no", label="No"),
            ],
            scoring=ScoringRule(
                response_score={"all_systems": 4, "critical_only": 3, "optional": 1, "no": 0}
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC6.1"),
                ControlRef(framework="cbn_cyber", code="4.2"),
            ],
        ),
        Question(
            id="ac.access_reviews",
            text="How often do you review who has access to systems and data?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="quarterly", label="Quarterly or more frequently"),
                Option(value="annually", label="Annually"),
                Option(value="ad_hoc", label="Only when something changes"),
                Option(value="never", label="We don't review access"),
            ],
            scoring=ScoringRule(
                response_score={"quarterly": 4, "annually": 2, "ad_hoc": 1, "never": 0}
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC6.2"),
                ControlRef(framework="cbn_cyber", code="4.2"),
            ],
        ),
        Question(
            id="ac.offboarding",
            text="When an employee or contractor leaves, how quickly is their access revoked?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="same_day", label="Same day, automated"),
                Option(value="same_day_manual", label="Same day, manual checklist"),
                Option(value="within_week", label="Within a week"),
                Option(value="ad_hoc", label="When we remember"),
            ],
            scoring=ScoringRule(
                response_score={
                    "same_day": 4,
                    "same_day_manual": 3,
                    "within_week": 1,
                    "ad_hoc": 0,
                }
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC6.3"),
                ControlRef(framework="cbn_cyber", code="4.2"),
            ],
        ),
        Question(
            id="ac.privileged_access",
            text="Is access to production systems and admin consoles restricted and logged?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="yes_full", label="Yes, restricted with logged access"),
                Option(value="restricted_no_logs", label="Restricted but not logged"),
                Option(value="logged_not_restricted", label="Logged but not properly restricted"),
                Option(value="no", label="No formal control"),
            ],
            scoring=ScoringRule(
                response_score={
                    "yes_full": 4,
                    "restricted_no_logs": 2,
                    "logged_not_restricted": 2,
                    "no": 0,
                }
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC6.1"),
                ControlRef(framework="ndpa", code="SEC_24"),
            ],
        ),
    ],
)


# --- Section 4: Tech stack & infrastructure ------------------------------------

SECTION_TECH = Section(
    id="tech",
    title="Tech stack and infrastructure",
    description="Your infrastructure shapes which controls and integrations are relevant.",
    questions=[
        Question(
            id="te.cloud_providers",
            text="Which cloud providers do you use? (Select all that apply)",
            type=QuestionType.MULTI_SELECT,
            options=[
                Option(value="aws", label="AWS"),
                Option(value="gcp", label="Google Cloud"),
                Option(value="azure", label="Microsoft Azure"),
                Option(value="digitalocean", label="DigitalOcean"),
                Option(value="other_cloud", label="Other cloud provider"),
                Option(value="self_hosted", label="Self-hosted / on-premise"),
                Option(value="none", label="No cloud infrastructure yet"),
            ],
        ),
        Question(
            id="te.code_repository",
            text="Where do you host your source code?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="github", label="GitHub"),
                Option(value="gitlab", label="GitLab"),
                Option(value="bitbucket", label="Bitbucket"),
                Option(value="self_hosted_git", label="Self-hosted Git"),
                Option(value="none", label="No version control yet"),
            ],
        ),
        Question(
            id="te.code_review",
            text="Are code changes reviewed before being deployed to production?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="required_all", label="Yes, mandatory peer review for all changes"),
                Option(value="required_critical", label="Required for critical changes only"),
                Option(value="encouraged", label="Encouraged but not enforced"),
                Option(value="no", label="No formal code review"),
            ],
            scoring=ScoringRule(
                response_score={
                    "required_all": 4,
                    "required_critical": 2,
                    "encouraged": 1,
                    "no": 0,
                }
            ),
            control_refs=[ControlRef(framework="soc2", code="CC8.1")],
        ),
        Question(
            id="te.backups",
            text="Are production data and systems backed up regularly with tested restore procedures?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="auto_tested", label="Automated backups with regular restore tests"),
                Option(value="auto_untested", label="Automated backups, never tested"),
                Option(value="manual", label="Manual or ad-hoc backups"),
                Option(value="no", label="No backups"),
            ],
            scoring=ScoringRule(
                response_score={"auto_tested": 4, "auto_untested": 2, "manual": 1, "no": 0}
            ),
            control_refs=[
                ControlRef(framework="soc2", code="A1.2"),
                ControlRef(framework="cbn_cyber", code="4.6"),
            ],
        ),
        Question(
            id="te.vulnerability_scanning",
            text="Do you scan your code and infrastructure for vulnerabilities?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="continuous", label="Continuous scanning (SAST, DAST, dependency)"),
                Option(value="periodic", label="Periodic scans (monthly or quarterly)"),
                Option(value="ad_hoc", label="Ad-hoc / before major releases"),
                Option(value="no", label="No scanning"),
            ],
            scoring=ScoringRule(
                response_score={"continuous": 4, "periodic": 3, "ad_hoc": 1, "no": 0}
            ),
            control_refs=[ControlRef(framework="soc2", code="CC7.1")],
        ),
        Question(
            id="te.logging_monitoring",
            text="Do you collect and review security-relevant logs (access, auth, errors)?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="centralized_alerting", label="Centralized with active alerting"),
                Option(value="centralized_no_alerts", label="Centralized but reviewed only on incident"),
                Option(value="scattered", label="Logs exist but scattered across services"),
                Option(value="no", label="No log collection"),
            ],
            scoring=ScoringRule(
                response_score={
                    "centralized_alerting": 4,
                    "centralized_no_alerts": 2,
                    "scattered": 1,
                    "no": 0,
                }
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC7.2"),
                ControlRef(framework="cbn_cyber", code="4.7"),
            ],
        ),
    ],
)


# --- Section 5: Third parties --------------------------------------------------

SECTION_VENDORS = Section(
    id="vendors",
    title="Third parties and vendors",
    description="Vendors with access to your systems or data are part of your security perimeter.",
    questions=[
        Question(
            id="ve.vendor_count",
            text="Approximately how many third-party vendors have access to your systems or data?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="0", label="None"),
                Option(value="1-5", label="1-5"),
                Option(value="6-20", label="6-20"),
                Option(value="20+", label="More than 20"),
            ],
        ),
        Question(
            id="ve.vendor_review",
            text="Do you assess the security of vendors before signing contracts?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="formal_dd", label="Yes, formal due diligence with security questionnaire"),
                Option(value="informal", label="Informally — we check what we can"),
                Option(value="critical_only", label="Only for vendors handling sensitive data"),
                Option(value="no", label="No vendor review"),
            ],
            scoring=ScoringRule(
                response_score={"formal_dd": 4, "critical_only": 2, "informal": 1, "no": 0}
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC9.2"),
                ControlRef(framework="ndpa", code="SEC_29"),
            ],
        ),
        Question(
            id="ve.dpa_signed",
            text="Do you have signed Data Processing Agreements (DPAs) with vendors who handle personal data?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="all", label="Yes, with all relevant vendors"),
                Option(value="some", label="With some vendors"),
                Option(value="none", label="No DPAs in place"),
                Option(value="unsure", label="Not sure"),
            ],
            scoring=ScoringRule(
                response_score={"all": 4, "some": 2, "none": 0, "unsure": 0}
            ),
            control_refs=[ControlRef(framework="ndpa", code="SEC_29")],
        ),
    ],
)


# --- Section 6: Policies & people ----------------------------------------------

SECTION_POLICIES = Section(
    id="policies",
    title="Policies and people",
    description="Documented policies and security training of staff.",
    questions=[
        Question(
            id="po.security_policy",
            text="Do you have a documented information security policy?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="yes_reviewed", label="Yes, reviewed annually and acknowledged by staff"),
                Option(value="yes_static", label="Yes, but rarely updated"),
                Option(value="draft", label="Draft / informal"),
                Option(value="no", label="No"),
            ],
            scoring=ScoringRule(
                response_score={"yes_reviewed": 4, "yes_static": 2, "draft": 1, "no": 0}
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC1.1"),
                ControlRef(framework="iso27001", code="A.5.1"),
            ],
        ),
        Question(
            id="po.privacy_policy_published",
            text="Do you have a published privacy policy that reflects how you actually handle data?",
            type=QuestionType.BOOLEAN,
            scoring=_yes_score(),
            control_refs=[
                ControlRef(framework="ndpa", code="SEC_25"),
                ControlRef(framework="popia", code="SEC_18"),
            ],
        ),
        Question(
            id="po.security_training",
            text="Do employees complete security awareness training?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="annual_tracked", label="Annually, completion tracked"),
                Option(value="onboarding_only", label="Once at onboarding"),
                Option(value="ad_hoc", label="Ad-hoc / informal"),
                Option(value="no", label="No formal training"),
            ],
            scoring=ScoringRule(
                response_score={
                    "annual_tracked": 4,
                    "onboarding_only": 2,
                    "ad_hoc": 1,
                    "no": 0,
                }
            ),
            control_refs=[ControlRef(framework="soc2", code="CC1.4")],
        ),
        Question(
            id="po.background_checks",
            text="Do you perform background checks on new hires (where legally permitted)?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="all", label="All hires"),
                Option(value="sensitive_roles", label="Roles with access to sensitive data"),
                Option(value="no", label="No background checks"),
            ],
            scoring=ScoringRule(
                response_score={"all": 4, "sensitive_roles": 3, "no": 0}
            ),
            control_refs=[ControlRef(framework="soc2", code="CC1.4")],
        ),
        Question(
            id="po.dpo_appointed",
            text="Have you appointed a Data Protection Officer (DPO) or data protection contact?",
            help_text="NDPA requires designated DPOs for certain processing activities.",
            type=QuestionType.BOOLEAN,
            scoring=_yes_score(),
            control_refs=[ControlRef(framework="ndpa", code="SEC_32")],
        ),
    ],
)


# --- Section 7: Incident response ----------------------------------------------

SECTION_INCIDENTS = Section(
    id="incidents",
    title="Incident response",
    description="How prepared are you to detect, respond to, and recover from a security incident?",
    questions=[
        Question(
            id="in.ir_plan",
            text="Do you have a documented incident response plan?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="yes_tested", label="Yes, tested at least annually"),
                Option(value="yes_untested", label="Yes, but not tested"),
                Option(value="informal", label="Informal — we'd figure it out"),
                Option(value="no", label="No plan"),
            ],
            scoring=ScoringRule(
                response_score={"yes_tested": 4, "yes_untested": 2, "informal": 1, "no": 0}
            ),
            control_refs=[
                ControlRef(framework="soc2", code="CC7.3"),
                ControlRef(framework="cbn_cyber", code="4.8"),
            ],
        ),
        Question(
            id="in.breach_in_last_year",
            text="Have you experienced a security incident or data breach in the past 12 months?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="no", label="No"),
                Option(value="minor", label="Yes, a minor incident (no data exposed)"),
                Option(value="data_exposed", label="Yes, data was exposed"),
                Option(value="unsure", label="I'm not sure"),
            ],
        ),
        Question(
            id="in.breach_notification_aware",
            text="Are you familiar with your jurisdiction's breach notification requirements?",
            help_text="NDPA requires notification to NDPC within 72 hours for certain breaches.",
            type=QuestionType.BOOLEAN,
            scoring=_yes_score(),
            control_refs=[ControlRef(framework="ndpa", code="SEC_40")],
        ),
    ],
)


# --- Section 8: Compliance goals -----------------------------------------------

SECTION_GOALS = Section(
    id="goals",
    title="Your compliance goals",
    description="Tells us where to focus the roadmap.",
    questions=[
        Question(
            id="go.target_frameworks",
            text="Which compliance frameworks are you targeting? (Select all that apply)",
            type=QuestionType.MULTI_SELECT,
            options=[
                Option(value="soc2", label="SOC 2"),
                Option(value="iso27001", label="ISO 27001"),
                Option(value="ndpa", label="NDPA (Nigeria)"),
                Option(value="popia", label="POPIA (South Africa)"),
                Option(value="kenya_dpa", label="Kenya Data Protection Act"),
                Option(value="cbn_cyber", label="CBN Cybersecurity Framework"),
                Option(value="pci_dss", label="PCI DSS"),
                Option(value="gdpr", label="GDPR"),
                Option(value="exploring", label="Exploring — not sure yet"),
            ],
        ),
        Question(
            id="go.target_timeline",
            text="When do you want to achieve your primary compliance goal?",
            type=QuestionType.SINGLE_SELECT,
            options=[
                Option(value="3_months", label="Within 3 months"),
                Option(value="6_months", label="Within 6 months"),
                Option(value="12_months", label="Within 12 months"),
                Option(value="exploring", label="Just exploring for now"),
            ],
        ),
        Question(
            id="go.driver",
            text="What's driving this compliance work? (Select all that apply)",
            type=QuestionType.MULTI_SELECT,
            options=[
                Option(value="customer_requirement", label="Customer is requiring it"),
                Option(value="investor_dd", label="Investor due diligence"),
                Option(value="regulatory", label="Regulatory requirement"),
                Option(value="competitive", label="Competitive advantage"),
                Option(value="internal_risk", label="Internal risk management"),
                Option(value="incident", label="Recent incident or near-miss"),
            ],
        ),
    ],
)


# --- The full questionnaire ----------------------------------------------------

QUESTIONNAIRE_V1 = QuestionnaireVersion(
    version="1.0.0",
    title="CyberCapSec Advisory — Initial Security & Compliance Assessment",
    description=(
        "A 15-20 minute assessment that produces a tailored security and "
        "compliance roadmap for your company. Your answers feed an AI-generated "
        "risk register, framework gap analysis, and 90-day action plan."
    ),
    sections=[
        SECTION_COMPANY,
        SECTION_DATA,
        SECTION_ACCESS,
        SECTION_TECH,
        SECTION_VENDORS,
        SECTION_POLICIES,
        SECTION_INCIDENTS,
        SECTION_GOALS,
    ],
)


# --- Registry ------------------------------------------------------------------

QUESTIONNAIRE_VERSIONS: dict[str, QuestionnaireVersion] = {
    "1.0.0": QUESTIONNAIRE_V1,
}
LATEST_VERSION = "1.0.0"


def get_questionnaire(version: str | None = None) -> QuestionnaireVersion:
    """Return a questionnaire by version, defaulting to latest."""
    return QUESTIONNAIRE_VERSIONS[version or LATEST_VERSION]
