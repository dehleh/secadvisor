import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  ClipboardCheck,
  FileCheck2,
  ListChecks,
  ShieldCheck,
  Sparkles,
  Target,
  UploadCloud,
  Zap,
} from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  ErrorMessage,
  LoadingPage,
  ScoreRing,
  SeverityBadge,
} from "@/components/UI";
import { useAuth } from "@/context/AuthContext";
import { useAssessments } from "@/hooks/useAssessments";
import { useCoverageMatrix } from "@/hooks/useEvidence";
import { usePolicies } from "@/hooks/usePolicies";
import { useReports } from "@/hooks/useReports";
import { useReport } from "@/hooks/useReports";
import { useRoadmapProgress } from "@/hooks/useRoadmap";
import { normalizeApiError } from "@/api";
import {
  assetLabels,
  frameworkLabels,
  getSecurityProgramProfile,
  objectiveLabels,
  priorityLabels,
} from "@/lib/securityProgram";
import { describeReadinessScore } from "@/lib/guidedReadiness";

interface NextAction {
  title: string;
  description: string;
  to: string;
  cta: string;
  icon: ReactNode;
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const reportsQuery = useReports();
  const assessmentsQuery = useAssessments();
  const progressQuery = useRoadmapProgress();
  const coverageQuery = useCoverageMatrix();
  const policiesQuery = usePolicies();

  const latestReportId = reportsQuery.data?.[0]?.id ?? null;
  const reportQuery = useReport(latestReportId);
  const profile = getSecurityProgramProfile(user?.company_id);

  if (
    reportsQuery.isLoading ||
    assessmentsQuery.isLoading ||
    progressQuery.isLoading ||
    policiesQuery.isLoading
  ) {
    return <LoadingPage />;
  }

  const error =
    reportsQuery.error ||
    assessmentsQuery.error ||
    progressQuery.error ||
    policiesQuery.error;
  if (error) {
    return <ErrorMessage message={normalizeApiError(error).message} />;
  }

