import type { RoadmapItem } from "@/types/api";
import type { FrameworkGuide, FrameworkKey } from "@/lib/frameworkReadiness";
import type { SecurityPriority } from "@/lib/securityProgram";

export type ReadinessGoalKey =
  | "need_pci_dss"
  | "need_soc2"
  | "reduce_breach_risk"
  | "customer_questionnaire"
  | "secure_payments"
  | "privacy_regulatory";

export interface ReadinessGoal {
  key: ReadinessGoalKey;
  title: string;
  description: string;
  recommendedFramework: FrameworkKey;
  outcome: string;
  firstMove: string;
}

export const readinessGoals: ReadinessGoal[] = [
  {
    key: "need_pci_dss",
    title: "I need PCI DSS",
    description: "I take card payments or a partner asked for payment security proof.",
    recommendedFramework: "pci_dss",
    outcome: "Understand payment scope, reduce card-data exposure, and prepare validation evidence.",
    firstMove: "Run the PCI DSS scope wizard before collecting evidence.",
  },
  {
    key: "need_soc2",
    title: "I need SOC 2",
    description: "Enterprise customers want a trust report or security proof.",
    recommendedFramework: "soc2",
    outcome: "Build operating controls for access, change, vendors, incidents, and evidence history.",
    firstMove: "Start with the assessment, then attach proof for the controls customers ask about.",
  },
  {
    key: "reduce_breach_risk",
    title: "Reduce breach risk",
    description: "I want the highest-risk security gaps fixed first.",
    recommendedFramework: "nist_csf",
    outcome: "Prioritize identity, cloud, data, app security, detection, response, and recovery work.",
    firstMove: "Take the 5-minute baseline, then move the top risks into the roadmap.",
  },
  {
    key: "customer_questionnaire",
    title: "Answer a security questionnaire",
    description: "A customer sent security questions and I need credible answers.",
    recommendedFramework: "soc2",
    outcome: "Use policies, evidence, roadmap status, and posture reports to answer with confidence.",
    firstMove: "Paste the question into the questionnaire helper and connect the answer to evidence.",
  },
  {
    key: "secure_payments",
    title: "Secure payments",
    description: "I want to reduce payment-system risk before a formal PCI push.",
    recommendedFramework: "pci_dss",
    outcome: "Map payment flows, limit sensitive data, harden access, logging, scans, and incident response.",
    firstMove: "Confirm whether payment data touches your systems or stays with the provider.",
  },
  {
    key: "privacy_regulatory",
    title: "Privacy or regulatory readiness",
    description: "I need NDPA, GDPR, CBN, HIPAA, POPIA, or another regulatory path.",
    recommendedFramework: "ndpa",
    outcome: "Map sensitive data, access, vendors, retention, incidents, and security evidence.",
    firstMove: "Start with data flows and vendor access before writing policy text.",
  },
];

export interface ScopeChoice {
  value: string;
  label: string;
  score: number;
  guidance: string;
}

export interface ScopeQuestion {
  id: string;
  question: string;
  helper: string;
  choices: ScopeChoice[];
}

