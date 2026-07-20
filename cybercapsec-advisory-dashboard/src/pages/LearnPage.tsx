import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  CreditCard,
  FileText,
  GraduationCap,
  ShieldCheck,
} from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Card, CardBody, CardHeader, CardTitle } from "@/components/UI";
import { evidenceExamples, glossaryTerms } from "@/lib/guidedReadiness";
import { frameworkGuides } from "@/lib/frameworkReadiness";

const lessons = [
  {
    title: "Readiness is not certification",
    body: "Readiness means you understand scope, gaps, evidence, owners, and remaining work. Certification or validation comes from the relevant auditor, assessor, payment partner, or regulator.",
    icon: GraduationCap,
  },
  {
    title: "PCI DSS starts with payment scope",
    body: "Before collecting evidence, understand where cardholder data enters, moves, gets stored, appears in logs, or can be accessed.",
    icon: CreditCard,
  },
  {
    title: "Security posture is the story of your controls",
    body: "A strong posture report explains risk, roadmap progress, evidence, policies, exceptions, and what customers can trust today.",
    icon: ShieldCheck,
  },
];

const sampleReports = [
  {
    title: "PCI DSS readiness report",
    summary:
      "Payment scope, card-data exposure, access hardening, logging, vulnerability management, incident response, evidence gaps, and validation next steps.",
    sections: ["Scope", "Top payment risks", "Evidence checklist", "Validation notes"],
  },
  {
    title: "SOC 2 readiness report",
    summary:
      "Customer trust controls across access, change management, vendors, incidents, monitoring, resilience, policies, and evidence history.",
    sections: ["Trust story", "Control gaps", "Evidence maturity", "Roadmap"],
  },
  {
    title: "General cyber posture report",
    summary:
      "A plain-English view of cyber risks, prioritized actions, owners, and the proof available for customers, investors, and leadership.",
    sections: ["Executive summary", "Top risks", "Owner actions", "Proof status"],
  },
];

export function LearnPage() {
  const navigate = useNavigate();

  return (
    <>
      <PageHeader
        title="Founder education hub"
        description="Learn the security concepts behind readiness, evidence, frameworks, customer questionnaires, and posture reports."
        action={
          <Button onClick={() => navigate("/frameworks")}>
            Framework guides
            <ArrowRight className="h-4 w-4" />
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {lessons.map((lesson) => {
          const Icon = lesson.icon;
          return (
            <Card key={lesson.title}>
              <CardBody>
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-brand-100 text-brand-700">
                  <Icon className="h-5 w-5" />
                </div>
                <h2 className="mt-4 text-base font-semibold text-slate-900">
                  {lesson.title}
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {lesson.body}
                </p>
              </CardBody>
            </Card>
          );
        })}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Sample readiness reports</CardTitle>
          <p className="mt-1 text-sm text-slate-600">
            These are the outputs clients should expect before they commit more
            time or money.
          </p>
        </CardHeader>
        <CardBody className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {sampleReports.map((report) => (
            <div
              key={report.title}
              className="rounded-md border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-brand-700" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {report.title}
                </h3>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {report.summary}
              </p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {report.sections.map((section) => (
                  <Badge key={section} variant="neutral">
                    {section}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </CardBody>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Framework comparison</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            {frameworkGuides.slice(0, 6).map((guide) => (
              <div
                key={guide.key}
                className="rounded-md border border-slate-200 bg-white p-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold text-slate-900">
                    {guide.shortName}
                  </h3>
                  <Badge variant="brand">{guide.category}</Badge>
                </div>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {guide.bestFor}
                </p>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Glossary</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            {glossaryTerms.slice(0, 8).map((term) => (
              <div key={term.term} className="rounded-md bg-slate-50 p-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-brand-700" />
                  <h3 className="text-sm font-semibold text-slate-900">
                    {term.term}
                  </h3>
                </div>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {term.plainEnglish}
                </p>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Evidence examples customers understand</CardTitle>
        </CardHeader>
        <CardBody className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          {evidenceExamples.slice(0, 8).map((example) => (
            <div
              key={example.title}
              className="rounded-md border border-slate-200 bg-white p-3"
            >
              <h3 className="text-sm font-semibold text-slate-900">
                {example.title}
              </h3>
              <p className="mt-1 text-xs leading-5 text-slate-600">
                {example.description}
              </p>
            </div>
          ))}
        </CardBody>
      </Card>
    </>
  );
}
