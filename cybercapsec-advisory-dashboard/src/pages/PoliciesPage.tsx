import { useNavigate } from "react-router-dom";
import { CheckCircle, FilePlus2, Send, ShieldCheck, Sparkles } from "lucide-react";

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
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import {
  usePolicies,
  useStarterPack,
} from "@/hooks/usePolicies";
import type { PolicyStatus } from "@/types/api";

const STATUS_VARIANT: Record<PolicyStatus, "neutral" | "success" | "warning"> =
  {
    draft: "warning",
    published: "success",
    archived: "neutral",
  };

export function PoliciesPage() {
  const navigate = useNavigate();
  const { data: policies, isLoading, error } = usePolicies();
  const starterPack = useStarterPack();

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorMessage message={normalizeApiError(error).message} />;

  const drafts = policies?.filter((p) => p.status === "draft") ?? [];
  const published = policies?.filter((p) => p.status === "published") ?? [];
  const archived = policies?.filter((p) => p.status === "archived") ?? [];
  const nextDraft = drafts[0];

  return (
    <>
      <PageHeader
        title="Policies"
        description="Generate, publish, and acknowledge security policies tailored to your company."
        action={
          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={() => starterPack.mutate()}
              loading={starterPack.isPending}
              disabled={(policies?.length ?? 0) > 0}
            >
              <Sparkles className="h-4 w-4" />
              Generate starter pack
            </Button>
          </div>
        }
      />

      <Card className="mb-6 border-brand-200 bg-brand-50/40">
        <CardBody className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-brand-800">
              <ShieldCheck className="h-4 w-4" />
              Security governance flow
            </div>
            <h2 className="mt-1 text-xl font-semibold text-slate-900">
              Turn roadmap gaps into approved team rules
            </h2>
            <p className="mt-1 text-sm leading-6 text-slate-700">
              Policies support cybersecurity operations: access control,
              incident response, vendor risk, backups, change management,
              acceptable use, data protection, and awareness. Compliance
              mappings are included where they help prove the work.
            </p>
          </div>
          <div className="rounded-md border border-slate-200 bg-white p-3">
            <div className="text-sm font-semibold text-slate-900">
              Next policy action
            </div>
            {!policies?.length ? (
              <>
                <p className="mt-1 text-sm text-slate-600">
                  Generate the starter pack, then review and publish.
                </p>
                <Button
                  className="mt-3 w-full"
                  size="sm"
                  onClick={() => starterPack.mutate()}
                  loading={starterPack.isPending}
                >
                  <Sparkles className="h-4 w-4" />
                  Generate pack
                </Button>
              </>
            ) : nextDraft ? (
              <>
                <p className="mt-1 text-sm text-slate-600">
                  Review and publish {nextDraft.title}.
                </p>
                <Button
                  className="mt-3 w-full"
                  size="sm"
                  onClick={() => navigate(`/policies/${nextDraft.id}`)}
                >
                  <Send className="h-4 w-4" />
                  Review draft
                </Button>
              </>
            ) : (
              <>
                <p className="mt-1 text-sm text-slate-600">
                  Published policies are ready for team acknowledgement.
                </p>
                <Button
                  className="mt-3 w-full"
                  size="sm"
                  variant="outline"
                  onClick={() => navigate("/team")}
                >
                  <CheckCircle className="h-4 w-4" />
                  Invite team
                </Button>
              </>
            )}
          </div>
        </CardBody>
      </Card>

      {!policies?.length ? (
        <Card>
          <CardBody>
            <EmptyState
              icon={<FilePlus2 className="h-12 w-12" />}
              title="No policies yet"
              description="Generate the starter pack to create 10 draft policies covering SOC 2, NDPA, CBN, and PCI DSS essentials."
              action={
                <Button
                  onClick={() => starterPack.mutate()}
                  loading={starterPack.isPending}
                  size="lg"
                >
                  Generate starter pack
                </Button>
              }
            />
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-6">
          {drafts.length > 0 && (
            <PolicyGroup
              title="Drafts"
              hint="Review, edit, and publish to make active."
              policies={drafts}
              onSelect={(id) => navigate(`/policies/${id}`)}
            />
          )}
          {published.length > 0 && (
            <PolicyGroup
              title="Published"
              policies={published}
              onSelect={(id) => navigate(`/policies/${id}`)}
            />
          )}
          {archived.length > 0 && (
            <PolicyGroup
              title="Archived"
              policies={archived}
              onSelect={(id) => navigate(`/policies/${id}`)}
            />
          )}
        </div>
      )}
    </>
  );
}

function PolicyGroup({
  title,
  hint,
  policies,
  onSelect,
}: {
  title: string;
  hint?: string;
  policies: NonNullable<ReturnType<typeof usePolicies>["data"]>;
  onSelect: (id: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {hint && <p className="text-sm text-slate-500 mt-1">{hint}</p>}
      </CardHeader>
      <CardBody className="-mx-5 -my-4 divide-y divide-slate-100">
        {policies.map((p) => (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            className="w-full text-left px-5 py-3 hover:bg-slate-50 transition-colors flex items-start justify-between gap-4"
          >
            <div className="flex-1 min-w-0">
              <div className="font-medium text-slate-900">{p.title}</div>
              <div className="flex flex-wrap gap-1 mt-1">
                {p.framework_codes.map((fw) => (
                  <Badge key={fw} variant="neutral">
                    {fw}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <Badge variant="neutral">v{p.version}</Badge>
              <Badge variant={STATUS_VARIANT[p.status]}>{p.status}</Badge>
            </div>
          </button>
        ))}
      </CardBody>
    </Card>
  );
}
