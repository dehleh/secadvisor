import { useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Archive, Check, Send } from "lucide-react";
import ReactMarkdown from "react-markdown";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  ErrorMessage,
  LoadingPage,
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import {
  useAcknowledgePolicy,
  useArchivePolicy,
  usePolicy,
  usePolicyAcknowledgments,
  usePublishPolicy,
} from "@/hooks/usePolicies";

export function PolicyDetailPage() {
  const navigate = useNavigate();
  const { policyId = "" } = useParams<{ policyId: string }>();
  const { data: policy, isLoading, error } = usePolicy(policyId);
  const { data: acks } = usePolicyAcknowledgments(policyId);

  const publish = usePublishPolicy();
  const archive = useArchivePolicy();
  const ack = useAcknowledgePolicy();

  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) return <LoadingPage />;
  if (error || !policy) {
    return (
      <ErrorMessage
        message={normalizeApiError(error ?? new Error("Not found")).message}
      />
    );
  }

  const handlePublish = async () => {
    setActionError(null);
    try {
      await publish.mutateAsync(policy.id);
    } catch (err) {
      setActionError(normalizeApiError(err).message);
    }
  };

  const handleArchive = async () => {
    setActionError(null);
    try {
      await archive.mutateAsync(policy.id);
    } catch (err) {
      setActionError(normalizeApiError(err).message);
    }
  };

  const handleAck = async () => {
    setActionError(null);
    try {
      await ack.mutateAsync({
        id: policy.id,
        acknowledged_text: "I have read and understood this policy.",
      });
    } catch (err) {
      setActionError(normalizeApiError(err).message);
    }
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="mb-4"
        onClick={() => navigate("/policies")}
      >
        <ArrowLeft className="h-4 w-4" /> Back to policies
      </Button>

      <PageHeader
        title={policy.title}
        description={`Version ${policy.version} · ${policy.template_code}`}
        action={
          <div className="flex gap-2">
            {policy.status === "draft" && (
              <Button onClick={handlePublish} loading={publish.isPending}>
                <Send className="h-4 w-4" />
                Publish
              </Button>
            )}
            {policy.status === "published" && (
              <>
                <Button
                  variant="outline"
                  onClick={handleAck}
                  loading={ack.isPending}
                >
                  <Check className="h-4 w-4" />
                  Acknowledge
                </Button>
                <Button
                  variant="outline"
                  onClick={handleArchive}
                  loading={archive.isPending}
                >
                  <Archive className="h-4 w-4" />
                  Archive
                </Button>
              </>
            )}
          </div>
        }
      />

      <div className="flex flex-wrap items-center gap-2 mb-6">
        <Badge
          variant={
            policy.status === "published"
              ? "success"
              : policy.status === "draft"
                ? "warning"
                : "neutral"
          }
        >
          {policy.status}
        </Badge>
        {policy.framework_codes.map((fw) => (
          <Badge key={fw} variant="brand">
            {fw}
          </Badge>
        ))}
        {policy.control_refs.map((c, i) => (
          <Badge key={i} variant="neutral">
            {c.framework} {c.code}
          </Badge>
        ))}
      </div>

      {actionError && (
        <div className="mb-4">
          <ErrorMessage message={actionError} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardBody className="prose prose-slate max-w-none prose-headings:font-semibold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
            <ReactMarkdown>{policy.content}</ReactMarkdown>
          </CardBody>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Acknowledgments</CardTitle>
            </CardHeader>
            <CardBody>
              {!acks?.length ? (
                <p className="text-sm text-slate-500">
                  {policy.status === "published"
                    ? "No acknowledgments yet."
                    : "Publish to enable acknowledgments."}
                </p>
              ) : (
                <ul className="space-y-2">
                  {acks.map((a) => (
                    <li
                      key={a.id}
                      className="text-sm text-slate-700 flex items-center justify-between"
                    >
                      <span className="font-mono text-xs text-slate-500">
                        {a.user_id.slice(0, 8)}…
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(a.created_at).toLocaleDateString()}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Variables used</CardTitle>
            </CardHeader>
            <CardBody className="space-y-2">
              {Object.entries(policy.rendered_variables).map(([k, v]) => (
                <div key={k} className="text-xs">
                  <span className="font-mono text-slate-500">{k}:</span>{" "}
                  <span className="text-slate-700">{String(v)}</span>
                </div>
              ))}
            </CardBody>
          </Card>
        </div>
      </div>
    </>
  );
}
