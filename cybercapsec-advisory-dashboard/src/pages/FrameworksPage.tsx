import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileCheck2,
  HelpCircle,
  Layers,
  ListChecks,
  ShieldCheck,
} from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Card, CardBody, CardHeader, CardTitle } from "@/components/UI";
import { useAuth } from "@/context/AuthContext";
import {
  frameworkLabels,
  getSecurityProgramProfile,
  priorityLabels,
} from "@/lib/securityProgram";
import {
  frameworkGuides,
  getDefaultFrameworkGuide,
  getFrameworkGuide,
  type FrameworkGuide,
} from "@/lib/frameworkReadiness";
import { cn } from "@/lib/cn";

const flowSteps = [
  {
    title: "Learn the goal",
    description: "Understand what the framework is really asking for in founder language.",
    icon: BookOpen,
  },
  {
    title: "Assess readiness",
    description: "Answer questions across security domains, not just compliance paperwork.",
    icon: ShieldCheck,
  },
  {
    title: "Work the roadmap",
    description: "Turn gaps into prioritized tasks with owners, effort, and target weeks.",
    icon: ListChecks,
  },
  {
    title: "Prove progress",
    description: "Attach evidence and share a posture story when customers or auditors ask.",
    icon: FileCheck2,
  },
];

const categoryVariants: Record<
  FrameworkGuide["category"],
  "brand" | "info" | "success" | "warning"
> = {
  Certification: "brand",
  "Customer trust": "success",
  "Security baseline": "info",
  Regulatory: "warning",
};

export function FrameworksPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const profile = getSecurityProgramProfile(user?.company_id);
  const defaultGuide = getDefaultFrameworkGuide(profile?.targetFrameworks);
  const [selectedKey, setSelectedKey] = useState(defaultGuide.key);
  const selectedGuide = getFrameworkGuide(selectedKey) ?? defaultGuide;
  const selectedProgramFrameworks =
    profile?.targetFrameworks.filter((key) => frameworkLabels[key]).slice(0, 5) ??
    [];

  return (
    <>
      <PageHeader
        title="Security and framework readiness"
        description="A founder-friendly guide to cybersecurity goals, certification paths, regulatory expectations, evidence, and roadmap work."
        action={
          <Button variant="outline" onClick={() => navigate("/onboarding")}>
            Update program focus
          </Button>
        }
      />

      <div className="mb-6 rounded-lg border border-brand-200 bg-white p-5 shadow-sm">
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.4fr_1fr] lg:items-center">
          <div>
            <Badge variant="brand">Guided readiness</Badge>
            <h2 className="mt-3 text-2xl font-semibold text-slate-900">
              Start with the security goal, then understand the framework.
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
              CyberCapSec-Advisory should help a client say, for example, "I need
              PCI DSS," and immediately see what that means: scope, major risks,
              readiness phases, evidence, owners, and the next task to complete.
            </p>
          </div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-start gap-3">
              <HelpCircle className="mt-0.5 h-5 w-5 text-brand-700" />
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  The product promise
                </h3>
                <p className="mt-1 text-sm leading-6 text-slate-700">
                  No founder should need to decode security jargon before they
                  can take the first correct step.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[320px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Choose a readiness path</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2">
            {frameworkGuides.map((guide) => {
              const selected = guide.key === selectedGuide.key;
              return (
                <button
                  key={guide.key}
                  type="button"
                  onClick={() => setSelectedKey(guide.key)}
                  className={cn(
                    "w-full rounded-md border p-3 text-left transition-colors",
                    selected
                      ? "border-brand-500 bg-brand-50"
                      : "border-slate-200 bg-white hover:bg-slate-50",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-slate-900">
                        {guide.shortName}
                      </div>
                      <p className="mt-1 text-xs leading-5 text-slate-600">
                        {guide.bestFor}
                      </p>
                    </div>
                    {selected && (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-brand-700" />
                    )}
                  </div>
                </button>
              );
            })}
          </CardBody>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge variant={categoryVariants[selectedGuide.category]}>
                    {selectedGuide.category}
                  </Badge>
                  <Badge variant="neutral">{selectedGuide.shortName}</Badge>
                </div>
                <CardTitle>{selectedGuide.name}</CardTitle>
              </div>
              <Button onClick={() => navigate("/assessment")}>
                Assess readiness
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardBody className="space-y-5">
              <p className="text-sm leading-6 text-slate-700">
                {selectedGuide.founderSummary}
              </p>

              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start gap-3">
                    <Layers className="mt-0.5 h-5 w-5 text-brand-700" />
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900">
                        First readiness question
                      </h3>
                      <p className="mt-1 text-sm leading-6 text-slate-700">
                        {selectedGuide.readinessQuestion}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Readiness note
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-700">
                    {selectedGuide.certificationNote}
                  </p>
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  Security domains covered
                </h3>
                <div className="flex flex-wrap gap-2">
                  {selectedGuide.securityDomains.map((domain) => (
                    <Badge key={domain} variant="brand">
                      {priorityLabels[domain]}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  What the client should understand
                </h3>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  {selectedGuide.outcomes.map((outcome) => (
                    <div
                      key={outcome}
                      className="rounded-md border border-slate-200 bg-white p-3"
                    >
                      <div className="flex gap-2">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                        <p className="text-sm leading-6 text-slate-700">
                          {outcome}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Readiness roadmap</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                The client sees the framework as phases, actions, and evidence
                instead of a dense control catalog.
              </p>
            </CardHeader>
            <CardBody className="space-y-4">
              {selectedGuide.phases.map((phase, index) => (
                <div
                  key={phase.title}
                  className="rounded-md border border-slate-200 bg-white p-4"
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="flex gap-3">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                        {index + 1}
                      </span>
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900">
                          {phase.title}
                        </h3>
                        <p className="mt-1 text-sm leading-6 text-slate-700">
                          {phase.goal}
                        </p>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigate("/roadmap")}
                    >
                      Open roadmap
                    </Button>
                  </div>
                  <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Actions
                      </h4>
                      <ul className="mt-2 space-y-2">
                        {phase.actions.map((action) => (
                          <li
                            key={action}
                            className="flex gap-2 text-sm leading-6 text-slate-700"
                          >
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Evidence to collect
                      </h4>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {phase.evidence.map((item) => (
                          <Badge key={item} variant="neutral">
                            {item}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">How CyberCapSec guides it</CardTitle>
              </CardHeader>
              <CardBody className="space-y-3">
                {flowSteps.map((step) => {
                  const Icon = step.icon;
                  return (
                    <div key={step.title} className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700">
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900">
                          {step.title}
                        </h3>
                        <p className="text-sm leading-6 text-slate-600">
                          {step.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Founder mistakes to avoid</CardTitle>
              </CardHeader>
              <CardBody className="space-y-3">
                {selectedGuide.commonTraps.map((trap) => (
                  <div key={trap} className="rounded-md bg-slate-50 p-3">
                    <p className="text-sm leading-6 text-slate-700">{trap}</p>
                  </div>
                ))}
              </CardBody>
            </Card>
          </div>

          {selectedProgramFrameworks.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Frameworks in your program
                </CardTitle>
              </CardHeader>
              <CardBody className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="flex flex-wrap gap-2">
                  {selectedProgramFrameworks.map((framework) => (
                    <Badge key={framework} variant="brand">
                      {frameworkLabels[framework]}
                    </Badge>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate("/evidence")}
                  >
                    Evidence
                  </Button>
                  <Button size="sm" onClick={() => navigate("/roadmap")}>
                    Roadmap
                  </Button>
                </div>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
