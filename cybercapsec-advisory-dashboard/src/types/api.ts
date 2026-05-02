// Type definitions matching the FastAPI backend Pydantic schemas.
// Keep in sync with app/schemas/* on the backend.

// ----- Auth ------------------------------------------------------------------

export type UserRole = "owner" | "admin" | "member" | "auditor";

export type Sector =
  | "fintech"
  | "healthtech"
  | "edtech"
  | "ecommerce"
  | "logistics"
  | "agritech"
  | "saas"
  | "insurtech"
  | "proptech"
  | "other";

export type CompanySize =
  | "solo"
  | "micro"
  | "small"
  | "medium"
  | "large"
  | "enterprise";

export type CompanyStage =
  | "idea"
  | "pre_seed"
  | "seed"
  | "series_a"
  | "series_b"
  | "series_c_plus"
  | "bootstrapped"
  | "established";

export interface User {
  id: string;
  email: string;
  full_name: string;
  job_title: string | null;
  role: UserRole;
  company_id: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  country: string;
  sector: Sector;
  size: CompanySize;
  stage: CompanyStage;
  website: string | null;
  description: string | null;
  subscription_tier: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface SignupResponse {
  user: User;
  company: Company;
  tokens: AuthTokens;
}

export interface SignupPayload {
  email: string;
  password: string;
  full_name: string;
  job_title?: string;
  company_name: string;
  country: string;
  sector: Sector;
  size: CompanySize;
  stage: CompanyStage;
}

export interface LoginPayload {
  email: string;
  password: string;
}

// ----- Questionnaire ---------------------------------------------------------

export type QuestionType =
  | "single_select"
  | "multi_select"
  | "boolean"
  | "text"
  | "scale"
  | "number";

export interface QuestionnaireOption {
  value: string;
  label: string;
  description: string | null;
}

export interface QuestionnaireQuestion {
  id: string;
  text: string;
  help_text: string | null;
  type: QuestionType;
  required: boolean;
  options: QuestionnaireOption[];
  depends_on_question_id: string | null;
  depends_on_values: string[];
}

export interface QuestionnaireSection {
  id: string;
  title: string;
  description: string | null;
  questions: QuestionnaireQuestion[];
}

export interface Questionnaire {
  version: string;
  title: string;
  description: string;
  sections: QuestionnaireSection[];
}

// ----- Assessments -----------------------------------------------------------

export type AssessmentStatus =
  | "draft"
  | "in_progress"
  | "submitted"
  | "processing"
  | "completed"
  | "failed";

export interface Assessment {
  id: string;
  company_id: string;
  questionnaire_version: string;
  status: AssessmentStatus;
  responses: Record<string, unknown>;
  overall_risk_score: number | null;
  soc2_readiness_score: number | null;
  ndpa_compliance_score: number | null;
}

export interface AssessmentProgress {
  version: string;
  visible_questions: number;
  answered_questions: number;
  completion_pct: number;
  remaining_question_ids: string[];
}

export interface FrameworkScore {
  framework: string;
  score: number;
  avg_maturity: number;
  controls_assessed: number;
  controls_total: number;
  coverage_pct: number;
}

export interface ControlScore {
  framework: string;
  code: string;
  maturity: number;
  maturity_pct: number;
  contributing_questions: string[];
}

export interface ScoringSummary {
  overall_risk_score: number;
  framework_scores: FrameworkScore[];
  control_scores: ControlScore[];
  response_count: number;
}

export interface AssessmentSubmitResponse {
  assessment: Assessment;
  scoring: ScoringSummary;
  report_id: string;
}

// ----- Reports ---------------------------------------------------------------

export type Severity =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "informational";

export type Effort = "quick_win" | "short" | "medium" | "large" | "program";

export interface FrameworkCitation {
  framework: string;
  control_code: string;
}

export interface ReportRisk {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  likelihood: "high" | "medium" | "low";
  business_impact: string;
  affected_areas: string[];
  framework_citations: FrameworkCitation[];
  related_question_ids: string[];
}

export interface ReportRoadmapTask {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  effort: Effort;
  week_target: number;
  addresses_risk_ids: string[];
  framework_citations: FrameworkCitation[];
  success_criteria: string[];
}

export interface FrameworkGap {
  framework: string;
  framework_name: string;
  readiness_score: number;
  summary: string;
  top_gaps: string[];
  next_steps: string[];
}

export interface Report {
  id: string;
  assessment_id: string;
  report_type: "initial" | "reassessment" | "quarterly" | "ad_hoc";
  executive_summary: string | null;
  risk_register: ReportRisk[];
  roadmap: ReportRoadmapTask[];
  framework_gaps: Record<string, FrameworkGap>;
  model_used: string | null;
  generation_tokens_input: number | null;
  generation_tokens_output: number | null;
  generation_ms: number | null;
  created_at: string;
}

export interface ReportSummary {
  id: string;
  assessment_id: string;
  report_type: "initial" | "reassessment" | "quarterly" | "ad_hoc";
  model_used: string | null;
  created_at: string;
}

// ----- Policies --------------------------------------------------------------

export type PolicyTemplateCode =
  | "information_security"
  | "access_control"
  | "data_protection"
  | "data_retention"
  | "incident_response"
  | "acceptable_use"
  | "business_continuity"
  | "vendor_management"
  | "change_management"
  | "secure_development"
  | "password"
  | "remote_work"
  | "backup_recovery"
  | "privacy"
  | "security_awareness";

export type PolicyStatus = "draft" | "published" | "archived";

export interface PolicyTemplateVariable {
  name: string;
  label: string;
  description: string | null;
  required: boolean;
  default: unknown;
}

export interface PolicyTemplate {
  template_code: string;
  template_version: string;
  title: string;
  description: string;
  framework_codes: string[];
  control_refs: Array<Record<string, string>>;
  variables: PolicyTemplateVariable[];
}

export interface Policy {
  id: string;
  company_id: string;
  template_code: PolicyTemplateCode;
  template_version: string;
  version: number;
  title: string;
  content: string;
  status: PolicyStatus;
  rendered_variables: Record<string, unknown>;
  framework_codes: string[];
  control_refs: Array<Record<string, string>>;
  created_at: string;
  updated_at: string;
}

export interface PolicySummary {
  id: string;
  template_code: PolicyTemplateCode;
  template_version: string;
  version: number;
  title: string;
  status: PolicyStatus;
  framework_codes: string[];
  created_at: string;
}

export interface PolicyAcknowledgment {
  id: string;
  user_id: string;
  acknowledged_text: string | null;
  created_at: string;
}

// ----- Evidence --------------------------------------------------------------

export type EvidenceKind =
  | "external_link"
  | "policy_ref"
  | "screenshot_url"
  | "narrative"
  | "file_upload";

export type EvidenceStatus = "draft" | "active" | "expired" | "rejected";

export interface Evidence {
  id: string;
  company_id: string;
  submitted_by_user_id: string | null;
  title: string;
  description: string | null;
  kind: EvidenceKind;
  status: EvidenceStatus;
  framework_code: string;
  control_code: string;
  external_url: string | null;
  referenced_policy_id: string | null;
  narrative_text: string | null;
  valid_until: string | null;
  created_at: string;
  updated_at: string;
}

export interface PropagatedControl {
  framework_code: string;
  control_code: string;
  title: string;
  strength: "equivalent" | "partial" | "related";
}

export interface EvidenceWithCoverage {
  evidence: Evidence;
  propagated_controls: PropagatedControl[];
}

export interface CoverageMatrix {
  coverage: Record<string, string[]>;
}

export interface ControlEvidence {
  framework_code: string;
  control_code: string;
  direct_evidence: Evidence[];
  propagated_evidence: Evidence[];
}

// ----- Roadmap ---------------------------------------------------------------

export type RoadmapStatus =
  | "todo"
  | "in_progress"
  | "blocked"
  | "done"
  | "cancelled";

export interface RoadmapItem {
  id: string;
  company_id: string;
  report_id: string;
  source_task_id: string;
  title: string;
  description: string;
  severity: Severity;
  effort: Effort;
  week_target: number;
  status: RoadmapStatus;
  assignee_user_id: string | null;
  due_date: string | null;
  completed_at: string | null;
  framework_citations: FrameworkCitation[];
  success_criteria: string[];
  addresses_risk_ids: string[];
  notes: string | null;
  blocked_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoadmapProgress {
  total: number;
  done: number;
  in_progress: number;
  blocked: number;
  todo: number;
  cancelled: number;
  overdue: number;
  completion_pct: number;
  by_status: Record<string, number>;
}

// ----- Errors ----------------------------------------------------------------

export interface ApiError {
  message: string;
  status?: number;
  detail?: unknown;
}

// ----- Billing ---------------------------------------------------------------

export type BillingCurrency = "NGN" | "KES" | "ZAR" | "GHS" | "USD";

export type BillingInterval = "monthly" | "annually";

export type SubscriptionTierCode = "free" | "starter" | "growth" | "audit_ready";

export type SubscriptionStatus =
  | "pending"
  | "active"
  | "non_renewing"
  | "attention"
  | "cancelled"
  | "completed";

export interface PlanOut {
  tier: SubscriptionTierCode;
  name: string;
  description: string;
  interval: BillingInterval;
  currency: BillingCurrency;
  amount_minor: number;
  amount_major: number;
  max_active_assessments: number | null;
  max_evidence_items: number | null;
  max_published_policies: number | null;
  max_frameworks: number | null;
  ai_advisor_enabled: boolean;
  custom_policy_drafting: boolean;
  dedicated_reviewer: boolean;
}

export interface PricingOut {
  currency: BillingCurrency;
  free: PlanOut;
  paid: PlanOut[];
}

export interface SubscriptionOut {
  id: string;
  tier: SubscriptionTierCode;
  interval: BillingInterval;
  currency: BillingCurrency;
  amount_minor: number;
  status: SubscriptionStatus;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  cancelled_at: string | null;
  created_at: string;
}

export interface CurrentSubscriptionOut {
  tier: SubscriptionTierCode;
  currency: BillingCurrency;
  active_subscription: SubscriptionOut | null;
}

export interface CheckoutResponse {
  subscription_id: string;
  authorization_url: string;
  reference: string;
}

/**
 * Tier-limit detail returned by the backend on 402 Payment Required.
 * The dashboard uses this shape to render upgrade prompts.
 */
export interface TierLimitError {
  error: "tier_limit";
  feature?: string;
  limit?: string;
  current_tier: SubscriptionTierCode;
  cap?: number;
  current_count?: number;
  message: string;
}