const pciScopeQuestions: ScopeQuestion[] = [
  {
    id: "payment_flow",
    question: "How do card payments happen today?",
    helper: "This is the fastest way to understand how much PCI DSS work may touch your systems.",
    choices: [
      {
        value: "redirect_provider",
        label: "Hosted checkout or redirect to payment provider",
        score: 90,
        guidance: "Likely lower direct scope, but you still need provider, access, and redirect controls.",
      },
      {
        value: "embedded_fields",
        label: "Embedded provider fields inside our product",
        score: 70,
        guidance: "Scope is usually more involved because your application can affect the payment page.",
      },
      {
        value: "direct_card_entry",
        label: "Our app directly collects card details",
        score: 35,
        guidance: "Treat this as high scope until a qualified payment expert confirms otherwise.",
      },
      {
        value: "not_sure",
        label: "I am not sure",
        score: 25,
        guidance: "Start with payment-flow mapping before making PCI DSS promises.",
      },
    ],
  },
  {
    id: "card_storage",
    question: "Does your company store cardholder data anywhere?",
    helper: "Check databases, logs, support exports, analytics tools, backups, and spreadsheets.",
    choices: [
      {
        value: "no",
        label: "No, we do not store it",
        score: 90,
        guidance: "Good. Prove this with data-flow notes and provider configuration evidence.",
      },
      {
        value: "tokens_only",
        label: "Only provider tokens or masked records",
        score: 75,
        guidance: "Usually safer, but confirm tokens, logs, and staff tools do not expose card data.",
      },
      {
        value: "yes",
        label: "Yes, card data is stored",
        score: 20,
        guidance: "This increases scope sharply. Reducing storage should become an urgent roadmap item.",
      },
      {
        value: "not_sure",
        label: "I am not sure",
        score: 25,
        guidance: "Search data stores and logs before continuing readiness planning.",
      },
    ],
  },
  {
    id: "staff_access",
    question: "Can staff or admins access payment records?",
    helper: "Support, finance, engineering, and operations access all matter.",
    choices: [
      {
        value: "least_privilege",
        label: "Yes, but only least-privilege roles with MFA",
        score: 80,
        guidance: "Keep access reviews, role lists, and MFA evidence ready.",
      },
      {
        value: "broad_access",
        label: "Several roles have broad access",
        score: 45,
        guidance: "Reduce access and document who truly needs payment-system privileges.",
      },
      {
        value: "no_access",
        label: "No internal access",
        score: 90,
        guidance: "Good. Keep provider access and emergency access evidence documented.",
      },
      {
        value: "not_sure",
        label: "I am not sure",
        score: 30,
        guidance: "Run an access review before relying on a readiness score.",
      },
    ],
  },
  {
    id: "payment_logs",
    question: "Could logs, analytics, or support tools contain payment data?",
    helper: "Many teams accidentally leak sensitive payment data into logs.",
    choices: [
      {
        value: "sanitized",
        label: "We sanitize and monitor logs",
        score: 85,
        guidance: "Collect log-redaction settings, test records, and monitoring evidence.",
      },
      {
        value: "possible",
        label: "It is possible",
        score: 40,
        guidance: "Treat log review and redaction as early PCI DSS readiness work.",
      },
      {
        value: "unknown",
        label: "Unknown",
        score: 25,
        guidance: "Review application, gateway, support, and analytics logs before audit planning.",
      },
      {
        value: "none",
        label: "No logs touch payment flows",
        score: 70,
        guidance: "Confirm this with engineering and keep the confirmation as evidence.",
      },
    ],
  },
];

const genericScopeQuestions: ScopeQuestion[] = [
  {
    id: "sensitive_data",
    question: "Do you know which sensitive data this framework covers?",
    helper: "Scope starts with knowing what data and systems matter.",
    choices: [
      {
        value: "mapped",
        label: "Yes, mapped and reviewed",
        score: 90,
        guidance: "Use the map as the evidence anchor for the roadmap.",
      },
      {
        value: "partial",
        label: "Partly mapped",
        score: 60,
        guidance: "Finish the missing systems, exports, vendors, and support workflows.",
      },
      {
        value: "not_yet",
        label: "Not yet",
        score: 25,
        guidance: "Start with data and asset mapping before deep control work.",
      },
    ],
  },
  {
    id: "owners",
    question: "Are there owners for access, incidents, vendors, and evidence?",
    helper: "Founder-friendly readiness still needs named owners.",
    choices: [
      {
        value: "named",
        label: "Yes, owners are named",
        score: 85,
        guidance: "Confirm each owner has a cadence and proof to maintain.",
      },
      {
        value: "informal",
        label: "Informal ownership",
        score: 55,
        guidance: "Turn informal ownership into roadmap assignments.",
      },
      {
        value: "founder_only",
        label: "Mostly founder-only",
        score: 35,
        guidance: "Assign task owners so readiness does not stall.",
      },
    ],
  },
  {
    id: "evidence",
    question: "Can you prove your controls operate?",
    helper: "Most readiness gaps are evidence gaps.",
    choices: [
      {
        value: "strong",
        label: "Yes, evidence is attached",
        score: 85,
        guidance: "Review evidence freshness and framework coverage.",
      },
      {
        value: "some",
        label: "Some evidence exists",
        score: 60,
        guidance: "Prioritize high-risk controls and customer-facing proof.",
      },
      {
        value: "little",
        label: "Very little evidence",
        score: 30,
        guidance: "Start collecting screenshots, policies, links, and review records.",
      },
    ],
  },
];

