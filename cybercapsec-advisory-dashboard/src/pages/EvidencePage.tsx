import { type FormEvent, useState } from "react";
import { ExternalLink, FilePlus2, Plus, ShieldCheck } from "lucide-react";

import { Button } from "@/components/Button";
import { Input, Select, Textarea } from "@/components/Field";
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
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import { asTierLimitError, UpgradePrompt } from "@/components/UpgradePrompt";
import {
  useCoverageMatrix,
  useCreateEvidence,
  useEvidenceList,
} from "@/hooks/useEvidence";
import { useRoadmapItems } from "@/hooks/useRoadmap";
import type {
  Evidence,
  EvidenceKind,
  PropagatedControl,
  RoadmapItem,
  TierLimitError,
} from "@/types/api";
import { evidenceExamples } from "@/lib/guidedReadiness";

const FRAMEWORKS = [
  { value: "soc2", label: "SOC 2" },
  { value: "ndpa", label: "NDPA" },
  { value: "cbn_cyber", label: "CBN Cybersecurity" },
  { value: "ndpr", label: "NDPR" },
  { value: "popia", label: "POPIA" },
  { value: "kenya_dpa", label: "Kenya DPA" },
  { value: "ghana_dpa", label: "Ghana DPA" },
  { value: "iso27001", label: "ISO 27001" },
  { value: "nist_csf", label: "NIST CSF" },
  { value: "cis_controls", label: "CIS Controls" },
  { value: "gdpr", label: "GDPR" },
  { value: "hipaa", label: "HIPAA" },
  { value: "pci_dss", label: "PCI DSS" },
];

const KINDS: Array<{ value: EvidenceKind; label: string }> = [
  { value: "external_link", label: "External link (Notion, GDrive, GitHub)" },
  { value: "policy_ref", label: "Internal policy reference" },
  { value: "screenshot_url", label: "Screenshot URL" },
  { value: "narrative", label: "Narrative description" },
];

const FRAMEWORK_LABEL_TO_CODE: Record<string, string> = {
  "SOC 2": "soc2",
  "ISO 27001": "iso27001",
  "NIST CSF": "nist_csf",
  "CIS Controls": "cis_controls",
  "PCI DSS": "pci_dss",
  NDPA: "ndpa",
  GDPR: "gdpr",
  CBN: "cbn_cyber",
  HIPAA: "hipaa",
};

interface SubmittedEvidence {
  evidence: Evidence;
  propagated: PropagatedControl[];
}

interface EvidenceFormSeed {
  title?: string;
  description?: string;
  kind?: EvidenceKind;
  framework_code?: string;
  control_code?: string;
  external_url?: string;
  narrative_text?: string;
}

