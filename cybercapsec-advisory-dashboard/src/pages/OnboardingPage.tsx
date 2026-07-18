import { useMemo, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle,
  Database,
  FileCheck2,
  Fingerprint,
  LockKeyhole,
  ShieldCheck,
  Target,
} from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Card, CardBody, CardHeader, CardTitle } from "@/components/UI";
import { cn } from "@/lib/cn";
import { useAuth } from "@/context/AuthContext";
import {
  assetLabels,
  frameworkLabels,
  objectiveLabels,
  priorityLabels,
  saveSecurityProgramProfile,
  type CriticalAsset,
  type SecurityObjective,
  type SecurityPriority,
} from "@/lib/securityProgram";
import {
  frameworkGuides,
  getFrameworkGuide,
  type FrameworkGuide,
} from "@/lib/frameworkReadiness";

const objectives: Array<{
  value: SecurityObjective;
  description: string;
}> = [
  {
    value: "reduce_breach_risk",
    description: "Find the highest-risk security gaps and close them first.",
  },
  {
    value: "secure_customer_data",
    description: "Protect sensitive data across people, apps, and vendors.",
  },
  {
    value: "prepare_for_audit",
    description: "Build evidence and controls for SOC 2, ISO, PCI, or regulators.",
  },
  {
    value: "win_customer_trust",
    description: "Answer security reviews and share a credible posture story.",
  },
  {
    value: "meet_regulatory_need",
    description: "Track security controls required by your market or sector.",
  },
];

const priorities: Array<{
  value: SecurityPriority;
  description: string;
}> = [
  {
    value: "identity_access",
    description: "MFA, access reviews, privileged users, offboarding.",
  },
  {
    value: "cloud_infrastructure",
    description: "Production cloud, backups, logging, network exposure.",
  },
  {
    value: "application_security",
    description: "Code review, dependency risk, secure releases, testing.",
  },
  {
    value: "data_protection",
    description: "Encryption, retention, data flows, privacy safeguards.",
  },
  {
    value: "incident_response",
    description: "Detection, escalation, tabletop exercises, notification.",
  },
  {
    value: "vendor_risk",
    description: "Third-party tools, DPAs, supplier reviews, shared access.",
  },
  {
    value: "people_awareness",
    description: "Security training, phishing, device hygiene, policies.",
  },
  {
    value: "business_resilience",
    description: "Continuity, restore tests, resilience, critical workflows.",
  },
];

const assets: CriticalAsset[] = [
  "customer_data",
  "payment_systems",
  "production_cloud",
  "source_code",
  "employee_devices",
  "third_party_tools",
];

const frameworks = [
  ...frameworkGuides.map((guide) => guide.key),
  "popia",
  "kenya_dpa",
];

const urgencyOptions = [
  { value: "this_month", label: "This month" },
  { value: "this_quarter", label: "This quarter" },
  { value: "this_half", label: "Next 6 months" },
  { value: "exploring", label: "Exploring" },
] as const;