export function getScopeQuestions(key: FrameworkKey): ScopeQuestion[] {
  return key === "pci_dss" ? pciScopeQuestions : genericScopeQuestions;
}

export interface ScopeReadinessResult {
  score: number;
  label: string;
  summary: string;
  nextSteps: string[];
  evidence: string[];
}

export function evaluateScopeReadiness(
  guide: FrameworkGuide,
  answers: Record<string, string>,
): ScopeReadinessResult {
  const questions = getScopeQuestions(guide.key);
  const answeredChoices = questions
    .map((question) =>
      question.choices.find((choice) => choice.value === answers[question.id]),
    )
    .filter((choice): choice is ScopeChoice => !!choice);

  if (answeredChoices.length === 0) {
    return {
      score: 20,
      label: "Scope not started",
      summary: `Start by answering the ${guide.shortName} scope questions so the roadmap can distinguish real security work from paperwork.`,
      nextSteps: [
        "Answer the readiness scope questions.",
        "Write down the systems, data, people, and vendors in scope.",
        "Run the quick baseline before assigning roadmap owners.",
      ],
      evidence: ["Asset list", "Data flow notes", "Vendor list"],
    };
  }

  const score = Math.round(
    answeredChoices.reduce((sum, choice) => sum + choice.score, 0) /
      answeredChoices.length,
  );
  const weakChoices = answeredChoices.filter((choice) => choice.score < 55);

  if (score >= 80) {
    return {
      score,
      label: "Strong starting point",
      summary: `${guide.shortName} scope looks reasonably clear. The next job is to prove controls and keep evidence fresh.`,
      nextSteps: [
        "Move high-priority controls into the roadmap.",
        "Attach evidence for access, logging, data protection, vendors, and incident response.",
        "Prepare a framework readiness report before sharing with customers or assessors.",
      ],
      evidence: ["Scope map", "Access review", "Control evidence", "Readiness report"],
    };
  }

  if (score >= 55) {
    return {
      score,
      label: "Partly ready",
      summary: `${guide.shortName} readiness is underway, but scope and evidence still need tightening before external review.`,
      nextSteps: [
        "Resolve the unclear scope answers first.",
        "Assign owners for evidence gaps.",
        "Use the roadmap timeline to separate urgent fixes from audit preparation.",
      ],
      evidence: ["Open gap list", "Owner assignments", "Evidence tracker"],
    };
  }

  return {
    score,
    label: "Needs scoping first",
    summary:
      weakChoices[0]?.guidance ??
      `The ${guide.shortName} path should start with scope and basic security controls before formal readiness work.`,
    nextSteps: [
      "Map scope before making certification or readiness commitments.",
      "Reduce risky data exposure where possible.",
      "Run the quick baseline and start the first 7-day security tasks.",
    ],
    evidence: ["Scope workshop notes", "Data minimization plan", "First 7-day task list"],
  };
}

export interface BaselineQuestion {
  id: string;
  domain: SecurityPriority;
  question: string;
  whyItMatters: string;
}

