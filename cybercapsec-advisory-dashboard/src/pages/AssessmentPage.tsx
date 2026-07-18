import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle, Clock, Save, ShieldCheck } from "lucide-react";

import { Button } from "@/components/Button";
import { Input, Select, Textarea } from "@/components/Field";
import { PageHeader } from "@/components/PageHeader";
import {
  Badge,
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  CardTitle,
  ErrorMessage,
  LoadingPage,
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import {
  useAssessment,
  useAssessments,
  useCreateAssessment,
  useQuestionnaire,
  useSaveResponses,
  useSubmitAssessment,
} from "@/hooks/useAssessments";
import type {
  QuestionnaireQuestion,
  QuestionnaireSection,
} from "@/types/api";

function sectionOutcome(section: QuestionnaireSection): string {
  const key = `${section.id} ${section.title}`.toLowerCase();
  if (key.includes("access") || key.includes("identity")) {
    return "Helps find account takeover, privilege, and offboarding risk.";
  }
  if (key.includes("data") || key.includes("privacy")) {
    return "Helps prioritize data protection, retention, and customer trust controls.";
  }
  if (key.includes("incident") || key.includes("response")) {
    return "Checks whether your team can detect, escalate, contain, and recover.";
  }
  if (key.includes("vendor") || key.includes("third")) {
    return "Surfaces supplier, SaaS, and shared-access risk in your environment.";
  }
  if (key.includes("cloud") || key.includes("infrastructure")) {
    return "Reviews production exposure, resilience, logging, and recovery foundations.";
  }
  if (key.includes("application") || key.includes("development")) {
    return "Connects engineering practices to vulnerabilities and release risk.";
  }
  return "Turns this domain into risks, roadmap tasks, evidence needs, and report language.";
}

// ----- Question rendering ----------------------------------------------------

function isQuestionVisible(
  q: QuestionnaireQuestion,
  responses: Record<string, unknown>,
): boolean {
  if (!q.depends_on_question_id) return true;
  const parent = responses[q.depends_on_question_id];
  if (parent == null) return false;
  if (Array.isArray(parent)) {
    return parent.some((v) => q.depends_on_values.includes(String(v)));
  }
  return q.depends_on_values.includes(String(parent));
}

function QuestionField({
  question,
  value,
  onChange,
}: {
  question: QuestionnaireQuestion;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const label = (
    <div>
      <div className="text-sm font-medium text-slate-900">
        {question.text}
        {question.required && <span className="text-red-500 ml-1">*</span>}
      </div>
      {question.help_text && (
        <p className="text-xs text-slate-500 mt-0.5">{question.help_text}</p>
      )}
    </div>
  );

  if (question.type === "boolean") {
    return (
      <div className="space-y-2">
        {label}
        <div className="flex gap-2">
          <Button
            type="button"
            variant={value === true ? "primary" : "outline"}
            size="sm"
            onClick={() => onChange(true)}
          >
            Yes
          </Button>
          <Button
            type="button"
            variant={value === false ? "primary" : "outline"}
            size="sm"
            onClick={() => onChange(false)}
          >
            No
          </Button>
        </div>
      </div>
    );
  }

  if (question.type === "single_select") {
    return (
      <div className="space-y-2">
        {label}
        <div className="space-y-1">
          {question.options.map((opt) => (
            <label
              key={opt.value}
              className={
                "flex items-start gap-3 p-3 rounded-md border cursor-pointer transition-colors " +
                (value === opt.value
                  ? "border-brand-500 bg-brand-50"
                  : "border-slate-200 hover:bg-slate-50")
              }
            >
              <input
                type="radio"
                name={question.id}
                checked={value === opt.value}
                onChange={() => onChange(opt.value)}
                className="mt-1 h-4 w-4 accent-brand-600"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-slate-900">
                  {opt.label}
                </div>
                {opt.description && (
                  <div className="text-xs text-slate-500 mt-0.5">
                    {opt.description}
                  </div>
                )}
              </div>
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (question.type === "multi_select") {
    const arr = Array.isArray(value) ? (value as string[]) : [];
    const toggle = (v: string) => {
      onChange(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);
    };
    return (
      <div className="space-y-2">
        {label}
        <div className="space-y-1">
          {question.options.map((opt) => (
            <label
              key={opt.value}
              className={
                "flex items-start gap-3 p-3 rounded-md border cursor-pointer transition-colors " +
                (arr.includes(opt.value)
                  ? "border-brand-500 bg-brand-50"
                  : "border-slate-200 hover:bg-slate-50")
              }
            >
              <input
                type="checkbox"
                checked={arr.includes(opt.value)}
                onChange={() => toggle(opt.value)}
                className="mt-1 h-4 w-4 accent-brand-600"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-slate-900">
                  {opt.label}
                </div>
                {opt.description && (
                  <div className="text-xs text-slate-500 mt-0.5">
                    {opt.description}
                  </div>
                )}
              </div>
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (question.type === "text") {
    return (
      <Textarea
        label={question.text}
        hint={question.help_text ?? undefined}
        required={question.required}
        value={typeof value === "string" ? value : ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }

  if (question.type === "number") {
    return (
      <Input
        label={question.text}
        type="number"
        hint={question.help_text ?? undefined}
        required={question.required}
        value={typeof value === "number" ? value : ""}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    );
  }

  if (question.type === "scale") {
    return (
      <Select
        label={question.text}
        hint={question.help_text ?? undefined}
        required={question.required}
        value={typeof value === "number" ? String(value) : ""}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        <option value="">Select…</option>
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </Select>
    );
  }

  return null;
}

// ----- Main page -------------------------------------------------------------

export function AssessmentPage() {
  const navigate = useNavigate();
  const { data: questionnaire, isLoading: qLoading } = useQuestionnaire();
  const { data: assessments, isLoading: aLoading } = useAssessments();
  const createAssessment = useCreateAssessment();

  const [activeId, setActiveId] = useState<string | null>(null);

  // Pick or create the working assessment
  useEffect(() => {
    if (!assessments || activeId) return;
    const draft = assessments.find(
      (a) => a.status === "draft" || a.status === "in_progress",
    );
    if (draft) {
      setActiveId(draft.id);
    } else if (!createAssessment.isPending) {
      createAssessment.mutate(undefined, {
        onSuccess: (a) => setActiveId(a.id),
      });
    }
  }, [assessments, activeId, createAssessment]);

  const { data: assessment } = useAssessment(activeId);
  const saveResponses = useSaveResponses(activeId ?? "");
  const submit = useSubmitAssessment(activeId ?? "");

  const [responses, setResponses] = useState<Record<string, unknown>>({});
  const [sectionIdx, setSectionIdx] = useState(0);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Hydrate local responses from the server when the assessment loads
  useEffect(() => {
    if (assessment?.responses) {
      setResponses(assessment.responses);
    }
  }, [assessment?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const visibleQuestions = useMemo(() => {
    if (!questionnaire) return new Set<string>();
    const set = new Set<string>();
    for (const section of questionnaire.sections) {
      for (const q of section.questions) {
        if (isQuestionVisible(q, responses)) set.add(q.id);
      }
    }
    return set;
  }, [questionnaire, responses]);

  const totalAnswered = useMemo(() => {
    let count = 0;
    for (const id of visibleQuestions) {
      const v = responses[id];
      if (v == null) continue;
      if (Array.isArray(v) && v.length === 0) continue;
      count++;
    }
    return count;
  }, [visibleQuestions, responses]);

  if (qLoading || aLoading || !questionnaire || !assessment) {
    return <LoadingPage />;
  }

  const sections = questionnaire.sections;
  const currentSection: QuestionnaireSection = sections[sectionIdx];
  const isLastSection = sectionIdx === sections.length - 1;
  const isFirstSection = sectionIdx === 0;

  const handleAnswer = (questionId: string, value: unknown) => {
    setResponses((r) => ({ ...r, [questionId]: value }));
  };

  const persistAndAdvance = async (advance: -1 | 0 | 1) => {
    setSubmitError(null);
    try {
      // Save only the visible-and-set subset
      const payload: Record<string, unknown> = {};
      for (const id of visibleQuestions) {
        if (responses[id] != null) payload[id] = responses[id];
      }
      if (Object.keys(payload).length > 0) {
        await saveResponses.mutateAsync(payload);
      }
      setSectionIdx((i) =>
        Math.max(0, Math.min(sections.length - 1, i + advance)),
      );
    } catch (err) {
      setSubmitError(normalizeApiError(err).message);
    }
  };

  const handleSubmit = async () => {
    setSubmitError(null);
    try {
      // Save first
      const payload: Record<string, unknown> = {};
      for (const id of visibleQuestions) {
        if (responses[id] != null) payload[id] = responses[id];
      }
      if (Object.keys(payload).length > 0) {
        await saveResponses.mutateAsync(payload);
      }
      const result = await submit.mutateAsync();
      navigate(`/reports/${result.report_id}`);
    } catch (err) {
      setSubmitError(normalizeApiError(err).message);
    }
  };

  const completionPct = visibleQuestions.size
    ? Math.round((totalAnswered / visibleQuestions.size) * 100)
    : 0;
  const remainingQuestions = Math.max(0, visibleQuestions.size - totalAnswered);
  const minutesRemaining = Math.max(2, Math.ceil(remainingQuestions * 0.6));

  return (
    <>
      <PageHeader
        title="Cybersecurity assessment"
        description={`${totalAnswered} of ${visibleQuestions.size} questions answered (${completionPct}%). Your answers create risks, roadmap tasks, evidence requests, policies, and compliance mapping.`}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        <Card>
          <CardBody className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-brand-700" />
            <div>
              <div className="text-sm font-semibold text-slate-900">
                About {minutesRemaining} min left
              </div>
              <div className="text-xs text-slate-500">
                Based on remaining visible questions
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="flex items-center gap-3">
            <Save className="h-5 w-5 text-brand-700" />
            <div>
              <div className="text-sm font-semibold text-slate-900">
                Progress is saved
              </div>
              <div className="text-xs text-slate-500">
                Answers save when you move between sections
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-brand-700" />
            <div>
              <div className="text-sm font-semibold text-slate-900">
                Security-first output
              </div>
              <div className="text-xs text-slate-500">
                Compliance mapping is included where relevant
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-600 transition-all"
            style={{ width: `${completionPct}%` }}
          />
        </div>
      </div>

      {/* Section nav */}
      <div className="flex flex-wrap gap-2 mb-4">
        {sections.map((s, i) => (
          <button
            key={s.id}
            type="button"
            onClick={() => void persistAndAdvance(0).then(() => setSectionIdx(i))}
            className={
              "text-xs font-medium px-3 py-1.5 rounded-full transition-colors " +
              (i === sectionIdx
                ? "bg-brand-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200")
            }
          >
            {i + 1}. {s.title}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle>{currentSection.title}</CardTitle>
              <p className="text-sm text-slate-600 mt-1">
                {sectionOutcome(currentSection)}
              </p>
            </div>
            <Badge variant="brand">
              Section {sectionIdx + 1} of {sections.length}
            </Badge>
          </div>
          {currentSection.description && (
            <p className="text-sm text-slate-600 mt-1">
              {currentSection.description}
            </p>
          )}
        </CardHeader>
        <CardBody className="space-y-6">
          {currentSection.questions
            .filter((q) => isQuestionVisible(q, responses))
            .map((q) => (
              <QuestionField
                key={q.id}
                question={q}
                value={responses[q.id]}
                onChange={(v) => handleAnswer(q.id, v)}
              />
            ))}

          {submitError && <ErrorMessage message={submitError} />}
        </CardBody>
        <CardFooter className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => void persistAndAdvance(-1)}
            disabled={isFirstSection || saveResponses.isPending}
          >
            <ArrowLeft className="h-4 w-4" /> Back
          </Button>

          {isLastSection ? (
            <Button
              onClick={handleSubmit}
              loading={submit.isPending || saveResponses.isPending}
            >
              <CheckCircle className="h-4 w-4" />
              Submit & generate report
            </Button>
          ) : (
            <Button
              onClick={() => void persistAndAdvance(1)}
              loading={saveResponses.isPending}
            >
              Next <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </CardFooter>
      </Card>
    </>
  );
}