  // First-run state — no assessments yet
  if (!assessmentsQuery.data?.length) {
    return (
      <>
        <PageHeader
          title={`Welcome${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
          description="Start with the security program you need, then run the assessment to turn it into a risk-ranked action plan."
        />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2">
            <CardBody>
              <EmptyState
                icon={<ClipboardCheck className="h-12 w-12" />}
                title="Build your cyber baseline"
                description="The 15-20 minute assessment covers identity, infrastructure, application security, data protection, vendors, people, resilience, and compliance readiness."
                action={
                  <div className="flex flex-col justify-center gap-2 sm:flex-row">
                    <Button
                      onClick={() =>
                        navigate(profile ? "/assessment" : "/onboarding")
                      }
                      size="lg"
                    >
                      {profile ? "Start your first assessment" : "Set up program"}
                    </Button>
                    <Button
                      onClick={() => navigate("/quick-baseline")}
                      size="lg"
                      variant="outline"
                    >
                      <Zap className="h-4 w-4" />
                      5-minute baseline
                    </Button>
                  </div>
                }
              />
            </CardBody>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">What happens next</CardTitle>
            </CardHeader>
            <CardBody className="space-y-3 text-sm text-slate-700">
              <div className="flex gap-2">
                <Badge variant="brand">1</Badge>
                <span>Define your cybersecurity priorities and critical assets.</span>
              </div>
              <div className="flex gap-2">
                <Badge variant="brand">2</Badge>
                <span>Answer the assessment to generate risks and a roadmap.</span>
              </div>
              <div className="flex gap-2">
                <Badge variant="brand">3</Badge>
                <span>Add evidence, publish policies, assign owners, and share reports.</span>
              </div>
            </CardBody>
          </Card>
        </div>
      </>
    );
  }

  const completedAssessment = assessmentsQuery.data.find(
    (a) => a.status === "completed",
  );
  const activeAssessment = assessmentsQuery.data.find(
    (a) => a.status === "draft" || a.status === "in_progress",
  );
  const report = reportQuery.data;
  const progress = progressQuery.data;
  const coverage = coverageQuery.data?.coverage ?? {};
  const policies = policiesQuery.data ?? [];
  const coverageCount = Object.values(coverage).reduce(
    (sum, controls) => sum + controls.length,
    0,
  );
  const postureDescription = describeReadinessScore(
    completedAssessment?.overall_risk_score,
    "overall cybersecurity posture",
  );
  const nextAction: NextAction = !profile
    ? {
        title: "Set up your security program",
        description:
          "Choose the cyber outcomes, assets, and risk areas that should drive your roadmap.",
        to: "/onboarding",
        cta: "Set up program",
        icon: <Target className="h-5 w-5" />,
      }
            : activeAssessment
      ? {
          title: "Finish the posture assessment",
          description:
            "Complete the remaining questions so the app can generate your risk report and action plan.",
          to: "/assessment",
          cta: "Continue assessment",
                icon: <ClipboardCheck className="h-5 w-5" />,
              }
      : !completedAssessment
        ? {
            title: "Run your first cybersecurity assessment",
            description:
              "Measure identity, cloud, app security, data protection, people, vendors, and response readiness.",
            to: "/assessment",
            cta: "Start assessment",
            icon: <ClipboardCheck className="h-5 w-5" />,
          }
        : !report
          ? {
              title: "Generate your security report",
              description:
                "Submit a completed assessment to turn answers into risks, priorities, and a roadmap.",
              to: "/assessment",
              cta: "Open assessment",
              icon: <ShieldCheck className="h-5 w-5" />,
            }
          : progress && progress.total > 0 && progress.done === 0
            ? {
                title: "Start the first roadmap task",
                description:
                  "Move one high-impact security task into progress and assign evidence as you go.",
                to: "/roadmap",
                cta: "Start roadmap",
                icon: <ListChecks className="h-5 w-5" />,
              }
            : coverageCount === 0
              ? {
                  title: "Add evidence for your top controls",
                  description:
                    "Attach screenshots, links, policies, or narratives to prove the controls are real.",
                  to: "/evidence",
                  cta: "Add evidence",
                  icon: <UploadCloud className="h-5 w-5" />,
                }
              : policies.length === 0
                ? {
                    title: "Generate core security policies",
                    description:
                      "Create the starter pack for access, incident response, vendor risk, data protection, and more.",
                    to: "/policies",
                    cta: "Generate policies",
                    icon: <FileCheck2 className="h-5 w-5" />,
                  }
                : {
                    title: "Share your security posture",
                    description:
                      "Create a read-only report link for auditors, enterprise customers, investors, or partners.",
                    to: latestReportId ? `/reports/${latestReportId}` : "/reports",
                    cta: "Open report",
                    icon: <Sparkles className="h-5 w-5" />,
                  };

  return (
    <>
      <PageHeader
        title={`Welcome${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
        description="Your cybersecurity posture, actions, evidence, and compliance readiness in one place."
        action={
          <Button variant="outline" onClick={() => navigate("/assessment")}>
            New assessment
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <Card className="lg:col-span-2 border-brand-200 bg-brand-50/50">
          <CardBody className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-brand-600 text-white">
                {nextAction.icon}
              </div>
              <div>
                <div className="text-sm font-semibold text-brand-900">
                  Next best action
                </div>
                <h2 className="mt-1 text-xl font-semibold text-slate-900">
                  {nextAction.title}
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-700">
                  {nextAction.description}
                </p>
              </div>
            </div>
            <Button
              className="shrink-0"
              onClick={() => navigate(nextAction.to)}
            >
              {nextAction.cta}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Program focus</CardTitle>
          </CardHeader>
          <CardBody>
            {profile ? (
              <div className="space-y-3">
                <p className="text-sm text-slate-700">
                  {objectiveLabels[profile.objective]}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {profile.priorities.slice(0, 3).map((priority) => (
                    <Badge key={priority} variant="brand">
                      {priorityLabels[priority]}
                    </Badge>
                  ))}
                </div>
                <div className="text-xs text-slate-500">
                  Securing{" "}
                  {profile.assets
                    .slice(0, 2)
                    .map((asset) => assetLabels[asset].toLowerCase())
                    .join(", ")}
                </div>
                {profile.targetFrameworks.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {profile.targetFrameworks.slice(0, 3).map((framework) => (
                      <Badge key={framework} variant="neutral">
                        {frameworkLabels[framework] ?? framework}
                      </Badge>
                    ))}
                  </div>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/frameworks")}
                >
                  <BookOpen className="h-4 w-4" />
                  Open guides
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-slate-600">
                  Set up your program to tailor recommendations beyond compliance.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/onboarding")}
                >
                  Configure focus
                </Button>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Score cards */}
      {completedAssessment && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardBody className="flex flex-col items-center justify-center text-center">
              <ScoreRing
                score={completedAssessment.overall_risk_score ?? 0}
                label="Overall posture"
              />
              <p className="mt-3 text-sm font-medium text-slate-900">
                {postureDescription.label}
              </p>
              <p className="mt-1 max-w-xs text-sm leading-6 text-slate-600">
                {postureDescription.summary}
              </p>
            </CardBody>
          </Card>
          <Card>
            <CardBody className="flex flex-col items-center justify-center text-center">
              <ScoreRing
                score={completedAssessment.soc2_readiness_score ?? 0}
                label="SOC 2 readiness"
              />
            </CardBody>
          </Card>
          <Card>
            <CardBody className="flex flex-col items-center justify-center text-center">
              <ScoreRing
                score={completedAssessment.ndpa_compliance_score ?? 0}
                label="NDPA compliance"
              />
            </CardBody>
          </Card>
        </div>
      )}

      {/* Roadmap progress + coverage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Roadmap progress</CardTitle>
          </CardHeader>
          <CardBody>
            {progress && progress.total > 0 ? (
              <>
                <div className="flex items-end justify-between mb-3">
                  <div>
                    <div className="text-3xl font-bold text-slate-900">
                      {progress.completion_pct}%
                    </div>
                    <div className="text-sm text-slate-600">
                      {progress.done} of {progress.total} tasks complete
                    </div>
                  </div>
                  <Link
                    to="/roadmap"
                    className="text-sm font-medium text-brand-600 hover:text-brand-700"
                  >
                    View roadmap →
                  </Link>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-brand-500 to-brand-600 transition-all"
                    style={{ width: `${progress.completion_pct}%` }}
                  />
                </div>
                <div className="grid grid-cols-4 gap-3 mt-4 text-center">
                  <div>
                    <div className="text-lg font-semibold text-slate-900">
                      {progress.todo}
                    </div>
                    <div className="text-xs text-slate-500">To do</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-sky-600">
                      {progress.in_progress}
                    </div>
                    <div className="text-xs text-slate-500">In progress</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-amber-600">
                      {progress.blocked}
                    </div>
                    <div className="text-xs text-slate-500">Blocked</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-emerald-600">
                      {progress.done}
                    </div>
                    <div className="text-xs text-slate-500">Done</div>
                  </div>
                </div>
                {progress.overdue > 0 && (
                  <div className="mt-3 flex items-center gap-2 text-sm text-amber-700">
                    <AlertTriangle className="h-4 w-4" />
                    {progress.overdue} overdue{" "}
                    {progress.overdue === 1 ? "task" : "tasks"}
                  </div>
                )}
              </>
            ) : (
              <EmptyState
                icon={<ListChecks className="h-12 w-12" />}
                title="No roadmap yet"
                description="Complete an assessment to get a 13-week roadmap."
              />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Framework coverage</CardTitle>
          </CardHeader>
          <CardBody>
            {Object.keys(coverage).length === 0 ? (
              <p className="text-sm text-slate-500">
                Submit evidence to see framework coverage.
              </p>
            ) : (
              <ul className="space-y-2">
                {Object.entries(coverage).map(([fw, controls]) => (
                  <li
                    key={fw}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="font-medium text-slate-700 uppercase">
                      {fw}
                    </span>
                    <Badge variant="brand">{controls.length} controls</Badge>
                  </li>
                ))}
              </ul>
            )}
            <Link
              to="/evidence"
              className="block text-sm font-medium text-brand-600 hover:text-brand-700 mt-3"
            >
              Manage evidence →
            </Link>
            <Link
              to="/frameworks"
              className="block text-sm font-medium text-brand-600 hover:text-brand-700 mt-2"
            >
              Read framework guides →
            </Link>
          </CardBody>
        </Card>
      </div>

      {/* Top risks */}
      {report && report.risk_register.length > 0 && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Top risks</CardTitle>
            <Link
              to="/reports"
              className="text-sm font-medium text-brand-600 hover:text-brand-700"
            >
              Full report →
            </Link>
          </CardHeader>
          <CardBody className="divide-y divide-slate-100 -mx-5 -my-4">
            {report.risk_register.slice(0, 5).map((risk) => (
              <div key={risk.id} className="px-5 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-slate-500">
                        {risk.id}
                      </span>
                      <SeverityBadge severity={risk.severity} />
                    </div>
                    <div className="text-sm font-medium text-slate-900">
                      {risk.title}
                    </div>
                    {risk.framework_citations.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {risk.framework_citations.map((c, i) => (
                          <Badge key={i} variant="neutral">
                            {c.framework} {c.control_code}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}
    </>
  );
}
