import { Link, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ClipboardCheck,
  ListChecks,
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
import { useReports } from "@/hooks/useReports";
import { useReport } from "@/hooks/useReports";
import { useRoadmapProgress } from "@/hooks/useRoadmap";
import { normalizeApiError } from "@/api";

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const reportsQuery = useReports();
  const assessmentsQuery = useAssessments();
  const progressQuery = useRoadmapProgress();
  const coverageQuery = useCoverageMatrix();

  const latestReportId = reportsQuery.data?.[0]?.id ?? null;
  const reportQuery = useReport(latestReportId);

  if (
    reportsQuery.isLoading ||
    assessmentsQuery.isLoading ||
    progressQuery.isLoading
  ) {
    return <LoadingPage />;
  }

  const error =
    reportsQuery.error ||
    assessmentsQuery.error ||
    progressQuery.error;
  if (error) {
    return <ErrorMessage message={normalizeApiError(error).message} />;
  }

  // First-run state — no assessments yet
  if (!assessmentsQuery.data?.length) {
    return (
      <>
        <PageHeader
          title={`Welcome${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
          description="Run your first assessment to get a tailored security and compliance roadmap."
        />
        <Card>
          <CardBody>
            <EmptyState
              icon={<ClipboardCheck className="h-12 w-12" />}
              title="No assessments yet"
              description="The 15-20 minute assessment generates an AI-tailored risk register, 13-week roadmap, and per-framework gap analysis. Let's start."
              action={
                <Button onClick={() => navigate("/assessment")} size="lg">
                  Start your first assessment
                </Button>
              }
            />
          </CardBody>
        </Card>
      </>
    );
  }

  const completedAssessment = assessmentsQuery.data.find(
    (a) => a.status === "completed",
  );
  const report = reportQuery.data;
  const progress = progressQuery.data;
  const coverage = coverageQuery.data?.coverage ?? {};

  return (
    <>
      <PageHeader
        title={`Welcome${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
        description="Your security and compliance posture at a glance."
        action={
          <Button variant="outline" onClick={() => navigate("/assessment")}>
            New assessment
          </Button>
        }
      />

      {/* Score cards */}
      {completedAssessment && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardBody className="flex flex-col items-center justify-center text-center">
              <ScoreRing
                score={completedAssessment.overall_risk_score ?? 0}
                label="Overall posture"
              />
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