export const baselineQuestions: BaselineQuestion[] = [
  {
    id: "mfa_admins",
    domain: "identity_access",
    question: "Is MFA required for admin, cloud, code, email, and payment systems?",
    whyItMatters: "Weak identity controls are one of the fastest ways attackers take over a small company.",
  },
  {
    id: "access_review",
    domain: "identity_access",
    question: "Have you reviewed who still has access in the last 90 days?",
    whyItMatters: "Old staff, vendors, and test accounts often keep powerful access for too long.",
  },
  {
    id: "critical_assets",
    domain: "cloud_infrastructure",
    question: "Do you know your critical systems, databases, repositories, and vendors?",
    whyItMatters: "You cannot protect, monitor, or recover what nobody has listed.",
  },
  {
    id: "secure_release",
    domain: "application_security",
    question: "Do code changes go through review, dependency checks, and release approval?",
    whyItMatters: "Product changes can quietly introduce customer-data and payment-system risk.",
  },
  {
    id: "data_map",
    domain: "data_protection",
    question: "Do you know where customer, payment, health, or personal data is stored and shared?",
    whyItMatters: "Data mapping is the foundation for privacy, PCI DSS, breach response, and customer trust.",
  },
  {
    id: "incident_plan",
    domain: "incident_response",
    question: "Could your team respond to a security incident today without improvising?",
    whyItMatters: "A simple incident plan reduces confusion when minutes matter.",
  },
  {
    id: "vendor_reviews",
    domain: "vendor_risk",
    question: "Do you review vendors that can access customer data or production systems?",
    whyItMatters: "Small teams inherit risk from payment, hosting, analytics, support, and AI tools.",
  },
  {
    id: "restore_test",
    domain: "business_resilience",
    question: "Have you tested backup restoration for critical systems?",
    whyItMatters: "Backups only matter if the team can restore them under pressure.",
  },
];

export type BaselineAnswer = "yes" | "partial" | "no" | "not_sure";

const baselineScores: Record<BaselineAnswer, number> = {
  yes: 100,
  partial: 60,
  no: 15,
  not_sure: 25,
};

export function evaluateQuickBaseline(answers: Record<string, BaselineAnswer>) {
  const answered = baselineQuestions.filter((question) => answers[question.id]);
  if (answered.length === 0) {
    return {
      score: 0,
      label: "Not started",
      summary: "Answer the quick baseline to reveal the first security actions.",
      urgentGaps: baselineQuestions.slice(0, 3),
    };
  }

  const score = Math.round(
    answered.reduce((sum, question) => sum + baselineScores[answers[question.id]], 0) /
      answered.length,
  );
  const urgentGaps = baselineQuestions.filter((question) =>
    ["no", "not_sure"].includes(answers[question.id]),
  );
  const description = describeReadinessScore(score, "cybersecurity baseline");

  return {
    score,
    label: description.label,
    summary: description.summary,
    urgentGaps,
  };
}

export function describeReadinessScore(
  score: number | null | undefined,
  context = "security readiness",
) {
  if (score === null || score === undefined) {
    return {
      label: "No score yet",
      summary: `Run an assessment or quick baseline to understand ${context} in plain English.`,
      tone: "neutral" as const,
    };
  }
  if (score >= 80) {
    return {
      label: "Strong, but keep proving it",
      summary: `Your ${context} looks strong. The main work is keeping evidence current and reviewing exceptions before sharing externally.`,
      tone: "success" as const,
    };
  }
  if (score >= 60) {
    return {
      label: "Good foundation with visible gaps",
      summary: `Your ${context} has a usable foundation, but customers or auditors may still ask for stronger access, evidence, incident, vendor, or monitoring proof.`,
      tone: "warning" as const,
    };
  }
  if (score >= 35) {
    return {
      label: "Not ready for pressure yet",
      summary: `Your ${context} needs focused remediation before a serious customer review, audit, or regulator conversation.`,
      tone: "danger" as const,
    };
  }
  return {
    label: "Start with fundamentals",
    summary: `Your ${context} should begin with MFA, asset/data mapping, backups, incident response, and evidence ownership.`,
    tone: "danger" as const,
  };
}

