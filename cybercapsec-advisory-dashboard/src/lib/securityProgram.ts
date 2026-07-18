export type SecurityObjective =
  | "reduce_breach_risk"
  | "secure_customer_data"
  | "prepare_for_audit"
  | "win_customer_trust"
  | "meet_regulatory_need";

export type SecurityPriority =
  | "identity_access"
  | "cloud_infrastructure"
  | "application_security"
  | "data_protection"
  | "incident_response"
  | "vendor_risk"
  | "people_awareness"
  | "business_resilience";

export type CriticalAsset =
  | "customer_data"
  | "payment_systems"
  | "production_cloud"
  | "source_code"
  | "employee_devices"
  | "third_party_tools";

export interface SecurityProgramProfile {
  objective: SecurityObjective;
  priorities: SecurityPriority[];
  assets: CriticalAsset[];
  targetFrameworks: string[];
  urgency: "this_month" | "this_quarter" | "this_half" | "exploring";
  completedAt: string;
}

const baseKey = "ccs.security_program_profile";

function storageKey(companyId: string | null | undefined): string {
  return companyId ? `${baseKey}.${companyId}` : baseKey;
}

export const objectiveLabels: Record<SecurityObjective, string> = {
  reduce_breach_risk: "Reduce breach risk",
  secure_customer_data: "Secure customer data",
  prepare_for_audit: "Prepare for an audit",
  win_customer_trust: "Win customer trust",
  meet_regulatory_need: "Meet a regulatory need",
};

export const priorityLabels: Record<SecurityPriority, string> = {
  identity_access: "Identity and access",
  cloud_infrastructure: "Cloud infrastructure",
  application_security: "Application security",
  data_protection: "Data protection",
  incident_response: "Incident response",
  vendor_risk: "Vendor risk",
  people_awareness: "People and awareness",
  business_resilience: "Business resilience",
};

export const assetLabels: Record<CriticalAsset, string> = {
  customer_data: "Customer data",
  payment_systems: "Payment systems",
  production_cloud: "Production cloud",
  source_code: "Source code",
  employee_devices: "Employee devices",
  third_party_tools: "Third-party tools",
};

export const frameworkLabels: Record<string, string> = {
  soc2: "SOC 2",
  iso27001: "ISO 27001",
  nist_csf: "NIST CSF",
  cis_controls: "CIS Controls",
  gdpr: "GDPR",
  ndpa: "NDPA",
  cbn_cyber: "CBN Cybersecurity",
  hipaa: "HIPAA",
  popia: "POPIA",
  kenya_dpa: "Kenya DPA",
  pci_dss: "PCI DSS",
};

export function getSecurityProgramProfile(
  companyId: string | null | undefined,
): SecurityProgramProfile | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(storageKey(companyId));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SecurityProgramProfile;
  } catch {
    return null;
  }
}

export function saveSecurityProgramProfile(
  companyId: string | null | undefined,
  profile: SecurityProgramProfile,
): void {
  window.localStorage.setItem(storageKey(companyId), JSON.stringify(profile));
}

export function hasSecurityProgramProfile(
  companyId: string | null | undefined,
): boolean {
  return !!getSecurityProgramProfile(companyId);
}