function EvidenceForm({
  onClose,
  onSuccess,
  initial,
}: {
  onClose: () => void;
  onSuccess: (result: SubmittedEvidence) => void;
  initial?: EvidenceFormSeed | null;
}) {
  const create = useCreateEvidence();
  const [error, setError] = useState<string | null>(null);
  const [tierLimit, setTierLimit] = useState<TierLimitError | null>(null);

  const [form, setForm] = useState<{
    title: string;
    description: string;
    kind: EvidenceKind;
    framework_code: string;
    control_code: string;
    external_url: string;
    narrative_text: string;
  }>({
    title: initial?.title ?? "",
    description: initial?.description ?? "",
    kind: initial?.kind ?? "external_link",
    framework_code: initial?.framework_code ?? "soc2",
    control_code: initial?.control_code ?? "",
    external_url: initial?.external_url ?? "",
    narrative_text: initial?.narrative_text ?? "",
  });

  const update = <K extends keyof typeof form>(
    key: K,
    value: (typeof form)[K],
  ) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const result = await create.mutateAsync({
        title: form.title,
        description: form.description || null,
        kind: form.kind,
        framework_code: form.framework_code,
        control_code: form.control_code,
        external_url:
          form.kind === "external_link" || form.kind === "screenshot_url"
            ? form.external_url
            : null,
        narrative_text: form.kind === "narrative" ? form.narrative_text : null,
      });
      onSuccess({
        evidence: result.evidence,
        propagated: result.propagated_controls,
      });
    } catch (err) {
      const tierErr = asTierLimitError(normalizeApiError(err));
      if (tierErr) {
        setTierLimit(tierErr);
        setError(null);
      } else {
        setError(normalizeApiError(err).message);
        setTierLimit(null);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto">
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Submit evidence</CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            {tierLimit && <UpgradePrompt error={tierLimit} />}
            {error && <ErrorMessage message={error} />}

            <Input
              label="Title"
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              required
              placeholder="MFA enforced on GitHub org"
            />

            <Textarea
              label="Description"
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              hint="Optional context for reviewers."
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Framework"
                value={form.framework_code}
                onChange={(e) => update("framework_code", e.target.value)}
                required
              >
                {FRAMEWORKS.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </Select>
              <Input
                label="Control code"
                value={form.control_code}
                onChange={(e) => update("control_code", e.target.value)}
                required
                placeholder="CC6.1, SEC_24, 4.2"
              />
            </div>

            <Select
              label="Evidence kind"
              value={form.kind}
              onChange={(e) =>
                update("kind", e.target.value as EvidenceKind)
              }
              required
            >
              {KINDS.map((k) => (
                <option key={k.value} value={k.value}>
                  {k.label}
                </option>
              ))}
            </Select>

            {(form.kind === "external_link" ||
              form.kind === "screenshot_url") && (
              <Input
                label="URL"
                type="url"
                value={form.external_url}
                onChange={(e) => update("external_url", e.target.value)}
                required
                placeholder="https://..."
              />
            )}

            {form.kind === "narrative" && (
              <Textarea
                label="Narrative"
                value={form.narrative_text}
                onChange={(e) => update("narrative_text", e.target.value)}
                required
                hint="Describe the control implementation in your own words."
                className="min-h-[120px]"
              />
            )}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Submit evidence
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}

function buildEvidenceRecommendations(items: RoadmapItem[] = []) {
  const seen = new Set<string>();
  const recs: Array<{
    key: string;
    title: string;
    description: string;
    framework: string;
    control: string;
    week: number;
    seed: EvidenceFormSeed;
  }> = [];

  for (const item of items) {
    if (item.status === "done" || item.status === "cancelled") continue;
    for (const citation of item.framework_citations) {
      const key = `${citation.framework}:${citation.control_code}`;
      if (seen.has(key)) continue;
      seen.add(key);
      recs.push({
        key,
        title: item.title,
        description: item.description,
        framework: citation.framework,
        control: citation.control_code,
        week: item.week_target,
        seed: {
          title: `Evidence for ${item.title}`,
          description: `Supports roadmap task: ${item.title}`,
          kind: "external_link",
          framework_code: citation.framework,
          control_code: citation.control_code,
        },
      });
    }
  }

  return recs.slice(0, 6);
}

function PropagationToast({
  result,
  onClose,
}: {
  result: SubmittedEvidence;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Evidence saved</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          <p className="text-sm text-slate-700">
            <span className="font-medium">{result.evidence.title}</span> is
            anchored at{" "}
            <Badge variant="brand">
              {result.evidence.framework_code} {result.evidence.control_code}
            </Badge>
            .
          </p>
          {result.propagated.length > 0 && (
            <div>
              <p className="text-sm font-medium text-slate-900 mb-2">
                Also satisfies:
              </p>
              <ul className="space-y-1">
                {result.propagated.map((p, i) => (
                  <li key={i} className="text-sm flex items-center gap-2">
                    <Badge variant="neutral">
                      {p.framework_code} {p.control_code}
                    </Badge>
                    <span className="text-xs text-slate-500">
                      ({p.strength})
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex justify-end pt-2">
            <Button onClick={onClose}>Done</Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

export function EvidencePage() {
  const { data: evidence, isLoading, error } = useEvidenceList();
  const { data: coverage } = useCoverageMatrix();
  const { data: roadmapItems } = useRoadmapItems();
  const [showForm, setShowForm] = useState(false);
  const [submitted, setSubmitted] = useState<SubmittedEvidence | null>(null);
  const [prefill, setPrefill] = useState<EvidenceFormSeed | null>(null);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorMessage message={normalizeApiError(error).message} />;

  const recommendations = buildEvidenceRecommendations(roadmapItems);

  return (
    <>
      <PageHeader
        title="Evidence"
        description="Attach evidence to controls. One piece of evidence often satisfies multiple frameworks."
        action={
          <Button
            onClick={() => {
              setPrefill(null);
              setShowForm(true);
            }}
          >
            <Plus className="h-4 w-4" />
            Submit evidence
          </Button>
        }
      />

      {recommendations.length > 0 && (
        <Card className="mb-6 border-brand-200 bg-brand-50/40">
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-brand-700" />
              <CardTitle>Recommended evidence</CardTitle>
            </div>
            <p className="text-sm text-slate-600 mt-1">
              Start with evidence tied to open roadmap work. One upload can
              improve several cybersecurity and compliance controls.
            </p>
          </CardHeader>
          <CardBody className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {recommendations.map((rec) => (
              <button
                key={rec.key}
                type="button"
                onClick={() => {
                  setPrefill(rec.seed);
                  setShowForm(true);
                }}
                className="rounded-md border border-slate-200 bg-white p-3 text-left transition-colors hover:border-brand-300 hover:bg-white"
              >
                <div className="mb-2 flex flex-wrap items-center gap-1">
                  <Badge variant="brand">
                    {rec.framework} {rec.control}
                  </Badge>
                  <Badge variant="neutral">Week {rec.week}</Badge>
                </div>
                <div className="text-sm font-medium text-slate-900">
                  {rec.title}
                </div>
                <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-600">
                  {rec.description}
                </p>
              </button>
            ))}
          </CardBody>
        </Card>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Evidence examples</CardTitle>
          <p className="mt-1 text-sm text-slate-600">
            Use these examples when a founder asks, "what should I upload for
            PCI DSS, SOC 2, ISO 27001, or general security readiness?"
          </p>
        </CardHeader>
        <CardBody className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          {evidenceExamples.map((example) => {
            const frameworkCode =
              FRAMEWORK_LABEL_TO_CODE[example.frameworks[0]] ?? "soc2";
            return (
              <button
                key={example.title}
                type="button"
                onClick={() => {
                  setPrefill({
                    title: example.title,
                    description: example.description,
                    kind: "narrative",
                    framework_code: frameworkCode,
                    control_code: "TBD",
                    narrative_text: example.description,
                  });
                  setShowForm(true);
                }}
                className="rounded-md border border-slate-200 bg-white p-3 text-left transition-colors hover:border-brand-300 hover:bg-slate-50"
              >
                <div className="text-sm font-semibold text-slate-900">
                  {example.title}
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-600">
                  {example.description}
                </p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {example.frameworks.slice(0, 2).map((framework) => (
                    <Badge key={framework} variant="neutral">
                      {framework}
                    </Badge>
                  ))}
                </div>
              </button>
            );
          })}
        </CardBody>
      </Card>

      {/* Coverage matrix */}
      {coverage?.coverage && Object.keys(coverage.coverage).length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Coverage by framework</CardTitle>
            <p className="text-sm text-slate-500 mt-1">
              Includes propagated coverage via cross-framework mappings.
            </p>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {Object.entries(coverage.coverage).map(([fw, ctrls]) => (
                <div
                  key={fw}
                  className="p-3 rounded-md border border-slate-200 bg-slate-50"
                >
                  <div className="text-xs font-semibold text-slate-700 uppercase mb-1">
                    {fw}
                  </div>
                  <div className="text-2xl font-bold text-slate-900">
                    {ctrls.length}
                  </div>
                  <div className="text-xs text-slate-500">controls covered</div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Evidence list */}
      {!evidence?.length ? (
        <Card>
          <CardBody>
            <EmptyState
              icon={<FilePlus2 className="h-12 w-12" />}
              title="No evidence yet"
              description="Submit your first piece of evidence to start building your compliance case."
              action={
                <Button onClick={() => setShowForm(true)} size="lg">
                  Submit evidence
                </Button>
              }
            />
          </CardBody>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>All evidence ({evidence.length})</CardTitle>
          </CardHeader>
          <CardBody className="-mx-5 -my-4 divide-y divide-slate-100">
            {evidence.map((e) => (
              <div key={e.id} className="px-5 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-slate-900">{e.title}</div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      <Badge variant="brand">
                        {e.framework_code} {e.control_code}
                      </Badge>
                      <Badge variant="neutral">
                        {e.kind.replace("_", " ")}
                      </Badge>
                      <Badge
                        variant={e.status === "active" ? "success" : "neutral"}
                      >
                        {e.status}
                      </Badge>
                    </div>
                    {e.description && (
                      <p className="text-sm text-slate-600 mt-1">
                        {e.description}
                      </p>
                    )}
                  </div>
                  {e.external_url && (
                    <a
                      href={e.external_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand-600 hover:text-brand-700 text-sm font-medium flex items-center gap-1 flex-shrink-0"
                    >
                      Open <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      {showForm && (
        <EvidenceForm
          initial={prefill}
          onClose={() => setShowForm(false)}
          onSuccess={(result) => {
            setShowForm(false);
            setPrefill(null);
            setSubmitted(result);
          }}
        />
      )}
      {submitted && (
        <PropagationToast
          result={submitted}
          onClose={() => setSubmitted(null)}
        />
      )}
    </>
  );
}