function ToggleCard({
  selected,
  title,
  description,
  icon,
  onClick,
}: {
  selected: boolean;
  title: string;
  description?: string;
  icon?: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full rounded-md border p-3 text-left transition-colors",
        selected
          ? "border-brand-500 bg-brand-50"
          : "border-slate-200 bg-white hover:bg-slate-50",
      )}
    >
      <div className="flex items-start gap-3">
        {icon && <div className="mt-0.5 text-brand-700">{icon}</div>}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-900">{title}</span>
            {selected && <CheckCircle className="h-4 w-4 text-brand-700" />}
          </div>
          {description && (
            <p className="mt-1 text-xs leading-5 text-slate-600">
              {description}
            </p>
          )}
        </div>
      </div>
    </button>
  );
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [objective, setObjective] =
    useState<SecurityObjective>("reduce_breach_risk");
  const [selectedPriorities, setSelectedPriorities] = useState<
    SecurityPriority[]
  >(["identity_access", "data_protection", "incident_response"]);
  const [selectedAssets, setSelectedAssets] = useState<CriticalAsset[]>([
    "customer_data",
    "production_cloud",
  ]);
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([
    "soc2",
    "ndpa",
  ]);
  const [urgency, setUrgency] =
    useState<(typeof urgencyOptions)[number]["value"]>("this_quarter");

  const canSubmit = selectedPriorities.length > 0 && selectedAssets.length > 0;

  const summary = useMemo(() => {
    const topPriority = selectedPriorities[0]
      ? priorityLabels[selectedPriorities[0]]
      : "selected security domains";
    const asset = selectedAssets[0]
      ? assetLabels[selectedAssets[0]]
      : "critical assets";
    return `${objectiveLabels[objective]} across ${asset.toLowerCase()} and ${topPriority.toLowerCase()}.`;
  }, [objective, selectedAssets, selectedPriorities]);

  const selectedGuides = selectedFrameworks
    .map((framework) => getFrameworkGuide(framework))
    .filter((guide): guide is FrameworkGuide => !!guide)
    .slice(0, 2);

  const toggle = <T extends string>(value: T, values: T[], setter: (v: T[]) => void) => {
    setter(
      values.includes(value)
        ? values.filter((item) => item !== value)
        : [...values, value],
    );
  };

  const handleSubmit = () => {
    if (!canSubmit) return;
    saveSecurityProgramProfile(user?.company_id, {
      objective,
      priorities: selectedPriorities,
      assets: selectedAssets,
      targetFrameworks: selectedFrameworks,
      urgency,
      completedAt: new Date().toISOString(),
    });
    navigate("/dashboard", { replace: true });
  };

  return (
    <>
      <PageHeader
        title="Set up your cybersecurity program"
        description="Tell us what you are securing first. Compliance reports still matter, but the workflow starts with cyber risk, assets, threats, and action."
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>1. Primary outcome</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                Pick the business outcome your security work needs to support.
              </p>
            </CardHeader>
            <CardBody className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {objectives.map((item) => (
                <ToggleCard
                  key={item.value}
                  selected={objective === item.value}
                  title={objectiveLabels[item.value]}
                  description={item.description}
                  icon={<Target className="h-4 w-4" />}
                  onClick={() => setObjective(item.value)}
                />
              ))}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>2. Security focus areas</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                Choose the domains that should drive your first roadmap.
              </p>
            </CardHeader>
            <CardBody className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {priorities.map((item) => (
                <ToggleCard
                  key={item.value}
                  selected={selectedPriorities.includes(item.value)}
                  title={priorityLabels[item.value]}
                  description={item.description}
                  icon={
                    item.value === "identity_access" ? (
                      <Fingerprint className="h-4 w-4" />
                    ) : item.value === "data_protection" ? (
                      <LockKeyhole className="h-4 w-4" />
                    ) : item.value === "incident_response" ? (
                      <AlertTriangle className="h-4 w-4" />
                    ) : (
                      <ShieldCheck className="h-4 w-4" />
                    )
                  }
                  onClick={() =>
                    toggle(item.value, selectedPriorities, setSelectedPriorities)
                  }
                />
              ))}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>3. Critical assets and obligations</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                This helps prioritize evidence, policy, roadmap, and report guidance.
              </p>
            </CardHeader>
            <CardBody className="space-y-5">
              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  Critical assets
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {assets.map((asset) => (
                    <ToggleCard
                      key={asset}
                      selected={selectedAssets.includes(asset)}
                      title={assetLabels[asset]}
                      icon={<Database className="h-4 w-4" />}
                      onClick={() =>
                        toggle(asset, selectedAssets, setSelectedAssets)
                      }
                    />
                  ))}
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  Frameworks or customer expectations
                </h3>
                <div className="flex flex-wrap gap-2">
                  {frameworks.map((framework) => {
                    const selected = selectedFrameworks.includes(framework);
                    return (
                      <button
                        key={framework}
                        type="button"
                        onClick={() =>
                          toggle(
                            framework,
                            selectedFrameworks,
                            setSelectedFrameworks,
                          )
                        }
                        className={cn(
                          "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
                          selected
                            ? "border-brand-500 bg-brand-50 text-brand-700"
                            : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
                        )}
                      >
                        {frameworkLabels[framework]}
                      </button>
                    );
                  })}
                </div>
                {selectedGuides.length > 0 && (
                  <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                    {selectedGuides.map((guide) => (
                      <div
                        key={guide.key}
                        className="rounded-md border border-brand-200 bg-brand-50 p-3"
                      >
                        <div className="flex gap-2">
                          <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-brand-700" />
                          <div>
                            <h4 className="text-sm font-semibold text-slate-900">
                              {guide.shortName} in plain English
                            </h4>
                            <p className="mt-1 text-xs leading-5 text-slate-700">
                              {guide.founderSummary}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  Timeline
                </h3>
                <div className="flex flex-wrap gap-2">
                  {urgencyOptions.map((item) => (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() => setUrgency(item.value)}
                      className={cn(
                        "rounded-md border px-3 py-2 text-sm font-medium transition-colors",
                        urgency === item.value
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
                      )}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>Your program brief</CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              <p className="text-sm leading-6 text-slate-700">{summary}</p>
              <div className="flex flex-wrap gap-1.5">
                {selectedPriorities.map((priority) => (
                  <Badge key={priority} variant="brand">
                    {priorityLabels[priority]}
                  </Badge>
                ))}
              </div>
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                <div className="flex gap-2">
                  <FileCheck2 className="mt-0.5 h-4 w-4 text-brand-700" />
                  <p className="text-sm text-slate-700">
                    Next: answer the assessment, receive a risk report, then
                    work the roadmap with evidence, policies, team owners, and
                    shareable security posture reports.
                  </p>
                </div>
              </div>
              <Button
                className="w-full"
                size="lg"
                onClick={handleSubmit}
                disabled={!canSubmit}
              >
                Build my security program
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                className="w-full"
                onClick={() => navigate("/dashboard", { replace: true })}
              >
                Set up later
              </Button>
            </CardBody>
          </Card>
        </div>
      </div>
    </>
  );
}
