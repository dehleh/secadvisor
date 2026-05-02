import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, FileText } from "lucide-react";

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
  SeverityBadge,
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import { useReport, useReports } from "@/hooks/useReports";

export function ReportsListPage() {
  const navigate = useNavigate();
  const { data: reports, isLoading, error } = useReports();

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorMessage message={normalizeApiError(error).message} />;

  if (!reports?.length) {
    return (
      <>
        <PageHeader title="Reports" />
        <Card>
          <CardBody>
            <EmptyState
              icon={<FileText className="h-12 w-12" />}
              title="No reports yet"
              description="Complete an assessment to generate your first AI-tailored report."
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
      <Button
        variant="ghost"
        size="sm"
        className="mb-4"
        onClick={() => navigate("/reports")}
      >
        <ArrowLeft className="h-4 w-4" /> Back to reports
      </Button>

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
    </>
  );
}
