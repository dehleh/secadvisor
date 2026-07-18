import type { SecurityPriority } from "@/lib/securityProgram";

export type FrameworkKey =
  | "pci_dss"
  | "soc2"
  | "iso27001"
  | "nist_csf"
  | "cis_controls"
  | "gdpr"
  | "ndpa"
  | "cbn_cyber"
  | "hipaa";

export interface ReadinessPhase {
  title: string;
  goal: string;
  actions: string[];
  evidence: string[];
}

export interface FrameworkGuide {
  key: FrameworkKey;
  name: string;
  shortName: string;
  category: "Certification" | "Customer trust" | "Security baseline" | "Regulatory";
  bestFor: string;
  founderSummary: string;
  readinessQuestion: string;
  certificationNote: string;
  securityDomains: SecurityPriority[];
  outcomes: string[];
  phases: ReadinessPhase[];
  commonTraps: string[];
}

const baselinePhases: ReadinessPhase[] = [
  {
    title: "Understand scope",
    goal: "Decide which systems, teams, data, vendors, and business processes are in scope.",
    actions: [
      "List the products, cloud accounts, databases, people, and vendors that touch sensitive data.",
      "Mark what is business critical and what customers or regulators care about most.",
    ],
    evidence: ["Asset list", "Data flow notes", "Vendor list"],
  },
  {
    title: "Close foundation gaps",
    goal: "Fix the basic security controls that most frameworks expect before deeper audit work starts.",
    actions: [
      "Turn on MFA, remove stale access, document backups, and confirm logging is active.",
      "Patch high-risk systems and define how incidents are reported and handled.",
    ],
    evidence: ["MFA screenshot", "Access review", "Backup test", "Incident plan"],
  },
  {
    title: "Prove controls",
    goal: "Collect evidence that shows security controls are operating in real life.",
    actions: [
      "Attach screenshots, tickets, policies, links, exports, and owner notes to matching controls.",
      "Assign owners for missing evidence so readiness work does not sit with the founder alone.",
    ],
    evidence: ["Policy approvals", "Ticket links", "Screenshots", "Owner attestations"],
  },
  {
    title: "Review and share",
    goal: "Turn the roadmap into a clear security posture story for customers, auditors, or leadership.",
    actions: [
      "Review open risks, exceptions, and remaining roadmap tasks before sharing.",
      "Publish a controlled posture report with the right level of detail for the recipient.",
    ],
    evidence: ["Risk register", "Readiness report", "Exception log"],
  },
];

