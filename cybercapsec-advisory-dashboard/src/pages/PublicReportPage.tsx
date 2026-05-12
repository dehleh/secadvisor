import { useParams } from "react-router-dom";

import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  LoadingPage,
  SeverityBadge,
} from "@/components/UI";
import { Button } from "@/components/Button";
import { normalizeApiError } from "@/api";
import { usePublicReport } from "@/hooks/useShares";

export function PublicReportPage() {
  const { token = "" } = useParams<{ token: string }>();
  const { data: report, isLoading, error } = usePublicReport(token);

  if (isLoading) return <LoadingPage />;
  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center">
          <img
            src="/logo.png"
            alt="CyberCapSec"
            className="h-12 w-12 mx-auto mb-4"
          />
          <h1 className="text-xl font-semibold text-slate-900 mb-2">
            Link unavailable
          </h1>
          <p className="text-sm text-slate-600">
            {normalizeApiError(error ?? new Error("Not found")).message}
          </p>
          <p className="text-xs text-slate-500 mt-4">
            This share link may have been revoked or expired. Please contact
            the company that shared it with you.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Branded header */}
      <header className="bg-white border-b border-slate-200 print:border-none">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="CyberCapSec" className="h-9 w-9" />
            <div>
              <div className="font-semibold text-slate-900 text-sm">
                CyberCapSec Advisory
              </div>
              <div className="text-xs text-slate-500">
                Read-only shared report
              </div>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => window.print()}
            className="print:hidden"
          >
            Print / save as PDF
          </Button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 print:py-2">
        {/* Cover */}
        <div className="mb-8 print:mb-4">
          <div className="text-xs uppercase tracking-wide text-brand-700 font-semibold mb-2">
            {report.company_name}
          </div>
          <h1 className="text-3xl font-bold text-slate-900">
            Security &amp; Compliance Report
          </h1>
          {report.label && (
            <p className="text-sm text-slate-600 mt-1">{report.label}</p>
          )}
          <p className="text-sm text-slate-500 mt-2">
            Generated {new Date(report.generated_at).toLocaleString()}
          </p>

          {/* Score grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
            <ScoreCard
              label="Overall risk posture"
              score={report.overall_risk_score}
              hint="Higher is better"
            />
            <ScoreCard
              label="SOC 2 readiness"
              score={report.soc2_readiness_score}
            />
            <ScoreCard
              label="NDPA compliance"
              score={report.ndpa_compliance_score}
            />
          </div>
        </div>

        {/* Executive summary */}
        {report.executive_summary && (
          <Card className="mb-6 print:break-inside-avoid">
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
              <Card key={g.framework} className="print:break-inside-avoid">
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
                <div
                  key={risk.id}
                  className="px-5 py-4 print:break-inside-avoid"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-xs text-slate-500">
                      {risk.id}
                    </span>
                    <SeverityBadge severity={risk.severity} />
                    <Badge variant="neutral">
                      {risk.likelihood} likelihood
                    </Badge>
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

        {/* Roadmap */}
        {report.roadmap.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>13-week roadmap</CardTitle>
            </CardHeader>
            <CardBody className="-mx-5 -my-4 divide-y divide-slate-100">
              {report.roadmap.map((task) => (
                <div
                  key={task.id}
                  className="px-5 py-3 print:break-inside-avoid"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-slate-500">
                      {task.id}
                    </span>
                    <SeverityBadge severity={task.severity} />
                    <Badge variant="neutral">Week {task.week_target}</Badge>
                    <Badge variant="neutral">
                      {task.effort.replace("_", " ")}
                    </Badge>
                  </div>
                  <div className="text-sm font-medium text-slate-900">
                    {task.title}
                  </div>
                  <div className="text-sm text-slate-600 mt-1">
                    {task.description}
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>
        )}

        <footer className="mt-10 pt-6 border-t border-slate-200 text-xs text-slate-500 text-center print:mt-4">
          <div>
            Generated by{" "}
            <a
              href="https://advisory.cybercapsec.com"
              className="text-brand-700 font-medium"
            >
              CyberCapSec Advisory
            </a>
            . This report is read-only. Confidential.
          </div>
        </footer>
      </main>
    </div>
  );
}

function ScoreCard({
  label,
  score,
  hint,
}: {
  label: string;
  score: number | null;
  hint?: string;
}) {
  const display = score === null || score === undefined ? "—" : `${score}/100`;
  const tone =
    score === null || score === undefined
      ? "text-slate-400"
      : score >= 70
        ? "text-emerald-600"
        : score >= 40
          ? "text-amber-600"
          : "text-red-600";
  return (
    <Card className="print:break-inside-avoid">
      <CardBody>
        <div className="text-xs uppercase tracking-wide text-slate-500 font-semibold">
          {label}
        </div>
        <div className={`text-3xl font-bold mt-2 ${tone}`}>{display}</div>
        {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
      </CardBody>
    </Card>
  );
}
