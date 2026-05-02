"""Lightweight knowledge retrieval for the AI advisor.

The AI doesn't get to make up regulatory citations. We retrieve relevant
control descriptions and regulatory excerpts from a curated knowledge base
and inject them into the prompt. The model paraphrases these but cannot
invent novel facts.

For v1, the knowledge base is bundled as Python modules. As it grows past
~100 entries we'll move to pgvector with semantic search behind the same
`KnowledgeRetriever` interface.

Design: each entry is a `KnowledgeSnippet` with:
  - id (stable, citable)
  - framework_codes (which frameworks it relates to)
  - tags (keywords for filtering)
  - content (the prose to inject into prompts)

Session 6 will seed the real knowledge base with full NDPA text, CBN
framework excerpts, SOC 2 TSC descriptions, etc. Session 3 ships a small
seed sufficient to make the AI advisor functional.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeSnippet:
    id: str  # e.g. "ndpa.sec24"
    title: str
    content: str
    framework_codes: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)
    source: str | None = None  # citable source URL or document reference


# ----- v1 seed corpus ---------------------------------------------------------
# Small but covers the highest-priority controls/regulations for the African
# fintech wedge. Session 6 expands this materially.

_SEED_SNIPPETS: list[KnowledgeSnippet] = [
    # --- NDPA (Nigeria Data Protection Act 2023) ------------------------------
    KnowledgeSnippet(
        id="ndpa.sec24.security_of_processing",
        title="NDPA Section 24 — Security of processing",
        content=(
            "Data controllers and processors must implement appropriate "
            "technical and organisational measures to ensure a level of "
            "security appropriate to the risk. This explicitly includes: "
            "pseudonymisation and encryption of personal data; the ability to "
            "ensure ongoing confidentiality, integrity, availability and "
            "resilience of processing systems; the ability to restore "
            "availability and access in a timely manner after a physical or "
            "technical incident; and a regular process for testing the "
            "effectiveness of measures. Companies must take into account "
            "state of the art, costs of implementation, and the nature, "
            "scope, context and purposes of processing."
        ),
        framework_codes=frozenset({"ndpa"}),
        tags=frozenset({"security", "encryption", "controls", "incident_response"}),
        source="NDPA 2023 §24",
    ),
    KnowledgeSnippet(
        id="ndpa.sec25.transparency",
        title="NDPA Section 25 — Lawful basis and transparency",
        content=(
            "Personal data must be processed on a lawful basis and the data "
            "subject must be informed at point of collection of the identity "
            "of the controller, the purposes of processing, the categories of "
            "data, recipients, retention period, and the data subject's "
            "rights including access, rectification, erasure, and lodging "
            "complaints with the Nigeria Data Protection Commission (NDPC). "
            "A published privacy policy that accurately reflects actual data "
            "practices is the core compliance artefact for this section."
        ),
        framework_codes=frozenset({"ndpa"}),
        tags=frozenset({"privacy_policy", "transparency", "notice"}),
        source="NDPA 2023 §25",
    ),
    KnowledgeSnippet(
        id="ndpa.sec26.retention",
        title="NDPA Section 26 — Storage limitation",
        content=(
            "Personal data must be kept in a form that permits identification "
            "of data subjects for no longer than is necessary for the purposes "
            "for which the data is processed. Companies must have documented "
            "retention schedules, with data deleted, anonymised, or archived "
            "with restricted access at the end of the retention period. "
            "Indefinite retention without a defined purpose is prohibited."
        ),
        framework_codes=frozenset({"ndpa"}),
        tags=frozenset({"retention", "deletion", "data_lifecycle"}),
        source="NDPA 2023 §26",
    ),
    KnowledgeSnippet(
        id="ndpa.sec29.processors",
        title="NDPA Section 29 — Data processor obligations",
        content=(
            "Where processing is carried out on behalf of a controller, the "
            "controller must use only processors that provide sufficient "
            "guarantees of appropriate technical and organisational measures. "
            "Processing by a processor must be governed by a binding written "
            "contract (a Data Processing Agreement) covering the subject "
            "matter, duration, nature and purposes of processing, types of "
            "data, categories of data subjects, and the obligations of the "
            "processor. Sub-processors require the controller's prior "
            "written authorisation."
        ),
        framework_codes=frozenset({"ndpa"}),
        tags=frozenset({"vendors", "third_party", "dpa", "contracts"}),
        source="NDPA 2023 §29",
    ),
    KnowledgeSnippet(
        id="ndpa.sec32.dpo",
        title="NDPA Section 32 — Data Protection Officer",
        content=(
            "A data controller or processor must designate a Data Protection "
            "Officer (DPO) where its core activities involve regular and "
            "systematic monitoring of data subjects on a large scale, or "
            "large-scale processing of sensitive personal data. The DPO "
            "advises the organisation on its obligations, monitors "
            "compliance, cooperates with the NDPC, and acts as a contact "
            "point for data subjects. The DPO must have expert knowledge of "
            "data protection law and operate independently."
        ),
        framework_codes=frozenset({"ndpa"}),
        tags=frozenset({"dpo", "governance"}),
        source="NDPA 2023 §32",
    ),
    KnowledgeSnippet(
        id="ndpa.sec40.breach",
        title="NDPA Section 40 — Breach notification",
        content=(
            "When a personal data breach is likely to result in a risk to the "
            "rights and freedoms of natural persons, the controller must "
            "notify the Nigeria Data Protection Commission within 72 hours "
            "of becoming aware of it. The notification must describe the "
            "nature of the breach, categories and approximate number of data "
            "subjects affected, likely consequences, and measures taken or "
            "proposed. Where the risk is high, affected data subjects must "
            "also be informed without undue delay."
        ),
        framework_codes=frozenset({"ndpa"}),
        tags=frozenset({"breach", "incident_response", "notification"}),
        source="NDPA 2023 §40",
    ),
    # --- SOC 2 Trust Services Criteria ----------------------------------------
    KnowledgeSnippet(
        id="soc2.cc6.1.logical_access",
        title="SOC 2 CC6.1 — Logical and physical access controls",
        content=(
            "The entity implements logical access security software, "
            "infrastructure, and architectures over protected information "
            "assets to protect them from security events. This includes "
            "identifying users, restricting access based on role and least "
            "privilege, encrypting data at rest and in transit, controlling "
            "access points, and securing credentials. Multi-factor "
            "authentication for privileged users is the de facto baseline "
            "expectation for SOC 2 Type II audits."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"access_control", "mfa", "encryption", "least_privilege"}),
        source="AICPA TSC 2017 (rev. 2022) CC6.1",
    ),
    KnowledgeSnippet(
        id="soc2.cc6.2.access_provisioning",
        title="SOC 2 CC6.2 — Access provisioning and removal",
        content=(
            "The entity authorises, provisions, modifies, and removes "
            "internal and external access based on role and need. Periodic "
            "access reviews (typically quarterly) confirm current access is "
            "still appropriate. Critical: when an employee or contractor "
            "leaves, all access must be revoked promptly — auditors look "
            "for documented same-day or next-day offboarding processes."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"access_control", "offboarding", "access_review"}),
        source="AICPA TSC 2017 (rev. 2022) CC6.2",
    ),
    KnowledgeSnippet(
        id="soc2.cc6.7.transmission_encryption",
        title="SOC 2 CC6.7 — Transmission of information",
        content=(
            "The entity restricts the transmission, movement, and removal of "
            "information to authorised internal and external users and "
            "processes, and protects it during transmission. TLS 1.2 or "
            "higher for all external traffic is the baseline; internal "
            "service-to-service encryption is increasingly expected."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"encryption", "transmission", "tls"}),
        source="AICPA TSC 2017 (rev. 2022) CC6.7",
    ),
    KnowledgeSnippet(
        id="soc2.cc7.1.vulnerability_mgmt",
        title="SOC 2 CC7.1 — Vulnerability management",
        content=(
            "The entity uses detection and monitoring procedures to identify "
            "changes that could introduce vulnerabilities. This requires "
            "continuous or scheduled vulnerability scanning of code "
            "(SAST/SCA), running infrastructure (DAST or external scans), "
            "and dependencies. Findings must be triaged with documented "
            "SLAs based on severity."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"vulnerability", "scanning", "monitoring"}),
        source="AICPA TSC 2017 (rev. 2022) CC7.1",
    ),
    KnowledgeSnippet(
        id="soc2.cc7.2.monitoring",
        title="SOC 2 CC7.2 — Anomalies and events",
        content=(
            "The entity monitors system components and the operation of "
            "those components for anomalies indicative of malicious acts, "
            "natural disasters, and errors affecting the entity's ability "
            "to meet its objectives. Centralised logging with active "
            "alerting on security-relevant events (failed auth, privilege "
            "escalation, anomalous traffic) is the expected control."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"logging", "monitoring", "siem", "alerts"}),
        source="AICPA TSC 2017 (rev. 2022) CC7.2",
    ),
    KnowledgeSnippet(
        id="soc2.cc7.3.incident_response",
        title="SOC 2 CC7.3 — Incident response",
        content=(
            "The entity evaluates security events to determine whether they "
            "could or have resulted in a failure of the entity to meet its "
            "objectives, and if so, takes actions to prevent or address "
            "such failures. A documented incident response plan, tested "
            "at least annually via tabletop exercises, is the expected "
            "evidence."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"incident_response", "ir_plan", "tabletop"}),
        source="AICPA TSC 2017 (rev. 2022) CC7.3",
    ),
    KnowledgeSnippet(
        id="soc2.cc1.4.training",
        title="SOC 2 CC1.4 — Personnel security",
        content=(
            "The entity demonstrates a commitment to attract, develop, and "
            "retain competent individuals in alignment with its objectives. "
            "Background checks (where legally permitted) before hire, "
            "documented job descriptions, and security awareness training "
            "completed annually with tracked completion are the typical "
            "evidence requirements."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"hr", "training", "background_checks", "awareness"}),
        source="AICPA TSC 2017 (rev. 2022) CC1.4",
    ),
    KnowledgeSnippet(
        id="soc2.cc8.1.change_mgmt",
        title="SOC 2 CC8.1 — Change management",
        content=(
            "The entity authorises, designs, develops, configures, "
            "documents, tests, approves, and implements changes to "
            "infrastructure, data, software, and procedures. Mandatory "
            "peer code review before merging to main, automated testing "
            "in CI, and change approval records (e.g. PRs with reviewer "
            "sign-off) are the de facto expected controls."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"change_management", "code_review", "ci_cd"}),
        source="AICPA TSC 2017 (rev. 2022) CC8.1",
    ),
    KnowledgeSnippet(
        id="soc2.cc9.2.vendor_mgmt",
        title="SOC 2 CC9.2 — Vendor and business partner management",
        content=(
            "The entity assesses and manages risks associated with vendors "
            "and business partners. This requires formal vendor due "
            "diligence (security questionnaires, review of vendor SOC 2 "
            "or similar reports), contracts with appropriate security "
            "obligations, and periodic reassessment based on vendor "
            "criticality."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"vendors", "third_party", "due_diligence"}),
        source="AICPA TSC 2017 (rev. 2022) CC9.2",
    ),
    KnowledgeSnippet(
        id="soc2.a1.2.backup",
        title="SOC 2 A1.2 — Recovery and backup",
        content=(
            "The entity authorises, designs, develops or acquires, "
            "implements, operates, approves, maintains, and monitors "
            "environmental protections, software, data backup processes, "
            "and recovery infrastructure. Automated backups with "
            "documented restore tests (at minimum annually, ideally "
            "quarterly) are standard expectations."
        ),
        framework_codes=frozenset({"soc2"}),
        tags=frozenset({"backup", "recovery", "availability"}),
        source="AICPA TSC 2017 (rev. 2022) A1.2",
    ),
    # --- CBN Risk-Based Cybersecurity Framework -------------------------------
    KnowledgeSnippet(
        id="cbn.4.2.access",
        title="CBN Cybersecurity Framework §4.2 — Access management",
        content=(
            "Banks and Other Financial Institutions (OFIs) must enforce "
            "strict access management including unique user IDs, MFA for "
            "privileged and remote access, role-based access control, "
            "documented access provisioning workflows, and quarterly "
            "access reviews. Privileged session activity must be logged "
            "and reviewed. Generic shared accounts on production systems "
            "are explicitly prohibited."
        ),
        framework_codes=frozenset({"cbn_cyber"}),
        tags=frozenset({"access_control", "mfa", "fintech", "banking"}),
        source="CBN Risk-Based Cybersecurity Framework §4.2",
    ),
    KnowledgeSnippet(
        id="cbn.4.5.data_protection",
        title="CBN Cybersecurity Framework §4.5 — Data protection",
        content=(
            "Sensitive data including customer financial information, "
            "authentication credentials, and PII must be encrypted at "
            "rest and in transit using approved cryptographic standards. "
            "Key management must follow documented procedures. Data must "
            "be classified, with handling rules per classification level."
        ),
        framework_codes=frozenset({"cbn_cyber"}),
        tags=frozenset({"encryption", "fintech", "data_classification"}),
        source="CBN Risk-Based Cybersecurity Framework §4.5",
    ),
    KnowledgeSnippet(
        id="cbn.4.7.monitoring",
        title="CBN Cybersecurity Framework §4.7 — Security monitoring",
        content=(
            "OFIs must implement 24/7 security monitoring with documented "
            "use cases for detecting fraud, unauthorised access, and "
            "anomalous transactions. Logs must be retained for at least "
            "90 days hot and 12 months in archive. Critical events must "
            "trigger alerts to a designated response team."
        ),
        framework_codes=frozenset({"cbn_cyber"}),
        tags=frozenset({"monitoring", "logging", "fraud", "fintech"}),
        source="CBN Risk-Based Cybersecurity Framework §4.7",
    ),
    KnowledgeSnippet(
        id="cbn.4.8.incident",
        title="CBN Cybersecurity Framework §4.8 — Incident response",
        content=(
            "Cyber incidents must be reported to the CBN within 24 hours "
            "of detection (more stringent than NDPA's 72 hours). A formal "
            "incident response plan covering detection, containment, "
            "eradication, recovery and lessons learned is required, with "
            "annual testing. Indicators of compromise must be shared "
            "through the financial sector's information sharing channels."
        ),
        framework_codes=frozenset({"cbn_cyber"}),
        tags=frozenset({"incident_response", "fintech", "notification"}),
        source="CBN Risk-Based Cybersecurity Framework §4.8",
    ),
    # --- Sector-specific (fintech in NG) --------------------------------------
    KnowledgeSnippet(
        id="sector.fintech.bvn_nin",
        title="Sector context: BVN and NIN handling in Nigerian fintech",
        content=(
            "BVN and NIN are national identifiers in Nigeria treated as "
            "sensitive personal data under NDPA, and fintechs handling "
            "them are subject to additional CBN, NIBSS, and NIMC rules. "
            "Storage requires encryption with restricted access; sharing "
            "with third parties requires explicit consent and a DPA; and "
            "use cases must align with what the customer was informed of "
            "at collection. Mishandling BVNs is a frequent enforcement "
            "trigger from regulators."
        ),
        framework_codes=frozenset({"ndpa", "cbn_cyber"}),
        tags=frozenset({"bvn", "nin", "fintech", "identity"}),
    ),
    KnowledgeSnippet(
        id="sector.fintech.sim_swap",
        title="Sector context: SIM swap fraud in African fintech",
        content=(
            "SIM swap is the dominant attack vector against mobile money "
            "and bank accounts in Nigeria, Kenya, and South Africa. "
            "Telco-coordinated SIM swap unlinks the legitimate user from "
            "the phone number used for OTP verification, allowing the "
            "attacker to receive auth codes. Mitigations: SIM swap "
            "detection APIs (e.g. via aggregators or directly with telcos), "
            "device binding, behavioural risk scoring, and reduced "
            "reliance on SMS OTP for high-value transactions."
        ),
        framework_codes=frozenset({"cbn_cyber"}),
        tags=frozenset({"sim_swap", "fraud", "fintech", "otp"}),
    ),
]


# ----- Retriever interface ----------------------------------------------------


class KnowledgeRetriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        *,
        framework_codes: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[KnowledgeSnippet]: ...

    @abstractmethod
    def get_by_id(self, snippet_id: str) -> KnowledgeSnippet | None: ...


class InMemoryRetriever(KnowledgeRetriever):
    """Filters the bundled corpus by framework + tag overlap.

    Ranking heuristic: snippets matching more requested tags rank higher.
    Snippets with no tag overlap but matching framework still appear at
    the bottom of the result.

    Snippet source resolution:
      1. Explicit list passed to constructor (test override)
      2. YAML files under app/data/knowledge/ (Session 6 corpus)
      3. _SEED_SNIPPETS hardcoded fallback (Session 3 minimal seed)
    """

    def __init__(self, snippets: list[KnowledgeSnippet] | None = None):
        if snippets is not None:
            self._snippets = snippets
        else:
            self._snippets = _load_yaml_corpus_or_fallback()

    def retrieve(
        self,
        *,
        framework_codes: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[KnowledgeSnippet]:
        framework_filter = set(framework_codes) if framework_codes else None
        tag_filter = set(tags) if tags else set()

        scored: list[tuple[int, KnowledgeSnippet]] = []
        for snippet in self._snippets:
            if framework_filter and not (snippet.framework_codes & framework_filter):
                continue
            tag_overlap = len(snippet.tags & tag_filter) if tag_filter else 0
            scored.append((tag_overlap, snippet))

        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored[:limit]]

    def get_by_id(self, snippet_id: str) -> KnowledgeSnippet | None:
        for snippet in self._snippets:
            if snippet.id == snippet_id:
                return snippet
        return None

    @property
    def all_snippets(self) -> list[KnowledgeSnippet]:
        return list(self._snippets)


def _load_yaml_corpus_or_fallback() -> list[KnowledgeSnippet]:
    """Try to load YAML corpus; fall back to hardcoded seed if it fails.

    YAML loading happens lazily and silently — broken YAML doesn't crash
    the process at import. The seed CLI (`python -m app.cli seed`) is the
    place where YAML errors fail loud.
    """
    try:
        from app.services.seed.loader import load_knowledge_snippets

        snippets = load_knowledge_snippets()
        if snippets:
            return snippets
    except Exception:
        # Seed package or YAML data not available — fall through to seed
        pass
    return list(_SEED_SNIPPETS)


# Default retriever — swap to pgvector-backed without changing callers
default_retriever: KnowledgeRetriever = InMemoryRetriever()