export interface RoadmapEducation {
  why: string;
  founderHow: string;
  engineerHow: string;
  evidence: string[];
}

const educationByDomain: Record<SecurityPriority, RoadmapEducation> = {
  identity_access: {
    why: "Most breaches begin with stolen credentials, over-permissioned users, or forgotten access.",
    founderHow: "Make MFA non-negotiable, approve who gets powerful access, and review leavers quickly.",
    engineerHow: "Enforce SSO/MFA, least privilege, privileged-account logging, and scheduled access reviews.",
    evidence: ["MFA settings", "Access review export", "User role list", "Offboarding ticket"],
  },
  cloud_infrastructure: {
    why: "Cloud misconfiguration can expose production systems, customer data, logs, and backups.",
    founderHow: "Know the critical cloud accounts, confirm backups, and ask for proof of secure configuration.",
    engineerHow: "Review IAM, network exposure, storage permissions, logging, secrets, patching, and backup restores.",
    evidence: ["Cloud inventory", "Configuration screenshot", "Backup restore proof", "Logging export"],
  },
  application_security: {
    why: "Application flaws can turn normal product usage into data exposure or account takeover.",
    founderHow: "Require code review and track vulnerabilities like product defects, not optional chores.",
    engineerHow: "Use review, dependency scanning, threat modeling for sensitive flows, secure release gates, and remediation SLAs.",
    evidence: ["Pull request review", "Dependency scan", "Release approval", "Vulnerability ticket"],
  },
  data_protection: {
    why: "Sensitive data creates customer, regulatory, payment, privacy, and breach-response obligations.",
    founderHow: "Know what sensitive data you collect, reduce what you do not need, and protect what remains.",
    engineerHow: "Maintain data maps, encryption, retention controls, access boundaries, deletion workflows, and log redaction.",
    evidence: ["Data flow map", "Encryption settings", "Retention rule", "Deletion record"],
  },
  incident_response: {
    why: "Incidents become much worse when nobody knows who decides, who investigates, or who notifies customers.",
    founderHow: "Create a simple escalation plan and rehearse the first hour of a serious incident.",
    engineerHow: "Define severity, detection sources, triage steps, evidence preservation, containment, communication, and postmortems.",
    evidence: ["Incident response plan", "Tabletop notes", "Alert screenshot", "Postmortem template"],
  },
  vendor_risk: {
    why: "Vendors can access your data, infrastructure, customers, and payment flow.",
    founderHow: "Review the few vendors that matter most before signing or renewing.",
    engineerHow: "Track processors, access paths, security docs, DPAs, SOC reports, sub-processors, and offboarding.",
    evidence: ["Vendor register", "DPA", "Security review", "Access removal proof"],
  },
  people_awareness: {
    why: "A small team can lose control through phishing, weak device hygiene, or unclear security behavior.",
    founderHow: "Set simple rules people can remember and check that training actually happened.",
    engineerHow: "Track onboarding training, phishing awareness, device requirements, acceptable use, and policy acknowledgement.",
    evidence: ["Training record", "Policy acknowledgement", "Device policy", "Awareness campaign"],
  },
  business_resilience: {
    why: "Customers care whether you can keep operating and recover after failure, compromise, or provider outage.",
    founderHow: "Know the most critical workflows and ask for restore proof, not just backup claims.",
    engineerHow: "Define RTO/RPO, run restore tests, document dependencies, monitor critical services, and rehearse continuity steps.",
    evidence: ["Restore test", "Continuity plan", "Dependency map", "Status-page record"],
  },
};

