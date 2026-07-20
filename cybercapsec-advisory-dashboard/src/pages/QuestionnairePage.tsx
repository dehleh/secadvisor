import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  FileCheck2,
  ListChecks,
  MessageSquareText,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/Button";
import { Textarea } from "@/components/Field";
import { PageHeader } from "@/components/PageHeader";
import { Badge, Card, CardBody, CardHeader, CardTitle } from "@/components/UI";
import { useAuth } from "@/context/AuthContext";
import { useEvidenceList } from "@/hooks/useEvidence";
import {
  useGuidedReadiness,
  useSaveGuidedReadiness,
} from "@/hooks/useGuidedReadiness";
import { useRoadmapItems } from "@/hooks/useRoadmap";
import {
  draftQuestionnaireAnswer,
  questionnaireSamples,
} from "@/lib/guidedReadiness";
import {
  getDefaultFrameworkGuide,
  getFrameworkGuide,
} from "@/lib/frameworkReadiness";
import { getSecurityProgramProfile } from "@/lib/securityProgram";

function keywordMatch(text: string, query: string) {
  const words = query
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((word) => word.length > 3);
  const lower = text.toLowerCase();
  return words.some((word) => lower.includes(word));
}

export function QuestionnairePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const profile = getSecurityProgramProfile(user?.company_id);
  const { data: guidedProfile } = useGuidedReadiness();
  const saveGuidedReadiness = useSaveGuidedReadiness();
  const { data: roadmapItems } = useRoadmapItems();
  const { data: evidence } = useEvidenceList();
  const [question, setQuestion] = useState(questionnaireSamples[0]);

  const guide =
    getFrameworkGuide(guidedProfile?.target_framework) ??
    getDefaultFrameworkGuide(profile?.targetFrameworks);
  const draft = draftQuestionnaireAnswer(question, guide);

  const relatedTasks = useMemo(
    () =>
      (roadmapItems ?? [])
        .filter((item) => keywordMatch(`${item.title} ${item.description}`, question))
        .slice(0, 4),
    [question, roadmapItems],
  );

  const evidenceMatches = useMemo(
    () =>
      (evidence ?? []).filter((item) =>
        draft.evidence.some((expected) =>
          keywordMatch(`${item.title} ${item.description ?? ""}`, expected),
        ),
      ),
    [draft.evidence, evidence],
  );

  const confidence = Math.min(
    95,
    45 + evidenceMatches.length * 15 + relatedTasks.length * 8,
  );

  const saveDraft = async () => {
    const existingDrafts = guidedProfile?.questionnaire_drafts ?? [];
    await saveGuidedReadiness.mutateAsync({
      selected_goal: guidedProfile?.selected_goal ?? "customer_questionnaire",
      target_framework: guide.key,
      questionnaire_drafts: [
        ...existingDrafts,
        {
          question,
          answer: draft.answer,
          evidence: draft.evidence,
          framework: guide.key,
          confidence,
          created_at: new Date().toISOString(),
        },
      ],
    });
  };

  return (
    <>
      <PageHeader
        title="Security questionnaire assistant"
        description="Paste a customer-security question and draft an answer from your readiness path, evidence expectations, and roadmap."
        action={
          <Button variant="outline" onClick={() => navigate("/frameworks")}>
            Read framework guide
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Paste the question</CardTitle>
              <p className="mt-1 text-sm text-slate-600">
                Try one of the sample questions or paste the exact text from a
                customer questionnaire.
              </p>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {questionnaireSamples.map((sample) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => setQuestion(sample)}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    {sample}
                  </button>
                ))}
              </div>
              <Textarea
                label="Customer question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="min-h-32"
              />
            </CardBody>
          </Card>

          <Card className="border-brand-200 bg-brand-50/40">
            <CardHeader>
              <div className="flex items-center gap-2 text-sm font-semibold text-brand-800">
                <MessageSquareText className="h-4 w-4" />
                Suggested answer
              </div>
            </CardHeader>
            <CardBody className="space-y-4">
              <p className="text-sm leading-6 text-slate-700">{draft.answer}</p>
              <div className="flex flex-wrap gap-2">
                {draft.evidence.map((item) => (
                  <Badge key={item} variant="brand">
                    {item}
                  </Badge>
                ))}
              </div>
              <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                <Button variant="outline" onClick={() => navigate("/evidence")}>
                  Add evidence
                </Button>
                <Button
                  onClick={() => void saveDraft()}
                  loading={saveGuidedReadiness.isPending}
                >
                  Save draft
                </Button>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Evidence and roadmap support</CardTitle>
            </CardHeader>
            <CardBody className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Evidence found
                </h3>
                <div className="mt-3 space-y-2">
                  {evidenceMatches.length > 0 ? (
                    evidenceMatches.slice(0, 4).map((item) => (
                      <div
                        key={item.id}
                        className="rounded-md border border-slate-200 bg-white p-3"
                      >
                        <div className="text-sm font-medium text-slate-900">
                          {item.title}
                        </div>
                        <Badge className="mt-2" variant="success">
                          {item.framework_code} {item.control_code}
                        </Badge>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
                      <p className="text-sm leading-6 text-slate-700">
                        No matching evidence yet. Add the suggested evidence
                        before sending this answer externally.
                      </p>
                    </div>
                  )}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Related roadmap tasks
                </h3>
                <div className="mt-3 space-y-2">
                  {relatedTasks.length > 0 ? (
                    relatedTasks.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => navigate("/roadmap")}
                        className="w-full rounded-md border border-slate-200 bg-white p-3 text-left hover:bg-slate-50"
                      >
                        <Badge variant="neutral">Week {item.week_target}</Badge>
                        <div className="mt-2 text-sm font-medium text-slate-900">
                          {item.title}
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                      <p className="text-sm leading-6 text-slate-600">
                        No matching roadmap item yet. Run an assessment or
                        create evidence to strengthen this answer.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Answer confidence</CardTitle>
            </CardHeader>
            <CardBody>
              <div className="text-4xl font-bold text-slate-900">
                {confidence}%
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Confidence rises when the answer is supported by current
                evidence and completed roadmap work.
              </p>
              <div className="mt-4 space-y-2">
                <div className="flex items-center gap-2 text-sm text-slate-700">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Framework context: {guide.shortName}
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-700">
                  <FileCheck2 className="h-4 w-4 text-emerald-600" />
                  Evidence matches: {evidenceMatches.length}
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-700">
                  <ListChecks className="h-4 w-4 text-emerald-600" />
                  Related tasks: {relatedTasks.length}
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Next best actions</CardTitle>
            </CardHeader>
            <CardBody className="space-y-3">
              <Button className="w-full justify-between" onClick={() => navigate("/evidence")}>
                Add missing evidence
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                className="w-full justify-between"
                variant="outline"
                onClick={() => navigate("/reports")}
              >
                Open posture report
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                className="w-full justify-between"
                variant="outline"
                onClick={() => navigate("/quick-baseline")}
              >
                Run quick baseline
                <Sparkles className="h-4 w-4" />
              </Button>
            </CardBody>
          </Card>
        </div>
      </div>
    </>
  );
}
