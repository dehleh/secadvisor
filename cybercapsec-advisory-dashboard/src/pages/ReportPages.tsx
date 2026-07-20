import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  FileText,
  ListChecks,
  Printer,
  Share2,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import { ShareReportModal } from "@/components/ShareReportModal";
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  ErrorMessage,
  LoadingPage,
  SeverityBadge,
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import { useReport, useReports } from "@/hooks/useReports";
import { frameworkGuides } from "@/lib/frameworkReadiness";
import { describeReadinessScore } from "@/lib/guidedReadiness";

export function ReportsListPage() {
  const navigate = useNavigate();
  const { data: reports, isLoading, error } = useReports();

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorMessage message={normalizeApiError(error).message} />;

  if (!reports?.length) {
    return (
      <>
        <PageHeader
          title="Reports"
          description="See what readiness reports will look like before the first assessment is complete."
        />
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          {[
            "PCI DSS readiness report",
            "SOC 2 readiness report",
            "General cyber posture report",
          ].map((title) => (
            <Card key={title}>
              <CardBody>
                <Badge variant="brand">Sample</Badge>
                <h2 className="mt-3 text-base font-semibold text-slate-900">
                  {title}
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Preview scope, top gaps, roadmap phases, evidence checklist,
                  owner actions, and plain-English readiness notes.
                </p>
                <Button
                  className="mt-4"
                  size="sm"
                  variant="outline"
                  onClick={() => navigate("/learn")}
                >
                  View sample
                </Button>
              </CardBody>
            </Card>
          ))}
        </div>
        <Card>
          <CardBody>
            <EmptyState
              icon={<FileText className="h-12 w-12" />}
              title="No reports yet"
              description="Complete a baseline or assessment to generate your first security posture and framework-readiness report."
              action={
                <Button onClick={() => navigate("/quick-baseline")}>
                  Start quick baseline
                </Button>
              }
            />
          </CardBody>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Reports"
        description="AI-generated security and compliance reports from your assessments."
      />
      <Card className="mb-6 border-brand-200 bg-brand-50/40">
        <CardHeader>
          <CardTitle>Framework readiness reports</CardTitle>
          <p className="mt-1 text-sm text-slate-600">
            Open a framework guide before sharing a report so the client sees
            what PCI DSS, SOC 2, ISO 27001, NIST CSF, CIS Controls, and
            regulatory readiness mean in plain English.
          </p>
        </CardHeader>
        <CardBody className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {frameworkGuides.slice(0, 6).map((guide) => (
            <button
              key={guide.key}
              type="button"
              onClick={() => navigate("/frameworks")}
              className="rounded-md border border-slate-200 bg-white p-3 text-left transition-colors hover:border-brand-300 hover:bg-white"
            >
              <Badge variant="brand">{guide.category}</Badge>
              <h3 className="mt-2 text-sm font-semibold text-slate-900">
                {guide.shortName} readiness
              </h3>
              <p className="mt-1 text-xs leading-5 text-slate-600">
                {guide.bestFor}
              </p>
            </button>
          ))}
        </CardBody>
      </Card>
      <Card>
        <CardBody className="-mx-5 -my-4 divide-y divide-slate-100">
          {reports.map((r) => (
            <button
              key={r.id}
              onClick={() => navigate(`/reports/${r.id}`)}
              className="w-full text-left px-5 py-4 hover:bg-slate-50 transition-colors flex items-start justify-between"
            >
              <div>
                <div className="font-medium text-slate-900">
                  {r.report_type === "initial"
                    ? "Initial Assessment Report"
                    : r.report_type === "reassessment"
                      ? "Reassessment Report"
                      : "Report"}
                </div>
                <div className="text-sm text-slate-500 mt-0.5">
                  Generated {new Date(r.created_at).toLocaleString()}
                </div>
              </div>
              <Badge variant="neutral">{r.report_type}</Badge>
            </button>
          ))}
        </CardBody>
      </Card>
    </>
  );
}

export function ReportDetailPage() {
  const navigate = useNavigate();
  const { reportId = "" } = useParams<{ reportId: string }>();
  const { data: report, isLoading, error } = useReport(reportId);
  const [shareOpen, setShareOpen] = useState(false);

  if (isLoading) return <LoadingPage />;
  if (error || !report) {
    return (
      <ErrorMessage
        message={normalizeApiError(error ?? new Error("Not found")).message}
      />
    );
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4 no-print">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/reports")}
        >
          <ArrowLeft className="h-4 w-4" /> Back to reports
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
          >
            <Printer className="h-4 w-4" /> Download PDF
          </Button>
          <Button size="sm" onClick={() => setShareOpen(true)}>
            <Share2 className="h-4 w-4" /> Share
          </Button>
        </div>
      </div>

      <PageHeader
        title={
          report.report_type === "initial"
            ? "Initial Assessment Report"
            : report.report_type === "reassessment"
              ? "Reassessment Report"
              : "Report"
        }
        description={`Generated ${new Date(report.created_at).toLocaleString()}`}
      />

      <Card className="mb-6 border-brand-200 bg-brand-50/50">
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-brand-800">
              <ShieldCheck className="h-4 w-4" />
              Security action plan
            </div>
            <CardTitle className="mt-1">
              Start with the highest-impact work
            </CardTitle>
            <p className="mt-1 text-sm text-slate-700">
              This report is the diagnosis. The roadmap, evidence vault,
              policies, and team assignments are how you reduce cyber risk.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              onClick={() => navigate("/roadmap")}
            >
              <ListChecks className="h-4 w-4" />
              Start roadmap
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => navigate("/evidence")}
            >
              <UploadCloud className="h-4 w-4" />
              Add evidence
            </Button>
          </div>
        </CardHeader>
        <CardBody className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">
              Top risks to reduce
            </h3>
            <div className="space-y-2">
              {report.risk_register.slice(0, 3).map((risk) => (
                <div
                  key={risk.id}
                  className="rounded-md border border-slate-200 bg-white p-3"
                >
                  <div className="mb-1 flex items-center gap-2">
                    <span className="font-mono text-xs text-slate-500">
                      {risk.id}
                    </span>
                    <SeverityBadge severity={risk.severity} />
                  </div>
                  <div className="text-sm font-medium text-slate-900">
                    {risk.title}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">
              First roadmap actions
            </h3>
            <div className="space-y-2">
              {report.roadmap.slice(0, 3).map((task) => (
                <button
                  key={task.id}
                  type="button"
                  onClick={() => navigate("/roadmap")}
                  className="w-full rounded-md border border-slate-200 bg-white p-3 text-left transition-colors hover:border-brand-300 hover:bg-white"
                >
                  <div className="mb-1 flex items-center gap-2">
                    <Badge variant="neutral">Week {task.week_target}</Badge>
                    <Badge variant="neutral">
                      {task.effort.replace("_", " ")}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-slate-900">
                      {task.title}
                    </span>
                    <ArrowRight className="h-4 w-4 text-brand-700" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Executive summary */}
      {report.executive_summary && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Executive summary</CardTitle>
          </CardHeader>
          <CardBody>
            <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
              {report.executive_summary}
            </p>
          </CardBody>
        </Card>
      )}

      {/* Framework gaps */}
      {Object.keys(report.framework_gaps).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {Object.values(report.framework_gaps).map((g) => (
            <Card key={g.framework}>
              <CardHeader className="flex items-start justify-between gap-2">
                <CardTitle>{g.framework_name}</CardTitle>
                <Badge
                  variant={
                    g.readiness_score >= 70
                      ? "success"
                      : g.readiness_score >= 40
                        ? "warning"
                        : "danger"
                  }
                >
                  {g.readiness_score}/100
                </Badge>
              </CardHeader>
              <CardBody>
                <p className="mb-2 text-sm font-medium text-slate-900">
                  {
                    describeReadinessScore(
                      g.readiness_score,
                      `${g.framework_name} readiness`,
                    ).label
                  }
                </p>
                <p className="text-sm text-slate-700 mb-3">{g.summary}</p>
                {g.top_gaps.length > 0 && (
                  <>
                    <h4 className="text-xs font-semibold text-slate-700 uppercase mb-2">
                      Top gaps
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {g.top_gaps.map((gap) => (
                        <Badge key={gap} variant="neutral">
                          {gap}
                        </Badge>
                      ))}
                    </div>
                  </>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Risk register */}
      {report.risk_register.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>
              Risk register ({report.risk_register.length})
            </CardTitle>
          </CardHeader>
          <CardBody className="-mx-5 -my-4 divide-y divide-slate-100">
            {report.risk_register.map((risk) => (
              <div key={risk.id} className="px-5 py-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-xs text-slate-500">
                    {risk.id}
                  </span>
                  <SeverityBadge severity={risk.severity} />
                  <Badge variant="neutral">{risk.likelihood} likelihood</Badge>
                </div>
                <h4 className="font-semibold text-slate-900">{risk.title}</h4>
                <p className="text-sm text-slate-700 mt-1">
                  {risk.description}
                </p>
                <p className="text-sm text-slate-600 mt-2">
                  <span className="font-medium">Business impact: </span>
                  {risk.business_impact}
                </p>
                {risk.framework_citations.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {risk.framework_citations.map((c, i) => (
                      <Badge key={i} variant="brand">
                        {c.framework} {c.control_code}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      {/* Roadmap snapshot */}
      {report.roadmap.length > 0 && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>13-week roadmap snapshot</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/roadmap")}
            >
              Track in roadmap →
            </Button>
          </CardHeader>
          <CardBody className="-mx-5 -my-4 divide-y divide-slate-100">
            {report.roadmap.map((task) => (
              <div key={task.id} className="px-5 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-slate-500">
                        {task.id}
                      </span>
                      <SeverityBadge severity={task.severity} />
                      <Badge variant="neutral">
                        Week {task.week_target}
                      </Badge>
                      <Badge variant="neutral">
                        {task.effort.replace("_", " ")}
                      </Badge>
                    </div>
                    <div className="text-sm font-medium text-slate-900">
                      {task.title}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      <ShareReportModal
        reportId={reportId}
        open={shareOpen}
        onClose={() => setShareOpen(false)}
      />
    </>
  );
}