function inferDomainFromText(text: string): SecurityPriority {
  const lower = text.toLowerCase();
  if (/(mfa|access|identity|privilege|user|admin|offboard)/.test(lower)) {
    return "identity_access";
  }
  if (/(cloud|backup|network|logging|infrastructure|server|storage)/.test(lower)) {
    return "cloud_infrastructure";
  }
  if (/(code|dependency|release|vulnerab|application|secure development)/.test(lower)) {
    return "application_security";
  }
  if (/(data|encryption|privacy|retention|payment|card|phi|personal)/.test(lower)) {
    return "data_protection";
  }
  if (/(incident|breach|detect|response|alert|tabletop)/.test(lower)) {
    return "incident_response";
  }
  if (/(vendor|supplier|third.?party|processor|dpa)/.test(lower)) {
    return "vendor_risk";
  }
  if (/(training|awareness|employee|policy acknowledgement)/.test(lower)) {
    return "people_awareness";
  }
  return "business_resilience";
}

export function getRoadmapEducation(item: RoadmapItem): RoadmapEducation {
  const domain = inferDomainFromText(`${item.title} ${item.description}`);
  return educationByDomain[domain];
}

export function getRoadmapTimelineLabel(weekTarget: number) {
  if (weekTarget <= 1) return "Next 7 days";
  if (weekTarget <= 4) return "Next 30 days";
  if (weekTarget <= 13) return "Next 90 days";
  return "Before audit or customer review";
}

export const evidenceExamples = [
  {
    title: "MFA enforcement screenshot",
    description: "Settings page showing MFA required for admin, cloud, code, email, or payment systems.",
    frameworks: ["PCI DSS", "SOC 2", "ISO 27001", "NIST CSF"],
    domains: ["identity_access"],
  },
  {
    title: "Access review record",
    description: "List of privileged users reviewed, approved, removed, or changed with date and owner.",
    frameworks: ["PCI DSS", "SOC 2", "ISO 27001", "CBN"],
    domains: ["identity_access"],
  },
  {
    title: "Payment data flow",
    description: "Diagram or notes showing checkout, payment provider, logs, support tools, and storage.",
    frameworks: ["PCI DSS"],
    domains: ["data_protection", "application_security"],
  },
  {
    title: "Vulnerability scan and remediation ticket",
    description: "Scan result plus linked task showing severity, owner, deadline, and fix status.",
    frameworks: ["PCI DSS", "SOC 2", "CIS Controls", "NIST CSF"],
    domains: ["application_security", "cloud_infrastructure"],
  },
  {
    title: "Backup restore test",
    description: "Evidence that a critical system was restored successfully, including date and result.",
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CBN"],
    domains: ["business_resilience"],
  },
  {
    title: "Incident response tabletop",
    description: "Scenario, participants, decisions, gaps found, and follow-up tasks.",
    frameworks: ["PCI DSS", "SOC 2", "ISO 27001", "NDPA", "CBN"],
    domains: ["incident_response"],
  },
  {
    title: "Vendor security review",
    description: "Vendor register entry with data access, contract/DPA, security review, and risk decision.",
    frameworks: ["SOC 2", "ISO 27001", "GDPR", "NDPA", "CBN"],
    domains: ["vendor_risk"],
  },
  {
    title: "Security policy approval",
    description: "Approved policy with owner, review date, acknowledgement, and mapped controls.",
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "NDPA"],
    domains: ["people_awareness", "data_protection"],
  },
];

export const questionnaireSamples = [
  "Do you require MFA for administrative access?",
  "Do you have an incident response plan?",
  "How do you protect payment card data?",
  "Do you perform vendor security reviews?",
  "Can you provide evidence of vulnerability management?",
];

