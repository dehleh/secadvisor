import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles } from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Card, CardBody, CardHeader, CardTitle } from "@/components/UI";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/cn";
import { priorityLabels } from "@/lib/securityProgram";
import {
  baselineQuestions,
  evaluateQuickBaseline,
  type BaselineAnswer,
} from "@/lib/guidedReadiness";
import {
  useGuidedReadiness,
  useSaveGuidedReadiness,
} from "@/hooks/useGuidedReadiness";

const answerOptions: Array<{
  value: BaselineAnswer;
  label: string;
  description: string;
}> = [
  {
    value: "yes",
    label: "Yes",
    description: "Implemented and can be evidenced.",
  },
  {
    value: "partial",
    label: "Partly",
    description: "Started, but inconsistent or missing proof.",
  },
  {
    value: "no",
    label: "No",
    description: "Not implemented yet.",
  },
  {
    value: "not_sure",
    label: "Not sure",
    description: "Needs investigation.",
  },
];

function storageKey(companyId: string | null | undefined) {
  return companyId
    ? `ccs.quick_baseline.${companyId}`
    : "ccs.quick_baseline";
}

function loadAnswers(companyId: string | null | undefined) {
  if (typeof window === "undefined") return {};
  const raw = window.localStorage.getItem(storageKey(companyId));
  if (!raw) return {};
  try {
    return JSON.parse(raw) as Record<string, BaselineAnswer>;
  } catch {
    return {};
  }
}

export function QuickBaselinePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data: guidedProfile } = useGuidedReadiness();
  const {
    mutate: saveGuidedProfile,
    isPending: isSavingGuidedProfile,
  } = useSaveGuidedReadiness();
  const [hydrated, setHydrated] = useState(false);
  const [answers, setAnswers] = useState<Record<string, BaselineAnswer>>(() =>
    loadAnswers(user?.company_id),
  );
  const result = useMemo(() => evaluateQuickBaseline(answers), [answers]);
  const answeredCount = Object.keys(answers).length;

  useEffect(() => {
    if (hydrated) return;
    const saved = guidedProfile?.baseline_answers as
      | Record<string, BaselineAnswer>
      | undefined;
    if (saved && Object.keys(saved).length > 0 && Object.keys(answers).length === 0) {
      setAnswers(saved);
    }
    if (guidedProfile !== undefined) setHydrated(true);
  }, [answers, guidedProfile, hydrated]);

  useEffect(() => {
    if (Object.keys(answers).length === 0) return;
    window.localStorage.setItem(storageKey(user?.company_id), JSON.stringify(answers));
    saveGuidedProfile({
      baseline_answers: answers,
      selected_goal: guidedProfile?.selected_goal ?? "reduce_breach_risk",
    });
  }, [answers, guidedProfile?.selected_goal, saveGuidedProfile, user?.company_id]);

  return (
    <>
      <PageHeader
        title="5-minute cybersecurity baseline"
        description="A founder-friendly first scan across identity, cloud, apps, data, vendors, incidents, people, and resilience."
        action={
          <Button variant="outline" onClick={() => navigate("/assessment")}>
            Full assessment
          </Button>
        }
      />

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        <Card>
          <CardBody className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-brand-100 text-brand-700">
              <Sparkles className="h-6 w-6" />
            </div>
            <div className="mt-4 text-4xl font-bold text-slate-900">
              {result.score}
            </div>
            <div className="mt-1 text-sm font-semibold text-slate-700">
              {result.label}
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              {result.summary}
            </p>
            <div className="mt-4 text-xs text-slate-500">
              {answeredCount} of {baselineQuestions.length} answered
              {isSavingGuidedProfile ? " · Saving" : ""}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>What to fix first</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            {result.urgentGaps.length === 0 ? (
              <div className="flex gap-3 rounded-md border border-emerald-200 bg-emerald-50 p-4">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    No urgent baseline gaps selected
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-700">
                    Move into the full assessment to produce the deeper roadmap,
                    evidence plan, and framework readiness report.
                  </p>
                </div>
              </div>
            ) : (
              result.urgentGaps.slice(0, 4).map((gap) => (
                <div
                  key={gap.id}
                  className="rounded-md border border-slate-200 bg-slate-50 p-4"
                >
                  <Badge variant="brand">{priorityLabels[gap.domain]}</Badge>
                  <h3 className="mt-2 text-sm font-semibold text-slate-900">
                    {gap.question}
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {gap.whyItMatters}
                  </p>
                </div>
              ))
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick scan questions</CardTitle>
          <p className="mt-1 text-sm text-slate-600">
            Choose the honest current state. The app turns weak or unknown
            answers into first roadmap priorities.
          </p>
        </CardHeader>
        <CardBody className="space-y-4">
          {baselineQuestions.map((question) => (
            <div
              key={question.id}
              className="rounded-md border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <div>
                  <Badge variant="neutral">{priorityLabels[question.domain]}</Badge>
                  <h3 className="mt-2 text-sm font-semibold text-slate-900">
                    {question.question}
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {question.whyItMatters}
                  </p>
                </div>
                <ShieldCheck className="hidden h-5 w-5 text-slate-300 md:block" />
              </div>
              <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {answerOptions.map((option) => {
                  const selected = answers[question.id] === option.value;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() =>
                        setAnswers((current) => ({
                          ...current,
                          [question.id]: option.value,
                        }))
                      }
                      className={cn(
                        "rounded-md border p-3 text-left transition-colors",
                        selected
                          ? "border-brand-500 bg-brand-50"
                          : "border-slate-200 bg-slate-50 hover:bg-white",
                      )}
                    >
                      <div className="flex items-center gap-2">
                        {selected && (
                          <CheckCircle2 className="h-4 w-4 text-brand-700" />
                        )}
                        <span className="text-sm font-semibold text-slate-900">
                          {option.label}
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-5 text-slate-600">
                        {option.description}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
            <Button variant="outline" onClick={() => navigate("/frameworks")}>
              Read guides
            </Button>
            <Button onClick={() => navigate("/roadmap")}>
              Open roadmap
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </CardBody>
      </Card>
    </>
  );
}