export const frameworkGuides: FrameworkGuide[] = [
  {
    key: "pci_dss",
    name: "PCI DSS readiness",
    shortName: "PCI DSS",
    category: "Certification",
    bestFor: "Teams that store, process, transmit, or can impact payment card data.",
    founderSummary:
      "PCI DSS is mainly about protecting payment card data. The founder job is to reduce the card-data footprint, lock down payment systems, prove the controls work, then prepare for validation with the right assessor or payment partner.",
    readinessQuestion:
      "Where does cardholder data enter, move, get stored, or get accessed in your product and operations?",
    certificationNote:
      "CyberCapSec should help you understand readiness, scope evidence, and close gaps. Final validation usually depends on your payment flow, merchant level, acquirer, and assessor requirements.",
    securityDomains: [
      "identity_access",
      "cloud_infrastructure",
      "application_security",
      "data_protection",
      "incident_response",
      "vendor_risk",
    ],
    outcomes: [
      "Know what is in and out of the card-data environment.",
      "Reduce payment data exposure before audit effort increases.",
      "Track access control, vulnerability management, logging, encryption, and incident-response evidence.",
    ],
    phases: [
      {
        title: "Map payment scope",
        goal: "Understand every place payment data enters, flows, or can be accessed.",
        actions: [
          "Document checkout, payment provider, admin tools, support workflows, logs, and databases.",
          "Separate payment systems from unrelated systems where practical.",
        ],
        evidence: ["Payment data flow", "Scoped asset list", "Provider contracts"],
      },
      {
        title: "Harden the environment",
        goal: "Reduce the risk of unauthorized access or exposure around payment systems.",
        actions: [
          "Enforce MFA, least privilege, secure configuration, patching, and secrets management.",
          "Review application security, vulnerability scanning, logging, and backup practices.",
        ],
        evidence: ["MFA settings", "Patch records", "Scan results", "Logging proof"],
      },
      {
        title: "Prepare validation evidence",
        goal: "Collect proof that payment security controls are implemented and operating.",
        actions: [
          "Attach evidence to each payment-relevant control and assign owners for missing items.",
          "Document compensating controls and exceptions before external review.",
        ],
        evidence: ["Control evidence", "Exception register", "Owner approvals"],
      },
      {
        title: "Review with assessor or partner",
        goal: "Enter validation with clean scope, clear ownership, and known remaining work.",
        actions: [
          "Package the readiness report and unresolved-risk list.",
          "Confirm validation format with the acquirer, payment provider, or qualified assessor.",
        ],
        evidence: ["Readiness report", "Open-risk summary", "Validation notes"],
      },
    ],
    commonTraps: [
      "Starting evidence collection before payment scope is clear.",
      "Assuming a payment provider removes every PCI DSS responsibility.",
      "Ignoring logs, admin access, support tools, and developer access paths.",
    ],
  },
  {
    key: "soc2",
    name: "SOC 2 readiness",
    shortName: "SOC 2",
    category: "Customer trust",
    bestFor: "SaaS teams selling to enterprise customers that ask security-review questions.",
    founderSummary:
      "SOC 2 is a trust report around how your company protects systems and customer data. The real work is consistent security operations: access reviews, change management, incident response, vendor risk, monitoring, and evidence.",
    readinessQuestion:
      "Can you prove your security controls operated consistently over time?",
    certificationNote:
      "CyberCapSec should help prepare your control story and evidence. A licensed CPA firm performs the SOC 2 examination.",
    securityDomains: [
      "identity_access",
      "application_security",
      "data_protection",
      "incident_response",
      "vendor_risk",
      "people_awareness",
      "business_resilience",
    ],
    outcomes: [
      "Turn customer trust requirements into controls and evidence.",
      "Build habits for access, change, incident, vendor, and continuity reviews.",
      "Share a stronger security posture before the formal report is complete.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Treating SOC 2 as policy writing instead of operating discipline.",
      "Collecting screenshots without owners or review cadence.",
      "Waiting for a customer deadline before building evidence history.",
    ],
  },
  {
    key: "iso27001",
    name: "ISO 27001 readiness",
    shortName: "ISO 27001",
    category: "Certification",
    bestFor: "Organizations that need a formal information security management system.",
    founderSummary:
      "ISO 27001 is about running information security as a management system. It expects leadership, risk treatment, policies, controls, review cadence, continuous improvement, and certification through an accredited audit path.",
    readinessQuestion:
      "Do you have a repeatable way to identify, treat, review, and improve information security risks?",
    certificationNote:
      "CyberCapSec should help structure the ISMS, risk register, evidence, and management rhythm. Certification is completed through an accredited certification body.",
    securityDomains: [
      "identity_access",
      "cloud_infrastructure",
      "application_security",
      "data_protection",
      "incident_response",
      "vendor_risk",
      "people_awareness",
      "business_resilience",
    ],
    outcomes: [
      "Create a practical ISMS that fits the business size.",
      "Link risk treatment decisions to controls and owners.",
      "Maintain evidence for internal reviews and certification audits.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Buying policy templates without building the management process.",
      "Skipping risk treatment ownership.",
      "Overbuilding controls that the team cannot operate consistently.",
    ],
  },
  {
    key: "nist_csf",
    name: "NIST CSF readiness",
    shortName: "NIST CSF",
    category: "Security baseline",
    bestFor: "Teams that want a plain cybersecurity risk-management structure without starting from an audit.",
    founderSummary:
      "NIST CSF is a flexible way to understand, prioritize, and communicate cybersecurity risk. It is especially useful when a founder needs a security roadmap before choosing a certification path.",
    readinessQuestion:
      "Can you explain how your company governs, identifies, protects, detects, responds to, and recovers from cyber risk?",
    certificationNote:
      "NIST CSF is a guidance framework, not a certification by itself. CyberCapSec should use it as a practical security maturity map.",
    securityDomains: [
      "identity_access",
      "cloud_infrastructure",
      "application_security",
      "data_protection",
      "incident_response",
      "people_awareness",
      "business_resilience",
    ],
    outcomes: [
      "Create a clear cybersecurity baseline across the business.",
      "Prioritize risks before spending heavily on audits or tools.",
      "Communicate cyber posture to leadership, customers, and partners.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Using NIST CSF as a checklist instead of a risk conversation.",
      "Ignoring governance and owner accountability.",
      "Improving protection controls while detection and recovery remain weak.",
    ],
  },
  {
    key: "cis_controls",
    name: "CIS Controls readiness",
    shortName: "CIS Controls",
    category: "Security baseline",
    bestFor: "Teams that need practical technical safeguards and quick risk reduction.",
    founderSummary:
      "CIS Controls are a prioritized set of safeguards for real-world cyber defense. They help a small team focus on inventory, secure configuration, access, vulnerability management, logging, malware defense, data protection, and recovery.",
    readinessQuestion:
      "Do you know what you own, how it is configured, who can access it, and whether it is monitored?",
    certificationNote:
      "CIS Controls are commonly used as a practical control baseline. CyberCapSec should translate them into owner-ready tasks and evidence.",
    securityDomains: [
      "identity_access",
      "cloud_infrastructure",
      "application_security",
      "data_protection",
      "incident_response",
      "business_resilience",
    ],
    outcomes: [
      "Close basic technical security gaps quickly.",
      "Create an implementation roadmap that engineers can execute.",
      "Build reusable evidence for stricter frameworks later.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Skipping asset inventory and jumping straight to tools.",
      "Running scans without assigning remediation owners.",
      "Treating configuration hardening as a one-time task.",
    ],
  },
  {
    key: "gdpr",
    name: "GDPR readiness",
    shortName: "GDPR",
    category: "Regulatory",
    bestFor: "Teams handling personal data from people in the European market.",
    founderSummary:
      "GDPR readiness is about knowing personal data flows, protecting that data, honoring rights, managing processors, and being ready to respond to incidents or privacy requests.",
    readinessQuestion:
      "What personal data do you collect, why do you collect it, where does it go, and who can access it?",
    certificationNote:
      "CyberCapSec should support security and privacy readiness. Legal interpretation and regulator-specific obligations should be reviewed with qualified privacy counsel.",
    securityDomains: [
      "data_protection",
      "identity_access",
      "vendor_risk",
      "incident_response",
      "people_awareness",
    ],
    outcomes: [
      "Understand personal-data collection, sharing, retention, and access.",
      "Tie privacy promises to security controls and vendor oversight.",
      "Prepare evidence for customer, partner, or regulator questions.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Writing a privacy notice before mapping actual data flows.",
      "Forgetting vendors, support exports, logs, and analytics tools.",
      "Keeping data longer than the business needs it.",
    ],
  },
  {
    key: "ndpa",
    name: "NDPA readiness",
    shortName: "NDPA",
    category: "Regulatory",
    bestFor: "Organizations handling personal data subject to Nigerian data protection expectations.",
    founderSummary:
      "NDPA readiness connects privacy governance with security operations: data mapping, access control, retention, vendor handling, incident response, and evidence that personal data is protected.",
    readinessQuestion:
      "Can you show how Nigerian personal data is collected, protected, shared, retained, and deleted?",
    certificationNote:
      "CyberCapSec should help operationalize readiness. Legal obligations, filings, or regulator-specific interpretation should be confirmed with qualified privacy counsel.",
    securityDomains: [
      "data_protection",
      "identity_access",
      "vendor_risk",
      "incident_response",
      "people_awareness",
    ],
    outcomes: [
      "Create a practical data-protection operating rhythm.",
      "Connect privacy duties to security controls and evidence.",
      "Improve confidence during customer and regulator reviews.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Treating privacy as a document exercise only.",
      "Leaving vendor data processing unmanaged.",
      "Not testing incident escalation for personal-data events.",
    ],
  },
  {
    key: "cbn_cyber",
    name: "CBN cybersecurity readiness",
    shortName: "CBN Cybersecurity",
    category: "Regulatory",
    bestFor: "Financial-services teams that need cybersecurity governance and operational discipline.",
    founderSummary:
      "CBN-style cybersecurity readiness is about governance, risk management, monitoring, incident response, resilience, third-party oversight, and leadership visibility into cyber risk.",
    readinessQuestion:
      "Can leadership see your cyber risks, controls, incidents, vendors, and recovery readiness in one place?",
    certificationNote:
      "CyberCapSec should help prepare governance and security evidence. Sector-specific regulatory interpretation should be reviewed with qualified advisors.",
    securityDomains: [
      "identity_access",
      "cloud_infrastructure",
      "data_protection",
      "incident_response",
      "vendor_risk",
      "business_resilience",
    ],
    outcomes: [
      "Build cybersecurity governance that leadership can understand.",
      "Track incident, vendor, and resilience readiness.",
      "Package security posture for board, regulator, and partner discussions.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Reporting controls without showing operational evidence.",
      "Leaving third-party and cloud risks outside the roadmap.",
      "Treating resilience as backup existence instead of restore readiness.",
    ],
  },
  {
    key: "hipaa",
    name: "HIPAA security readiness",
    shortName: "HIPAA",
    category: "Regulatory",
    bestFor: "Health, benefits, or care-related teams handling protected health information.",
    founderSummary:
      "HIPAA security readiness focuses on protecting health information through administrative, technical, and physical safeguards, with clear owners, access control, vendor handling, incident response, and audit-ready evidence.",
    readinessQuestion:
      "Where does protected health information live, who can access it, and how would you prove safeguards are working?",
    certificationNote:
      "CyberCapSec should help organize security readiness and evidence. HIPAA obligations and legal interpretation should be reviewed with qualified healthcare privacy counsel.",
    securityDomains: [
      "identity_access",
      "data_protection",
      "incident_response",
      "vendor_risk",
      "people_awareness",
      "business_resilience",
    ],
    outcomes: [
      "Map protected-health-information systems and workflows.",
      "Prove access, encryption, incident, vendor, and workforce safeguards.",
      "Give leadership a clearer view of healthcare security risk.",
    ],
    phases: baselinePhases,
    commonTraps: [
      "Assuming a cloud provider or EHR tool covers every safeguard.",
      "Ignoring workforce training and support workflows.",
      "Not documenting vendor and business associate responsibilities.",
    ],
  },
];

export function getFrameworkGuide(key: string | null | undefined) {
  return frameworkGuides.find((guide) => guide.key === key);
}

export function getDefaultFrameworkGuide(targetFrameworks: string[] = []) {
  const firstKnown = targetFrameworks
    .map((framework) => getFrameworkGuide(framework))
    .find((guide): guide is FrameworkGuide => !!guide);
  return firstKnown ?? frameworkGuides[0];
}