export function draftQuestionnaireAnswer(question: string, guide: FrameworkGuide) {
  const lower = question.toLowerCase();
  if (/(mfa|multi-factor|2fa|access)/.test(lower)) {
    return {
      answer:
        "We require strong access controls for administrative and sensitive systems, including MFA where supported, least-privilege roles, and periodic access reviews. Evidence should include MFA configuration, privileged-user exports, and access-review records.",
      evidence: ["MFA settings", "Privileged user list", "Access review record"],
    };
  }
  if (/(incident|breach|response|notify)/.test(lower)) {
    return {
      answer:
        "We maintain an incident response process that defines escalation, triage, containment, communication, and post-incident review. Evidence should include the incident response plan, tabletop notes, alert examples, and postmortem templates.",
      evidence: ["Incident response plan", "Tabletop notes", "Alert example"],
    };
  }
  if (/(payment|card|pci|cardholder)/.test(lower)) {
    return {
      answer:
        "Payment-security readiness starts with scope. We document payment flows, provider responsibilities, access paths, log handling, vulnerability management, and evidence for controls that can affect cardholder data.",
      evidence: ["Payment data flow", "Provider contract", "Access review", "Scan result"],
    };
  }
  if (/(vendor|supplier|third.?party|processor)/.test(lower)) {
    return {
      answer:
        "Vendors with access to sensitive data or production systems are tracked and reviewed based on risk. Evidence should include vendor register entries, DPAs or contracts, security documentation, access approvals, and offboarding records.",
      evidence: ["Vendor register", "DPA", "Security review", "Access approval"],
    };
  }
  if (/(vulnerab|scan|patch|penetration|pentest)/.test(lower)) {
    return {
      answer:
        "Vulnerability management should include discovery, severity ranking, owner assignment, remediation deadlines, verification, and exception tracking. Evidence should connect scan findings to tickets and completed fixes.",
      evidence: ["Scan result", "Remediation ticket", "Exception log"],
    };
  }
  return {
    answer: `For ${guide.shortName}, answer this by naming the control, the owner, the operating cadence, and the evidence. A strong response explains what is implemented today, what is monitored, and what remains on the roadmap.`,
    evidence: ["Policy", "Screenshot", "Review record", "Roadmap task"],
  };
}

export const glossaryTerms = [
  {
    term: "Cardholder data environment",
    plainEnglish: "The people, systems, apps, networks, and vendors that store, process, transmit, or can affect payment card data.",
    founderWhy: "PCI DSS readiness is much easier when this scope is small and clearly documented.",
  },
  {
    term: "MFA",
    plainEnglish: "A second proof of identity, such as an authenticator app, required after a password.",
    founderWhy: "It is one of the cheapest ways to reduce account takeover risk.",
  },
  {
    term: "Least privilege",
    plainEnglish: "People and systems only get the access they need to do their job.",
    founderWhy: "It limits damage when an account, vendor, or employee device is compromised.",
  },
  {
    term: "Evidence",
    plainEnglish: "Proof that a security control exists and actually operates.",
    founderWhy: "Customers, auditors, investors, and regulators trust evidence more than promises.",
  },
  {
    term: "Vulnerability management",
    plainEnglish: "Finding, prioritizing, fixing, and verifying security weaknesses.",
    founderWhy: "It turns scary scan findings into owned work with deadlines.",
  },
  {
    term: "Incident response",
    plainEnglish: "The agreed way your team detects, escalates, contains, communicates, and learns from security events.",
    founderWhy: "When something goes wrong, this prevents confusion from becoming business damage.",
  },
  {
    term: "Data flow",
    plainEnglish: "A map of where sensitive data enters, moves, is stored, is shared, and is deleted.",
    founderWhy: "It is the backbone of PCI DSS, privacy, breach response, and customer trust.",
  },
  {
    term: "Control owner",
    plainEnglish: "The person accountable for keeping a security control working and evidenced.",
    founderWhy: "Security stalls when everything remains founder-owned.",
  },
  {
    term: "Readiness",
    plainEnglish: "How prepared you are for a customer review, audit, regulator request, or real cyber incident.",
    founderWhy: "Readiness is the honest state before someone external asks for proof.",
  },
  {
    term: "Exception",
    plainEnglish: "A known gap or accepted risk with an owner, reason, review date, and compensating action.",
    founderWhy: "Honest exceptions are better than pretending every control is complete.",
  },
];
