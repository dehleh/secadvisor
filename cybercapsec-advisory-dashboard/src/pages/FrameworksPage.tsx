import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ClipboardList,
  FileCheck2,
  HelpCircle,
  Layers,
  ListChecks,
  MessageSquareText,
  Search,
  ShieldCheck,
  Sparkles,
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
  type FrameworkKey,
} from "@/lib/frameworkReadiness";
import {
  describeReadinessScore,
  draftQuestionnaireAnswer,
  evaluateScopeReadiness,
  evidenceExamples,
  getScopeQuestions,
  glossaryTerms,
  questionnaireSamples,
  readinessGoals,
  type ReadinessGoalKey,
} from "@/lib/guidedReadiness";
import { cn } from "@/lib/cn";
import {
  useGuidedReadiness,
  useSaveGuidedReadiness,
} from "@/hooks/useGuidedReadiness";

const flowSteps = [
  {
    title: "Learn the goal",
    description: "Understand the framework in founder language before starting work.",
    icon: BookOpen,
  },
  {
    title: "Assess readiness",
    description: "Answer scope and security questions that reveal real-world risk.",
    icon: ShieldCheck,
  },
  {
    title: "Work the roadmap",
    description: "Turn gaps into owner-ready tasks by timeline and priority.",
    icon: ListChecks,
  },
  {
    title: "Prove progress",
    description: "Attach evidence and share a plain-English readiness report.",
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

function barColor(score: number) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}

export function FrameworksPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const profile = getSecurityProgramProfile(user?.company_id);
  const { data: guidedProfile } = useGuidedReadiness();
  const saveGuidedReadiness = useSaveGuidedReadiness();
  const defaultGuide = getDefaultFrameworkGuide(profile?.targetFrameworks);
  const [selectedKey, setSelectedKey] = useState<FrameworkKey>(defaultGuide.key);
  const [selectedGoalKey, setSelectedGoalKey] =
    useState<ReadinessGoalKey>("need_pci_dss");
  const [scopeAnswers, setScopeAnswers] = useState<Record<string, string>>({});
  const [questionText, setQuestionText] = useState(questionnaireSamples[2]);
  const [glossarySearch, setGlossarySearch] = useState("");
  const [hydrated, setHydrated] = useState(false);

  const selectedGuide = getFrameworkGuide(selectedKey) ?? defaultGuide;
  const selectedGoal =
    readinessGoals.find((goal) => goal.key === selectedGoalKey) ??
    readinessGoals[0];
  const scopeQuestions = getScopeQuestions(selectedGuide.key);
  const scopeResult = evaluateScopeReadiness(selectedGuide, scopeAnswers);
  const scoreDescription = describeReadinessScore(
    scopeResult.score,
    `${selectedGuide.shortName} readiness`,
  );
  const questionnaireDraft = draftQuestionnaireAnswer(
    questionText,
    selectedGuide,
  );
  const selectedProgramFrameworks =
    profile?.targetFrameworks.filter((key) => frameworkLabels[key]).slice(0, 5) ??
    [];

  const matchingEvidence = useMemo(
    () =>
      evidenceExamples.filter(
        (example) =>
          example.frameworks.includes(selectedGuide.shortName) ||
          selectedGuide.securityDomains.some((domain) =>
            example.domains.includes(domain),
          ),
      ),
    [selectedGuide],
  );

  const filteredGlossary = glossaryTerms.filter((item) => {
    const search = glossarySearch.trim().toLowerCase();
    if (!search) return true;
    return (
      item.term.toLowerCase().includes(search) ||
      item.plainEnglish.toLowerCase().includes(search) ||
      item.founderWhy.toLowerCase().includes(search)
    );
  });

  useEffect(() => {
    if (hydrated || guidedProfile === undefined) return;
    const savedGuide = getFrameworkGuide(guidedProfile?.target_framework);
    const savedGoal = readinessGoals.find(
      (goal) => goal.key === guidedProfile?.selected_goal,
    );
    if (savedGuide) setSelectedKey(savedGuide.key);
    if (savedGoal) setSelectedGoalKey(savedGoal.key);
    if (
      guidedProfile?.scope_answers &&
      Object.keys(guidedProfile.scope_answers).length > 0
    ) {
      setScopeAnswers(guidedProfile.scope_answers as Record<string, string>);
    }
    setHydrated(true);
  }, [guidedProfile, hydrated]);

  const chooseFramework = (key: FrameworkKey) => {
    setSelectedKey(key);
    setScopeAnswers({});
    saveGuidedReadiness.mutate({
      selected_goal: selectedGoalKey,
      target_framework: key,
      scope_answers: {},
    });
  };

  const chooseGoal = (key: ReadinessGoalKey) => {
    const goal = readinessGoals.find((item) => item.key === key);
    if (!goal) return;
    setSelectedGoalKey(goal.key);
    setSelectedKey(goal.recommendedFramework);
    setScopeAnswers({});
    saveGuidedReadiness.mutate({
      selected_goal: goal.key,
      target_framework: goal.recommendedFramework,
      scope_answers: {},
    });
  };

  return (
    <>
      <PageHeader
        title="Security and framework readiness"
        description="A guided workspace for founders who need cybersecurity clarity, PCI DSS readiness, customer trust, regulatory confidence, and evidence-backed progress."
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
              A founder can start with "I need PCI DSS," "a customer sent a
              questionnaire," or "I want to reduce breach risk" and see the
              scope, roadmap, evidence, language, and report needed to move.
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
                  No client should need to decode security jargon before they
                  can take the first correct step.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>1. Start from the client goal</CardTitle>
          <p className="mt-1 text-sm text-slate-600">
            The app recommends a readiness path and first move from the business
            reason, not from a blank control list.
          </p>
        </CardHeader>
        <CardBody className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {readinessGoals.map((goal) => {
            const selected = goal.key === selectedGoal.key;
            return (
              <button
                key={goal.key}
                type="button"
                onClick={() => chooseGoal(goal.key)}
                className={cn(
                  "rounded-md border p-4 text-left transition-colors",
                  selected
                    ? "border-brand-500 bg-brand-50"
                    : "border-slate-200 bg-white hover:bg-slate-50",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">
                      {goal.title}
                    </h3>
                    <p className="mt-1 text-xs leading-5 text-slate-600">
                      {goal.description}
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
                  onClick={() => chooseFramework(guide.key)}
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
                Deep assessment
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardBody className="space-y-5">
              <p className="text-sm leading-6 text-slate-700">
                {selectedGuide.founderSummary}
              </p>

              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-4 lg:col-span-2">
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
                    Recommended first move
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-700">
                    {selectedGoal.firstMove}
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
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>2. Scope wizard</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                {selectedGuide.key === "pci_dss"
                  ? "PCI DSS starts with payment scope. These questions help the client understand the likely shape of the work."
                  : "Every readiness path starts by clarifying systems, data, owners, and evidence."}
              </p>
            </CardHeader>
            <CardBody className="space-y-4">
              {scopeQuestions.map((question) => (
                <div
                  key={question.id}
                  className="rounded-md border border-slate-200 bg-white p-4"
                >
                  <h3 className="text-sm font-semibold text-slate-900">
                    {question.question}
                  </h3>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {question.helper}
                  </p>
                  <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
                    {question.choices.map((choice) => {
                      const selected = scopeAnswers[question.id] === choice.value;
                      return (
                        <button
                          key={choice.value}
                          type="button"
                          onClick={() => {
                            const nextAnswers = {
                              ...scopeAnswers,
                              [question.id]: choice.value,
                            };
                            setScopeAnswers(nextAnswers);
                            saveGuidedReadiness.mutate({
                              selected_goal: selectedGoal.key,
                              target_framework: selectedGuide.key,
                              scope_answers: nextAnswers,
                            });
                          }}
                          className={cn(
                            "rounded-md border p-3 text-left transition-colors",
                            selected
                              ? "border-brand-500 bg-brand-50"
                              : "border-slate-200 bg-slate-50 hover:bg-white",
                          )}
                        >
                          <div className="flex items-start gap-2">
                            {selected && (
                              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-700" />
                            )}
                            <div>
                              <div className="text-sm font-medium text-slate-900">
                                {choice.label}
                              </div>
                              <p className="mt-1 text-xs leading-5 text-slate-600">
                                {choice.guidance}
                              </p>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>3. Plain-English readiness score</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                The score explains why readiness is blocked instead of showing a
                lonely percentage.
              </p>
            </CardHeader>
            <CardBody>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-[220px_1fr] lg:items-center">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-center">
                  <div className="text-4xl font-bold text-slate-900">
                    {scopeResult.score}
                  </div>
                  <div className="mt-1 text-sm font-medium text-slate-700">
                    {scopeResult.label}
                  </div>
                  <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={cn("h-full rounded-full", barColor(scopeResult.score))}
                      style={{ width: `${scopeResult.score}%` }}
                    />
                  </div>
                </div>
                <div className="space-y-3">
                  <Badge
                    variant={
                      scoreDescription.tone === "success"
                        ? "success"
                        : scoreDescription.tone === "warning"
                          ? "warning"
                          : scoreDescription.tone === "danger"
                            ? "danger"
                            : "neutral"
                    }
                  >
                    {scoreDescription.label}
                  </Badge>
                  <p className="text-sm leading-6 text-slate-700">
                    {scopeResult.summary}
                  </p>
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Next actions
                      </h4>
                      <ul className="mt-2 space-y-2">
                        {scopeResult.nextSteps.map((step) => (
                          <li key={step} className="flex gap-2 text-sm text-slate-700">
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                            {step}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Evidence to prepare
                      </h4>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {scopeResult.evidence.map((item) => (
                          <Badge key={item} variant="neutral">
                            {item}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>4. Quick baseline or deep assessment</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                A founder can start light, then move into the full security
                assessment when they are ready.
              </p>
            </CardHeader>
            <CardBody className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-md border border-slate-200 bg-white p-4">
                <div className="flex gap-3">
                  <Sparkles className="mt-0.5 h-5 w-5 text-brand-700" />
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">
                      5-minute quick baseline
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      Identify the first security gaps without forcing the full
                      assessment journey.
                    </p>
                    <Button
                      className="mt-3"
                      size="sm"
                      onClick={() => navigate("/quick-baseline")}
                    >
                      Start quick baseline
                    </Button>
                  </div>
                </div>
              </div>
              <div className="rounded-md border border-slate-200 bg-white p-4">
                <div className="flex gap-3">
                  <ClipboardList className="mt-0.5 h-5 w-5 text-brand-700" />
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">
                      Full cybersecurity assessment
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      Generate the deeper risk register, roadmap, evidence plan,
                      and reports.
                    </p>
                    <Button
                      className="mt-3"
                      size="sm"
                      variant="outline"
                      onClick={() => navigate("/assessment")}
                    >
                      Open deep assessment
                    </Button>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>5. Framework readiness report</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                Each framework gets its own plain-English report before the
                client shares a formal posture report.
              </p>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <Badge variant={categoryVariants[selectedGuide.category]}>
                      {selectedGuide.category}
                    </Badge>
                    <h3 className="mt-2 text-lg font-semibold text-slate-900">
                      {selectedGuide.shortName} readiness report
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-700">
                      {selectedGuide.certificationNote}
                    </p>
                  </div>
                  <Button variant="outline" onClick={() => navigate("/reports")}>
                    Reports
                  </Button>
                </div>
                <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
                  {selectedGuide.outcomes.map((outcome) => (
                    <div key={outcome} className="rounded-md bg-white p-3">
                      <p className="text-sm leading-6 text-slate-700">{outcome}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">
                    Readiness phases
                  </h4>
                  <div className="mt-3 space-y-3">
                    {selectedGuide.phases.map((phase, index) => (
                      <div key={phase.title} className="flex gap-3">
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                          {index + 1}
                        </span>
                        <div>
                          <h5 className="text-sm font-medium text-slate-900">
                            {phase.title}
                          </h5>
                          <p className="text-sm leading-6 text-slate-600">
                            {phase.goal}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">
                    Common traps
                  </h4>
                  <div className="mt-3 space-y-2">
                    {selectedGuide.commonTraps.map((trap) => (
                      <div key={trap} className="rounded-md bg-white p-3">
                        <p className="text-sm leading-6 text-slate-700">{trap}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>6. Evidence examples</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                Show clients what proof looks like before they upload anything.
              </p>
            </CardHeader>
            <CardBody className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {matchingEvidence.slice(0, 6).map((example) => (
                <div
                  key={example.title}
                  className="rounded-md border border-slate-200 bg-white p-4"
                >
                  <h3 className="text-sm font-semibold text-slate-900">
                    {example.title}
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {example.description}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {example.frameworks.slice(0, 3).map((framework) => (
                      <Badge key={framework} variant="neutral">
                        {framework}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>7. Questionnaire assistant</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                Draft customer-security answers from the selected framework,
                evidence expectations, and roadmap language.
              </p>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {questionnaireSamples.map((sample) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => setQuestionText(sample)}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    {sample}
                  </button>
                ))}
              </div>
              <label className="block">
                <span className="text-sm font-medium text-slate-900">
                  Customer question
                </span>
                <textarea
                  className="mt-2 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  value={questionText}
                  onChange={(event) => setQuestionText(event.target.value)}
                />
              </label>
              <div className="rounded-md border border-brand-200 bg-brand-50 p-4">
                <div className="flex gap-3">
                  <MessageSquareText className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" />
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">
                      Draft answer
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-700">
                      {questionnaireDraft.answer}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {questionnaireDraft.evidence.map((item) => (
                        <Badge key={item} variant="brand">
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>8. Founder security glossary</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                Security terms explained in the language of business decisions.
              </p>
            </CardHeader>
            <CardBody className="space-y-4">
              <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
                <Search className="h-4 w-4 text-slate-400" />
                <input
                  className="w-full border-0 bg-transparent text-sm outline-none"
                  placeholder="Search glossary"
                  value={glossarySearch}
                  onChange={(event) => setGlossarySearch(event.target.value)}
                />
              </label>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {filteredGlossary.map((item) => (
                  <div
                    key={item.term}
                    className="rounded-md border border-slate-200 bg-white p-4"
                  >
                    <h3 className="text-sm font-semibold text-slate-900">
                      {item.term}
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      {item.plainEnglish}
                    </p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">
                      Founder relevance: {item.founderWhy}
                    </p>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">9. How CyberCapSec guides it</CardTitle>
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
                <CardTitle className="text-base">10. Connected next steps</CardTitle>
              </CardHeader>
              <CardBody className="space-y-3">
                <p className="text-sm leading-6 text-slate-700">
                  The guide is connected to quick baseline, full assessment,
                  roadmap, evidence, policies, team owners, and shareable
                  reports so readiness becomes an operating flow.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={() => navigate("/roadmap")}>
                    Roadmap
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate("/evidence")}
                  >
                    Evidence
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate("/reports")}
                  >
                    Reports
                  </Button>
                </div>
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
                <Button size="sm" onClick={() => navigate("/onboarding")}>
                  Update selected frameworks
                </Button>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
